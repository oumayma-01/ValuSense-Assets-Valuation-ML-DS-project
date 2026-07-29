import streamlit as st

st.set_page_config(page_title="About", page_icon="chart_with_upwards_trend", layout="wide")
st.title("About ValuSense")

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

## Key References

| Reference | Role in Project |
|-----------|----------------|
| Hull, J.C. (2018). *Options, Futures and Other Derivatives*, 10th ed. | Valuation model foundations |
| IASB (2011). *IFRS 13 — Fair Value Measurement* | Three-level fair value hierarchy |
| Black, F. & Scholes, M. (1973). The Pricing of Options | European option pricing |
| Cox, J., Ross, S. & Rubinstein, M. (1979). Option Pricing | Binomial tree pricing |
| Merton, R.C. (1974). On the Pricing of Corporate Debt | Structural credit risk model |
| Lundberg, S. & Lee, S. (2017). SHAP Values | Explainability framework |
| Gu, Kelly & Xiu (2020). ML in Asset Pricing | ML applications in finance |
| Chen, T. & Guestrin (2016). XGBoost | Core classification algorithm |

---

## Technical Stack

- **Python 3.9+** — Core language
- **XGBoost** — Classification model (tuned hyperparameters via RandomizedSearchCV)
- **SHAP** — Tree-based explainability (TreeExplainer)
- **CatBoost / Random Forest** — Baseline comparison models
- **Streamlit** — Web interface
- **yfinance / FRED API / Alpha Vantage / Finnhub** — Data sources
- **FinanceDatabase** — Instrument catalog (353K+ instruments)

---

## Contact

Developed at **VERMEG** — End-of-Studies Internship Project — 2026
""")
