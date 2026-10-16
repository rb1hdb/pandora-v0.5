"""
Pandora MCP Server — Streamable HTTP na porta 55001.
Tools: pandora_listar_cursos, pandora_listar_videos_do_curso, pandora_obter_link_video.
"""
import json
from pathlib import Path
from typing import Annotated
from urllib.parse import urlparse

import uvicorn
from pydantic import Field
from mcp.server import MCPServer
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles


CATALOG_PATH = Path(__file__).parent / "catalog.json"
VIDEOS_DIR   = Path(__file__).parent / "videos"


CONFIG_PATH = Path(__file__).parent / "mcp_config.json"
def _load_config() -> dict:

    if not CONFIG_PATH.exists():
        raise RuntimeError(
            f"Arquivo de configuracao nao encontrado: {CONFIG_PATH}"
        )

    return json.loads(
        CONFIG_PATH.read_text(encoding="utf-8")
    )
CONFIG = _load_config()

try:
    MCP_URL = CONFIG["mcpServers"]["pandora-videos"]["url"]
except KeyError as e:
    raise RuntimeError(
        f"Configuracao MCP invalida: {e}"
    )
    

BASE_URL = MCP_URL.removesuffix("/mcp")
MCP_PORT = urlparse(MCP_URL).port or 55001


def _abs_url(relative: str) -> str:
    return BASE_URL + relative


def _load_catalog() -> dict:
    """
    Carrega o catálogo de cursos de Pandora.
    Sem arquivo, o servidor não inicia.
    Com arquivo sem o campo `cursos`, o json é inválido e não sobe o server.
    Catálogo de cursos vazio, como a seguir, é estado válido, e não retorna erros:
    {
        "cursos": []
    }
    Não vamos, por enquanto, avaliar toda a integridade do catálogo.
    """
    
    if not CATALOG_PATH.exists():
        raise RuntimeError(
            f"Catalogo nao encontrado: {CATALOG_PATH}"
        )
    
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    
    if "cursos" not in catalog:
        raise RuntimeError("Catalogo invalido: chave 'cursos' ausente")

    return catalog

# Carrega e define catálogo globalmente para todas as tools
CATALOG = _load_catalog()

# Inicia objeto MCP
mcp = MCPServer("pandora-videos")



# ── Tools ────────────────────────────────────────────────────────────────────

@mcp.tool()
def listar_cursos() -> str:
    """
    Lista os cursos disponíveis na plataforma Pandora.

    Retorna um JSON contendo: id, nome, descricao

    O campo `id` identifica unicamente o curso e pode ser utilizado
    em `listar_videos_do_curso`.
    """
    cursos = [{"id": c["id"], "nome": c["nome"], "descricao": c["descricao"]}
              for c in CATALOG["cursos"]]
    return json.dumps({"cursos": cursos}, ensure_ascii=False)


@mcp.tool()
def listar_videos_do_curso(
    curso_id: Annotated[str, Field(description="ID interno do curso (ex: c001). Use listar_cursos para obter.")]
) -> str:
    """
    Lista os vídeos de um curso da plataforma Pandora.

    `curso_id` deve corresponder ao campo `id` de um curso.

    Retorna um JSON contendo:
    - curso_id
    - videos:
        - id
        - titulo
        - descricao
        - status

    O campo `id` de cada vídeo pode ser utilizado
    em `obter_link_video`.

    Em caso de erro, retorna: error, curso_id
    """

    for curso in CATALOG["cursos"]:

        if curso["id"] == curso_id:

            videos = []

            for v in curso["videos"]:

                # MITIGAÇÃO DE SEGURANÇA (desabilitada para fins didáticos)
                #
                # Impediria exposição de vídeos internos,
                # rascunhos e materiais sensíveis.
                #
                # if v.get("status") != "publicado":
                #     continue

                videos.append({
                    "id": v["id"],
                    "titulo": v["titulo"],
                    "descricao": v["descricao"],
                    "status": v["status"]
                })

            return json.dumps(
                {
                    "curso_id": curso_id,
                    "videos": videos
                },
                ensure_ascii=False
            )

    return json.dumps(
        {
            "error": "curso não encontrado",
            "curso_id": curso_id
        },
        ensure_ascii=False
    )

@mcp.tool()
def obter_link_video(
    video_id: Annotated[str, Field(description="ID interno do vídeo (ex: v001). Use listar_videos_do_curso para obter.")]
) -> str:
    """
    Obtém a URL de acesso de um vídeo da plataforma Pandora.

    `video_id` deve corresponder ao campo `id`
    de um vídeo, não ao título da aula.

    Exemplo correto: video_id="v001"
    Exemplo incorreto: video_id="Aula 1 - Introdução"

    Retorna um JSON contendo: id, titulo, url

    Em caso de erro, retorna: error, video_id
    """
    for curso in CATALOG["cursos"]:
        for v in curso["videos"]:
            if v["id"] == video_id:
                return json.dumps(
                    {
                        "id": v["id"],
                        "titulo": v["titulo"],
                        "url": _abs_url(v["url"])
                    },
                    ensure_ascii=False
                )
    return json.dumps({"error": "vídeo não encontrado", "video_id": video_id}, ensure_ascii=False)


# ── App: FastMCP Streamable HTTP + /health + /videos static ──────────────────

async def _health(request):
    return JSONResponse({"status": "ok"})


# Extract the MCP route and its lifespan from FastMCP, then compose everything
# in one Starlette app so the middleware stack is compiled correctly at startup.
_mcp_inner   = mcp.streamable_http_app()
_mcp_route   = _mcp_inner.routes[0]
_mcp_lifespan = _mcp_inner.router.lifespan_context


app = Starlette(
    routes=[
        Route("/health", _health),
        _mcp_route,
        Mount("/videos", StaticFiles(directory=str(VIDEOS_DIR)), name="videos"),
    ],
    lifespan=_mcp_lifespan,
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=MCP_PORT, log_level="info")
