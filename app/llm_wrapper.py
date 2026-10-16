"""
LLM wrapper — pipeline de defesas D1→D2→(D3+D4 no prompt)→LLM→D5→D6.
Tool discovery dinâmica via MCP Streamable HTTP (sem TOOLS_SCHEMA hardcoded).
"""
import asyncio
import json
import time
import requests
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from logger import new_request_id, log_entry
from providers import get_provider_api, build_chat_url
from rag import get_rag_context
from defenses import (
    d1_input_filter, d2_input_judge,
    LOCK_RULES, d3_sp_lock,
    ALIGNMENT_RULES, d4_sp_alignment,
    d5_output_judge, d6_output_sanitizer,
)

CONFIG_PATH = Path(__file__).parent / "config.json"

# ── Config ────────────────────────────────────────────────────────────────────

def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


# ── Dynamic MCP tool discovery ────────────────────────────────────────────────

_tools_cache: list[dict] | None = None


def invalidate_tools_cache() -> None:
    global _tools_cache
    _tools_cache = None


async def _fetch_tools_schema(mcp_base: str) -> list[dict]:
    url = mcp_base.rstrip("/") + "/mcp"
    async with streamable_http_client(url=url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description or "",
                        "parameters": t.input_schema,
                    },
                }
                for t in result.tools
            ]


def get_tools_schema(mcp_base: str, request_id: str) -> list[dict]:
    global _tools_cache
    if _tools_cache is not None:
        return _tools_cache
    t0 = time.monotonic()
    try:
        _tools_cache = asyncio.run(_fetch_tools_schema(mcp_base))
        elapsed = (time.monotonic() - t0) * 1000
        names = [tool["function"]["name"] for tool in _tools_cache]
        log_entry(request_id, "MCP", "DISCOVERY", f"tools={names}", elapsed)
    except Exception as e:
        elapsed = (time.monotonic() - t0) * 1000
        # FIX: invalida cache para permitir retry na próxima request (não fica travado em erro).
        _tools_cache = None
        log_entry(request_id, "APP", "ERROR",
                  f"MCP discovery: {e} (cache invalidado, retry na proxima request)", elapsed)
        return []
    return _tools_cache


# ── MCP tool call via Streamable HTTP client ──────────────────────────────────

async def _call_tool_async(tool_name: str, args: dict, mcp_base: str) -> str:
    url = mcp_base.rstrip("/") + "/mcp"
    async with streamable_http_client(url=url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, args)
            texts = [c.text for c in result.content if hasattr(c, "text") and c.text]
            # FIX: indicar erro em vez de devolver {} silencioso. LLM não fica confuso/loopando.
            if not texts:
                return json.dumps({"_error": "no_text_content", "_tool": tool_name})
            return texts[0]


def _call_mcp_tool(tool_name: str, args: dict, mcp_base_url: str, request_id: str) -> str:
    t0 = time.monotonic()
    try:
        result = asyncio.run(_call_tool_async(tool_name, args, mcp_base_url))
        elapsed = (time.monotonic() - t0) * 1000
        args_str = json.dumps(args, ensure_ascii=False)
        log_entry(request_id, "MCP", "TOOL_CALL",
                  f"tool={tool_name} args={args_str} result_len={len(result)}",
                  elapsed)
        return result
    except Exception as e:
        elapsed = (time.monotonic() - t0) * 1000
        log_entry(request_id, "APP", "ERROR", f"MCP tool={tool_name}: {e}", elapsed)
        return json.dumps({"error": str(e)})


# ── chat() ────────────────────────────────────────────────────────────────────

def _get_endpoint_format(llm: dict) -> str:
    """Detecta formato de endpoint: gemini-native ou openai-compat (default)."""
    if "endpoint_type" in llm:
        return llm["endpoint_type"]

    base_url = llm.get("base_url", "") or llm.get("url", "")
    if "/v1beta/openai" in base_url:
        return "openai-compat"
    if "generativelanguage.googleapis.com" in base_url or ":generateContent" in base_url:
        return "gemini-native"

    return "openai-compat"


def _call_llm_openai_compat(llm: dict, messages: list, tools: list, rid: str, config: dict) -> dict:
    """Chamada a endpoint OpenAI-compatível (padrão para a maioria)."""
    chat_url = build_chat_url(llm.get("url") or llm["base_url"], llm["model"])

    resp = requests.post(
        chat_url,
        headers={"Authorization": f"Bearer {llm['api_key']}"},
        json={
            "model":       llm["model"],
            "temperature": llm["temperature"],
            "max_tokens":  llm.get("max_tokens", 1024),
            "messages":    messages,
            "tools":       tools,
        },
        timeout=llm.get("timeout", 60),
    )
    resp.raise_for_status()
    return resp.json()


