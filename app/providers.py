"""Mapeamento de providers → endpoints e formatos de API."""

import re

_OPENAI_COMPAT = {
    "embed_input_field": "input",
    "embed_nested":      True,
    "response_style":    "openai",
}

_OLLAMA = {
    "embed_input_field": "prompt",
    "embed_nested":      False,
    "response_style":    "openai",
}

PROVIDERS: dict[str, dict] = {
    "ollama-local":       _OLLAMA,
    "ollama-remote":      _OLLAMA,
    "ollama-on-notebook": _OLLAMA,
    "openai":             _OPENAI_COMPAT,
    "gemini":             _OPENAI_COMPAT,
}


def get_provider_api(provider: str) -> dict:
    """Retorna config de API do provider. Default: OpenAI-compatible."""
    return PROVIDERS.get(provider, _OPENAI_COMPAT)


# ── URL helpers ──────────────────────────────────────────────────────────────

_KNOWN_SUFFIXES = [
    "/v1/chat/completions",
    "/v1/embeddings",
    "/api/embeddings",
    "/api/generate",
    "/api/text",
    "/v1",
]

def _normalize_base(url: str) -> str:
    """Strip known endpoint paths to get just the server base URL.
    Accepts both old full URLs and new server-only URLs."""
    url = url.rstrip("/")
    for suffix in _KNOWN_SUFFIXES:
        if url.endswith(suffix):
            return url[:-len(suffix)]
    url = re.sub(r'/v1beta/models/[^/]+:(generateContent|embedContent)$', '', url)
    return url


def _is_gemini_native(url: str) -> bool:
    return "generativelanguage.googleapis.com" in url and "/v1beta/openai" not in url


def _gemini_openai_base(url: str) -> str:
    """Extract .../v1beta/openai from a URL that contains it."""
    idx = url.index("/v1beta/openai")
    return url[:idx + len("/v1beta/openai")]


def build_chat_url(base_url: str, model: str = "") -> str:
    if "/v1beta/openai" in base_url:
        return f"{_gemini_openai_base(base_url)}/chat/completions"
    base = _normalize_base(base_url)
    if _is_gemini_native(base):
        return f"{base}/v1beta/models/{model}:generateContent"
    return f"{base}/v1/chat/completions"


def build_embedding_url(base_url: str, model: str = "", provider: str = "") -> str:
    if "/v1beta/openai" in base_url:
        return f"{_gemini_openai_base(base_url)}/embeddings"
    base = _normalize_base(base_url)
    if _is_gemini_native(base):
        return f"{base}/v1beta/models/{model}:embedContent"
    if provider.startswith("ollama"):
        return f"{base}/api/embeddings"
    return f"{base}/v1/embeddings"


def build_sdk_base(base_url: str) -> str:
    """For OpenAI SDK (judge in defenses.py) — returns server/v1 or .../v1beta/openai."""
    if "/v1beta/openai" in base_url:
        return _gemini_openai_base(base_url)
    base = _normalize_base(base_url)
    return f"{base}/v1"
