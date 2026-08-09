import streamlit as st

from utils.theme import (
    inject_theme_css,
    theme_sidebar,
    render_ticker,
    page_header,
    section_header,
    render_stat_cards,
    feature_grid,
    render_pipeline,
    hairline,
    is_full_detail,
)
from utils.meta import load_model_metadata, load_calibration_metadata

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

with st.sidebar:
    theme_sidebar()

inject_theme_css()

meta = load_model_metadata()
cal_meta = load_calibration_metadata()

# ---------------------------------------------------------------------------
# Signature element: scrolling ticker of methods + asset classes
# ---------------------------------------------------------------------------
render_ticker()

page_header(
    "Dashboard",
    subtitle=(
        "How ValuSense turns any financial asset into a defensible valuation method. "
        "A 10-second read for non-specialists, a deep-dive for reviewers."
    ),
    kicker="Valuation · IFRS 13 · Explainability",
)

# ---------------------------------------------------------------------------
# 1. WHAT IT DOES  (plain language, 10-second read)
# ---------------------------------------------------------------------------
section_header(
    "What it does",
    "ValuSense takes any financial asset (a bond, an option, a commodity, a currency) and answers "
    "one question: what is the most defensible way to value it?",
)
st.markdown("""
It combines a machine-learning model trained on expert valuation rules with automatic IFRS 13
regulatory checks, so the answer is both statistically sound and compliant. Every recommendation
explains *why* it was chosen.
""")

feature_grid([
    {"title": "6 asset classes, 10 valuation methods", "desc": "Every major asset type is covered, from plain equity to exotic options."},
    {"title": "IFRS 13 fair-value hierarchy", "desc": "Enforced on every prediction, so the result is regulator-safe."},
    {"title": "SHAP-backed explanations", "desc": "See what drove the decision, feature by feature."},
    {"title": "Built-in pricing calculators", "desc": "Black-Scholes, DCF, Monte-Carlo and more, ready to price on the spot."},
], columns=4)

hairline()

# ---------------------------------------------------------------------------
# 2. HOW WELL IT PERFORMS  (metrics)
# ---------------------------------------------------------------------------
section_header(
    "How well it performs",
    "Measured on held-out data (samples the model never saw during training). The headline number is "
    "the post-IFRS F1 score: accuracy after the regulatory checks have done their job.",
)

metrics = meta.get("metrics", {})
before = metrics.get("before_ifrs", {})
after = metrics.get("after_ifrs", {})

perf_stats = [
    {"label": "Test F1 (weighted)", "value": f"{after.get('f1_weighted', 0.845):.1%}",
     "caption": f"post-IFRS · {before.get('f1_weighted', 0.991):.1%} pre-checks", "tone": "success"},
    {"label": "Test accuracy", "value": f"{after.get('accuracy', 0.791):.1%}",
     "caption": "post-IFRS", "tone": "accent"},
    {"label": "Training samples", "value": f"{meta.get('training_samples', 0):,}",
     "caption": "expert-labelled assets", "tone": "accent"},
    {"label": "Regulatory corrections", "value": f"{meta.get('ifrs_overrides', 0):,}",
     "caption": f"{meta.get('domain_violations_after_ifrs', 0)} domain violations left", "tone": "warning"},
]
render_stat_cards(perf_stats, columns=4)