def _convert_messages_to_gemini(messages: list[dict]) -> list[dict]:
    """Converte mensagens OpenAI-format para formato Gemini."""
    gemini_contents = []
    system_prompt = ""

    for msg in messages:
        role = msg.get("role", "user").lower()
        content = msg.get("content", "")

        if role == "system":
            system_prompt += content + "\n\n"
        elif role == "user":
            gemini_contents.append({
                "role": "user",
                "parts": [{"text": content}]
            })
        elif role == "assistant":
            gemini_contents.append({
                "role": "model",
                "parts": [{"text": content}]
            })

    # Adiciona system prompt no começo da primeira mensagem user
    if system_prompt and gemini_contents and gemini_contents[0]["role"] == "user":
        gemini_contents[0]["parts"][0]["text"] = system_prompt + gemini_contents[0]["parts"][0]["text"]

    return gemini_contents


def _call_llm_gemini_native(llm: dict, messages: list, tools: list, rid: str, config: dict) -> dict:
    """Chamada a endpoint nativo do Gemini (v1beta/models/gemini-*:generateContent)."""
    chat_url = build_chat_url(llm.get("url") or llm["base_url"], llm["model"])

    # Converter mensagens para formato Gemini
    gemini_contents = _convert_messages_to_gemini(messages)

    resp = requests.post(
        chat_url,
        params={"key": llm["api_key"]},
        json={
            "contents": gemini_contents,
            "generationConfig": {
                "temperature": llm.get("temperature", 0),
                "maxOutputTokens": llm.get("max_tokens", 1024),
            }
        },
        timeout=llm.get("timeout", 60),
    )
    resp.raise_for_status()
    data = resp.json()

    # Extrair resposta do formato Gemini
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError("Gemini retornou sem candidates")

    content = candidates[0].get("content", {})
    parts = content.get("parts", [])
    response_text = parts[0].get("text", "") if parts else ""

    output_tokens = data.get("usageMetadata", {}).get("outputTokenCount", len(response_text.split()))

    return {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": response_text,
            }
        }],
        "usage": {
            "completion_tokens": output_tokens,
        }
    }


# Mapa extensível de handlers por tipo de endpoint
_ENDPOINT_HANDLERS = {
    "openai-compat": _call_llm_openai_compat,
    "gemini-native": _call_llm_gemini_native,
}


