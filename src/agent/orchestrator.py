import os
import json
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()

try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except Exception:
    OpenAI = None
    _OPENAI_AVAILABLE = False


def _get_secret(key: str):
    """Resolve an API key from Streamlit secrets, falling back to env vars.

    Works identically on Streamlit Community Cloud (st.secrets / Settings →
    Secrets) and on a local run (.env file). Never hardcodes a key here.
    """
    try:
        import streamlit as st
        secrets = getattr(st, "secrets", {})
        if key in secrets:
            return secrets[key]
    except Exception:
        pass
    return os.environ.get(key)

# ---------------------------------------------------------------------------
# Provider chain — all use OpenAI-compatible clients, so the tool set is identical.
# Primary: Groq. Fallback: OpenAI. Final fallback: Anthropic (Claude).
# ---------------------------------------------------------------------------
_PROVIDERS = [
    {
        "name": "Groq",
        "env_key": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama-3.3-70b-versatile",
    },
    {
        "name": "OpenAI",
        "env_key": "OPENAI_API_KEY",
        "base_url": None,
        "model": "gpt-4o-mini",
    },
    {
        "name": "Anthropic (Claude)",
        "env_key": "ANTHROPIC_API_KEY",
        "base_url": "https://api.anthropic.com/v1",
        "model": "claude-3-5-sonnet-20241022",
    },
]

NO_KEY_MESSAGE = (
    "The AI assistant needs an API key, but none was found. Add **GROQ_API_KEY**, "
    "**OPENAI_API_KEY**, or **ANTHROPIC_API_KEY** to your `.env` file (or to "
    "**Streamlit Secrets** → Settings → Secrets), then restart the app. "
    "All the other ValuSense features work without it."
)

DEPS_MESSAGE = (
    "The AI assistant's dependencies are not installed. Install them with "
    "`pip install -r requirements-web.txt` (at minimum `openai`), then restart the app. "
    "All the other ValuSense features work without it."
)


def provider_status() -> Optional[str]:
    """Return the name of the active provider, or None if the assistant can't run
    (missing API key or missing `openai` package)."""
    if not _OPENAI_AVAILABLE:
        return None
    for p in _PROVIDERS:
        if _get_secret(p["env_key"]):
            return p["name"]
    return None


def active_provider_info() -> Optional[dict]:
    """Return {"name", "model"} for the active provider, or None if unavailable."""
    provider, _ = _active_provider()
    if provider is None:
        return None
    return {"name": provider["name"], "model": provider["model"]}


def provider_block_message() -> str:
    if not _OPENAI_AVAILABLE:
        return DEPS_MESSAGE
    return NO_KEY_MESSAGE


def _active_provider():
    for p in _PROVIDERS:
        key = _get_secret(p["env_key"])
        if key:
            return p, key
    return None, None


def get_agent_client() -> OpenAI:
    if not _OPENAI_AVAILABLE:
        raise RuntimeError(DEPS_MESSAGE)
    provider, key = _active_provider()
    if provider is None:
        raise RuntimeError(NO_KEY_MESSAGE)
    if provider["base_url"]:
        return OpenAI(api_key=key, base_url=provider["base_url"])
    return OpenAI(api_key=key)


from src.agent.tool_definitions import TOOL_DEFINITIONS as ANTHROPIC_TOOLS

SYSTEM_PROMPT = """You are ValuSense AI, an expert financial valuation assistant.

You help users classify financial assets, recommend IFRS 13-compliant valuation methods,
explain predictions, run numerical valuations, and answer questions using a knowledge base.

## Language
- ALWAYS respond in English, no matter what language the user writes in.
- Only use English-language sources from the knowledge base. Never quote French documents or
  French source titles in your answer.
- If a retrieved passage is not in English, paraphrase and translate the key points into English
  yourself, without exposing the French source.

## Your tools

### Asset valuation tools (call these for hands-on computation)
1. `classify_asset` - Classify an asset and predict the best valuation method.
   Call this FIRST before any valuation. The user must describe the asset; extract features
   from their description. Required: asset_class, asset_subclass, ifrs_level, has_market_price,
   has_cash_flows, has_options_features, is_exchange_traded, liquidity, maturity_years,
   volatility_available, data_availability. Auto-fill sensible defaults for any missing fields.

2. `check_ifrs_compliance` - Confirm the predicted method complies with IFRS 13.
   Call this after classify_asset. Returns whether an override was applied and why.

3. `explain_prediction` - Provide SHAP-based explanation for the recommended method.
   Use when the user asks "why" a method was chosen.

4. `run_valuation` - Run a numerical calculation using a specific method.
   Call classify_asset first to determine the right method. Collect required params from the user.

### Knowledge retrieval tool
5. `retrieve_knowledge` - Search the ValuSense knowledge base (Hull textbook, regulatory
   frameworks, IFRS guidelines, valuation methodologies) for answers to conceptual questions.
   Use this for questions like "What is Black-Scholes?", "How does IFRS 13 work?",
   "What are the types of options?", etc. Always cite the source when presenting knowledge.

## Guidelines
- Always call classify_asset before any valuation-related tools.
- If the user asks a conceptual question, use retrieve_knowledge.
- Be concise and professional. Use clear headings and formatting.
- When citing knowledge, include source name and page number.
- If the user's query is ambiguous, ask clarifying questions.
- If a tool returns an error, explain it to the user and suggest corrections."""


