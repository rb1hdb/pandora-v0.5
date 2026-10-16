"""
RAG em memória: embeddings via Ollama ou OpenAI-compatible, similaridade coseno em Python puro.
Chunking: prefixo [documento: <arquivo>] + H1 + preâmbulo + cada seção H2 viram um chunk separado. Sem ChromaDB.
Configuração via config.json → rag.embedding.{provider,model,base_url,api_key,timeout}.
"""
import json
import math
import sys
import time
from pathlib import Path

import requests

from providers import get_provider_api, build_embedding_url

BASE_DIR    = Path(__file__).parent
DOCS_DIR    = BASE_DIR / "documents"
CONFIG_PATH = BASE_DIR / "config.json"

_index: list[dict] = []


# ── Config helpers ────────────────────────────────────────────────────────────

def _load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def invalidate_index() -> None:
    global _index
    _index = []


# ── Embedding (provider-agnostic) ─────────────────────────────────────────────

def _embed(text: str, config: dict) -> list[float]:
    emb_cfg  = config.get("rag", {}).get("embedding", {})
    provider = emb_cfg.get("provider", "ollama")
    model    = emb_cfg.get("model", "bge-m3")
    api_key  = emb_cfg.get("api_key", "")
    timeout  = emb_cfg.get("timeout", 60)

    api = get_provider_api(provider)
    raw_url = emb_cfg.get("url") or emb_cfg.get("base_url") or config["llm"]["base_url"]
    url = build_embedding_url(raw_url, model=model, provider=provider)

    is_gemini_native = "generativelanguage.googleapis.com" in url and "/v1beta/openai" not in raw_url
    resp = requests.post(
        url,
        params={"key": api_key} if is_gemini_native else None,
        headers=None if is_gemini_native else {"Authorization": f"Bearer {api_key or 'x'}"},
        json={"model": model, api["embed_input_field"]: text},
        timeout=timeout,
    )
    resp.raise_for_status()

    body = resp.json()
    if api["embed_nested"]:
        data = body.get("data") or []
        emb  = data[0].get("embedding", []) if data else []
    else:
        emb = body.get("embedding") or []

    if not emb:
        raise RuntimeError(f"Embedding vazio (provider={provider}, model={model}) para texto de {len(text)} chars")
    return emb


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na  = math.sqrt(sum(x * x for x in a))
    nb  = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


# ── Chunking ──────────────────────────────────────────────────────────────────

def _chunk_document(text: str, source: str) -> list[dict]:
    """Cada chunk = prefixo [documento: <arquivo>] + H1 + preâmbulo + (título H2 + conteúdo).
    Se não houver H2, o documento inteiro é um único chunk."""
    lines = text.splitlines()

    h1_line   = ""
    preamble: list[str] = []
    sections: list[tuple[str, list[str]]] = []   # [(h2_title_line, [body_lines]), ...]

    state = "preamble"   # "preamble" | "section"
    cur_title = ""
    cur_body: list[str] = []

    for line in lines:
        if line.startswith("# ") and not h1_line:
            h1_line = line.rstrip()
            continue

        if line.startswith("## "):
            if state == "section":
                sections.append((cur_title, cur_body))
            cur_title = line.rstrip()
            cur_body = []
            state = "section"
            continue

        if state == "preamble":
            preamble.append(line)
        else:
            cur_body.append(line)

    if state == "section":
        sections.append((cur_title, cur_body))

    preamble_text = "\n".join(preamble).strip()
    header_block  = "\n".join(p for p in [h1_line, preamble_text] if p).strip()

    chunks: list[dict] = []
    prefix = f"[documento: {source}]"

    if not sections:
        full = (header_block + "\n" + "\n".join(cur_body).strip()).strip() if cur_body else header_block
        if full:
            chunks.append({"text": f"{prefix}\n\n{full}", "source": source})
        return chunks

    for title, body in sections:
        body_text = "\n".join(body).strip()
        content = "\n\n".join(p for p in [header_block, title, body_text] if p)
        if content:
            chunks.append({"text": f"{prefix}\n\n{content}", "source": source})

    return chunks


# ── Indexação ─────────────────────────────────────────────────────────────────

def _probe_embedding(config: dict) -> bool:
    """Testa o endpoint de embedding com uma chamada real (texto curto)."""
    try:
        _embed("probe", config)
        return True
    except Exception as exc:
        # FIX: logar com timestamp + tipo do erro para diagnóstico (era silencioso antes).
        print(f"[RAG] probe falhou: {type(exc).__name__}: {exc}", file=sys.stderr)
        return False


def _build_index(config: dict) -> int:
    """Lê todos os .md, gera chunks + embeddings, popula _index. Retorna nº de chunks."""
    global _index
    _index = []

    if not _probe_embedding(config):
        emb_url = config.get("rag", {}).get("embedding", {}).get("base_url", "(não configurada)")
        # FIX: usar log_entry quando possível (passa request_id=init para distinguir no log viewer).
        print(f"[RAG] ✗ Embedding endpoint não responde ({emb_url}) — indexação adiada.", file=sys.stderr)
        print("[RAG]   Configure o provider na tela Admin e clique REINDEXAR.", file=sys.stderr)
        # FIX: levantar exceção explícita em vez de retornar 0 silenciosamente.
        # Antes: api_reindex_rag recebia 0 e retornava HTTP 200 {"ok":true,"chunks":0}.
        # Agora: propaga o erro para que o chamador saiba que falhou.
        raise RuntimeError(f"Embedding endpoint não responde ({emb_url}). RAG não indexado.")

    total = 0
    for md_path in sorted(DOCS_DIR.glob("*.md")):
        text   = md_path.read_text(encoding="utf-8")
        chunks = _chunk_document(text, md_path.name)
        for c in chunks:
            emb = _embed(c["text"], config)
            _index.append({"text": c["text"], "source": c["source"], "embedding": emb})
        print(f"[RAG] {md_path.name} → {len(chunks)} chunks")
        total += len(chunks)

    return total


