# Pandora v0.5 : ataque & defesa em app LLM

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![License: CC BY 4.0](https://img.shields.io/badge/Content-CC%20BY%204.0-lightgrey.svg)](LICENSE-CONTENT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)](docker-compose.yml)

> **🌐 Idioma:** [English](README.md) | Português | [Español](README.es.md)

Plataforma educacional para demonstração e exploração de vulnerabilidades em aplicações baseadas em LLM (Large Language Models), permitindo aprender e treinar tanto ataques quanto defesas.

A aplicação simula uma plataforma de cursos online ("Pandora Academy") com um assistente virtual (Sage) alimentado por LLM + RAG + MCP — propositalmente vulnerável, com defesas que podem ser ligadas/desligadas em tempo real para demonstrar ataque e mitigação.

> **⚠️ AVISO DE SEGURANÇA:** Esta aplicação é **intencionalmente vulnerável**. **Não a exponha em redes públicas ou ambientes de produção.** Execute apenas em ambientes controlados e autorizados (localhost, rede isolada) para fins educacionais e de pesquisa de segurança.

## Screenshots

| Chat | Admin (Defesas) |
|------|-----------------|
| ![Chat](app/static/screenshots/chat.png) | ![Admin](app/static/screenshots/admin.png) |

## Licenciamento

Este projeto utiliza duas licenças:

- `LICENSE` — MIT License para software.
- `LICENSE-CONTENT` — CC BY 4.0 para conteúdo educacional e não-software.

## Arquitetura

```
                          ┌──────────────┐
                          │   Browser    │
                          │  Chat/Admin  │
                          └──────┬───────┘
                                 │ POST /api/chat
                                 v
┌────────────────────────────────────────────────────────────────────┐
│                     FastAPI  :55000                                │
│                                                                   │
│  user_input ──> D1 (regex) ──> D2 (LLM judge) ──> RAG ──>        │
│                                     │               │             │
│          ┌──────────────────────────┘               │ embed       │
│          │                                          v             │
│          │  ┌───────────────────────────────────────────────┐     │
│          │  │  System Prompt + secrets                      │     │
│          │  │    + RAG context (documentos recuperados)     │     │
│          │  │    + D3 SP Lock    + D4 Alignment             │     │
│          │  └────────────────────────┬──────────────────────┘     │
│          │                           │                            │
│          │                           v                            │
│          │  ┌─────────────────────────────────────────────┐       │
│          │  │  LLM call (tool calling loop)               │       │
│          │  │  messages + tools (MCP discovery) ──────────>│──┐   │
│          │  └──────────────────────┬──────────────────────┘  │   │
│          │                         │                          │   │
│          │                         v                          │   │
│          │  output ──> D5 (LLM judge) ──> D6 (regex) ──> resposta │
│          │                  │                                     │
│          └──────────────────┘                                     │
│                                                                   │
│  D1,D6: deterministico (regex)    D2,D5: LLM-based (classifier)  │
│  D3,D4: deterministico (prompt)   Todas nascem OFF (lab mode)     │
│                                                                   │
└───────────┬──────────────────────────────────────────────────────┘
            │ tool calls (Streamable HTTP)     │ chat / judge / embed
            v                                  v
┌───────────────────────┐       ┌──────────────────────────────────┐
│  MCP Server  :55001   │       │  LLM Provider                    │
│                       │       │  (Ollama / OpenAI / Gemini)       │
│  Tools:               │       │                                  │
│  · listar_cursos      │       │  Chat:  qwen3 4B (alinhado)       │
│  · listar_videos      │       │  Judge: mesmo modelo              │
│  · obter_link_video   │       │  Embed: bge-m3                   │
│                       │       │                                  │
│  Static: /videos/*.mp4│       │  Configurável via tela Admin     │
└───────────────────────┘       └──────────────────────────────────┘
```

**LLM runtime:** qualquer provider compatível com a API OpenAI — Ollama (local ou remoto), OpenAI, Google Gemini. Escolhido na instalação (passo 2) e ajustável na tela Admin.

## Instalação

Escolha **uma** das duas formas de executar: [Docker](#opção-a--docker) ou [venv](#opção-b--venv-sem-docker). Os dois primeiros passos são comuns.

### Antes de começar

| SO | Recomendado | Observação |
|---|---|---|
| **Linux** (Debian/Ubuntu/Kali, Fedora, Arch) | ✅ Testado | Caminho principal — Docker ou venv |
| **macOS** (12+) | ✅ Via Docker Desktop | Opção A recomendada; venv também funciona |
| **Windows** (10/11) | ⚠️ Via WSL 2 + Docker Desktop | Caminho mais simples; nativo não suportado |

Requisitos: **8 GB de RAM** (16 GB para 8B/14B), **10 GB de disco livre**, conexão de internet.

### 1. Obter o código

```bash
git clone https://github.com/rb1hdb/pandora-v0.5.git
cd pandora-v0.5
```

Execute todos os comandos abaixo a partir desta pasta (raiz do repositório).

### 2. Escolher o provider e o modelo

A app só inicia com uma configuração ativa em `app/config.json`. Escolha um perfil em `app/providers/` e copie:

| Provider | Perfil | Requisitos |
|----------|--------|------------|
| Ollama remoto | `config.json.ollama-remote.<modelo>.json` | Servidor Ollama acessível pela rede (padrão `http://10.0.0.30:11434`) |
| Ollama local | `config.json.ollama-local.<modelo>.json` | Ollama nesta máquina (`localhost:11434`) — **somente venv** |
| Google Gemini | `config.json.gemini-3.5-flash-lite.json` | API key do Gemini |
| OpenAI | `config.json.gpt-4o-mini.json` | API key da OpenAI |

Para Ollama, os modelos disponíveis são:

| Variante | Modelos |
|---|---|
| **Alinhado** (com safety training) | `0.6b-qwen-no-think`, `1.7b-qwen-no-think`, `4b-qwen-no-think`, `8b-qwen-no-think`, `14b-qwen-no-think` |
| **Abliterated** (safety removida — use apenas em lab) | `0.6b-qwen-abliterated-no-think`, `1.7b-qwen-abliterated-no-think`, `4b-qwen-abliterated-no-think`, `8b-qwen-abliterated-no-think`, `14b-qwen-abliterated-no-think` |

⚠️ **Abliterated** = modelo sem filtro de segurança, usado no workshop de pentest. **Use apenas em ambiente isolado** (localhost ou rede controlada).

Exemplos:

```bash
# Ollama remoto, modelo 4B alinhado
cp app/providers/config.json.ollama-remote.4b-qwen-no-think.json app/config.json

# Ollama remoto, modelo 8B abliterated (padrão do workshop)
cp app/providers/config.json.ollama-remote.8b-qwen-abliterated-no-think.json app/config.json
```

Depois ajuste o perfil, se necessário:

- **Ollama (remoto ou local):** o servidor precisa estar no ar e já ter os modelos citados no perfil (campos `model`). Se o seu servidor não é `10.0.0.30`, edite o `base_url` em `app/config.json` (seções LLM, Judge e RAG Embedding). Os Modelfiles para criar os modelos `*-qwen-no-think` estão em `modelfiles/`.
- **Gemini / OpenAI:** substitua o placeholder do `api_key` (`YOUR_GEMINI_API_KEY` / `SUA_OPENAI_API_KEY`) pela sua chave em `app/config.json`.

Você também pode alterar tudo depois no painel **Admin** (**Salvar Configuração** para aplicar). Se `app/config.json` não existir, a app aborta na inicialização e lista os perfis disponíveis.

---

## Opção A — Docker

> O Docker usa os perfis **remoto** e **cloud**. O perfil `ollama-local` não funciona dentro do container (`localhost` é o próprio container) — para ele use [venv](#opção-b--venv-sem-docker).

### Requisitos

```bash
docker --version
docker compose version
```

Se faltar o Docker: no Linux execute `curl -fsSL https://get.docker.com | sh && sudo usermod -aG docker $USER` (depois faça logout/login); no Windows (WSL 2) e macOS instale o [Docker Desktop](https://www.docker.com/products/docker-desktop/).

### Iniciar

```bash
docker compose up -d --build
```

### Verificar

```bash
docker compose ps
docker compose logs -f app          # Ctrl+C sai dos logs, a app continua rodando
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:55000/health    # esperado: 200
```

Acesse **http://localhost:55000**.

> O RAG inicia desabilitado. Para habilitar: **Admin > RAG > enabled=true**, configure o modelo de embedding e clique em **Reindexar**.

> **WSL2 (Windows):** se `localhost:55000` não abrir no navegador do Windows, execute `hostname -I` e use `http://<IP>:55000`.

### Gerenciar

| Ação | Comando |
|------|---------|
| Logs (coloridos) | `docker compose logs -f app` |
| Parar | `docker compose down` |
| Iniciar novamente | `docker compose up -d` |
| Reiniciar (ex.: após alterar `app/config.json`) | `docker compose restart` |
| Rebuild (após atualizar o código) | `docker compose up -d --build` |
| Shell no container | `docker exec -it pandora bash` |
| Remover (container e imagem) | `docker compose down --rmi all` |

`config.json`, logs e código ficam no host (bind mount `./:/app`), então sobrevivem a parar/iniciar e rebuild.

---

## Opção B — venv (sem Docker)

### Requisitos

Python 3.10+ com `venv` e `pip`:

```bash
python3 --version
python3 -m venv --help > /dev/null && echo ok
```

Em Debian/Ubuntu/Kali: `sudo apt install -y python3 python3-pip python3-venv`.

### Instalar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Iniciar (3 processos separados)

A Pandora tem **3 processos independentes** que precisam rodar **simultaneamente**. Abra **3 abas ou janelas de terminal** na raiz do repositório e execute um comando em cada — **na ordem abaixo** (a app aborta se o MCP não estiver UP).

💡 Dica: use `tmux`, `screen` ou as abas do Windows Terminal/iTerm2 para manter os 3 processos lado a lado.

**Terminal 1** — MCP Server (porta 55001) — *iniciar primeiro*
```bash
cd mcp-server && source ../.venv/bin/activate && python3 server.py
```

**Terminal 2** — App (porta 55000) — *iniciar depois do MCP*
```bash
cd app && source ../.venv/bin/activate && python3 main.py
```

**Terminal 3** — Log Viewer (opcional, visualização em tempo real)
```bash
cd app && source ../.venv/bin/activate && python3 log_viewer.py
```

### Verificar

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:55000/health    # esperado: 200
```

Acesse **http://localhost:55000**.

> O RAG inicia desabilitado. Para habilitar: **Admin > RAG > enabled=true**, configure o modelo de embedding e clique em **Reindexar**.

### Parar e remover

Parar: `Ctrl+C` em cada um dos 3 terminais. Para remover tudo que a instalação criou:

```bash
rm -rf .venv app/config.json app/logs/
find app mcp-server -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
```

## Estrutura do repositório

```
pandora-v0.5/
├── app/                              # Aplicação FastAPI (:55000)
│   ├── main.py                       # Rotas e startup
│   ├── llm_wrapper.py                # Pipeline de chat (LLM + RAG + defesas)
│   ├── defenses.py                   # Defesas D1–D6 (toggles)
│   ├── rag.py                        # RAG com embeddings in-memory
│   ├── providers.py                  # Mapeamento de providers (Ollama/OpenAI/Gemini)
│   ├── logger.py                     # Logging JSONL
│   ├── log_viewer.py                 # Visualizador de log colorido
│   ├── config.json                   # Config ativa (copiada de providers/; editável via Admin, no .gitignore)
│   ├── config-defenses/              # Regras das defesas D1–D6 (JSON)
│   ├── documents/                    # Documentos RAG
│   │   ├── sobre_pandora.md
│   │   ├── faq_cursos.md
│   │   ├── politica_comercial.md
│   │   ├── politica_interna.md       # Dados sensíveis (proposital)
│   │   └── alunos.md                 # PII sintético (proposital)
│   ├── providers/                    # Configs prontos por provider
│   ├── templates/                    # Jinja2 (chat, admin, cursos, help)
│   ├── static/                       # CSS, JS, imagens
│   └── logs/                         # Logs JSONL (gerados em runtime)
├── mcp-server/                       # MCP Server de vídeos (:55001)
│   ├── server.py                     # Servidor MCP
│   ├── catalog.json                  # Catálogo de cursos/aulas
│   └── videos/                       # Vídeos por curso (3 cursos, 9 vídeos)
├── modelfiles/                       # Modelfiles Ollama (thinking off)
├── Dockerfile                        # Imagem Docker
├── docker-compose.yml                # App
├── entrypoint.sh                     # Entrypoint (3 processos)
├── requirements.txt
├── README.md                         # English documentation
├── README.pt.md
├── README.es.md                      # Documentación en español
├── LICENSE                           # MIT (software)
└── LICENSE-CONTENT                   # CC BY 4.0 (conteúdo)
```

## Defesas (toggles)

Todas as defesas nascem **desligadas** — o estado padrão é vulnerável (para demonstrar o ataque). Ative/desative em tempo real pela tela Admin da app Pandora.

| Toggle | Defesa | O que faz |
|--------|--------|-----------|
| D1 | Input Filter | Filtra padrões de injeção conhecidos (delimitadores, tokens especiais, credenciais) |
| D2 | Input Judge | LLM-as-judge avalia se o input é malicioso antes de processar |
| D3 | System Prompt Lock | Bloqueia tentativas de sobrescrever o system prompt |
| D4 | System Prompt Alignment | Injeta instruções de alinhamento no system prompt |
| D5 | Output Judge | LLM-as-judge avalia se a resposta vaza dados sensíveis |
| D6 | Output Sanitizer | Filtra credenciais e dados sensíveis na saída |

## OWASP LLM Top 10

Vulnerabilidades demonstráveis no lab, mapeadas para o [OWASP Top 10 for LLM Applications (2025)](https://genai.owasp.org/llm-top-10/):

| OWASP | Categoria | Como explorar no lab | Defesas relacionadas |
|-------|-----------|---------------------|----------------------|
| LLM01 | Prompt Injection | Injetar instruções no chat para alterar o comportamento do Sage (direct PI) ou via documentos RAG (indirect PI) | D1, D2, D3, D4 |
| LLM02 | Sensitive Information Disclosure | Extrair PII de alunos, credenciais e dados internos via chat | D5, D6 |
| LLM06 | Excessive Agency | Sage executa tools MCP (listar cursos, obter links de vídeo) sem confirmação do usuário | — |
| LLM07 | System Prompt Leakage | Extrair o system prompt completo (com segredos embutidos) | D3 |

> As demais categorias do OWASP LLM Top 10 (Training Data Poisoning, Supply Chain, etc.) estão fora do escopo deste lab.

## Documentos RAG (dados sintéticos)

A base de conhecimento do assistente é composta por documentos Markdown em `app/documents/`:

- `sobre_pandora.md` — informações institucionais
- `faq_cursos.md` — perguntas frequentes
- `politica_comercial.md` — política comercial
- `politica_interna.md` — política interna (contém dados sensíveis propositalmente)
- `alunos.md` — dados de alunos (PII proposital, para demonstrar data leakage)

## Pandora v1.0 — LLMAS: Pentest Edition

<p align="center">
  <img src="app/static/screenshots/pandora-v1.0.png" alt="Pandora v1.0" width="720">
</p>

A Pandora v0.5 é o lab compacto e open-source. A **Pandora v1.0** é a plataforma completa utilizada no curso LLMAS — Pentest Edition de [Renato Braga](https://linkedin.com/in/renatobr).

Enquanto a v0.5 tem um único assistente com uma interface de chat, a v1.0 simula uma aplicação real multi-tenant — múltiplos agentes, tools e MCP servers, integração com Telegram, upload de arquivos, memória e serviços internos por trás do LLM. A superfície de ataque é significativamente maior, com **mais de 50 cenários** cobrindo o OWASP LLM Top 10.

Não é uma coleção de desafios isolados. É uma aplicação realista onde as vulnerabilidades se encadeiam — do reconhecimento à exfiltração de dados, escalação de privilégios e, no clímax, **pivotar através do LLM para alcançar aplicações internas** que nunca deveriam estar expostas.

Interessado? Entre em contato pelo [LinkedIn](https://linkedin.com/in/renatobr).

## Licença

### Software

O código-fonte deste projeto, incluindo a aplicação Python, MCP Server,
scripts, Dockerfile, entrypoint e demais componentes de software,
é disponibilizado sob a MIT License.

### Conteúdo educacional

A documentação, tutoriais, documentos Markdown, materiais educacionais,
conteúdo destinado a RAG, roteiros e demais conteúdos não classificados
como software são disponibilizados sob a Creative Commons
Attribution 4.0 International (CC BY 4.0).

### Vídeos e mídia

Os vídeos e demais materiais multimídia criados especificamente para
este projeto são disponibilizados sob CC BY 4.0.

### Conteúdo de terceiros

Componentes, bibliotecas, modelos, imagens, vídeos, textos e outros
materiais de terceiros permanecem sujeitos às respectivas licenças.
A disponibilização deste repositório não altera os termos dessas
licenças.

### Uso educacional e de segurança

Pandora é um laboratório educacional desenvolvido para demonstração,
treinamento e pesquisa de segurança em ambientes controlados e
autorizados.

As vulnerabilidades, técnicas de exploração, configurações inseguras
e dados utilizados no laboratório são intencionais e destinam-se ao
ambiente de laboratório. O operador é responsável por utilizar o
software somente em sistemas e ambientes para os quais possua
autorização.

Os documentos que simulam informações pessoais ou confidenciais,
incluindo os dados presentes em `alunos.md` e `politica_interna.md`,
são dados sintéticos destinados exclusivamente à demonstração.