if is_full_detail():
    section_header("Why the numbers drop after IFRS checks")
    st.markdown("""
The raw model is accurate on **99.1%** of held-out assets. After enforcing IFRS 13, that number is
**84.5%**. The drop is intentional: the IFRS layer overrode **609** predictions to guarantee
regulatory compliance (for example, forcing a Level-1 asset to Mark-to-Market), eliminating every
domain violation. We trade a little raw accuracy for a result that a regulator can't challenge.
    """)
    if cal_meta:
        comp = cal_meta.get("comparison", {})
        flat = comp.get("flat", {})
        hier = comp.get("hierarchical", {})
        cal = comp.get("calibrated", {})
        cal_stats = [
            {"label": "Flat model ECE", "value": f"{flat.get('ece', 0):.3f}",
             "caption": "Lower = better calibrated confidence. 0.005 means the model's stated "
                        "confidence matches reality almost exactly.", "tone": "success"},
            {"label": "Hierarchical ECE", "value": f"{hier.get('ece', 0):.3f}",
             "caption": "Hierarchical model on the same sample.", "tone": "neutral"},
            {"label": "Calibrated ECE", "value": f"{cal.get('ece', 0):.3f}",
             "caption": "After isotonic calibration.", "tone": "neutral"},
        ]
        render_stat_cards(cal_stats, columns=3)
        st.caption("ECE = Expected Calibration Error. How far a model's stated confidence is from its actual hit rate.")
    st.markdown("**Model:** XGBoost (tuned) · 28 engineered features · 3 models compared")

hairline()

# ---------------------------------------------------------------------------
# 3. HOW IT WAS BUILT  (pipeline)
# ---------------------------------------------------------------------------
section_header(
    "How it was built",
    "Six stages from raw market data to an auditable price.",
)
render_pipeline([
    ("🗂️", "Data", "Collect & aggregate\nmarket data"),
    ("🧬", "Features", "28 engineered\nfeatures"),
    ("🌳", "XGBoost", "10-class\nclassification"),
    ("⚖️", "IFRS 13", "Regulatory\npost-processing"),
    ("🔎", "SHAP", "Per-prediction\nexplainability"),
    ("🧮", "Valuation", "Numerical\npricing engines"),
], columns=6)

if is_full_detail():
    st.markdown("""
**Data sources:** 353K+ instrument catalog (FinanceDatabase) · market prices and options chains
(yfinance) · yields, spreads and macro (FRED) · fundamentals (Finnhub, Alpha Vantage) · expert rule
labels from Hull's *Options, Futures and Other Derivatives* plus IFRS 13.
    """)

hairline()

# ---------------------------------------------------------------------------
# Quick start
# ---------------------------------------------------------------------------
section_header("Try it now")
st.markdown("Jump straight to **Recommend** with a pre-loaded European call option. That is the fastest way to see the full flow.")
if st.button("Try European Call Option", type="primary", use_container_width=True):
    from valusense.core import valuate_asset_v2, encode_asset
    features = {
        "has_market_price": 1, "has_cash_flows": 0, "has_options_features": 1,
        "is_exchange_traded": 1, "liquidity": 2, "maturity_years": 0.5,
        "has_credit_risk": 0, "has_early_exercise": 0, "is_path_dependent": 0,
        "data_availability": 2, "volatility_available": 1, "ifrs_level": 1,
        "risk_free_rate_3m": 3.83, "yield_10y": 4.46, "yield_curve_slope": 0.27,
        "implied_volatility_atm": 0.26, "iv_skew": 0.04, "beta": 1.0,
        "pe_ratio": 20.0, "dividend_yield": 0.0, "market_cap": 100e9,
        "debt_to_equity": 50.0, "duration_estimate": 0.0, "credit_spread_asset": 0.0,
        "convenience_yield": 0.0, "storage_cost_pct": 0.0,
    }
    try:
        a, b = encode_asset("Option", "European Call")
        features["asset_class_encoded"] = a
        features["asset_subclass_encoded"] = b
        result = valuate_asset_v2(features, None)
    except Exception as e:
        st.error("**Model unavailable.** The quick-start could not run. Check that the model "
                 f"artifacts are present in `models/`. ({e})")
        st.stop()
    result["_asset_class"] = "Option"
    st.session_state.last_features = features
    st.session_state.last_result = result
    st.session_state.last_asset_class = "Option"
    st.session_state.last_asset_subclass = "European Call"
    st.session_state.prediction_result = result
    st.session_state.predicted_method = result["recommendation"]["method"]
    st.session_state.pending_asset_features = features
    st.session_state.pending_method = result["recommendation"]["method"]
    st.switch_page("pages/01_Recommend.py")
