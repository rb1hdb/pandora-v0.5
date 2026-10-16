import json
import socket
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import requests as _req
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from logger import init_logger
from llm_wrapper import chat, invalidate_tools_cache
from rag import ensure_indexed, reindex, diagnostico_rag, get_embeddings_diagnostico, embed_texto, invalidate_index, chunk_count

BASE_DIR      = Path(__file__).parent
CONFIG_PATH   = BASE_DIR / "config.json"
CATALOG_PATH  = BASE_DIR.parent / "mcp-server" / "catalog.json"
APP_PORT      = 55000  # sobrescrito em _preflight a partir do config


# ── Pré-flight ────────────────────────────────────────────────────────────────

def _preflight() -> None:
    """Verifica pré-condições antes de iniciar o servidor. Aborta em erros fatais."""
    erros: list[str] = []

    def erro(msg: str) -> None: erros.append(msg)

    cfg: dict = {}
    try:
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        profiles = sorted(p.name for p in (BASE_DIR / "providers").glob("config.json.*.json"))
        hint = "\n    Perfis disponíveis:\n" + "\n".join(f"      cp providers/{p} config.json" for p in profiles) if profiles else ""
        erro(f"config.json não encontrado em {CONFIG_PATH}\n    Copie um perfil de providers/ para ativá-lo:{hint}")
    except json.JSONDecodeError as e:
        erro(f"config.json inválido: {e}")

    global APP_PORT
    APP_PORT = cfg.get("app", {}).get("port", 55000)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("0.0.0.0", APP_PORT))
        except OSError:
            erro(f"Porta {APP_PORT} já está em uso — encerre o processo existente antes de reiniciar")

    logs_dir = BASE_DIR / "logs"
    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
        probe = logs_dir / ".write_probe"
        probe.touch()
        probe.unlink()
    except Exception as e:
        erro(f"logs/ não acessível: {e}")

    # Validação de defesas (JSONs externos)
    # Com bind mount ./:/app, as defesas estão em /app/app/config-defenses/
    # (caminho relativo ao BASE_DIR). Sem bind mount (venv), BASE_DIR
    # aponta para o app/ local, mesmo resultado.
    defenses_dir = BASE_DIR / "config-defenses"
    required = ["d1-injection.json", "d1-delimiters.json", "d1-secrets.json",
                "d2.json", "d3.json", "d4.json", "d5.json",
                "d6-html-escape.json", "d6-url-remove.json",
                "d6-pii-redact.json", "d6-creds-redact.json"]
    if not defenses_dir.exists():
        erro(f"Diretório de defesas não existe: {defenses_dir}")
    else:
        import json as _json
        for fname in required:
            fpath = defenses_dir / fname
            if not fpath.exists():
                erro(f"DEFESA INEXISTENTE: {fpath}")
                continue
            try:
                with open(fpath) as ff:
                    _json.load(ff)
            except _json.JSONDecodeError as e:
                erro(f"DEFESA INVÁLIDA (JSON malformado) em {fpath}: {e}")
        if not erros:
            print(f"[Pandora] PREFLIGHT OK: {len(required)} defesas validadas ({', '.join(required)})")

    if erros:
        print("[Pandora] Erros de inicialização — servidor não iniciado:", file=sys.stderr)
        for msg in erros:
            print(f"[Pandora]   ✗ {msg}", file=sys.stderr)
        sys.exit(1)


# ── Health check ─────────────────────────────────────────────────────────────

def _probe_url(url: str, timeout: int = 3, expect_status: tuple[int, ...] = (200, 204)) -> bool:
    """Testa conectividade com uma URL.

    Sucesso = resposta HTTP com código em `expect_status` (default: só 200/204).
    Considera DOWN: connection refused, timeout, ou status fora do esperado
    (404, 500, 503, etc.).
    """
    if not url:
        return False
    try:
        resp = _req.get(url.rstrip("/"), timeout=timeout)
        return resp.status_code in expect_status
    except Exception:
        return False


def _server_origin(url: str) -> str:
    """Extract scheme://host:port from a full URL for connectivity probes."""
    from urllib.parse import urlparse
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}" if p.scheme and p.netloc else url


