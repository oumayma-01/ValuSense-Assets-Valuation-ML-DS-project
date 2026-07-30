import streamlit as st

st.set_page_config(page_title="About", page_icon="chart_with_upwards_trend", layout="wide")
from utils.theme import inject_theme_css
inject_theme_css()
st.title("About ValuSense")

tab_about, tab_ifrs, tab_limits, tab_refs = st.tabs(["Overview", "IFRS 13 Rules", "Limitations", "References & Stack"])

with tab_about:
    st.markdown("""
    ## Intelligent Financial Asset Valuation Method Recommendation

    **ValuSense** is an ML-powered system developed during an end-of-studies internship at **VERMEG**.
    It automatically recommends the optimal valuation method for any financial asset,
    with IFRS 13 compliance and SHAP-based explainability.

    ---

    ## The Problem

    Selecting the right valuation method for a financial asset is a complex decision that depends on
    the asset's type, liquidity, data availability, regulatory context, and market conditions.
    A mismatched method — applying Black-Scholes to a bond, or DCF to an exotic option — produces
    unreliable estimates and exposes firms to regulatory risk under IFRS 13.

    ValuSense addresses this by building a machine learning pipeline that:

    1. **Classifies** the asset (equity, bond, option, commodity, currency, derivative)
    2. **Recommends** the most appropriate valuation method from 10 approaches
    3. **Explains** the recommendation using SHAP values for full auditability
    4. **Enforces** IFRS 13 fair value hierarchy constraints (Level 1 / 2 / 3)

    ---

    ## The Decision Layer: Mark-to-Market vs. Mark-to-Model

    At the core of the recommendation logic is a two-tier decision framework:

    - **Mark-to-Market** (IFRS Level 1): When reliable, observable market prices exist, use them directly — no model needed.
    - **Mark-to-Model** (IFRS Levels 2-3): When market prices are absent, sparse, or unreliable, select the most appropriate pricing model based on asset characteristics.

    This framing ensures regulatory alignment before any model-specific recommendation (DCF, Black-Scholes, Monte Carlo, etc.) is made.

    ---

    ## Methodology

    The system follows the **CRISP-DM** framework:

    | Phase | Description | Status |
    |-------|-------------|--------|
    | 1. Business Understanding | Problem framing, IFRS 13 requirements, VERMEG workflow | Complete |
    | 2. Data Understanding | Source evaluation, data audit, catalog exploration | Complete |
    | 3. Data Preparation | Collection pipeline, synthetic labeling, feature engineering | Complete |
    | 4. Modeling | XGBoost/CatBoost training, cross-validation, hyperparameter tuning | Complete |
    | 5. Evaluation | F1 per class, confusion matrix, SHAP analysis, domain validation | Complete |
    | 6. Deployment | API packaging, documentation, web interface | Complete |

    ---

    ## Architecture

    The system is structured in three layers:

    **Data Layer**
    Aggregates data from 5+ free financial data sources including FinanceDatabase (353K+ instruments),
    yfinance (market prices, options chains), FRED (interest rates, credit spreads, macro indicators),
    Alpha Vantage (technical indicators), and Finnhub (company fundamentals).

    **Recommendation Engine**
    An XGBoost classifier trained on 12,207 samples (after augmentation and balancing) predicts the
    optimal valuation method from 28 engineered features. A post-processing layer enforces 9 IFRS 13
    domain rules to ensure regulatory compliance. SHAP TreeExplainer provides per-prediction
    feature attribution for full auditability.

    **Output Layer**
    For each asset, the system returns:
    - Recommended valuation method with confidence score
    - Top 3 alternative methods with probabilities
    - Top-5 SHAP drivers explaining the decision
    - Fair value calculation when parameters are provided
    - IFRS 13 compliance status

    ---

    ## 10 Valuation Methods

    | Method | Best For | Foundation |
    |--------|----------|------------|
    | **DCF** | Bonds, any asset with predictable cash flows | Hull Ch. 4 |
    | **DDM** | Dividend-paying equities | Gordon Growth Model |
    | **Black-Scholes** | European options | Black-Scholes (1973) |
    | **Binomial Tree** | American options | Cox-Ross-Rubinstein (1979) |
    | **Monte Carlo** | Exotic/path-dependent options | Hull Ch. 18 |
    | **Cost-of-Carry** | Commodity forwards | Hull Ch. 5 |
    | **Forward Pricing** | FX forwards (CIP) | Interest Rate Parity |
    | **Mark-to-Market** | Liquid assets with observable prices | IFRS 13 sec 72-75 |
    | **Relative Valuation** | Growth equities with peers | Multiples approach |
    | **Credit Model** | Corporate bonds, credit-risky assets | Merton (1974) |

    ---

    ## Data Sources

    | Source | Data Type | Coverage |
    |--------|-----------|----------|
    | FinanceDatabase | Instrument classifications | 353,749 instruments across 7 asset classes |
    | yfinance | OHLCV, options chains, fundamentals | Global equities, options, ETFs, forex |
    | FRED | Treasury yields, credit spreads, macro | Full US yield curve, 28+ series |
    | Alpha Vantage | Technical indicators | Equities, forex, commodities |
    | Finnhub | Company profiles, financials | Global equities, fundamental metrics |
    | Expert Rules (Hull + IFRS 13) | Labeled training data | 4,150+ samples across 10 methods |

    ---

    ## Model Performance

    The tuned XGBoost model achieves:

    | Metric | Before IFRS | After IFRS |
    |--------|-------------|------------|
    | Accuracy | 99.1% | 79.1% |
    | F1 (weighted) | 99.1% | 84.5% |
    | F1 (macro) | 98.8% | 79.3% |
    | Cohen's Kappa | 98.9% | 76.2% |

    The drop after IFRS enforcement is expected — the IFRS layer overrides ML predictions to enforce
    regulatory compliance (609 overrides on the validation set), creating 0 domain violations.

    ---

    ## Contact

    Developed at **VERMEG** — End-of-Studies Internship Project — 2026
    """)

