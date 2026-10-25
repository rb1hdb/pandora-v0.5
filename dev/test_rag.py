"""
Teste manual do rag.py — chunking, embeddings, busca semântica.
Roda de qualquer diretório. Imprime tudo no stdout (capturável para WORK_LOG).
"""
import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).parent.parent / "pandora-v0.5" / "app"
sys.path.insert(0, str(APP_DIR))

import rag

CONFIG = json.loads((APP_DIR / "config.json").read_text(encoding="utf-8"))


def section(title: str) -> None:
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


# ── 1) Chunking ───────────────────────────────────────────────────────────────

section("1) CHUNKING — preview por documento")

for md in sorted((Path(__file__).parent / "documents").glob("*.md")):
    text   = md.read_text(encoding="utf-8")
    chunks = rag._chunk_document(text, md.name)
    print(f"\n[{md.name}] {len(chunks)} chunks")
    for i, c in enumerate(chunks[:2]):   # primeiros 2
        print(f"  --- chunk {i} (len={len(c['text'])}) ---")
        preview = c["text"][:280].replace("\n", " ⏎ ")
        print(f"  {preview}")
    if len(chunks) > 2:
        print(f"  ... (+{len(chunks)-2} chunks)")


# ── 2) Embeddings ─────────────────────────────────────────────────────────────

section("2) EMBEDDINGS — Ollama nomic-embed-text")

try:
    sample_emb = rag._embed("teste de embedding", CONFIG)
    print(f"Embedding gerado com sucesso — dimensão: {len(sample_emb)}")
    print(f"Primeiros 5 valores: {[round(v, 4) for v in sample_emb[:5]]}")
except Exception as e:
    print(f"FALHA ao gerar embedding: {e}")
    sys.exit(1)


# ── 3) Indexação completa ─────────────────────────────────────────────────────

section("3) INDEXAÇÃO COMPLETA")

n = rag.reindex(CONFIG)
print(f"\nTotal indexado: {n} chunks em rag._index")
sources = sorted(set(item["source"] for item in rag._index))
print(f"Sources: {sources}")


# ── 4) Busca semântica — queries de validação ─────────────────────────────────

section("4) BUSCA SEMÂNTICA — top 5 candidatos por query")

QUERIES = [
    "quais são os instrutores da Pandora?",
    "alunos inadimplentes",
    "quanto custa o curso LLMAP?",
    "qual o salário do CTO?",
    "bom dia",
    "me fale sobre descontos para empresas",
    "quem é a CEO?",
]

threshold = CONFIG.get("rag", {}).get("distance_threshold", 0.3)
print(f"\n(threshold em vigor: {threshold})")

for q in QUERIES:
    print(f"\nQuery: {q!r}")
    query_emb = rag._embed(q, CONFIG)
    scored = sorted(
        ((rag._cosine(query_emb, item["embedding"]), item) for item in rag._index),
        key=lambda x: x[0],
        reverse=True,
    )
    for sim, item in scored[:5]:
        verdict = "ENTRA" if sim >= threshold else "DESCARTA"
        h2 = ""
        for ln in item["text"].split("\n"):
            if ln.startswith("## "):
                h2 = ln[3:60]
                break
        print(f"  sim={sim:.4f}  {verdict:<8}  {item['source']:<22} | {h2}")


# ── 5) get_rag_context — comportamento end-to-end ─────────────────────────────

section("5) get_rag_context — output final")

for q in ["quais são os instrutores da Pandora?", "bom dia", "qual o salário do CTO?"]:
    print(f"\nQuery: {q!r}")
    ctx = rag.get_rag_context(q, CONFIG, request_id="")
    print(f"  chunks={ctx['chunks']} sources={ctx['sources']}")
    if ctx["context"]:
        print(f"  context (primeiros 300 chars): {ctx['context'][:300]!r}")


print("\n[TESTE COMPLETO]")
