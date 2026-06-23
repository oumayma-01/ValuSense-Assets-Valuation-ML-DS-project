<p align="center">
  <img src="docs/assets/banner.png" alt="ValuSense Banner" width="800"/>
</p>

<h1 align="center">ValuSense</h1>
<h3 align="center">Intelligent Financial Asset Valuation Method Recommendation</h3>

<p align="center">
  <em>An ML-powered system that automatically recommends the optimal valuation method for any financial asset, with IFRS 13 compliance and SHAP-based explainability.</em>
</p>

<p align="center">
  <a href="#overview">Overview</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#data-sources">Data Sources</a> •
  <a href="#methodology">Methodology</a> •
  <a href="#project-structure">Project Structure</a> •
  <a href="#results">Results</a> •
  <a href="#references">References</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License"/>
  <img src="https://img.shields.io/badge/IFRS_13-compliant-orange" alt="IFRS 13"/>
  <img src="https://img.shields.io/badge/methodology-CRISP--DM-purple" alt="CRISP-DM"/>
  <img src="https://img.shields.io/badge/explainability-SHAP-red" alt="SHAP"/>
</p>

---

## Overview

Selecting the right valuation method for a financial asset is a complex decision that depends on the asset's type, liquidity, data availability, regulatory context, and market conditions. A mismatched method — applying Black-Scholes to a bond, or DCF to an exotic option — produces unreliable estimates and exposes firms to regulatory risk under IFRS 13.

**ValuSense** addresses this by building a machine learning pipeline that:

1. **Classifies** the asset (equity, bond, option, commodity, currency, derivative)
2. **Recommends** the most appropriate valuation method from a set of 10 approaches
3. **Explains** the recommendation using SHAP values for full auditability
4. **Enforces** IFRS 13 fair value hierarchy constraints (Level 1 → 2 → 3)

The system is designed for fintech platforms managing multi-asset portfolios where valuation method selection is currently manual, inconsistent, or opaque.

### The Decision Layer: Mark-to-Market vs. Mark-to-Model

At the core of the recommendation logic is a two-tier decision framework:

- **Mark-to-Market** (IFRS Level 1): When reliable, observable market prices exist, use them directly — no model needed.
- **Mark-to-Model** (IFRS Levels 2–3): When market prices are absent, sparse, or unreliable, select the most appropriate pricing model based on asset characteristics.

This framing ensures regulatory alignment before any model-specific recommendation (DCF, Black-Scholes, Monte Carlo, etc.) is made.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                               │
│  FinanceDatabase │ yfinance │ FRED │ Alpha Vantage │ Finnhub   │
│  (353K+ instruments across 7 asset classes)                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FEATURE ENGINEERING                            │
│  Market features  │  Risk metrics  │  Structural flags          │
│  (price, volume,  │  (volatility,  │  (liquidity, data avail,  │
│   bid-ask spread) │   VaR, beta)   │   IFRS level, maturity)   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  RECOMMENDATION ENGINE                           │
│                                                                  │
│  ┌──────────────┐    ┌───────────────────┐    ┌──────────────┐  │
│  │    Asset      │    │  IFRS 13 Filter   │    │  Valuation   │  │
│  │ Classifier    │───▶│  (Level 1 → MtM)  │───▶│  Method      │  │
│  │ (XGBoost)     │    │  (Level 2/3 →     │    │  Recommender │  │
│  └──────────────┘    │   Model-based)     │    │  (XGBoost)   │  │
│                       └───────────────────┘    └──────┬───────┘  │
│                                                       │          │
│                                                       ▼          │
│                                              ┌──────────────┐    │
│                                              │    SHAP       │    │
│                                              │ Explainability│    │
│                                              └──────────────┘    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     OUTPUT                                       │
│  Recommended method + Confidence score + SHAP explanation        │
│                                                                  │
│  Supported methods:                                              │
│  DCF │ DDM │ Relative │ Black-Scholes │ Binomial Tree │         │
│  Monte Carlo │ Cost-of-Carry │ Forward Pricing │                │
│  Credit Model │ Mark-to-Market                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Features

- **Multi-asset coverage**: Equities, bonds, options (European, American, exotic), commodities, currencies, swaps, and structured products
- **10 valuation methods**: DCF, DDM, Relative Valuation, Black-Scholes, Binomial Tree, Monte Carlo, Cost-of-Carry, Forward Pricing, Credit Model, Mark-to-Market
- **IFRS 13 compliance**: Automatic enforcement of the fair value hierarchy — Level 1 assets default to Mark-to-Market before any model is considered
- **SHAP explainability**: Every recommendation includes feature-level explanations showing *why* a method was selected, critical for audit trails
- **Instrument catalog**: Built on the FinanceDatabase with 353,000+ classified financial instruments
- **Multi-source data pipeline**: Aggregates data from yfinance, FRED, Alpha Vantage, Finnhub, and FinanceDatabase with rate limiting and error recovery
- **Expert-rule labeled dataset**: 4,150 labeled training samples generated from Hull's quantitative finance framework and IFRS 13 decision rules

