#!/usr/bin/env python3
"""
Gera cheat-sheet-pandora_v0_5.html — versão autossuficiente (offline) com Wiki + Demo.
CSS inline, imagens em base64, abas Wiki/Demo, todas as seções abertas.
"""
import base64
import re
from pathlib import Path

ROOT    = Path(__file__).parent.parent
APP     = ROOT / "app"
WIKI    = APP / "templates" / "wiki.html"
DEMO    = APP / "templates" / "demo.html"
CSS     = APP / "static" / "style.css"
BANNER  = APP / "static" / "Banner-pandora-1920x480.png"
FAVICON = APP / "static" / "favicon-pandora-48x48.png"
OUT     = ROOT / "cheat-sheet-pandora_v0_5.html"


def b64_data_uri(path: Path, mime: str) -> str:
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def extract_main(html: str) -> str:
    m = re.search(r"<main>(.*?)</main>", html, re.DOTALL)
    return m.group(1).strip() if m else html


def main() -> None:
    css  = CSS.read_text(encoding="utf-8")
    wiki = WIKI.read_text(encoding="utf-8")
    demo = DEMO.read_text(encoding="utf-8")

    banner_uri  = b64_data_uri(BANNER,  "image/png")
    favicon_uri = b64_data_uri(FAVICON, "image/png")

    # Remove Google Fonts — funciona sem internet
    css = re.sub(r"@import url\('https://fonts\.googleapis\.com/[^']+'\);?\n?", "", css)
    css = css.replace("'Inter', 'Segoe UI', sans-serif",
                      "'Segoe UI', 'Helvetica Neue', Arial, sans-serif")
    css = css.replace("'JetBrains Mono', 'Fira Code', monospace",
                      "'Courier New', Courier, monospace")

    wiki_body = extract_main(wiki)
    demo_body = extract_main(demo)

    # Troca imagens por base64
    for src in (wiki_body, demo_body):
        pass  # feito abaixo com replace direto
    wiki_body = wiki_body.replace('src="/static/Banner-pandora-1920x480.png"', f'src="{banner_uri}"')
    demo_body = demo_body.replace('src="/static/Banner-pandora-1920x480.png"', f'src="{banner_uri}"')

    # Links internos que não funcionam offline → desativa ou troca por aba
    demo_body = demo_body.replace('href="/wiki"', 'href="javascript:switchTab(\'wiki\')"')
    for page in ("/chat", "/admin", "/cursos", "/demo", "/wiki"):
        wiki_body = wiki_body.replace(f'href="{page}"', 'href="#"')
        demo_body = demo_body.replace(f'href="{page}"', 'href="#"')

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pandora — Cheat Sheet</title>
<link rel="icon" type="image/png" href="{favicon_uri}">
<style>
{css}

/* ── CHEAT-SHEET EXTRAS ── */
body {{
    padding-top: 60px;
}}
.cs-tabs {{
    display: flex;
    gap: 0;
    background: var(--bg-secondary);
    border-bottom: 2px solid var(--border);
    padding: 0 2rem;
    position: sticky;
    top: 60px;
    z-index: 90;
}}
.cs-tab {{
    padding: 0.65rem 1.8rem;
    cursor: pointer;
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text-secondary);
    border-bottom: 2px solid transparent;
    margin-bottom: -2px;
    transition: color 0.2s, border-color 0.2s;
    user-select: none;
}}
.cs-tab:hover {{ color: var(--text-primary); }}
.cs-tab.active {{ color: var(--neon-orange); border-bottom-color: var(--neon-orange); }}
.cs-page {{ display: none; }}
.cs-page.active {{ display: block; }}
.cs-badge {{
    position: fixed;
    top: 20px;
    right: 1.2rem;
    font-family: 'Courier New', monospace;
    font-size: 0.65rem;
    color: var(--neon-green);
    opacity: 0.65;
    z-index: 200;
    letter-spacing: 1px;
}}
.cs-page .page-content {{
    padding-top: 1.5rem;
}}
</style>
</head>
<body>
<header>
  <span class="logo">
    <img src="{banner_uri}" alt="Pandora Academy">
    <span class="app-version">v0.5</span>
  </span>
</header>
<span class="cs-badge">OFFLINE · CHEAT-SHEET</span>
<div class="cs-tabs">
  <div class="cs-tab active" onclick="switchTab('wiki')">Wiki</div>
  <div class="cs-tab"        onclick="switchTab('demo')">Demo</div>
</div>

<div id="page-wiki" class="cs-page active">
{wiki_body}
</div>
<div id="page-demo" class="cs-page">
{demo_body}
</div>

<script>
function switchTab(name) {{
  ['wiki','demo'].forEach(function(n,i) {{
    document.querySelectorAll('.cs-tab')[i].classList.toggle('active', n === name);
    document.getElementById('page-' + n).classList.toggle('active', n === name);
  }});
  window.scrollTo(0, 0);
}}
function toggleSection(header)    {{ header.parentElement.classList.toggle('open'); }}
function toggleSubSection(header) {{ header.parentElement.classList.toggle('open'); }}
function toggleDemoBlock(header)  {{ header.parentElement.classList.toggle('open'); }}

</script>
</body>
</html>"""

    OUT.write_text(html, encoding="utf-8")
    kb = len(html.encode("utf-8")) / 1024
    print(f"[OK] {OUT.name} gerado ({kb:.0f} KB) — abas Wiki + Demo, {len(html)} chars")


if __name__ == "__main__":
    main()
