import streamlit as st

from utils.theme import (
    inject_theme_css,
    theme_sidebar,
    page_header,
    feature_grid,
)

from src.agent.orchestrator import (
    provider_status,
    provider_block_message,
    active_provider_info,
)

st.set_page_config(page_title="AI Assistant", page_icon="🤖", layout="wide")

with st.sidebar:
    theme_sidebar()
    st.markdown("---")
    st.markdown("### About")
    st.markdown(
        "The AI assistant connects ValuSense to a large language model (Groq by default, "
        "with OpenAI and Anthropic as automatic fallbacks). It can classify assets, check IFRS "
        "compliance, explain predictions, run valuations, and answer conceptual questions from "
        "the knowledge base."
    )

active_provider = provider_status()
provider_info = active_provider_info()
if provider_info:
    st.sidebar.caption(
        f"Active provider: **{provider_info['name']}** · Model: `{provider_info['model']}`"
    )
elif active_provider:
    st.sidebar.caption(f"Active provider: **{active_provider}**")
if st.sidebar.button("Clear chat", width="stretch"):
    st.session_state.chat_messages = []
    st.rerun()

inject_theme_css()

page_header(
    "ValuSense AI Assistant",
    "Ask ValuSense to classify an asset, check IFRS 13 compliance, explain a prediction, "
    "run a valuation, or answer a conceptual finance question, with citations from the "
    "knowledge base (Hull's *Options, Futures and Other Derivatives* and the valuation "
    "framework docs).",
    kicker="RAG · IFRS 13 · Explainability",
)

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "orchestrator_ready" not in st.session_state:
    st.session_state.orchestrator_ready = False

if active_provider is None:
    block_msg = provider_block_message()
    st.warning(f"**AI assistant unavailable.** {block_msg}")
    st.markdown("#### What it would do once configured:")
    feature_grid([
        {"title": "Recommend a method",
         "desc": "\"Recommend a method for a European call option on a large cap stock\": classifies, checks IFRS, explains."},
        {"title": "Explain a prediction",
         "desc": "\"Why did it choose DCF over Black-Scholes?\": a SHAP-based explanation."},
        {"title": "Answer from the knowledge base",
         "desc": "\"What is the Cost-of-Carry model?\": an answer with citations from Hull."},
    ], columns=3)
    st.stop()

for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "citations" in msg and msg["citations"]:
            with st.expander("Sources", expanded=True):
                for c in msg["citations"]:
                    st.markdown(f"- {c}")

if provider_info:
    st.caption(f"Answered by **{provider_info['name']}** (`{provider_info['model']}`)")

st.info(
    "**Privacy note:** do not enter confidential, proprietary, or real client asset data in "
    "this chat. The assistant is a demonstration tool."
)

if prompt := st.chat_input("Ask about valuation, IFRS, asset classification..."):
    st.session_state.chat_messages.append({"role": "user", "content": prompt, "citations": []})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if not st.session_state.orchestrator_ready:
            with st.spinner("Loading AI engine (first load may take ~30s)..."):
                try:
                    from src.agent.orchestrator import run_agent
                    st.session_state.orchestrator_ready = True
                except Exception as e:
                    st.error(f"Failed to load the AI engine: {e}")
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": f"Error initializing the AI engine: {e}",
                        "citations": [],
                    })
                    st.stop()

        with st.spinner("Thinking..."):
            try:
                text, _ = run_agent(prompt)
                st.markdown(text)
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": text,
                    "citations": [],
                })
            except RuntimeError as e:
                msg = str(e)
                st.error(msg)
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": msg,
                    "citations": [],
                })
            except Exception as e:
                err_msg = f"Something went wrong while answering: {e}"
                st.error(err_msg)
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": err_msg,
                    "citations": [],
                })