---

## Installation

### Prerequisites

- Python 3.10+
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/<your-username>/ValuSense.git
cd ValuSense

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### API Keys (free tiers)

The data pipeline uses three free APIs. Get your keys and set them as environment variables:

| Service | Free Tier | Get Key |
|---------|-----------|---------|
| **Alpha Vantage** | 25 requests/day | [alphavantage.co/support](https://www.alphavantage.co/support/#api-key) |
| **Finnhub** | 60 requests/min | [finnhub.io/register](https://finnhub.io/register) |
| **FRED** | 120 requests/min | [fred.stlouisfed.org/docs/api](https://fred.stlouisfed.org/docs/api/api_key.html) |

```bash
export ALPHA_VANTAGE_KEY="your_key_here"
export FINNHUB_KEY="your_key_here"
export FRED_KEY="your_key_here"
```

---

## Usage

### 1. Data Collection

```bash
# Run the full data collection pipeline (~30-45 min)
python src/data/collect_data.py --run-all

# Or run individual collectors
python src/data/collect_data.py --source financedatabase   # Instrument catalog
python src/data/collect_data.py --source yfinance          # Equities + Options
python src/data/collect_data.py --source fred              # Rates + Macro
python src/data/collect_data.py --source synthetic         # Labeled dataset
```

### 2. Feature Engineering

```bash
python src/features/build_features.py
```

### 3. Model Training

```bash
# Train the valuation method recommender
python src/models/train_model.py --model xgboost

# Evaluate with cross-validation
python src/models/evaluate_model.py --cv 5
```

### 4. Generate SHAP Explanations

```bash
python src/explainability/shap_analysis.py --sample 100
```

### 5. Run a Prediction

```python
from valusense import ValuSenseRecommender

model = ValuSenseRecommender.load("models/best_model.pkl")

recommendation = model.recommend({
    "asset_class": "Option",
    "asset_subclass": "European Option",
    "has_market_price": True,
    "liquidity": "High",
    "maturity_years": 0.5,
    "volatility_available": True,
    "has_early_exercise": False,
    "is_path_dependent": False,
    "ifrs_level": 1,
})

print(recommendation)
# {
#   "recommended_method": "Black-Scholes",
#   "confidence": 0.94,
#   "ifrs_level": 1,
#   "shap_explanation": { ... }
# }
```

---

## Data Sources

| Source | Data Type | API Key | Coverage |
|--------|-----------|---------|----------|
| [**FinanceDatabase**](https://github.com/JerBouma/FinanceDatabase) | 353K+ instrument classifications | No | Equities, ETFs, Funds, Indices, Currencies, Crypto, Money Markets |
| [**yfinance**](https://github.com/ranaroussi/yfinance) | OHLCV, fundamentals, options chains | No | Equities, Options (IV + Greeks), ETFs, Commodities, Forex |
| [**FRED**](https://fred.stlouisfed.org/) | Treasury yields, interest rates, credit spreads, macro | Free | Full US yield curve (1M–30Y), SOFR, Fed Funds, VIX, CPI, GDP |
| [**Alpha Vantage**](https://www.alphavantage.co/) | Technical indicators (RSI, MACD, Bollinger) | Free | Equities, Forex, Commodities |
| [**Finnhub**](https://finnhub.io/) | Company profiles, 30+ years financials | Free | Global equities, fundamental metrics |
| **Expert Rules** | Labeled training dataset (Hull + IFRS 13) | N/A | 4,150 samples across 10 valuation methods |

### Why Not Bloomberg/Reuters/SeekingAlpha?

These sources are paywalled, anti-scraping, or non-structured. The five free sources above provide equivalent coverage for this project's scope. See [`docs/data_source_assessment.md`](docs/data_source_assessment.md) for the full evaluation.

---

## Methodology

This project follows the **CRISP-DM** (Cross-Industry Standard Process for Data Mining) framework:

| Phase | Description | Status |
|-------|-------------|--------|
| **1. Business Understanding** | Problem framing, IFRS 13 requirements, VERMEG workflow analysis | ✅ Complete |
| **2. Data Understanding** | Source evaluation, data audit, catalog exploration | ✅ Complete |
| **3. Data Preparation** | Collection pipeline, synthetic labeling, feature engineering | 🔄 In Progress |
| **4. Modeling** | XGBoost/CatBoost training, cross-validation, hyperparameter tuning | ⬜ Upcoming |
| **5. Evaluation** | F1 per class, confusion matrix, SHAP analysis, domain validation | ⬜ Upcoming |
| **6. Deployment** | API packaging, documentation, VERMEG integration | ⬜ Upcoming |

### Theoretical Foundation

The valuation method mapping is grounded in:

- **Hull (2018)** — *Options, Futures and Other Derivatives*: Core pricing models (Black-Scholes, Binomial Trees, Monte Carlo, DCF)
- **IFRS 13** — *Fair Value Measurement*: Three-level hierarchy governing when market prices vs. models should be used
- **Blanquet, Pereira & Petrov (2025)** — Interpretable ML for company valuation (Decision Analytics Journal)
- **Lundberg & Lee (2017)** — SHAP values for model-agnostic explainability

---

## Project Structure

```
ValuSense/
├── data/
│   ├── raw/                       # Raw collected data
│   │   ├── equities/              # Stock prices, fundamentals
│   │   ├── options/               # Options chains with IV
│   │   ├── bonds/                 # Bond ETF proxies, yield curves
│   │   ├── commodities/           # Commodity futures
│   │   ├── forex/                 # FX pair data
│   │   └── macro/                 # FRED rates, spreads, macro
│   ├── catalogs/                  # FinanceDatabase 353K+ catalog
│   └── processed/                 # Labeled training dataset
│
├── src/
│   ├── data/
│   │   ├── collect_data.py        # Multi-source data collection pipeline
│   │   └── build_synthetic.py     # Expert-rule labeled dataset generator
│   ├── features/
│   │   └── build_features.py      # Feature engineering pipeline
│   ├── models/
│   │   ├── train_model.py         # Model training (XGBoost, CatBoost)
│   │   └── evaluate_model.py      # Evaluation and cross-validation
│   ├── explainability/
│   │   └── shap_analysis.py       # SHAP explanations
│   └── valusense.py               # Main recommender API
│
├── notebooks/
│   ├── 01_data_collection.ipynb   # Data collection walkthrough
│   ├── 02_eda.ipynb               # Exploratory data analysis
│   ├── 03_feature_engineering.ipynb
│   ├── 04_model_training.ipynb
│   └── 05_shap_explainability.ipynb
│
├── models/                        # Trained model artifacts
├── docs/                          # Documentation and report assets
│   ├── assets/                    # Diagrams, banner
│   └── data_source_assessment.md
├── tests/                         # Unit tests
│
├── requirements.txt
├── README.md
└── LICENSE
```

---

## Results

> *This section will be updated as the modeling phase progresses.*

### Labeled Dataset Distribution

| Valuation Method | Samples | Asset Classes |
|-----------------|---------|---------------|
| DCF | 1,056 | Bond, Equity, Derivative |
| Black-Scholes | 500 | Option (European) |
| Cost-of-Carry | 400 | Commodity |
| DDM | 400 | Equity (Dividend) |
| Binomial Tree | 400 | Option (American) |
| Mark-to-Market | 300 | Equity, ETF, Commodity (liquid) |
| Forward Pricing | 300 | Currency (FX Forward) |
| Monte Carlo | 300 | Option (Exotic) |
| Relative Valuation | 254 | Equity (Growth) |
| Credit Model | 240 | Bond (Corporate, High-Yield) |

### Instrument Catalog Coverage

| Asset Class | Instruments |
|-------------|-------------|
| Equities | 160,942 |
| Indices | 91,181 |
| Funds | 57,853 |
| ETFs | 36,483 |
| Cryptocurrencies | 3,367 |
| Currencies | 2,556 |
| Money Markets | 1,367 |
| **Total** | **353,749** |

---

## Key References

| Reference | Role in Project |
|-----------|----------------|
| Hull, J.C. (2018). *Options, Futures and Other Derivatives*, 10th ed. Pearson. | Valuation model foundations: BSM, Binomial Trees, Monte Carlo, DCF |
| IASB (2011). *IFRS 13 — Fair Value Measurement*. | Three-level fair value hierarchy, Mark-to-Market vs. Mark-to-Model |
| Black, F. & Scholes, M. (1973). *The Pricing of Options and Corporate Liabilities*. JPE. | European option pricing model |
| Cox, J., Ross, S. & Rubinstein, M. (1979). *Option Pricing: A Simplified Approach*. JFE. | Binomial tree pricing |
| Merton, R.C. (1974). *On the Pricing of Corporate Debt*. JF. | Structural credit risk model |
| Lundberg, S. & Lee, S. (2017). *A Unified Approach to Interpreting Model Predictions*. NeurIPS. | SHAP explainability framework |
| Blanquet, Pereira & Petrov (2025). *Interpretable ML for Company Valuation*. Decision Analytics Journal. | ML for valuation, explainability |
| Gu, Kelly & Xiu (2020). *Empirical Asset Pricing via Machine Learning*. RFS. | ML applications in asset pricing |
| Chen, T. & Guestrin, C. (2016). *XGBoost: A Scalable Tree Boosting System*. KDD. | Core classification algorithm |
| Breiman, L. (2001). *Random Forests*. Machine Learning. | Baseline classification algorithm |

---

## Contributing

This project is developed as part of an end-of-studies internship at [VERMEG](https://www.vermeg.com/). Contributions, issues, and suggestions are welcome.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <sub>Built with Python • XGBoost • SHAP • yfinance • FRED • FinanceDatabase</sub>
  <br/>
  <sub>End-of-Studies Internship Project @ <a href="https://www.vermeg.com/">VERMEG</a> — 2026</sub>
</p>
