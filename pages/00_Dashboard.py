import streamlit as st
import json
from pathlib import Path
import pandas as pd

st.set_page_config(page_title="Dashboard", page_icon="chart_with_upwards_trend", layout="wide")

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"
FIG_DIR = REPORTS_DIR / "figures"

meta = {}
meta_path = MODELS_DIR / "model_metadata.json"
if meta_path.exists():
    with open(meta_path) as f:
        meta = json.load(f)

cal_meta = None
cal_path = MODELS_DIR / "metadata_calibrated_v3_calibrated.json"
if cal_path.exists():
    with open(cal_path) as f:
        cal_meta = json.load(f)

from utils.theme import inject_theme_css
inject_theme_css()
st.title("Dashboard")

st.markdown("""
<div style='font-size:1.2rem;margin-bottom:1rem'>
<strong>ValuSense</strong> automatically recommends the optimal valuation method for any financial asset —
powered by XGBoost, SHAP explainability, and IFRS 13 fair value hierarchy enforcement.
</div>
""", unsafe_allow_html=True)

cols = st.columns(4)
metrics = [
    ("Test F1 (weighted)", f"{meta.get('metrics', {}).get('before_ifrs', {}).get('f1_weighted', 0.991):.1%}", "green"),
    ("Calibration ECE", f"{cal_meta.get('comparison', {}).get('flat', {}).get('ece', 0.033):.3f}", "orange" if cal_meta else "gray"),
    ("Training Samples", f"{meta.get('training_samples', 12207):,}", "blue"),
    ("Valuation Methods", f"{meta.get('n_classes', 10)}", "purple"),
]
for col, (label, val, color) in zip(cols, metrics):
    col.markdown(
        f"<div class='kpi-card' style='--kpi-color:{color}'>"
        f"<div class='kpi-label'>{label}</div>"
        f"<div class='kpi-value' style='color:{color}'>{val}</div></div>",
        unsafe_allow_html=True,
    )

st.markdown("## Pipeline")
cols = st.columns(6)
steps = [
    ("Data", "Collect & aggregate\nmarket data"),
    ("Features", "28 engineered\nfeatures"),
    ("XGBoost", "10-class\nclassification"),
    ("IFRS 13", "Regulatory\npost-processing"),
    ("SHAP", "Per-prediction\nexplainability"),
    ("Valuation", "Numerical\npricing engines"),
]
for col, (title, desc) in zip(cols, steps):
    with col:
        st.markdown(
            f"<div class='pipeline-step'>"
            f"<div class='title'>{title}</div>"
            f"<div class='desc'>{desc}</div></div>",
            unsafe_allow_html=True,
        )

st.markdown("## Quick Start: Try It Now")
st.markdown("Click below to jump straight to **Recommend** with a pre-loaded European call option.")
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
    a, b = encode_asset("Option", "European Call")
    features["asset_class_encoded"] = a
    features["asset_subclass_encoded"] = b
    result = valuate_asset_v2(features, None)
    st.session_state.last_features = features
    st.session_state.last_result = result
    st.session_state.last_asset_class = "Option"
    st.session_state.last_asset_subclass = "European Call"
    st.switch_page("pages/01_Recommend.py")
