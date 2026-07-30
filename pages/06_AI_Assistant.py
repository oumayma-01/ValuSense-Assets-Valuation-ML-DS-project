import streamlit as st
from utils.theme import inject_theme_css

st.set_page_config(page_title="AI Assistant", page_icon="robot", layout="wide")
inject_theme_css()
st.title("ValuSense AI Assistant")

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "orchestrator_ready" not in st.session_state:
    st.session_state.orchestrator_ready = False

with st.sidebar:
    st.markdown("### About")
    st.markdown(
        "The AI Assistant connects ValuSense to Claude (Anthropic). "
        "It can classify assets, check IFRS compliance, explain predictions, "
        "run valuations, and answer conceptual questions from the knowledge base."
    )
    if st.button("Clear chat", use_container_width=True):
        st.session_state.chat_messages = []
        st.rerun()

for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "citations" in msg and msg["citations"]:
            with st.expander("Sources", expanded=False):
                for c in msg["citations"]:
                    st.markdown(f"- {c}")

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
                    st.error(f"Failed to load AI engine: {e}")
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": f"Error initializing AI engine: {e}",
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
            except Exception as e:
                err_msg = f"Error: {e}"
                st.error(err_msg)
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": err_msg,
                    "citations": [],
                })