def _run_health(cfg: dict) -> dict:
    """Checa todos os componentes e retorna status."""
    timeout = cfg.get("app", {}).get("preflight_ollama_timeout", 5)
    mcp_base = cfg.get("mcp", {}).get("base_url", "http://localhost:55001")
    llm_cfg      = cfg.get("llm", {})
    judge_cfg    = cfg.get("judge", {})
    rag_emb_cfg  = cfg.get("rag", {}).get("embedding", {})
    llm_url      = llm_cfg.get("url")     or llm_cfg.get("base_url", "")
    judge_url    = judge_cfg.get("url")   or judge_cfg.get("base_url", "")
    rag_url      = rag_emb_cfg.get("url") or rag_emb_cfg.get("base_url", "")

    mcp_health_url = mcp_base.rstrip("/") + "/health"
    return {
        "app": {"status": "ok"},
        "mcp": {
            "status": "ok" if _probe_url(mcp_health_url, timeout) else "down",
            "url": mcp_base,
        },
        "llm": {
            "status": "ok" if _probe_url(_server_origin(llm_url), timeout) else "down",
            "url": llm_url,
        },
        "judge": {
            "status": "ok" if _probe_url(_server_origin(judge_url), timeout) else "down",
            "url": judge_url,
        },
        "rag_embedding": {
            "status": "disabled" if not cfg.get("rag", {}).get("enabled", True)
                      else "ok" if _probe_url(_server_origin(rag_url), timeout) else "down",
            "url": rag_url,
            "chunks": chunk_count(),
        },
    }


# ── Banner de startup ────────────────────────────────────────────────────────

_G = "\033[32m"     # verde
_R = "\033[31m"     # vermelho
_Y = "\033[33m"     # amarelo
_B = "\033[1m"      # negrito
_0 = "\033[0m"      # reset


def _print_banner(health: dict) -> None:
    """Imprime o banner de startup com status dos componentes."""
    def _line(name: str, key: str) -> str:
        dots = "." * (19 - len(name))
        s = health[key]
        if s["status"] == "disabled":
            return f"  {_Y}–{_0} {name} {dots} desabilitado"
        if s["status"] == "ok":
            extra = ""
            if key == "rag_embedding" and s.get("chunks"):
                extra = f"  ({s['chunks']} chunks)"
            return f"  {_G}✓{_0} {name} {dots} OK{extra}"
        return f"  {_R}✗{_0} {name} {dots} não acessível"

    llm_keys = ("llm", "judge")
    any_llm_down = any(health[k]["status"] == "down" for k in llm_keys)
    rag_disabled = health["rag_embedding"]["status"] == "disabled"
    mcp_down = health["mcp"]["status"] == "down"

    lines = [
        "",
        f"{_B}════════════════════════════════════════════════════{_0}",
        f"  {_B}Pandora v0.5 running{_0}",
        "",
        _line("App", "app"),
        _line("MCP Vídeos", "mcp"),
        _line("LLM", "llm"),
        _line("Judge", "judge"),
        _line("RAG Embedding", "rag_embedding"),
    ]

    if mcp_down:
        lines.append("")
        lines.append(f"  {_R}Reinicialize o container: docker restart pandora{_0}")

    if any_llm_down:
        lines.append("")
        lines.append(f"  {_Y}Componentes sem conexão não funcionam.{_0}")
        lines.append(f"  {_Y}Configure na tela Admin ou veja o README.md{_0}")

    if rag_disabled:
        lines.append("")
        lines.append(f"  {_Y}RAG desabilitado — chat funciona sem documentos internos.{_0}")
        lines.append(f"  {_Y}Para habilitar: Admin > RAG > enabled=true > Reindexar{_0}")

    lines.extend([
        "",
        f"  Health: http://localhost:{APP_PORT}/health",
        f"  App:    http://localhost:{APP_PORT}",
        f"  Logs:   docker logs -f pandora",
        f"{_B}════════════════════════════════════════════════════{_0}",
        "",
    ])

    print("\n".join(lines))


# ── App ──────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_logger(BASE_DIR)
    except Exception as e:
        print(f"[Pandora] ✗ Logger falhou: {e}", file=sys.stderr)

    # FIX: pré-check do MCP no lifespan (garante que está UP antes do App subir)
    cfg = load_config()
    mcp_health_url = cfg.get("mcp", {}).get("base_url", "").rstrip("/") + "/health"
    if mcp_health_url:
        if not _probe_url(mcp_health_url, timeout=5):
            print(f"[Pandora] ✗ MCP não está UP em {mcp_health_url}", file=sys.stderr)
            print(f"[Pandora]   Inicie o MCP Server: cd 'mcp-server' && source ../.venv/bin/activate && python3 server.py", file=sys.stderr)
            sys.exit(1)

    try:
        ensure_indexed()
    except Exception as e:
        print(f"[Pandora] ✗ RAG — falha na indexação: {e}", file=sys.stderr)

    health = _run_health(cfg)
    _print_banner(health)
    yield


app = FastAPI(title="Pandora", lifespan=lifespan)


templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


