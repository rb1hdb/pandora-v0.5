# Pandora v0.5 : ataque y defensa en apps LLM

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![License: CC BY 4.0](https://img.shields.io/badge/Content-CC%20BY%204.0-lightgrey.svg)](LICENSE-CONTENT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)](docker-compose.yml)

> **🌐 Idioma:** [English](README.md) | [Português](README.pt.md) | Español

Plataforma educativa para demostración y exploración de vulnerabilidades en aplicaciones basadas en LLM (Large Language Models), que permite aprender y practicar tanto ataques como defensas.

La aplicación simula una plataforma de cursos en línea ("Pandora Academy") con un asistente virtual (Sage) impulsado por LLM + RAG + MCP — intencionalmente vulnerable, con defensas que se pueden activar/desactivar en tiempo real para demostrar ataques y mitigación.

> **⚠️ ADVERTENCIA DE SEGURIDAD:** Esta aplicación es **intencionalmente vulnerable**. **No la exponga en redes públicas ni en entornos de producción.** Ejecútela solo en entornos controlados y autorizados (localhost, red aislada) con fines educativos y de investigación de seguridad.

## Capturas de pantalla

| Chat | Admin (Defensas) |
|------|-----------------|
| ![Chat](app/static/screenshots/chat.png) | ![Admin](app/static/screenshots/admin.png) |

## Licenciamiento

Este proyecto utiliza dos licencias:

- `LICENSE` — MIT License para software.
- `LICENSE-CONTENT` — CC BY 4.0 para contenido educativo y no-software.

## Arquitectura

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
│          │  output ──> D5 (LLM judge) ──> D6 (regex) ──> respuesta│
│          │                  │                                     │
│          └──────────────────┘                                     │
│                                                                   │
│  D1,D6: determinístico (regex)    D2,D5: LLM-based (classifier)  │
│  D3,D4: determinístico (prompt)   Todas inician OFF (modo lab)    │
│                                                                   │
└───────────┬──────────────────────────────────────────────────────┘
            │ tool calls (Streamable HTTP)     │ chat / judge / embed
            v                                  v
┌───────────────────────┐       ┌──────────────────────────────────┐
│  MCP Server  :55001   │       │  LLM Provider                    │
│                       │       │  (Ollama / OpenAI / Gemini)       │
│  Tools:               │       │                                  │
│  · listar_cursos      │       │  Chat:  qwen3 4B (alineado)      │
│  · listar_videos      │       │  Judge: mismo modelo              │
│  · obter_link_video   │       │  Embed: bge-m3                   │
│                       │       │                                  │
│  Static: /videos/*.mp4│       │  Configurable vía panel Admin    │
└───────────────────────┘       └──────────────────────────────────┘
```

**LLM runtime:** cualquier proveedor compatible con la API OpenAI — Ollama (local o remoto), OpenAI, Google Gemini. Se elige en la instalación (paso 2) y es ajustable en el panel Admin.

## Instalación

Elija **una** de las dos formas de ejecutar: [Docker](#opción-a--docker) o [venv](#opción-b--venv-sin-docker). Los dos primeros pasos son comunes.

### Antes de empezar

| SO | Recomendado | Observación |
|---|---|---|
| **Linux** (Debian/Ubuntu/Kali, Fedora, Arch) | ✅ Probado | Camino principal — Docker o venv |
| **macOS** (12+) | ✅ Via Docker Desktop | Opción A recomendada; venv también funciona |
| **Windows** (10/11) | ⚠️ Via WSL 2 + Docker Desktop | Camino más simple; nativo no soportado |

Requisitos: **8 GB de RAM** (16 GB para 8B/14B), **10 GB de disco libre**, conexión a internet.

### 1. Obtener el código

```bash
git clone https://github.com/rb1hdb/pandora-v0.5.git
cd pandora-v0.5
```

Ejecute todos los comandos siguientes desde esta carpeta (raíz del repositorio).

### 2. Elegir el provider y el modelo

La app solo inicia con una configuración activa en `app/config.json`. Elija un perfil en `app/providers/` y cópielo:

| Provider | Perfil | Requisitos |
|----------|--------|------------|
| Ollama remoto | `config.json.ollama-remote.<modelo>.json` | Servidor Ollama accesible por la red (por defecto `http://10.0.0.30:11434`) |
| Ollama local | `config.json.ollama-local.<modelo>.json` | Ollama en esta máquina (`localhost:11434`) — **solo venv** |
| Google Gemini | `config.json.gemini-3.5-flash-lite.json` | API key de Gemini |
| OpenAI | `config.json.gpt-4o-mini.json` | API key de OpenAI |

Para Ollama, los modelos disponibles son:

| Variante | Modelos |
|---|---|
| **Alineado** (con safety training) | `0.6b-qwen-no-think`, `1.7b-qwen-no-think`, `4b-qwen-no-think`, `8b-qwen-no-think`, `14b-qwen-no-think` |
| **Abliterated** (safety removido — solo en lab) | `0.6b-qwen-abliterated-no-think`, `1.7b-qwen-abliterated-no-think`, `4b-qwen-abliterated-no-think`, `8b-qwen-abliterated-no-think`, `14b-qwen-abliterated-no-think` |

⚠️ **Abliterated** = modelo sin filtro de seguridad, usado en el workshop de pentest. **Use solo en un entorno aislado** (localhost o red controlada).

Ejemplos:

```bash
# Ollama remoto, modelo 4B alineado
cp app/providers/config.json.ollama-remote.4b-qwen-no-think.json app/config.json

# Ollama remoto, modelo 8B abliterated (estándar del workshop)
cp app/providers/config.json.ollama-remote.8b-qwen-abliterated-no-think.json app/config.json
```

Luego ajuste el perfil si es necesario:

- **Ollama (remoto o local):** el servidor debe estar activo y ya tener los modelos citados en el perfil (campos `model`). Si su servidor no es `10.0.0.30`, edite `base_url` en `app/config.json` (secciones LLM, Judge y RAG Embedding). Los Modelfiles para crear los modelos `*-qwen-no-think` están en `modelfiles/`.
- **Gemini / OpenAI:** reemplace el placeholder de `api_key` (`YOUR_GEMINI_API_KEY` / `SUA_OPENAI_API_KEY`) por su clave en `app/config.json`.

También puede cambiar todo después en el panel **Admin** (**Guardar Configuración** para aplicar). Si `app/config.json` no existe, la app aborta al iniciar y lista los perfiles disponibles.

---

## Opción A — Docker

> Docker usa los perfiles **remoto** y **cloud**. El perfil `ollama-local` no funciona dentro del contenedor (`localhost` es el propio contenedor) — para él use [venv](#opción-b--venv-sin-docker).

### Requisitos

```bash
docker --version
docker compose version
```

Si falta Docker: en Linux ejecute `curl -fsSL https://get.docker.com | sh && sudo usermod -aG docker $USER` (luego cierre y abra sesión); en Windows (WSL 2) y macOS instale [Docker Desktop](https://www.docker.com/products/docker-desktop/).

### Iniciar

```bash
docker compose up -d --build
```

### Verificar

```bash
docker compose ps
docker compose logs -f app          # Ctrl+C sale de los logs, la app sigue corriendo
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:55000/health    # esperado: 200
```

Acceda a **http://localhost:55000**.

> El RAG inicia deshabilitado. Para habilitarlo: **Admin > RAG > enabled=true**, configure el modelo de embedding y haga clic en **Reindexar**.

> **WSL2 (Windows):** si `localhost:55000` no abre en el navegador de Windows, ejecute `hostname -I` y use `http://<IP>:55000`.

### Gestionar

| Acción | Comando |
|--------|---------|
| Logs (coloridos) | `docker compose logs -f app` |
| Detener | `docker compose down` |
| Iniciar nuevamente | `docker compose up -d` |
| Reiniciar (ej.: tras cambiar `app/config.json`) | `docker compose restart` |
| Rebuild (tras actualizar el código) | `docker compose up -d --build` |
| Shell en el contenedor | `docker exec -it pandora bash` |
| Eliminar (contenedor e imagen) | `docker compose down --rmi all` |

`config.json`, logs y código quedan en el host (bind mount `./:/app`), por lo que sobreviven a detener/iniciar y rebuild.

---

## Opción B — venv (sin Docker)

### Requisitos

Python 3.10+ con `venv` y `pip`:

```bash
python3 --version
python3 -m venv --help > /dev/null && echo ok
```

En Debian/Ubuntu/Kali: `sudo apt install -y python3 python3-pip python3-venv`.

### Instalar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Iniciar (3 procesos separados)

Pandora tiene **3 procesos independientes** que deben ejecutarse **simultáneamente**. Abra **3 pestañas o ventanas de terminal** en la raíz del repositorio y ejecute un comando en cada una — **en el orden indicado** (la app aborta si el MCP no está UP).

💡 Consejo: use `tmux`, `screen` o las pestañas de Windows Terminal/iTerm2 para mantener los 3 procesos lado a lado.

**Terminal 1** — MCP Server (puerto 55001) — *iniciar primero*
```bash
cd mcp-server && source ../.venv/bin/activate && python3 server.py
```

**Terminal 2** — App (puerto 55000) — *iniciar después del MCP*
```bash
cd app && source ../.venv/bin/activate && python3 main.py
```

**Terminal 3** — Log Viewer (opcional, visualización en tiempo real)
```bash
cd app && source ../.venv/bin/activate && python3 log_viewer.py
```

### Verificar

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:55000/health    # esperado: 200
```

Acceda a **http://localhost:55000**.

> El RAG inicia deshabilitado. Para habilitarlo: **Admin > RAG > enabled=true**, configure el modelo de embedding y haga clic en **Reindexar**.

### Detener y eliminar

Detener: `Ctrl+C` en cada una de las 3 terminales. Para eliminar todo lo que creó la instalación:

```bash
rm -rf .venv app/config.json app/logs/
find app mcp-server -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
```

## Estructura del repositorio

```
pandora-v0.5/
├── app/                              # Aplicación FastAPI (:55000)
│   ├── main.py                       # Rutas y startup
│   ├── llm_wrapper.py                # Pipeline de chat (LLM + RAG + defensas)
│   ├── defenses.py                   # Defensas D1–D6 (toggles)
│   ├── rag.py                        # RAG con embeddings en memoria
│   ├── providers.py                  # Mapeo de proveedores (Ollama/OpenAI/Gemini)
│   ├── logger.py                     # Logging JSONL
│   ├── log_viewer.py                 # Visualizador de log colorizado
│   ├── config.json                   # Config activa (copiada de providers/; editable vía Admin, en .gitignore)
│   ├── config-defenses/              # Reglas de defensas D1–D6 (JSON)
│   ├── documents/                    # Documentos RAG
│   │   ├── sobre_pandora.md
│   │   ├── faq_cursos.md
│   │   ├── politica_comercial.md
│   │   ├── politica_interna.md       # Datos sensibles (intencional)
│   │   └── alunos.md                 # PII sintético (intencional)
│   ├── providers/                    # Configs listos por proveedor
│   ├── templates/                    # Jinja2 (chat, admin, cursos, help)
│   ├── static/                       # CSS, JS, imágenes
│   └── logs/                         # Logs JSONL (generados en runtime)
├── mcp-server/                       # MCP Server de videos (:55001)
│   ├── server.py                     # Servidor MCP
│   ├── catalog.json                  # Catálogo de cursos/lecciones
│   └── videos/                       # Videos por curso (3 cursos, 9 videos)
├── modelfiles/                       # Modelfiles Ollama (thinking off)
├── Dockerfile                        # Imagen Docker
├── docker-compose.yml                # App
├── entrypoint.sh                     # Entrypoint (3 procesos)
├── requirements.txt
├── README.md                         # Documentación en inglés
├── README.pt.md                      # Documentación en portugués
├── README.es.md
├── LICENSE                           # MIT (software)
└── LICENSE-CONTENT                   # CC BY 4.0 (contenido)
```

## Defensas (toggles)

Todas las defensas inician **desactivadas** — el estado predeterminado es vulnerable (para demostrar el ataque). Actívelas/desactívelas en tiempo real vía el panel Admin de la app Pandora.

| Toggle | Defensa | Qué hace |
|--------|---------|----------|
| D1 | Input Filter | Filtra patrones de inyección conocidos (delimitadores, tokens especiales, credenciales) |
| D2 | Input Judge | LLM-as-judge evalúa si el input es malicioso antes de procesarlo |
| D3 | System Prompt Lock | Bloquea intentos de sobrescribir el system prompt |
| D4 | System Prompt Alignment | Inyecta instrucciones de alineamiento en el system prompt |
| D5 | Output Judge | LLM-as-judge evalúa si la respuesta filtra datos sensibles |
| D6 | Output Sanitizer | Filtra credenciales y datos sensibles en la salida |

## OWASP LLM Top 10

Vulnerabilidades demostrables en el lab, mapeadas al [OWASP Top 10 for LLM Applications (2025)](https://genai.owasp.org/llm-top-10/):

| OWASP | Categoría | Cómo explotar en el lab | Defensas relacionadas |
|-------|-----------|------------------------|----------------------|
| LLM01 | Prompt Injection | Inyectar instrucciones en el chat para alterar el comportamiento de Sage (direct PI) o vía documentos RAG (indirect PI) | D1, D2, D3, D4 |
| LLM02 | Sensitive Information Disclosure | Extraer PII de alumnos, credenciales y datos internos vía chat | D5, D6 |
| LLM06 | Excessive Agency | Sage ejecuta tools MCP (listar cursos, obtener links de video) sin confirmación del usuario | — |
| LLM07 | System Prompt Leakage | Extraer el system prompt completo (con secretos embebidos) | D3 |

> Las demás categorías del OWASP LLM Top 10 (Training Data Poisoning, Supply Chain, etc.) están fuera del alcance de este lab.

## Documentos RAG (datos sintéticos)

La base de conocimiento del asistente está compuesta por documentos Markdown en `app/documents/`:

- `sobre_pandora.md` — información institucional
- `faq_cursos.md` — preguntas frecuentes
- `politica_comercial.md` — política comercial
- `politica_interna.md` — política interna (contiene datos sensibles intencionalmente)
- `alunos.md` — datos de alumnos (PII intencional, para demostrar data leakage)

## Pandora v1.0 — LLMAS: Pentest Edition

<p align="center">
  <img src="app/static/screenshots/pandora-v1.0.png" alt="Pandora v1.0" width="720">
</p>

Pandora v0.5 es el lab compacto y open-source. **Pandora v1.0** es la plataforma completa utilizada en el curso LLMAS — Pentest Edition de [Renato Braga](https://linkedin.com/in/renatobr).

Mientras la v0.5 tiene un único asistente con una interfaz de chat, la v1.0 simula una aplicación real multi-tenant — múltiples agentes, tools y MCP servers, integración con Telegram, carga de archivos, memoria y servicios internos detrás del LLM. La superficie de ataque es significativamente mayor, con **más de 50 escenarios** cubriendo el OWASP LLM Top 10.

No es una colección de desafíos aislados. Es una aplicación realista donde las vulnerabilidades se encadenan — desde el reconocimiento hasta la exfiltración de datos, escalamiento de privilegios y, en el clímax, **pivotar a través del LLM para alcanzar aplicaciones internas** que nunca debían estar expuestas.

¿Interesado? Contacte por [LinkedIn](https://linkedin.com/in/renatobr).

## Licencia

### Software

El código fuente de este proyecto, incluyendo la aplicación Python, MCP Server,
scripts, Dockerfile, entrypoint y demás componentes de software,
se pone a disposición bajo la MIT License.

### Contenido educativo

La documentación, tutoriales, documentos Markdown, materiales educativos,
contenido destinado a RAG, guiones y demás contenidos no clasificados
como software se ponen a disposición bajo la Creative Commons
Attribution 4.0 International (CC BY 4.0).

### Videos y medios

Los videos y demás materiales multimedia creados específicamente para
este proyecto se ponen a disposición bajo CC BY 4.0.

### Contenido de terceros

Componentes, bibliotecas, modelos, imágenes, videos, textos y otros
materiales de terceros permanecen sujetos a sus respectivas licencias.
La disponibilidad de este repositorio no altera los términos de esas
licencias.

### Uso educativo y de seguridad

Pandora es un laboratorio educativo desarrollado para demostración,
capacitación e investigación de seguridad en entornos controlados y
autorizados.

Las vulnerabilidades, técnicas de explotación, configuraciones inseguras
y datos utilizados en el laboratorio son intencionales y están destinados
al entorno de laboratorio. El operador es responsable de utilizar el
software solo en sistemas y entornos para los cuales posea
autorización.

Los documentos que simulan información personal o confidencial,
incluyendo los datos presentes en `alunos.md` y `politica_interna.md`,
son datos sintéticos destinados exclusivamente a la demostración.