def _to_openai_tool(anthropic_tool: dict) -> dict:
    """Convert an Anthropic tool definition to OpenAI function-calling format."""
    params = dict(anthropic_tool.get("input_schema", {}))
    required = params.get("required", [])
    props = params.get("properties", {})
    return {
        "type": "function",
        "function": {
            "name": anthropic_tool["name"],
            "description": anthropic_tool.get("description", ""),
            "parameters": {
                "type": "object",
                "properties": props,
                "required": list(required) if required else [],
            },
        },
    }


def _build_tools() -> list:
    oai_tools = [_to_openai_tool(t) for t in ANTHROPIC_TOOLS]
    oai_tools.append(
        {
            "type": "function",
            "function": {
                "name": "retrieve_knowledge",
                "description": "Search the ValuSense knowledge base for conceptual answers about financial valuation, IFRS, derivatives, and asset classification. Returns up to 4 English-language passages from textbooks, regulatory docs, and internal methodology guides.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query (natural language, in English).",
                        },
                        "source_filter": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional. Restrict search to specific English-language sources. Common values: 'Hull', 'Financial Asset Valuation Framework.docx'.",
                        },
                    },
                    "required": ["query"],
                },
            },
        }
    )
    return oai_tools


TOOLS = _build_tools()


def _load_tool_handlers():
    """Lazily import the heavy valusense-backed tools so the app stays responsive
    (and doesn't load the ML models) until the assistant is actually used."""
    from src.agent.tools import (
        classify_asset,
        check_ifrs_compliance,
        explain_prediction,
        run_valuation,
    )
    from src.agent.knowledge_base import retrieve_knowledge

    return {
        "classify_asset": classify_asset,
        "check_ifrs_compliance": check_ifrs_compliance,
        "explain_prediction": explain_prediction,
        "run_valuation": run_valuation,
        "retrieve_knowledge": retrieve_knowledge,
    }


_FEATURES_TOOLS = {"classify_asset", "check_ifrs_compliance", "explain_prediction"}

_SKIP_FEATURE_KEYS = {"method", "predicted_method"}


def _coerce_feature_values(features: dict) -> dict:
    """Coerce string flags/numbers ("0", "2", "0.5") to int/float so downstream
    validators (e.g. `ifrs_level in (1, 2, 3)`) accept LLM-provided values."""
    coerced = {}
    for k, v in features.items():
        if isinstance(v, str):
            if v in ("0", "1", "2", "3"):
                coerced[k] = int(v)
            else:
                try:
                    coerced[k] = float(v)
                except (TypeError, ValueError):
                    coerced[k] = v
        else:
            coerced[k] = v
    return coerced


def _normalize_tool_args(tool_name: str, tool_input: dict) -> dict:
    """Some models flatten a tool's nested `features` object into top-level
    fields. Accept that form by wrapping them back into a `features` dict."""
    if tool_name not in _FEATURES_TOOLS:
        return tool_input
    if "features" in tool_input:
        if isinstance(tool_input["features"], dict):
            tool_input["features"] = _coerce_feature_values(tool_input["features"])
        return tool_input
    top_level = {
        k: v for k, v in tool_input.items()
        if k not in _SKIP_FEATURE_KEYS
    }
    if not top_level:
        return tool_input
    return {
        "features": _coerce_feature_values(top_level),
        **{k: v for k, v in tool_input.items() if k in _SKIP_FEATURE_KEYS},
    }


def _handle_tool_call(tool_name: str, tool_input: dict, handlers: dict) -> str:
    tool_input = _normalize_tool_args(tool_name, tool_input)
    if tool_name == "retrieve_knowledge":
        results = handlers["retrieve_knowledge"](
            tool_input.get("query", ""),
            k=4,
            source_filter=tool_input.get("source_filter"),
            languages=["en"],
        )
        result = {
            "results": [
                {
                    "text": r["text"],
                    "source": r["source"],
                    "citation": r["citation"],
                    "score": r["score"],
                }
                for r in results
            ]
        }
    elif tool_name in handlers:
        result = handlers[tool_name](**tool_input)
    else:
        result = {"error": f"Unknown tool: {tool_name}"}
    return json.dumps(result, ensure_ascii=False, default=str)


def run_agent(
    user_message: str,
    history: Optional[List[dict]] = None,
    max_tool_rounds: int = 8,
    model: Optional[str] = None,
) -> tuple[str, List[dict]]:
    if not _OPENAI_AVAILABLE:
        raise RuntimeError(DEPS_MESSAGE)
    provider, key = _active_provider()
    if provider is None:
        raise RuntimeError(NO_KEY_MESSAGE)

    if history is None:
        history = []

    client = OpenAI(
        api_key=key,
        base_url=provider["base_url"],
    ) if provider["base_url"] else OpenAI(api_key=key)

    effective_model = model or provider["model"]

    messages = list(history)
    messages.append({"role": "user", "content": user_message})

    handlers = _load_tool_handlers()

    for _ in range(max_tool_rounds):
        resp = client.chat.completions.create(
            model=effective_model,
            max_tokens=4096,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, *messages],
            tools=TOOLS,
        )

        choice = resp.choices[0]
        msg = choice.message

        if not msg.tool_calls:
            messages.append({"role": "assistant", "content": msg.content or ""})
            return msg.content or "", messages

        messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": [
            {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in msg.tool_calls
        ]})

        for tc in msg.tool_calls:
            tool_name = tc.function.name
            try:
                tool_input = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                tool_input = {}
            tool_result = _handle_tool_call(tool_name, tool_input, handlers)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": tool_result,
            })

    return "I've reached the maximum number of reasoning steps. Please try a simpler query.", messages
