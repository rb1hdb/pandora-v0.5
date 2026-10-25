#!/usr/bin/env bash
set -euo pipefail

# ── Configuração ─────────────────────────────────────────────
REPO_NAME="pandora-v0.5"
GH_USER="rb1hdb"                  # seu username no GitHub
SOURCE_DIR="$HOME/pandora/pandora-v0.5"

# ── Git user (se não configurado) ────────────────────────────
if [ -z "$(git config --global user.email)" ]; then
    git config --global user.email "renatobraga.bb@gmail.com"
    git config --global user.name "Renato Braga"
    echo "Git user configurado: Renato Braga <renatobraga.bb@gmail.com>"
fi

# ── Limpar artefatos ─────────────────────────────────────────
cd "$SOURCE_DIR"
echo "Limpando __pycache__ e logs ..."
find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
rm -rf app/logs/*.jsonl

# ── .gitignore ───────────────────────────────────────────────
cat > .gitignore <<'GITIGNORE'
__pycache__/
*.pyc
*.pyo
app/logs/
app/chroma_store/
*.sqlite3
*.db
.env
.DS_Store
GITIGNORE

# ── Git init + commit ────────────────────────────────────────
if [ -d .git ]; then
    echo "Git já inicializado."
else
    git init -b main
fi

git add -A
git commit -m "Pandora LLMAS Pentest Lab — v0.5

Plataforma educacional de labs para pentest de aplicações LLM-based.
FastAPI + Ollama + RAG (ChromaDB) + MCP Server."

# ── Remote + push ────────────────────────────────────────────
git remote add origin "git@github.com:$GH_USER/$REPO_NAME.git" 2>/dev/null \
    || git remote set-url origin "git@github.com:$GH_USER/$REPO_NAME.git"

echo ""
echo "Fazendo push para origin/main ..."
git push -u origin main

echo ""
echo "DONE: https://github.com/$GH_USER/$REPO_NAME"