with tab_ifrs:
    st.subheader("IFRS 13 Fair Value Hierarchy Rules")
    st.markdown("""
    The following 9 domain rules are enforced as a post-processing layer after the ML prediction.
    Each rule maps to an IFRS 13 requirement and may override the ML-recommended method.
    """)
    rules = [
        ("R1", "Mark-to-Market Required", "IFRS 13 §72–75", "If `has_market_price == 1` and `ifrs_level == 1`, override to **Mark-to-Market** regardless of ML prediction."),
        ("R2", "No Market → Level 2/3", "IFRS 13 §76–81", "If `has_market_price == 0`, downgrade to Level 2 or 3; prohibit Mark-to-Market."),
        ("R3", "Cash Flow Required", "IFRS 13 B11-B12", "If `has_cash_flows == 0`, exclude DCF and DDM (both require cash flow projections)."),
        ("R4", "Options Feature Required", "IFRS 13 §83", "If `has_options_features == 0`, exclude Black-Scholes, Binomial-Tree, Monte-Carlo (options models)."),
        ("R5", "Volatility Required", "IFRS 13 B26", "If `volatility_available == 0`, exclude Black-Scholes (requires sigma)."),
        ("R6", "Credit Risk Required", "IFRS 13 §42–43", "If `has_credit_risk == 0`, exclude Credit-Model (only for credit-risky assets)."),
        ("R7", "Exchange-Traded", "IFRS 13 §76", "If `is_exchange_traded == 0`, **discourage** Mark-to-Market (OTC assets lack transparent pricing)."),
        ("R8", "Liquidity Filter", "IFRS 13 §73", "If `liquidity < 1`, downgrade from Level 1 to Level 2 even if market price exists."),
        ("R9", "Data Availability Gate", "IFRS 13 §81", "If `data_availability < 1`, force Level 3 and prohibit fully observable models."),
    ]
    import pandas as pd
    df_rules = pd.DataFrame(rules, columns=["ID", "Rule", "IFRS Reference", "Logic"])
    st.dataframe(df_rules, use_container_width=True, hide_index=True)

with tab_limits:
    st.subheader("Known Limitations")
    st.markdown("""
    1. **Training data is synthetic:** All 12,207 samples were generated by expert rules (Hull + IFRS 13),
       not collected from real valuation decisions. The model learns the rule-based labeling system,
       not necessarily real-world practitioner judgement.

    2. **28 features are hard-coded:** The feature set was manually engineered and fixed during data
       preparation. New asset types or valuation methods require re-engineering features and retraining.

    3. **No time-series component:** The model treats each prediction independently. It does not learn
       from temporal patterns, volatility regime shifts, or macroeconomic cycles.

    4. **Valuation engine stub:** The numerical calculation (Black-Scholes, DCF, etc.) is a thin wrapper
       around textbook formulas — not production-grade pricing libraries. Greeks are first-order only.

    5. **OTC and exotic assets:** Coverage for OTC derivatives, structured products, and illiquid
       alternative assets (private equity, real estate, infrastructure) is limited or absent.

    6. **Calibration dependency:** The calibrated confidence scores depend on `v3_calibrated` metadata
       being present in the models directory. Without it, the app falls back to raw XGBoost probabilities.

    7. **SHAP speed:** Per-prediction SHAP explanations add ~200ms latency. For batch predictions,
       this would need optimization (e.g., KernelSHAP approximation or pre-computed SHAP baselines).

    8. **Language:** The UI and explanations are in English only. Multi-language support (especially for
       French — VERMEG's primary operating language) is not implemented.
    """)

with tab_refs:
    st.subheader("Key References")
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
    st.dataframe(df_refs, use_container_width=True, hide_index=True)

    st.subheader("Technical Stack")
    st.markdown("""
    - **Python 3.9+** — Core language
    - **XGBoost** — Classification model (tuned hyperparameters via RandomizedSearchCV)
    - **SHAP** — Tree-based explainability (TreeExplainer)
    - **CatBoost / Random Forest** — Baseline comparison models
    - **Streamlit** — Web interface
    - **scikit-learn** — Pipeline utilities, evaluation metrics, calibration (Platt / Isotonic)
    - **yfinance / FRED API / Alpha Vantage / Finnhub** — Data sources
    - **FinanceDatabase** — Instrument catalog (353K+ instruments)
    - **Plotly / Matplotlib / Seaborn** — Visualizations and charts
    """)
