import os
import pandas as pd
from datetime import datetime
from pathlib import Path

import streamlit as st

from utils.theme import (
    inject_theme_css,
    theme_sidebar,
    page_header,
    section_header,
    render_table,
    badge,
    hairline,
)
from utils.meta import load_model_metadata

st.set_page_config(page_title="About", page_icon="📖", layout="wide")

with st.sidebar:
    theme_sidebar()

inject_theme_css()

meta = load_model_metadata()

MODEL_META_PATH = Path(__file__).resolve().parent.parent / "models" / "model_metadata.json"


def _last_updated() -> str:
    try:
        return datetime.fromtimestamp(MODEL_META_PATH.stat().st_mtime).strftime("%B %Y")
    except Exception:
        return "2026"


version = meta.get("version", "2.0")
last_updated = _last_updated()

page_header(
    "About ValuSense",
    "A decision-support tool that recommends the right way to value any financial asset, with "
    "IFRS 13 compliance and explainable reasoning.",
    kicker="Overview · Compliance · Scope",
)

st.markdown(
    f"<div class='badge-row'>"
    f"{badge(f'Model version {version}', tone='accent')}"
    f"{badge(f'Last updated {last_updated}', tone='neutral')}"
    f"</div>",
    unsafe_allow_html=True,
)

tab_about, tab_ifrs, tab_limits, tab_refs = st.tabs(
    ["Overview", "IFRS 13 Rules", "Known Limitations", "References & Stack"]
)

with tab_about:
    section_header("What ValuSense is")
    st.markdown("""
ValuSense helps you pick the right way to value a financial asset. Give it a description of any
asset (an equity, a bond, an option, a commodity, a currency) and it will recommend the most
defensible valuation method, explain *why* in plain language, check the result against IFRS 13
fair-value rules, and price the asset on the spot. It is a decision-support tool, not a substitute
for professional judgment.
    """)

    section_header("Who it's for")
    st.markdown("""
- **Portfolio managers and analysts** who need a documented, defensible valuation approach.
- **Risk and compliance teams** who need IFRS 13 alignment and explainable outputs.
- **Anyone** who has watched a colleague apply Black-Scholes to a bond and wanted a way to stop it.
    """)

    hairline()

    section_header("The decision layer: Mark-to-Market vs Mark-to-Model")
    st.markdown("""
Before any pricing model is chosen, ValuSense decides between two routes:

- **Mark-to-Market (IFRS Level 1).** When a reliable, observable market price exists, use it directly. No model needed.
- **Mark-to-Model (IFRS Levels 2 and 3).** When prices are absent, sparse or unreliable, pick the most appropriate pricing model for the asset's characteristics.

This ordering keeps every recommendation aligned with the regulator before a model is even considered.
    """)

    section_header("The 10 valuation methods covered")
    st.markdown("""
| Method | Best For | Foundation |
|--------|----------|------------|
| DCF | Bonds, any asset with predictable cash flows | Hull Ch. 4 |
| DDM | Dividend-paying equities | Gordon Growth Model |
| Black-Scholes | European options | Black-Scholes (1973) |
| Binomial Tree | American options | Cox-Ross-Rubinstein (1979) |
| Monte Carlo | Exotic/path-dependent options | Hull Ch. 18 |
| Cost-of-Carry | Commodity forwards | Hull Ch. 5 |
| Forward Pricing | FX forwards (CIP) | Interest Rate Parity |
| Mark-to-Market | Liquid assets with observable prices | IFRS 13 §72–75 |
| Relative Valuation | Growth equities with peers | Multiples approach |
| Credit Model | Corporate bonds, credit-risky assets | Merton (1974) |
    """)

    section_header("Measured performance")
    st.markdown("""
| Metric | Before IFRS | After IFRS |
|--------|-------------|------------|
| Accuracy | 99.1% | 79.1% |
| F1 (weighted) | 99.1% | 84.5% |
| F1 (macro) | 98.8% | 79.3% |
| Cohen's Kappa | 98.9% | 76.2% |
    """)
    st.caption(
        "The drop after IFRS enforcement is expected: the compliance layer overrides a small number "
        "of predictions to guarantee regulatory alignment, and that is the point."
    )