def chat(user_input: str, history: list | None = None) -> str:
    config   = load_config()
    defenses = config.get("defenses", {})
    rid      = new_request_id()

    log_entry(rid, "CHAT", "USER_INPUT", user_input[:100], 0.0)

    try:
        # D1 — Input Filter
        t  = time.monotonic()
        d1 = d1_input_filter(user_input, defenses.get("d1_input_filter", False))
        if defenses.get("d1_input_filter", False):
            if not d1["passed"]:
                log_entry(rid, "D1", "BLOCKED",
                          f"category={d1['blocked_by']} rule={d1.get('rule', '')}",
                          (time.monotonic() - t) * 1000)
            else:
                log_entry(rid, "D1", "PASSED", "", (time.monotonic() - t) * 1000)
        if not d1["passed"]:
            resp = f"⚠️ Mensagem bloqueada (D1 — Input Filter: {d1['blocked_by']})."
            log_entry(rid, "CHAT", "RESPONSE", resp[:150], 0.0)
            return resp

        # D2 — Input Judge
        t  = time.monotonic()
        d2 = d2_input_judge(user_input, config)
        if defenses.get("d2_input_judge", False):
            if not d2.get("safe", True):
                log_entry(rid, "D2", "BLOCKED", d2.get("reason", ""),
                          (time.monotonic() - t) * 1000)
            else:
                log_entry(rid, "D2", "SAFE", d2.get("reason", ""),
                          (time.monotonic() - t) * 1000)
        if not d2.get("safe", True):
            resp = f"⚠️ Mensagem bloqueada (D2 — Input Judge: {d2.get('reason', '')})."
            log_entry(rid, "CHAT", "RESPONSE", resp[:150], 0.0)
            return resp

        # RAG
        rag = get_rag_context(user_input, config, rid)

        system = config["system_prompt"]
        if rag["context"]:
            system += f"\n\nDOCUMENTOS INTERNOS PARA REFERÊNCIA:\n{rag['context']}"

        # D3 — SP Lock (appenda ao system prompt)
        t      = time.monotonic()
        system = d3_sp_lock(system, defenses.get("d3_sp_lock", False))
        if defenses.get("d3_sp_lock", False):
            log_entry(rid, "D3", "APPLIED",
                      f"rules={len(LOCK_RULES)} prompt_len={len(system)}",
                      (time.monotonic() - t) * 1000)

        # D4 — SP Alignment (appenda ao system prompt)
        t      = time.monotonic()
        system = d4_sp_alignment(system, defenses.get("d4_sp_alignment", False))
        if defenses.get("d4_sp_alignment", False):
            log_entry(rid, "D4", "APPLIED",
                      f"rules={len(ALIGNMENT_RULES)} prompt_len={len(system)}",
                      (time.monotonic() - t) * 1000)

        # Montar mensagens
        messages = [{"role": "system", "content": system}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_input})

        log_entry(rid, "CHAT", "LLM_PAYLOAD",
                  json.dumps(messages, ensure_ascii=False), 0.0)

        llm      = config["llm"]
        llm_api  = get_provider_api(llm.get("provider", "ollama"))
        tools    = get_tools_schema(config["mcp"]["base_url"], rid)

        # Auto-detectar formato de endpoint (openai-compat ou ollama-native, etc)
        endpoint_format = _get_endpoint_format(llm)
        endpoint_handler = _ENDPOINT_HANDLERS.get(endpoint_format, _call_llm_openai_compat)

        # Loop de tool calling — tools sempre enviadas; sai quando LLM responde texto.
        # FIX: limite de iterações para evitar loop infinito quando LLM fica chamando tools sem fim.
        MAX_TOOL_ITERATIONS = 5
        output     = ""
        iteration  = 0
        while iteration < MAX_TOOL_ITERATIONS:
            iteration += 1
            log_entry(rid, "APP", "LLM_REQUEST",
                      f"model={llm['model']} messages={len(messages)} tools={bool(tools)} endpoint={endpoint_format} call={iteration}",
                      0.0)
            t = time.monotonic()
            try:
                # Usar handler detectado automaticamente
                data = endpoint_handler(llm, messages, tools, rid, config)
                elapsed = (time.monotonic() - t) * 1000
            except Exception as e:
                elapsed = (time.monotonic() - t) * 1000
                log_entry(rid, "APP", "ERROR", f"LLM call={iteration}: {e}", elapsed)
                return f"Erro ao chamar o LLM: {e}"

            msg = data["choices"][0]["message"]
            tcs = msg.get("tool_calls") or []

            if tcs:
                names = [tc["function"]["name"] for tc in tcs]
                log_entry(rid, "APP", "LLM_RESPONSE",
                          f"tool_call={names} iter={iteration}", elapsed)
                messages.append(msg)
                for tc in tcs:
                    fn_name = tc["function"]["name"]
                    try:
                        fn_args = json.loads(tc["function"].get("arguments", "{}"))
                    except json.JSONDecodeError:
                        fn_args = {}
                    tool_result = _call_mcp_tool(fn_name, fn_args, config["mcp"]["base_url"], rid)
                    messages.append({
                        "role":         "tool",
                        "tool_call_id": tc["id"],
                        "content":      tool_result,
                    })
                continue

            output = msg.get("content") or ""
            log_entry(rid, "APP", "LLM_RESPONSE",
                      f"text len={len(output)} iter={iteration}", elapsed)
            break
        else:
            # FIX: loop esgotou MAX_TOOL_ITERATIONS sem LLM dar resposta textual.
            # Em vez de loopar eternamente, retorna mensagem e loga o sintoma.
            log_entry(rid, "APP", "ERROR",
                      f"tool-calling loop excedeu {MAX_TOOL_ITERATIONS} iteracoes sem resposta textual", 0.0)
            output = "⚠️ O assistente excedeu o número máximo de iterações de tool-calling. Tente reformular a pergunta."

        # D5 — Output Judge
        t  = time.monotonic()
        d5 = d5_output_judge(output, config)
        if defenses.get("d5_output_judge", False):
            if not d5.get("safe", True):
                log_entry(rid, "D5", "UNSAFE",
                          f"reason={d5.get('reason', '')} | redacted",
                          (time.monotonic() - t) * 1000)
            else:
                log_entry(rid, "D5", "SAFE", d5.get("reason", ""),
                          (time.monotonic() - t) * 1000)
        if not d5.get("safe", True):
            output = d5.get("redacted", output)

        # D6 — Output Sanitizer
        t              = time.monotonic()
        output, d6_n   = d6_output_sanitizer(output, defenses.get("d6_output_sanitizer", False))
        if defenses.get("d6_output_sanitizer", False):
            action = "REDACTED" if d6_n > 0 else "CLEAN"
            log_entry(rid, "D6", action, f"patterns={d6_n}",
                      (time.monotonic() - t) * 1000)

        log_entry(rid, "CHAT", "RESPONSE", output[:150], 0.0)
        return output

    except Exception as e:
        log_entry(rid, "APP", "ERROR", str(e), 0.0)
        raise
