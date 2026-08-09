import streamlit as st
from utils.history import init_history
from utils.theme import (
    inject_theme_css,
    theme_sidebar,
    render_stat_cards,
    section_header,
    feature_grid,
    hairline,
    badge,
    AUDIENCE_QUICK,
)
from utils.meta import hero_stats

st.set_page_config(
    page_title="ValuSense - Asset Valuation Method Recommender",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

for key, default in [
    ("audience_mode", AUDIENCE_QUICK),
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
    theme_sidebar()
    st.markdown("---")
    st.markdown("### Current Asset")
    if st.session_state.last_result is not None:
        cls = st.session_state.last_asset_class or "Not set"
        sub = st.session_state.last_asset_subclass or "Not set"
        method = st.session_state.last_result["recommendation"]["method"]
        conf = st.session_state.last_result["recommendation"]["confidence"]
        tone = "success" if conf >= 0.8 else "warning"
        st.markdown(f"**Class:** {cls}")
        st.markdown(f"**Subclass:** {sub}")
        st.markdown(f"**Method:** `{method}`")
        st.markdown(badge(f"{conf:.0%} confidence", tone=tone), unsafe_allow_html=True)
        if st.button("Clear", use_container_width=True):
            for k in ["last_features", "last_result", "last_asset_class",
                       "last_asset_subclass", "pending_method",
                       "pending_valuation_params", "pending_asset_features"]:
                st.session_state[k] = None
            st.rerun()
    else:
        st.caption("No asset analyzed yet.")
        if st.button("Analyze an asset", use_container_width=True):
            st.switch_page("pages/01_Recommend.py")

inject_theme_css()

stats = hero_stats()
for stat in stats:
    stat.setdefault("tone", "accent")

st.markdown("""
<div class="main-header">
    <h1>ValuSense</h1>
    <p class="hero-prop">Recommends the right valuation method for any financial asset, with IFRS 13
    compliance and SHAP-backed explanations. Built for a fintech workflow, not a black box.</p>
    <p class="sub">ML-POWERED · IFRS 13 COMPLIANT · SHAP EXPLAINABLE</p>
</div>
""", unsafe_allow_html=True)

render_stat_cards(stats, columns=5)

hairline()
c1, c2 = st.columns([2, 1])
with c1:
    section_header("What is ValuSense?")
    st.markdown("""
Choosing the wrong valuation method, applying Black-Scholes to a bond, or DCF to an exotic
option, produces unreliable numbers and exposes a firm to regulatory risk. ValuSense removes the
guesswork: describe any financial asset, and it **recommends the most defensible valuation
method**, explains *why* in plain language, enforces IFRS 13 fair-value rules automatically, and
can price the asset on the spot.
    """)
    feature_grid([
        {"title": "10 valuation methods", "desc": "The full pricing toolkit: DCF, Black-Scholes, Monte-Carlo and more."},
        {"title": "6 asset classes", "desc": "Equity, bond, option, commodity, currency, derivative."},
        {"title": "IFRS 13 built in", "desc": "Fair-value hierarchy enforced on every prediction."},
        {"title": "SHAP explanations", "desc": "See what drove each recommendation, feature by feature."},
    ], columns=4)
with c2:
    section_header("Where to start")
    if st.button("Recommend a valuation method", type="primary", use_container_width=True):
        st.switch_page("pages/01_Recommend.py")
    if st.button("See it proven: 10 scenarios", use_container_width=True):
        st.switch_page("pages/03_Scenarios.py")
    if st.button("Talk to the AI assistant", use_container_width=True):
        st.switch_page("pages/04_AI_Assistant.py")
    st.caption("Deep-dive for finance reviewers: Model Insights.")

st.markdown(
    "<div style='margin-top:2.5rem; border-top:1px solid var(--border); padding-top:0.9rem;'>"
    "<p class='fc-desc'>ValuSense is a decision-support tool and is not a substitute for "
    "professional judgment.</p></div>",
    unsafe_allow_html=True,
)