# FIX: exception handler global — antes o FastAPI devolvia HTTP 500 com body genérico
# ("Internal Server Error") sem nenhuma info útil para diagnóstico. Agora loga o traceback
# completo em stderr e devolve mensagem legível ao frontend.
@app.exception_handler(Exception)
async def _global_exception_handler(request: Request, exc: Exception):
    import traceback as tb
    print(f"[Pandora] ✗ Exceção não tratada em {request.method} {request.url.path}: "
          f"{type(exc).__name__}: {exc}", file=sys.stderr)
    print(tb.format_exc(), file=sys.stderr)
    return JSONResponse(
        status_code=500,
        content={"error": f"{type(exc).__name__}: {exc}"},
    )


# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health_endpoint():
    """Status de todos os componentes (diagnóstico rápido)."""
    return _run_health(load_config())


# ── Páginas ──────────────────────────────────────────────────────────────────

@app.get("/", response_class=RedirectResponse)
def root():
    return RedirectResponse(url="/chat")


@app.get("/chat", response_class=HTMLResponse)
def chat_page(request: Request):
    return templates.TemplateResponse(request=request, name="chat.html")


@app.get("/cursos", response_class=HTMLResponse)
def cursos_page(request: Request):
    try:
        cursos = _load_catalog_published()
    except Exception:
        cursos = []
    return templates.TemplateResponse(request=request, name="cursos.html", context={"cursos": cursos})


@app.get("/help", response_class=HTMLResponse)
def help_page(request: Request):
    return templates.TemplateResponse(request=request, name="help.html")


@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    return templates.TemplateResponse(request=request, name="admin.html")



# ── API ───────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    history: list = []


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    return {"response": chat(req.message, req.history or None)}


@app.get("/api/config")
def api_get_config():
    return load_config()


@app.post("/api/config")
async def api_set_config(request: Request):
    data = await request.json()
    try:
        old = load_config()
    except Exception:
        old = {}
    save_config(data)

    invalidated: list[str] = []

    if data.get("rag", {}).get("embedding") != old.get("rag", {}).get("embedding"):
        invalidate_index()
        invalidated.append("rag_index")

    if data.get("mcp", {}).get("base_url") != old.get("mcp", {}).get("base_url"):
        invalidate_tools_cache()
        invalidated.append("mcp_tools")

    needs_restart: list[str] = []
    if data.get("app", {}).get("port") != old.get("app", {}).get("port"):
        needs_restart.append("app.port")

    return {"ok": True, "invalidated": invalidated, "needs_restart": needs_restart}


@app.get("/api/cursos")
def api_cursos():
    try:
        return {"cursos": _load_catalog_published()}
    except Exception as e:
        return JSONResponse(status_code=503, content={"error": str(e)})


@app.get("/api/admin/rag-diagnostico")
def api_rag_diagnostico():
    try:
        return diagnostico_rag()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/admin/rag-embeddings")
def api_rag_embeddings(query: str = ""):
    if not query.strip():
        return JSONResponse(status_code=400, content={"error": "Parâmetro 'query' é obrigatório"})
    try:
        config = load_config()
        return get_embeddings_diagnostico(query, config)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/admin/rag-embed-texto")
def api_rag_embed_texto(texto: str = ""):
    if not texto.strip():
        return JSONResponse(status_code=400, content={"error": "Parâmetro 'texto' é obrigatório"})
    try:
        config = load_config()
        return embed_texto(texto, config)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


PROVIDERS_DIR = BASE_DIR / "providers"


@app.get("/api/admin/providers")
def api_list_providers():
    if not PROVIDERS_DIR.is_dir():
        return []
    return sorted(f.name for f in PROVIDERS_DIR.glob("*.json"))


@app.get("/api/admin/providers/{filename}")
def api_get_provider(filename: str):
    path = PROVIDERS_DIR / filename
    if not path.is_file() or not path.suffix == ".json" or ".." in filename:
        return JSONResponse(status_code=404, content={"error": "not found"})
    return json.loads(path.read_text(encoding="utf-8"))


@app.post("/api/admin/reindex-rag")
def api_reindex_rag():
    try:
        config = load_config()
        n      = reindex(config)
        return {"ok": True, "chunks": n}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_catalog_published() -> list[dict]:
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return [
        {**c, "videos": [v for v in c["videos"] if v["status"] == "publicado"]}
        for c in data.get("cursos", [])
    ]


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(data: dict):
    CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    import uvicorn
    _preflight()
    try:
        uvicorn.run(app, host="0.0.0.0", port=APP_PORT, log_level="info")
    except Exception as e:
        print(f"[Pandora] ✗ Falha fatal ao iniciar servidor: {e}", file=sys.stderr)
        sys.exit(1)
