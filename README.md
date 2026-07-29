# ValuSense

**Intelligent Financial Asset Valuation Method Recommendation**

An ML-powered system that automatically recommends the optimal valuation method for any financial asset, with IFRS 13 compliance and SHAP-based explainability.

---

## Overview

Selecting the right valuation method for a financial asset is a complex decision that depends on the asset's type, liquidity, data availability, regulatory context, and market conditions. A mismatched method produces unreliable estimates and exposes firms to regulatory risk under IFRS 13.

ValuSense addresses this by building a machine learning pipeline that:

1. **Classifies** the asset (equity, bond, option, commodity, currency, derivative)
2. **Recommends** the most appropriate valuation method from 10 approaches
3. **Explains** the recommendation using SHAP values for full auditability
4. **Enforces** IFRS 13 fair value hierarchy constraints (Level 1 / 2 / 3)

---

## Web Interface

A Streamlit-based web interface is included for interactive use:

```bash
pip install -e .
streamlit run app.py
```

**5 pages:**
- **Recommend** — Describe an asset and get a recommendation with SHAP explanation
- **Scenarios** — Run all 10 predefined test scenarios
- **Valuation Engine** — Direct access to any of the 10 valuation calculators
- **Model Insights** — Model comparison, SHAP global importance, confusion matrices
- **About** — Project documentation

---

## Package Usage

```python
from valusense.core import valuate_asset, encode_asset

ac, sc = encode_asset("Option", "European Option")
result = valuate_asset({
    "has_options_features": 1, "has_early_exercise": 0,
    "has_market_price": 1, "liquidity": 2,
    "ifrs_level": 1, "maturity_years": 0.5,
    "implied_volatility_atm": 0.26,
    "asset_class_encoded": ac, "asset_subclass_encoded": sc,
}, {"S": 195, "K": 200, "T": 0.5, "r": 0.045, "sigma": 0.26})

print(result["recommendation"]["method"])  # Black-Scholes
print(result["recommendation"]["confidence"])  # 0.93
```

---

## Features

- **Multi-asset coverage**: Equities, bonds, options, commodities, currencies, derivatives
- **10 valuation methods**: DCF, DDM, Relative, Black-Scholes, Binomial Tree, Monte Carlo, Cost-of-Carry, Forward Pricing, Credit Model, Mark-to-Market
- **IFRS 13 compliance**: 9 domain rules enforcing the fair value hierarchy
- **SHAP explainability**: Per-prediction feature attribution for audit trails
- **Instrument catalog**: 353K+ classified instruments from FinanceDatabase
- **Multi-source data pipeline**: yfinance, FRED, Alpha Vantage, Finnhub

---

## Model Performance

Tuned XGBoost classifier (28 features, 10 classes):

| Metric | Before IFRS | After IFRS |
|--------|-------------|------------|
| Accuracy | 99.1% | 79.1% |
| F1 (weighted) | 99.1% | 84.5% |
| F1 (macro) | 98.8% | 79.3% |

- 12,207 training samples (augmented + balanced)
- 3,052 validation samples
- 609 IFRS overrides, 0 domain violations

---

## Architecture

```
Data Layer
  FinanceDatabase | yfinance | FRED | Alpha Vantage | Finnhub
       |
Feature Engineering
  Market features | Risk metrics | Structural flags
       |
Recommendation Engine
  XGBoost Classifier -> IFRS 13 Filter -> SHAP Explainer
       |
Output
  Recommended method + Confidence + SHAP explanation + Valuation
```

---

## Data Sources

| Source | Coverage | Key |
|--------|----------|-----|
| FinanceDatabase | 353K+ instrument classifications | Free (no key) |
| yfinance | Market prices, options chains, fundamentals | Free (no key) |
| FRED | Treasury yields, credit spreads, macro | Free |
| Alpha Vantage | Technical indicators | Free |
| Finnhub | Company profiles, financials | Free |
| Expert Rules (Hull + IFRS 13) | 4,150+ labeled training samples | N/A |

---

## Key References

- **Hull (2018)** — Options, Futures and Other Derivatives (valuation model foundations)
- **IFRS 13** — Fair Value Measurement three-level hierarchy
- **Lundberg & Lee (2017)** — SHAP values for explainability
- **Chen & Guestrin (2016)** — XGBoost classification algorithm

---

## Project Structure

```
valusense/          ML package (importable)
  config.py         Model loading, lookups, defaults
  engines.py        10 valuation engine functions
  ifrs.py           IFRS 13 constraint rules
  core.py           valuate_asset() unified API

pages/              Streamlit multi-page app
  app.py            Entry point
  01_Recommend.py   Single asset recommendation
  02_Scenarios.py   Batch test scenarios
  03_Valuation_Engine.py  Direct calculators
  04_Model_Insights.py    SHAP + comparison
  05_About.py       Documentation

models/             Trained model artifacts (.pkl, .json)
reports/            Figures, EDA summaries, model comparison
data_valuation_project/  Raw and processed data
```

---

## License

MIT License — End-of-Studies Internship Project @ VERMEG — 2026
