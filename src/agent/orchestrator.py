import os
import json
from typing import List, Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.environ.get("XAI_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "XAI_API_KEY not set. Add it to .env or set the environment variable."
    )

client = OpenAI(base_url="https://api.x.ai/v1", api_key=API_KEY)

from src.agent.tools import (
    classify_asset,
    check_ifrs_compliance,
    explain_prediction,
    run_valuation,
)
from src.agent.tool_definitions import TOOL_DEFINITIONS as ANTHROPIC_TOOLS
from src.agent.knowledge_base import retrieve_knowledge

SYSTEM_PROMPT = """You are ValuSense AI, an expert financial valuation assistant.

You help users classify financial assets, recommend IFRS 13-compliant valuation methods,
explain predictions, run numerical valuations, and answer questions using a knowledge base.

## Your tools

### Asset valuation tools (call these for hands-on computation)
1. `classify_asset` — Classify an asset and predict the best valuation method.
   Call this FIRST before any valuation. The user must describe the asset; extract features
   from their description. Required: asset_class, asset_subclass, ifrs_level, has_market_price,
   has_cash_flows, has_options_features, is_exchange_traded, liquidity, maturity_years,
   volatility_available, data_availability. Auto-fill sensible defaults for any missing fields.

2. `check_ifrs_compliance` — Confirm the predicted method complies with IFRS 13.
   Call this after classify_asset. Returns whether an override was applied and why.

3. `explain_prediction` — Provide SHAP-based explanation for the recommended method.
   Use when the user asks "why" a method was chosen.

4. `run_valuation` — Run a numerical calculation using a specific method.
   Call classify_asset first to determine the right method. Collect required params from the user.

### Knowledge retrieval tool
5. `retrieve_knowledge` — Search the ValuSense knowledge base (Hull textbook, regulatory
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
                "description": "Search the ValuSense knowledge base for conceptual answers about financial valuation, IFRS, derivatives, and asset classification. Returns up to 4 relevant passages from textbooks, regulatory docs, and internal methodology guides.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query (natural language, in English or French).",
                        },
                        "source_filter": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional. Restrict search to specific sources. Values: 'Hull', 'Cadre de Valorisation des Actifs Financiers.docx', 'Financial Asset Valuation Framework.docx', 'Méthodes de Valorisation des Actifs Financiers'.",
                        },
                    },
                    "required": ["query"],
                },
            },
        }
    )
    return oai_tools


TOOLS = _build_tools()


def _handle_tool_call(tool_name: str, tool_input: dict) -> str:
    if tool_name == "classify_asset":
        result = classify_asset(**tool_input)
    elif tool_name == "check_ifrs_compliance":
        result = check_ifrs_compliance(**tool_input)
    elif tool_name == "explain_prediction":
        result = explain_prediction(**tool_input)
    elif tool_name == "run_valuation":
        result = run_valuation(**tool_input)
    elif tool_name == "retrieve_knowledge":
        results = retrieve_knowledge(
            tool_input.get("query", ""),
            k=4,
            source_filter=tool_input.get("source_filter"),
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
    else:
        result = {"error": f"Unknown tool: {tool_name}"}
    return json.dumps(result, ensure_ascii=False, default=str)


def run_agent(
    user_message: str,
    history: Optional[List[dict]] = None,
    max_tool_rounds: int = 8,
    model: str = "grok-3",
) -> tuple[str, List[dict]]:
    if history is None:
        history = []

    messages = list(history)
    messages.append({"role": "user", "content": user_message})

    for _ in range(max_tool_rounds):
        resp = client.chat.completions.create(
            model=model,
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
            tool_result = _handle_tool_call(tool_name, tool_input)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": tool_result,
            })

    return "I've reached the maximum number of reasoning steps. Please try a simpler query.", messages