with tab_ifrs:
    section_header(
        "IFRS 13 Fair Value Hierarchy Rules",
        "Nine domain rules, enforced between the model and the answer. Each maps to an IFRS 13 "
        "requirement and may override the model's pick.",
    )
    rules = [
        ("R1", "Level 1 asset with observable market price",
         "Force Mark-to-Market (use the observed price directly)", "IFRS 13 §72–75"),
        ("R2", "No market price available",
         "Downgrade to Level 2/3 and prohibit Mark-to-Market", "IFRS 13 §76–81"),
        ("R3", "Asset has no cash flows",
         "Exclude DCF and DDM (both need cash-flow projections)", "IFRS 13 B11–B12"),
        ("R4", "Asset has no option features",
         "Exclude Black-Scholes, Binomial-Tree, Monte-Carlo (option models)", "IFRS 13 §83"),
        ("R5", "Volatility data unavailable",
         "Exclude Black-Scholes (requires volatility)", "IFRS 13 B26"),
        ("R6", "Asset has no credit risk",
         "Exclude Credit-Model (only for credit-risky assets)", "IFRS 13 §42–43"),
        ("R7", "Asset is not exchange-traded",
         "Discourage Mark-to-Market (OTC assets lack transparent pricing)", "IFRS 13 §76"),
        ("R8", "Liquidity is low (< 1)",
         "Downgrade from Level 1 to Level 2 despite a market price", "IFRS 13 §73"),
        ("R9", "Data availability is poor (< 1)",
         "Force Level 3 and prohibit fully observable models", "IFRS 13 §81"),
    ]
    df_rules = pd.DataFrame(rules, columns=["Rule", "Condition", "Action", "Reference"])
    render_table(df_rules)
    st.caption(
        "On the validation set these rules corrected 609 predictions and left 0 domain violations: "
        "the edge cases are caught by the regulator, not left to chance."
    )

with tab_limits:
    section_header(
        "Known limitations",
        "Every system has boundaries. Naming ours is part of earning your trust: here is exactly "
        "where ValuSense is strong, where it is not, and what we are doing about it.",
    )
    limits = [
        ("Training data is rule-generated",
         "The 12,207 samples come from expert rules (Hull + IFRS 13), not live practitioner decisions. The model learns that labelling system faithfully, but it has not yet seen real valuation judgements.",
         "Next step: collect real labelled valuations from the production flow and fine-tune."),
        ("28 features are fixed",
         "The feature set was engineered and frozen during data preparation. New asset types or methods would require re-engineering features and retraining.",
         "The feature list is explicit and documented; extending it is a defined process."),
        ("No time-series component",
         "Each prediction is independent. The model does not learn from volatility regimes, rate cycles or market phases.",
         "A future version can add sequential features without changing the architecture."),
        ("Engines are textbook formulas",
         "The pricing calculators are correct, transparent implementations of the standard models, not a production-grade pricing library.",
         "They are deliberately readable and auditable, and can be swapped for a licensed library at deployment."),
    ]
    df_limits = pd.DataFrame(limits, columns=["Limitation", "What it means", "How we address it"])
    render_table(df_limits)
    st.markdown(
        "**Bottom line:** within its scope (6 asset classes, 10 methods), ValuSense is accurate, "
        "compliant and auditable, and it makes every assumption visible instead of hiding it."
    )

with tab_refs:
    section_header("Key references")
    refs = [
        ("Hull, J.C. (2018)", "Options, Futures and Other Derivatives, 10th ed.", "Valuation model foundations for all 10 methods"),
        ("IASB (2011)", "IFRS 13 — Fair Value Measurement", "Three-level fair value hierarchy and disclosure requirements"),
        ("Black, F. & Scholes, M. (1973)", "The Pricing of Options and Corporate Liabilities", "European option pricing model"),
        ("Cox, J., Ross, S. & Rubinstein, M. (1979)", "Option Pricing: A Simplified Approach", "Binomial tree pricing for American options"),
        ("Merton, R.C. (1974)", "On the Pricing of Corporate Debt", "Structural credit risk model foundation"),
        ("Lundberg, S. & Lee, S. (2017)", "A Unified Approach to Interpreting Model Predictions", "SHAP values for explainable ML"),
        ("Gu, S., Kelly, B. & Xiu, D. (2020)", "Empirical Asset Pricing via Machine Learning", "Systematic ML approach to asset pricing"),
        ("Chen, T. & Guestrin, C. (2016)", "XGBoost: A Scalable Tree Boosting System", "Core classification algorithm"),
    ]
    df_refs = pd.DataFrame(refs, columns=["Authors", "Title", "Role"])
    render_table(df_refs)

    with st.expander("Technical stack (for reviewers)", expanded=False):
        st.markdown("""
- **Python 3.9+** - core language
- **XGBoost** - classification model (tuned via RandomizedSearchCV)
- **SHAP** - tree-based explainability (TreeExplainer)
- **CatBoost / Random Forest** - baseline comparison models
- **Streamlit** - web interface
- **scikit-learn** - pipeline utilities, evaluation metrics, calibration (Platt / Isotonic)
- **yfinance / FRED API / Alpha Vantage / Finnhub** - data sources
- **FinanceDatabase** - instrument catalog (353K+ instruments)
- **Plotly / Matplotlib / Seaborn** - visualizations and charts
        """)