def reindex(config: dict | None = None) -> int:
    if config is None:
        config = _load_config()
    n = _build_index(config)
    print(f"[RAG] {n} chunks indexados com sucesso.")
    return n


def chunk_count() -> int:
    """Retorna o número de chunks indexados."""
    return len(_index)


def ensure_indexed() -> None:
    config = _load_config()
    if not config.get("rag", {}).get("enabled", True):
        print("[RAG] Indexação desabilitada (rag.enabled=false).")
        return
    if _index:
        print(f"[RAG] Já indexado ({len(_index)} chunks).")
        return
    reindex(config)


# ── Diagnóstico ───────────────────────────────────────────────────────────────

def diagnostico_rag() -> dict:
    def _body(text: str, n: int = 600) -> str:
        lines = text.splitlines()
        body = "\n".join(l for l in lines if not l.startswith("#")).lstrip()
        return body[:n] if body else text[:n]

    chunks = [
        {
            "id":           f"chunk_{i}",
            "source":       item["source"],
            "text_preview": _body(item["text"]),
            "text_len":     len(item["text"]),
        }
        for i, item in enumerate(_index)
    ]
    return {"total_chunks": len(_index), "chunks": chunks}


def get_embeddings_diagnostico(query: str, config: dict | None = None) -> dict:
    if config is None:
        config = _load_config()
    if not _index:
        return {"error": "Índice vazio — chame reindex primeiro"}

    query_emb = _embed(query, config)
    top_k     = config.get("rag", {}).get("top_k", 3)

    scored = [
        (_cosine(query_emb, item["embedding"]), i, item)
        for i, item in enumerate(_index)
    ]
    scored.sort(key=lambda x: x[0], reverse=True)

    def _content_preview(text: str, n: int = 600) -> str:
        lines = text.splitlines()
        # pula linhas de cabeçalho (# / ##) e vazias no início
        body = "\n".join(l for l in lines if not l.startswith("#")).lstrip()
        return body[:n] if body else text[:n]

    results = [
        {
            "chunk_id":          f"chunk_{i}",
            "source":            item["source"],
            "text_preview":      _content_preview(item["text"]),
            "distance":          round(float(sim), 6),
            "embedding_preview": [round(float(v), 6) for v in item["embedding"][:10]],
        }
        for sim, i, item in scored[:top_k]
    ]

    return {
        "query":                   query,
        "query_embedding_preview": [round(float(v), 6) for v in query_emb[:10]],
        "embedding_dimensions":    len(query_emb),
        "results":                 results,
    }


def embed_texto(texto: str, config: dict | None = None) -> dict:
    """Retorna o vetor completo de um texto — útil para inspeção didática."""
    if config is None:
        config = _load_config()
    emb = _embed(texto, config)
    return {
        "texto":      texto,
        "dimensions": len(emb),
        "embedding":  [round(float(v), 6) for v in emb],
    }


# ── Busca semântica ───────────────────────────────────────────────────────────

def get_rag_context(user_message: str, config: dict, request_id: str = "") -> dict:
    from logger import log_entry

    empty = {"context": "", "chunks": 0, "sources": []}
    if not config.get("rag", {}).get("enabled", True):
        if request_id:
            log_entry(request_id, "RAG", "DISABLED", "RAG desabilitado em config", 0.0)
        return empty
    if not _index:
        # FIX: distinguir "índice vazio (RAG quebrado)" de "índice populado mas sem match".
        # Antes retornava empty silenciosamente, LLM operava "no escuro".
        if request_id:
            log_entry(request_id, "RAG", "EMPTY_INDEX",
                      f"RAG habilitado mas indice vazio (0 chunks). Faca REINDEXAR no Admin.", 0.0)
        return empty

    t0 = time.monotonic()

    try:
        query_emb = _embed(user_message, config)
    except Exception as e:
        if request_id:
            log_entry(request_id, "APP", "ERROR", f"RAG embed query: {e}",
                      (time.monotonic() - t0) * 1000)
        return empty

    threshold = config.get("rag", {}).get("distance_threshold", 0.5)
    top_k     = config.get("rag", {}).get("top_k", 3)

    scored = sorted(
        ((_cosine(query_emb, item["embedding"]), item) for item in _index),
        key=lambda x: x[0],
        reverse=True,
    )

    candidates = scored[:top_k]
    parts, kept_docs, kept_sources = [], [], []
    for sim, item in candidates:
        src     = item["source"]
        kept    = sim >= threshold
        verdict = "ENTRA" if kept else "DESCARTA"
        parts.append(f"{src} (sim={round(sim, 3)} >> {verdict})")
        if kept:
            kept_docs.append(item["text"])
            kept_sources.append(src)

    elapsed = (time.monotonic() - t0) * 1000
    if request_id:
        log_entry(request_id, "RAG", "CONTEXT", " | ".join(parts), elapsed)

    return {
        "context": "\n---\n".join(kept_docs),
        "chunks":  len(kept_docs),
        "sources": kept_sources,
    }
