import streamlit as st
from valusense.config import TARGET_CLASSES, AC_REVERSE
from utils.history import init_history
from utils.theme import inject_theme_css

st.set_page_config(
    page_title="ValuSense - Asset Valuation Method Recommender",
    page_icon="chart_with_upwards_trend",
    layout="wide",
    initial_sidebar_state="expanded",
)

for key, default in [
    ("dark_mode", False),
    ("last_features", None),
    ("last_result", None),
    ("last_asset_class", None),
    ("last_asset_subclass", None),
    ("pending_method", None),
    ("pending_valuation_params", None),
    ("pending_asset_features", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

init_history()

with st.sidebar:
    st.markdown("### Settings")
    dark = st.toggle("Dark mode", value=st.session_state.dark_mode, key="dark_toggle")
    if dark != st.session_state.dark_mode:
        st.session_state.dark_mode = dark
        st.rerun()

    st.markdown("---")
    st.markdown("### Current Asset")
    if st.session_state.last_result is not None:
        cls = st.session_state.last_asset_class or "—"
        sub = st.session_state.last_asset_subclass or "—"
        method = st.session_state.last_result["recommendation"]["method"]
        conf = st.session_state.last_result["recommendation"]["confidence"]
        c = "green" if conf >= 0.8 else ("orange" if conf >= 0.6 else "red")
        st.markdown(f"**Class:** {cls}")
        st.markdown(f"**Subclass:** {sub}")
        st.markdown(f"**Method:** {method}")
        st.markdown(f"**Confidence:** :{c}[{conf:.1%}]")
        if st.button("Clear", use_container_width=True):
            for k in ["last_features", "last_result", "last_asset_class",
                       "last_asset_subclass", "pending_method",
                       "pending_valuation_params", "pending_asset_features"]:
                st.session_state[k] = None
            st.rerun()
    else:
        st.caption("No asset loaded yet. Use **Recommend** to begin.")

inject_theme_css()

st.markdown(f"""
<div class="main-header">
    <h1>ValuSense</h1>
    <p>Intelligent Financial Asset Valuation Method Recommendation</p>
    <p class="sub">ML-powered | IFRS 13 Compliant | SHAP Explainable</p>
</div>
""", unsafe_allow_html=True)
