#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
 DATA COLLECTION PIPELINE — ML-Based Asset Valuation Recommendation System
================================================================================
 Internship Project @ VERMEG
 Objective: Collect, structure and store financial data across all major asset
            classes to train an ML model that recommends the optimal valuation
            method (DCF, Black-Scholes, Monte Carlo, Binomial Tree, etc.)

 Run this file as a Jupyter notebook (VS Code / JupyterLab) or convert:
     jupytext --to notebook data_collection_asset_valuation.py

 Author : Med
 Date   : June 2026
================================================================================
"""

# %% [markdown]
# # 📊 Data Collection Pipeline — Asset Valuation Recommendation System
#
# ## Source Assessment & Strategy
#
# | Source | Verdict | Reason |
# |--------|---------|--------|
# | Reuters / Bloomberg | ❌ Skip | Paywalled, anti-scraping, no free API |
# | SeekingAlpha | ❌ Skip | Paywalled articles, limited free API |
# | Investopedia | ❌ Skip | Educational content, not structured data |
# | FinanceDatabase (GitHub) | ✅ Keep | 300k+ classified instruments — perfect for classification layer |
# | The-FinAI/FinData (GitHub) | ⚠️ Limited | Academic NLP dataset, not valuation data |
# | **yfinance** | ✅ **ADD** | Free: equities, options chains, fundamentals, ETFs, bonds |
# | **FRED (St. Louis Fed)** | ✅ **ADD** | Free: treasury yields, interest rates, macro indicators |
# | **Alpha Vantage** | ✅ **ADD** | Free tier: stocks, forex, commodities, technical indicators |
# | **Finnhub** | ✅ **ADD** | Free tier: real-time quotes, fundamentals, forex, crypto |
# | **CBOE (via yfinance)** | ✅ **ADD** | Options chains with Greeks & IV via yfinance proxy |
# | **Kaggle Datasets** | ✅ **ADD** | Historical options, bond risk, commodity futures |
# | **OpenBB / pandas-datareader** | ✅ **ADD** | Multi-source aggregator |

# %% [markdown]
# ## 0. Installation & Setup
# Run once to install all dependencies:
# ```bash
# pip install yfinance financedatabase fredapi pandas numpy requests 
#             openpyxl tqdm alpha_vantage finnhub-python kaggle
# ```

# %%
# ═══════════════════════════════════════════════════════════════════════════════
# CELL 0 — Imports & Configuration
# ═══════════════════════════════════════════════════════════════════════════════

import os
import time
import json
import warnings
import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from tqdm import tqdm

warnings.filterwarnings("ignore")

# ── Project directories ──────────────────────────────────────────────────────
BASE_DIR = Path("./data_valuation_project")
RAW_DIR = BASE_DIR / "raw"
PROCESSED_DIR = BASE_DIR / "processed"
CATALOG_DIR = BASE_DIR / "catalogs"

for d in [RAW_DIR, PROCESSED_DIR, CATALOG_DIR,
          RAW_DIR / "equities", RAW_DIR / "options", RAW_DIR / "bonds",
          RAW_DIR / "commodities", RAW_DIR / "forex", RAW_DIR / "derivatives",
          RAW_DIR / "macro", RAW_DIR / "credit"]:
    d.mkdir(parents=True, exist_ok=True)

print(f"✅ Project structure created at: {BASE_DIR.resolve()}")

# ── API Keys (set your own — all free tiers) ────────────────────────────────
# Get free keys at:
#   Alpha Vantage : https://www.alphavantage.co/support/#api-key
#   Finnhub       : https://finnhub.io/register
#   FRED          : https://fred.stlouisfed.org/docs/api/api_key.html

ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY", "YOUR_AV_KEY_HERE")
FINNHUB_KEY       = os.getenv("FINNHUB_KEY", "YOUR_FINNHUB_KEY_HERE")
FRED_KEY          = os.getenv("FRED_KEY", "YOUR_FRED_KEY_HERE")

# ── Rate limiting helper ─────────────────────────────────────────────────────
def rate_limit(seconds=1.0):
    """Simple rate limiter between API calls."""
    time.sleep(seconds)

def safe_request(url, params=None, retries=3, delay=2):
    """Robust HTTP GET with retries."""
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay * (attempt + 1))
            else:
                print(f"  ⚠ Failed after {retries} attempts: {e}")
                return None

print("✅ Configuration loaded")


# %% [markdown]
# ---
# ## 1. FinanceDatabase — Asset Classification Catalog (300k+ instruments)
#
# This is the **backbone of the classification layer**. It provides pre-classified
# instruments across Equities, ETFs, Funds, Indices, Currencies, Crypto, and
# Money Markets — with sector, industry, country, and exchange metadata.

# %%
# ═══════════════════════════════════════════════════════════════════════════════
# CELL 1 — FinanceDatabase: Build Classification Catalog
# ═══════════════════════════════════════════════════════════════════════════════

import financedatabase as fd

def collect_financedatabase_catalog():
    """
    Download and structure the full FinanceDatabase catalog.
    Maps each instrument to an asset_class label for the ML classification layer.
    """
    catalog_frames = []
    
    # ── 1.1 Equities ─────────────────────────────────────────────────────────
    print("📥 Loading Equities...")
    equities = fd.Equities()
    eq_df = equities.search()
    eq_df["asset_class"] = "Equity"
    eq_df["asset_subclass"] = eq_df["sector"].fillna("Unknown")
    catalog_frames.append(eq_df[["name", "currency", "sector", "industry_group",
                                  "industry", "exchange", "market", "country",
                                  "market_cap", "asset_class", "asset_subclass"]])
    print(f"  → {len(eq_df):,} equities loaded")
    
    # ── 1.2 ETFs ─────────────────────────────────────────────────────────────
    print("📥 Loading ETFs...")
    etfs = fd.ETFs()
    etf_df = etfs.search()
    etf_df["asset_class"] = "ETF"
    etf_df["asset_subclass"] = etf_df.get("category_group", "Unknown")
    cols = [c for c in ["name", "currency", "category_group", "category",
                         "exchange", "market", "asset_class", "asset_subclass"] 
            if c in etf_df.columns]
    catalog_frames.append(etf_df[cols])
    print(f"  → {len(etf_df):,} ETFs loaded")
    
    # ── 1.3 Funds ────────────────────────────────────────────────────────────
    print("📥 Loading Funds...")
    funds = fd.Funds()
    fund_df = funds.search()
    fund_df["asset_class"] = "Fund"
    fund_df["asset_subclass"] = fund_df.get("category_group", "Unknown")
    cols = [c for c in ["name", "currency", "category_group", "category",
                         "exchange", "market", "asset_class", "asset_subclass"]
            if c in fund_df.columns]
    catalog_frames.append(fund_df[cols])
    print(f"  → {len(fund_df):,} funds loaded")
    
    # ── 1.4 Indices ──────────────────────────────────────────────────────────
    print("📥 Loading Indices...")
    indices = fd.Indices()
    idx_df = indices.search()
    idx_df["asset_class"] = "Index"
    idx_df["asset_subclass"] = "Market Index"
    cols = [c for c in ["name", "currency", "exchange", "market",
                         "asset_class", "asset_subclass"]
            if c in idx_df.columns]
    catalog_frames.append(idx_df[cols])
    print(f"  → {len(idx_df):,} indices loaded")
    
    # ── 1.5 Currencies ──────────────────────────────────────────────────────
    print("📥 Loading Currencies...")
    currencies = fd.Currencies()
    cur_df = currencies.search()
    cur_df["asset_class"] = "Currency"
    cur_df["asset_subclass"] = "FX Pair"
    cols = [c for c in ["name", "base_currency", "quote_currency",
                         "exchange", "asset_class", "asset_subclass"]
            if c in cur_df.columns]
    catalog_frames.append(cur_df[cols])
    print(f"  → {len(cur_df):,} currency pairs loaded")
    
    # ── 1.6 Cryptos ──────────────────────────────────────────────────────────
    print("📥 Loading Cryptocurrencies...")
    cryptos = fd.Cryptos()
    crypto_df = cryptos.search()
    crypto_df["asset_class"] = "Cryptocurrency"
    crypto_df["asset_subclass"] = "Digital Asset"
    cols = [c for c in ["name", "cryptocurrency", "currency",
                         "exchange", "asset_class", "asset_subclass"]
            if c in crypto_df.columns]
    catalog_frames.append(crypto_df[cols])
    print(f"  → {len(crypto_df):,} cryptos loaded")
    
    # ── 1.7 Money Markets ────────────────────────────────────────────────────
    print("📥 Loading Money Markets...")
    mm = fd.Moneymarkets()
    mm_df = mm.search()
    mm_df["asset_class"] = "MoneyMarket"
    mm_df["asset_subclass"] = "Short-Term Fixed Income"
    cols = [c for c in ["name", "currency", "family",
                         "exchange", "asset_class", "asset_subclass"]
            if c in mm_df.columns]
    catalog_frames.append(mm_df[cols])
    print(f"  → {len(mm_df):,} money market instruments loaded")
    
    # ── Merge all ────────────────────────────────────────────────────────────
    full_catalog = pd.concat(catalog_frames, ignore_index=False, sort=False)
    full_catalog.index.name = "symbol"
    
    # Save
    output_path = CATALOG_DIR / "full_instrument_catalog.parquet"
    full_catalog.to_parquet(output_path)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 FULL CATALOG SUMMARY")
    print("=" * 60)
    print(f"Total instruments: {len(full_catalog):,}")
    print(f"\nBy asset class:")
    print(full_catalog["asset_class"].value_counts().to_string())
    print(f"\nSaved to: {output_path}")
    
    return full_catalog

catalog = collect_financedatabase_catalog()


# %% [markdown]
# ---
# ## 2. yfinance — Equities, Options, Fundamentals & Historical Prices
#
# yfinance provides the richest **free** data for our project:
# - **Historical OHLCV** prices (equities, ETFs, indices, crypto, forex)
# - **Options chains** with strike, expiry, bid/ask, volume, open interest,
#   implied volatility — essential for Black-Scholes and Greeks features
# - **Fundamentals** (P/E, market cap, beta, dividends, financials)
# - **Bond proxies** via Treasury ETFs (TLT, IEF, SHY, BND, AGG)

# %%
# ═══════════════════════════════════════════════════════════════════════════════
# CELL 2 — yfinance: Equity Historical Data & Fundamentals
# ═══════════════════════════════════════════════════════════════════════════════

import yfinance as yf

# ── 2.1 Representative ticker universe ───────────────────────────────────────
# We select a diverse sample across sectors, market caps, and geographies
# to build a representative training set for the classification layer.

EQUITY_TICKERS = {
    # US Large Cap (diverse sectors)
    "Tech":       ["AAPL", "MSFT", "GOOGL", "NVDA", "META"],
    "Finance":    ["JPM", "GS", "BAC", "BRK-B", "V"],
    "Healthcare": ["JNJ", "UNH", "PFE", "ABBV", "MRK"],
    "Energy":     ["XOM", "CVX", "COP", "SLB", "EOG"],
    "Consumer":   ["AMZN", "TSLA", "WMT", "PG", "KO"],
    "Industrial": ["CAT", "BA", "GE", "UNP", "HON"],
    "Utilities":  ["NEE", "DUK", "SO", "D", "AEP"],
    "RealEstate": ["AMT", "PLD", "CCI", "EQIX", "SPG"],
    # Mid/Small Cap
    "MidCap":     ["ETSY", "ROKU", "DKNG", "CROX", "FIVE"],
    # International ADRs
    "Intl":       ["TSM", "NVO", "ASML", "SAP", "BABA"],
}

# Flatten
all_equity_tickers = [t for group in EQUITY_TICKERS.values() for t in group]
print(f"📋 Equity universe: {len(all_equity_tickers)} tickers across {len(EQUITY_TICKERS)} sectors")


def collect_equity_data(tickers, period="5y"):
    """
    For each equity ticker, collect:
      - Historical OHLCV (5 years daily)
      - Key fundamentals (P/E, beta, market cap, sector, etc.)
      - Dividend history
    Returns a dict of DataFrames.
    """
    all_history = {}
    fundamentals = []
    
    print(f"\n📥 Downloading equity data for {len(tickers)} tickers...")
    
    # Batch download historical prices
    print("  → Batch downloading historical prices...")
    try:
        hist_data = yf.download(
            tickers, period=period, group_by="ticker",
            auto_adjust=True, progress=True, threads=True
        )
        print(f"  → Historical data shape: {hist_data.shape}")
    except Exception as e:
        print(f"  ⚠ Batch download failed: {e}")
        hist_data = pd.DataFrame()
    
    # Per-ticker fundamentals
    print("  → Fetching fundamentals per ticker...")
    for ticker_str in tqdm(tickers, desc="  Fundamentals"):
        try:
            tkr = yf.Ticker(ticker_str)
            info = tkr.info
            
            fundamentals.append({
                "symbol": ticker_str,
                "name": info.get("longName", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "quoteType": info.get("quoteType", ""),
                "market_cap": info.get("marketCap", np.nan),
                "enterprise_value": info.get("enterpriseValue", np.nan),
                "pe_ratio": info.get("trailingPE", np.nan),
                "forward_pe": info.get("forwardPE", np.nan),
                "peg_ratio": info.get("pegRatio", np.nan),
                "price_to_book": info.get("priceToBook", np.nan),
                "ev_to_ebitda": info.get("enterpriseToEbitda", np.nan),
                "beta": info.get("beta", np.nan),
                "dividend_yield": info.get("dividendYield", np.nan),
                "payout_ratio": info.get("payoutRatio", np.nan),
                "roe": info.get("returnOnEquity", np.nan),
                "roa": info.get("returnOnAssets", np.nan),
                "profit_margin": info.get("profitMargins", np.nan),
                "revenue_growth": info.get("revenueGrowth", np.nan),
                "debt_to_equity": info.get("debtToEquity", np.nan),
                "current_ratio": info.get("currentRatio", np.nan),
                "free_cashflow": info.get("freeCashflow", np.nan),
                "total_revenue": info.get("totalRevenue", np.nan),
                "52w_high": info.get("fiftyTwoWeekHigh", np.nan),
                "52w_low": info.get("fiftyTwoWeekLow", np.nan),
                "avg_volume": info.get("averageVolume", np.nan),
                # Valuation method hint
                "asset_class": "Equity",
                "recommended_method": "DCF",  # default; refined later
            })
            rate_limit(0.3)
            
        except Exception as e:
            print(f"    ⚠ {ticker_str}: {e}")
    
    fundamentals_df = pd.DataFrame(fundamentals)
    
    # Save
    if not hist_data.empty:
        hist_data.to_parquet(RAW_DIR / "equities" / "equity_historical_prices.parquet")
    fundamentals_df.to_parquet(RAW_DIR / "equities" / "equity_fundamentals.parquet")
    fundamentals_df.to_csv(RAW_DIR / "equities" / "equity_fundamentals.csv", index=False)
    
    print(f"\n✅ Equity data saved: {len(fundamentals_df)} tickers with fundamentals")
    return hist_data, fundamentals_df


# Uncomment to run (takes ~5-10 min):
# equity_hist, equity_fund = collect_equity_data(all_equity_tickers)


# %% [markdown]
# ---
# ## 3. yfinance — Options Data (Greeks, IV, Chains)
#
# Options data is **critical** for:
# - Training the model to recommend Black-Scholes vs Binomial vs Monte Carlo
# - Extracting features: strike, expiry, IV, moneyness, Greeks
# - Understanding derivative pricing dynamics

# %%
# ═══════════════════════════════════════════════════════════════════════════════
# CELL 3 — yfinance: Options Chains with Greeks & IV
# ═══════════════════════════════════════════════════════════════════════════════

# High-volume, liquid options tickers (best data quality)
OPTIONS_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "SPY",
    "QQQ", "IWM", "GLD", "SLV", "EEM", "XLF", "XLE", "TLT",
    "JPM", "BAC", "GS", "XOM", "AMD", "INTC", "NFLX", "DIS"
]


def collect_options_data(tickers):
    """
    For each ticker, collect full options chains across all available expirations.
    Extracts: strike, bid, ask, last price, volume, open interest,
              implied volatility, contract type (call/put), expiration date,
              plus computed features (moneyness, time to expiry).
    """
    all_options = []
    
    print(f"\n📥 Collecting options chains for {len(tickers)} tickers...")
    
    for ticker_str in tqdm(tickers, desc="  Options"):
        try:
            tkr = yf.Ticker(ticker_str)
            spot_price = tkr.info.get("regularMarketPrice",
                         tkr.info.get("previousClose", np.nan))
            
            expirations = tkr.options
            if not expirations:
                continue
            
            # Collect first 6 expirations (near-term most liquid)
            for exp_date in expirations[:6]:
                try:
                    chain = tkr.option_chain(exp_date)
                    
                    for opt_type, opt_df in [("call", chain.calls), ("put", chain.puts)]:
                        if opt_df.empty:
                            continue
                        
                        df = opt_df.copy()
                        df["symbol"] = ticker_str
                        df["underlying_price"] = spot_price
                        df["expiration"] = exp_date
                        df["option_type"] = opt_type
                        
                        # Compute features
                        df["moneyness"] = df["strike"] / spot_price if spot_price else np.nan
                        exp_dt = pd.to_datetime(exp_date)
                        df["days_to_expiry"] = (exp_dt - pd.Timestamp.now()).days
                        df["time_to_expiry_years"] = df["days_to_expiry"] / 365.25
                        
                        # In-the-money flag
                        if opt_type == "call":
                            df["in_the_money"] = df["strike"] < spot_price
                        else:
                            df["in_the_money"] = df["strike"] > spot_price
                        
                        df["asset_class"] = "Option"
                        df["asset_subclass"] = f"{opt_type.title()} Option"
                        
                        all_options.append(df)
                    
                    rate_limit(0.2)
                    
                except Exception as e:
                    pass  # Skip problematic expirations silently
            
            rate_limit(0.5)
            
        except Exception as e:
            print(f"    ⚠ {ticker_str}: {e}")
    
    if all_options:
        options_df = pd.concat(all_options, ignore_index=True)
        
        # Standardize column names
        col_rename = {
            "impliedVolatility": "implied_volatility",
            "openInterest": "open_interest",
            "lastPrice": "last_price",
            "percentChange": "pct_change",
            "inTheMoney": "itm_flag",
            "contractSymbol": "contract_symbol",
            "contractSize": "contract_size",
            "lastTradeDate": "last_trade_date",
        }
        options_df.rename(columns=col_rename, inplace=True)
        
        # Save
        options_df.to_parquet(RAW_DIR / "options" / "options_chains_full.parquet")
        options_df.to_csv(RAW_DIR / "options" / "options_chains_full.csv", index=False)
        
        print(f"\n✅ Options data saved: {len(options_df):,} contracts")
        print(f"   Tickers covered: {options_df['symbol'].nunique()}")
        print(f"   Expirations: {options_df['expiration'].nunique()}")
        print(f"   Calls: {(options_df['option_type']=='call').sum():,}")
        print(f"   Puts:  {(options_df['option_type']=='put').sum():,}")
        
        return options_df
    else:
        print("  ⚠ No options data collected")
        return pd.DataFrame()


# Uncomment to run (takes ~10-15 min):
# options_df = collect_options_data(OPTIONS_TICKERS)


# %% [markdown]
# ---
# ## 4. FRED API — Treasury Yields, Interest Rates, Macro Indicators
#
# The Federal Reserve Economic Data (FRED) is the **gold standard** for:
# - Treasury yield curves (essential for bond DCF and risk-free rate)
# - Interest rates (Fed Funds, LIBOR/SOFR, swap rates)
# - Credit spreads (Baa-Aaa spread, high-yield OAS)
# - Macro indicators (GDP, CPI, unemployment — context features)

# %%
# ═══════════════════════════════════════════════════════════════════════════════
# CELL 4 — FRED API: Bonds, Rates & Macro Data
# ═══════════════════════════════════════════════════════════════════════════════

# FRED series IDs organized by category
FRED_SERIES = {
    # ── Treasury Yield Curve ─────────────────────────────────────────────
    "treasury_yields": {
        "DGS1MO": "1-Month Treasury Yield",
        "DGS3MO": "3-Month Treasury Yield",
        "DGS6MO": "6-Month Treasury Yield",
        "DGS1":   "1-Year Treasury Yield",
        "DGS2":   "2-Year Treasury Yield",
        "DGS3":   "3-Year Treasury Yield",
        "DGS5":   "5-Year Treasury Yield",
        "DGS7":   "7-Year Treasury Yield",
        "DGS10":  "10-Year Treasury Yield",
        "DGS20":  "20-Year Treasury Yield",
        "DGS30":  "30-Year Treasury Yield",
    },
    # ── Interest Rates ───────────────────────────────────────────────────
    "interest_rates": {
        "FEDFUNDS":   "Federal Funds Rate",
        "SOFR":       "SOFR (Secured Overnight Financing Rate)",
        "DPRIME":     "Bank Prime Loan Rate",
        "MORTGAGE30US": "30-Year Fixed Mortgage Rate",
        "MORTGAGE15US": "15-Year Fixed Mortgage Rate",
    },
    # ── Credit Spreads ───────────────────────────────────────────────────
    "credit_spreads": {
        "BAMLC0A0CM":  "ICE BofA US Corp Master OAS",
        "BAMLH0A0HYM2": "ICE BofA US High Yield OAS",
        "T10Y2Y":      "10Y-2Y Treasury Spread",
        "T10Y3M":      "10Y-3M Treasury Spread",
        "AAA":         "Moody's AAA Corporate Bond Yield",
        "BAA":         "Moody's BAA Corporate Bond Yield",
    },
    # ── Macro Indicators ─────────────────────────────────────────────────
    "macro": {
        "GDP":         "Gross Domestic Product",
        "CPIAUCSL":    "Consumer Price Index (All Urban)",
        "UNRATE":      "Unemployment Rate",
        "VIXCLS":      "CBOE VIX Index",
        "DCOILWTICO":  "WTI Crude Oil Price",
        "GOLDAMGBD228NLBM": "Gold Price (London Fix)",
    },
}


def collect_fred_data(api_key, start_date="2010-01-01"):
    """
    Collect all FRED series using the FRED API.
    Falls back to the free CSV endpoint if API key is not set.
    """
    results = {}
    
    print(f"\n📥 Collecting FRED economic data...")
    
    for category, series_dict in FRED_SERIES.items():
        print(f"\n  📂 Category: {category}")
        category_frames = {}
        
        for series_id, description in series_dict.items():
            try:
                if api_key and api_key != "YOUR_FRED_KEY_HERE":
                    # Use API
                    url = "https://api.stlouisfed.org/fred/series/observations"
                    params = {
                        "series_id": series_id,
                        "api_key": api_key,
                        "file_type": "json",
                        "observation_start": start_date,
                    }
                    resp = safe_request(url, params=params)
                    if resp:
                        data = resp.json()
                        obs = data.get("observations", [])
                        df = pd.DataFrame(obs)
                        df["date"] = pd.to_datetime(df["date"])
                        df["value"] = pd.to_numeric(df["value"], errors="coerce")
                        df = df[["date", "value"]].dropna()
                        df.columns = ["date", series_id]
                        category_frames[series_id] = df.set_index("date")
                else:
                    # Fallback: free CSV endpoint (no API key needed)
                    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
                    df = pd.read_csv(url, parse_dates=["DATE"])
                    df.columns = ["date", series_id]
                    df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
                    df = df.dropna()
                    category_frames[series_id] = df.set_index("date")
                
                print(f"    ✓ {series_id}: {description}")
                rate_limit(0.3)
                
            except Exception as e:
                print(f"    ✗ {series_id}: {e}")
        
        if category_frames:
            merged = pd.concat(category_frames.values(), axis=1)
            merged.to_parquet(RAW_DIR / "macro" / f"fred_{category}.parquet")
            merged.to_csv(RAW_DIR / "macro" / f"fred_{category}.csv")
            results[category] = merged
            print(f"  → Saved {category}: {merged.shape}")
    
    # ── Build yield curve snapshots ──────────────────────────────────────
    if "treasury_yields" in results:
        yc = results["treasury_yields"]
        yc_latest = yc.iloc[-1:].T
        yc_latest.columns = ["yield_pct"]
        yc_latest["maturity_months"] = [1, 3, 6, 12, 24, 36, 60, 84, 120, 240, 360]
        yc_latest.to_csv(RAW_DIR / "bonds" / "latest_yield_curve.csv")
        print(f"\n  📈 Latest yield curve saved ({yc.index[-1].date()})")
    
    return results


# Uncomment to run:
# fred_data = collect_fred_data(FRED_KEY)


# %% [markdown]
# ---
# ## 5. Bond & Fixed Income Data via ETF Proxies
#
# Since individual bond data is hard to get for free, we use **bond ETF proxies**:
# - **TLT** (20+ Year Treasury) — long-duration government bonds
# - **IEF** (7-10 Year Treasury) — medium-duration
# - **SHY** (1-3 Year Treasury) — short-duration
# - **BND** (Total Bond Market) — aggregate
# - **LQD** (Investment Grade Corporate) — corporate bonds
# - **HYG** (High Yield Corporate) — junk bonds / credit risk
# - **AGG** (US Aggregate Bond) — broad fixed income

# %%
# ═══════════════════════════════════════════════════════════════════════════════
# CELL 5 — Bond ETF Proxies: Duration, Yield, Credit Risk Features
# ═══════════════════════════════════════════════════════════════════════════════

BOND_ETFS = {
    # Government bonds (different durations)
    "SHY": {"description": "1-3 Year Treasury", "duration_bucket": "short", "credit": "sovereign"},
    "IEI": {"description": "3-7 Year Treasury", "duration_bucket": "medium", "credit": "sovereign"},
    "IEF": {"description": "7-10 Year Treasury", "duration_bucket": "medium-long", "credit": "sovereign"},
    "TLT": {"description": "20+ Year Treasury", "duration_bucket": "long", "credit": "sovereign"},
    "TIP": {"description": "TIPS (Inflation-Protected)", "duration_bucket": "medium", "credit": "sovereign"},
    # Corporate bonds
    "LQD": {"description": "Investment Grade Corporate", "duration_bucket": "medium", "credit": "investment_grade"},
    "HYG": {"description": "High Yield Corporate", "duration_bucket": "medium", "credit": "high_yield"},
    "JNK": {"description": "Junk Bonds", "duration_bucket": "medium", "credit": "high_yield"},
    # Broad aggregates
    "BND": {"description": "Total US Bond Market", "duration_bucket": "medium", "credit": "mixed"},
    "AGG": {"description": "US Aggregate Bond", "duration_bucket": "medium", "credit": "mixed"},
    # International
    "BNDX": {"description": "International Bond (ex-US)", "duration_bucket": "medium", "credit": "mixed"},
    "EMB":  {"description": "Emerging Market Bonds", "duration_bucket": "medium", "credit": "emerging"},
}


def collect_bond_etf_data():
    """
    Collect bond ETF data as proxies for fixed income valuation features.
    For each ETF: historical prices, volume, yield proxy, duration bucket.
    """
    print(f"\n📥 Collecting bond ETF data ({len(BOND_ETFS)} instruments)...")
    
    tickers = list(BOND_ETFS.keys())
    
    # Batch download
    try:
        hist = yf.download(tickers, period="10y", auto_adjust=True, progress=True)
        hist.to_parquet(RAW_DIR / "bonds" / "bond_etf_prices.parquet")
        print(f"  → Historical prices: {hist.shape}")
    except Exception as e:
        print(f"  ⚠ Price download: {e}")
    
    # Fundamentals / characteristics
    bond_meta = []
    for ticker_str, meta in tqdm(BOND_ETFS.items(), desc="  Bond ETF info"):
        try:
            tkr = yf.Ticker(ticker_str)
            info = tkr.info
            bond_meta.append({
                "symbol": ticker_str,
                "name": info.get("longName", meta["description"]),
                "description": meta["description"],
                "duration_bucket": meta["duration_bucket"],
                "credit_quality": meta["credit"],
                "yield_pct": info.get("yield", np.nan),
                "expense_ratio": info.get("annualReportExpenseRatio", np.nan),
                "total_assets": info.get("totalAssets", np.nan),
                "nav_price": info.get("navPrice", np.nan),
                "avg_volume": info.get("averageVolume", np.nan),
                "beta_3y": info.get("beta3Year", np.nan),
                "asset_class": "Bond",
                "recommended_method": "DCF",
            })
            rate_limit(0.3)
        except Exception as e:
            print(f"    ⚠ {ticker_str}: {e}")
    
    bond_meta_df = pd.DataFrame(bond_meta)
    bond_meta_df.to_parquet(RAW_DIR / "bonds" / "bond_etf_metadata.parquet")
    bond_meta_df.to_csv(RAW_DIR / "bonds" / "bond_etf_metadata.csv", index=False)
    
    print(f"✅ Bond ETF data saved: {len(bond_meta_df)} instruments")
    return bond_meta_df


# Uncomment to run:
# bond_data = collect_bond_etf_data()


# %% [markdown]
# ---
# ## 6. Commodities Data
#
# Commodity pricing follows **Cost-of-Carry** and **convenience yield** models.
# We collect futures/spot data via yfinance commodity tickers.

# %%
# ═══════════════════════════════════════════════════════════════════════════════
# CELL 6 — Commodities: Spot Prices, Futures Proxies
# ═══════════════════════════════════════════════════════════════════════════════

COMMODITY_TICKERS = {
    # Precious Metals
    "GC=F":  {"name": "Gold Futures",        "category": "Precious Metals", "method": "Cost-of-Carry"},
    "SI=F":  {"name": "Silver Futures",       "category": "Precious Metals", "method": "Cost-of-Carry"},
    "PL=F":  {"name": "Platinum Futures",     "category": "Precious Metals", "method": "Cost-of-Carry"},
    # Energy
    "CL=F":  {"name": "Crude Oil WTI",        "category": "Energy", "method": "Cost-of-Carry"},
    "BZ=F":  {"name": "Brent Crude",          "category": "Energy", "method": "Cost-of-Carry"},
    "NG=F":  {"name": "Natural Gas",          "category": "Energy", "method": "Cost-of-Carry"},
    "RB=F":  {"name": "RBOB Gasoline",        "category": "Energy", "method": "Cost-of-Carry"},
    # Agriculture
    "ZC=F":  {"name": "Corn Futures",         "category": "Agriculture", "method": "Cost-of-Carry"},
    "ZW=F":  {"name": "Wheat Futures",        "category": "Agriculture", "method": "Cost-of-Carry"},
    "ZS=F":  {"name": "Soybean Futures",      "category": "Agriculture", "method": "Cost-of-Carry"},
    "KC=F":  {"name": "Coffee Futures",       "category": "Agriculture", "method": "Cost-of-Carry"},
    "CC=F":  {"name": "Cocoa Futures",        "category": "Agriculture", "method": "Cost-of-Carry"},
    # Industrial Metals
    "HG=F":  {"name": "Copper Futures",       "category": "Industrial Metals", "method": "Cost-of-Carry"},
    # ETF proxies for spot
    "GLD":   {"name": "Gold ETF (spot proxy)", "category": "Precious Metals", "method": "Mark-to-Market"},
    "USO":   {"name": "Oil ETF (spot proxy)",  "category": "Energy", "method": "Mark-to-Market"},
}


def collect_commodity_data():
    """Collect commodity futures and ETF spot proxy data."""
    print(f"\n📥 Collecting commodity data ({len(COMMODITY_TICKERS)} instruments)...")
    
    tickers = list(COMMODITY_TICKERS.keys())
    
    # Batch download
    try:
        hist = yf.download(tickers, period="10y", auto_adjust=True, progress=True)
        hist.to_parquet(RAW_DIR / "commodities" / "commodity_prices.parquet")
        print(f"  → Historical prices: {hist.shape}")
    except Exception as e:
        print(f"  ⚠ Download failed: {e}")
    
    # Build metadata
    commodity_meta = pd.DataFrame([
        {"symbol": sym, **meta, "asset_class": "Commodity", "recommended_method": meta["method"]}
        for sym, meta in COMMODITY_TICKERS.items()
    ])
    commodity_meta.to_csv(RAW_DIR / "commodities" / "commodity_metadata.csv", index=False)
    
    print(f"✅ Commodity data saved")
    return commodity_meta


# Uncomment to run:
# commodity_data = collect_commodity_data()


# %% [markdown]
# ---
# ## 7. Forex Data
#
# Currency pairs are valued using **interest rate parity** and **forward pricing**.
# Relevant for the Forward/Futures valuation method recommendation.

# %%
# ═══════════════════════════════════════════════════════════════════════════════
# CELL 7 — Forex: Major Currency Pairs
# ═══════════════════════════════════════════════════════════════════════════════

FOREX_TICKERS = {
    "EURUSD=X": "EUR/USD", "GBPUSD=X": "GBP/USD", "USDJPY=X": "USD/JPY",
    "USDCHF=X": "USD/CHF", "AUDUSD=X": "AUD/USD", "USDCAD=X": "USD/CAD",
    "NZDUSD=X": "NZD/USD", "EURGBP=X": "EUR/GBP", "EURJPY=X": "EUR/JPY",
    "GBPJPY=X": "GBP/JPY", "USDTND=X": "USD/TND",  # Tunisia
}


def collect_forex_data():
    """Collect major FX pair historical data."""
    print(f"\n📥 Collecting forex data ({len(FOREX_TICKERS)} pairs)...")
    tickers = list(FOREX_TICKERS.keys())
    
    try:
        hist = yf.download(tickers, period="10y", auto_adjust=True, progress=True)
        hist.to_parquet(RAW_DIR / "forex" / "forex_prices.parquet")
        print(f"  → Forex data: {hist.shape}")
    except Exception as e:
        print(f"  ⚠ {e}")
    
    fx_meta = pd.DataFrame([
        {"symbol": sym, "pair_name": name, "asset_class": "Currency",
         "recommended_method": "Interest Rate Parity / Forward Pricing"}
        for sym, name in FOREX_TICKERS.items()
    ])
    fx_meta.to_csv(RAW_DIR / "forex" / "forex_metadata.csv", index=False)
    
    print(f"✅ Forex data saved")
    return fx_meta


# Uncomment to run:
# forex_data = collect_forex_data()


# %% [markdown]
# ---
# ## 8. Alpha Vantage — Complementary Stock & Indicator Data
#
# Alpha Vantage provides **technical indicators** (RSI, MACD, Bollinger Bands)
# and **fundamental data** that complement yfinance. Free tier: 25 requests/day.

# %%
# ═══════════════════════════════════════════════════════════════════════════════
# CELL 8 — Alpha Vantage: Technical Indicators & Fundamentals
# ═══════════════════════════════════════════════════════════════════════════════

AV_BASE_URL = "https://www.alphavantage.co/query"


def collect_alpha_vantage_data(tickers, api_key):
    """
    Collect technical indicators from Alpha Vantage (free tier: 25 req/day).
    Focus on indicators useful as ML features:
      - RSI, MACD, Bollinger Bands, SMA, EMA, ATR, ADX, Stochastic
    """
    if api_key == "YOUR_AV_KEY_HERE":
        print("  ⚠ Alpha Vantage API key not set. Get one free at:")
        print("    https://www.alphavantage.co/support/#api-key")
        return pd.DataFrame()
    
    print(f"\n📥 Collecting Alpha Vantage indicators for {len(tickers)} tickers...")
    print("  ⚠ Free tier = 25 requests/day. Collecting key indicators only.\n")
    
    indicators = ["RSI", "MACD", "BBANDS", "SMA", "EMA", "ATR", "ADX"]
    all_data = []
    request_count = 0
    
    for ticker_str in tickers[:5]:  # Limit to 5 tickers on free tier
        for indicator in indicators[:3]:  # Top 3 indicators per ticker
            if request_count >= 24:
                print("  ⚠ Approaching daily limit, stopping.")
                break
            
            try:
                params = {
                    "function": indicator,
                    "symbol": ticker_str,
                    "interval": "daily",
                    "time_period": 14,
                    "series_type": "close",
                    "apikey": api_key,
                }
                
                resp = safe_request(AV_BASE_URL, params=params)
                if resp:
                    data = resp.json()
                    # Parse the nested response
                    ts_key = [k for k in data.keys() if "Technical" in k or "Meta" not in k]
                    if ts_key:
                        df = pd.DataFrame(data[ts_key[-1]]).T
                        df.index = pd.to_datetime(df.index)
                        df["symbol"] = ticker_str
                        df["indicator"] = indicator
                        all_data.append(df)
                        print(f"    ✓ {ticker_str} / {indicator}")
                
                request_count += 1
                rate_limit(12)  # 5 requests/min on free tier
                
            except Exception as e:
                print(f"    ✗ {ticker_str}/{indicator}: {e}")
    
    if all_data:
        result = pd.concat(all_data)
        result.to_csv(RAW_DIR / "equities" / "alpha_vantage_indicators.csv")
        print(f"\n✅ Alpha Vantage data saved: {len(result)} rows")
        return result
    
    return pd.DataFrame()


# Uncomment to run:
# av_data = collect_alpha_vantage_data(["AAPL", "MSFT", "JPM", "XOM", "GLD"], ALPHA_VANTAGE_KEY)


# %% [markdown]
# ---
# ## 9. Finnhub — Real-Time Quotes & Company Fundamentals
#
# Finnhub provides **free real-time** data, company profiles, earnings,
# and financial statements — useful for cross-validating yfinance data.

# %%
# ═══════════════════════════════════════════════════════════════════════════════
# CELL 9 — Finnhub: Company Profiles, Earnings, Financial Metrics
# ═══════════════════════════════════════════════════════════════════════════════

FINNHUB_BASE = "https://finnhub.io/api/v1"


def collect_finnhub_data(tickers, api_key):
    """
    Collect company profiles and basic financial metrics from Finnhub.
    Free tier: 60 API calls/minute.
    """
    if api_key == "YOUR_FINNHUB_KEY_HERE":
        print("  ⚠ Finnhub API key not set. Get one free at:")
        print("    https://finnhub.io/register")
        return pd.DataFrame()
    
    print(f"\n📥 Collecting Finnhub data for {len(tickers)} tickers...")
    
    profiles = []
    for ticker_str in tqdm(tickers, desc="  Finnhub"):
        try:
            # Company profile
            resp = safe_request(
                f"{FINNHUB_BASE}/stock/profile2",
                params={"symbol": ticker_str, "token": api_key}
            )
            if resp and resp.status_code == 200:
                profile = resp.json()
                
                # Basic financials
                resp2 = safe_request(
                    f"{FINNHUB_BASE}/stock/metric",
                    params={"symbol": ticker_str, "metric": "all", "token": api_key}
                )
                metrics = {}
                if resp2 and resp2.status_code == 200:
                    m = resp2.json().get("metric", {})
                    metrics = {
                        "52WeekHigh": m.get("52WeekHigh"),
                        "52WeekLow": m.get("52WeekLow"),
                        "beta": m.get("beta"),
                        "peRatio": m.get("peTTM"),
                        "pbRatio": m.get("pbQuarterly"),
                        "roeTTM": m.get("roeTTM"),
                        "debtEquity": m.get("totalDebt/totalEquityQuarterly"),
                        "revenueGrowth3Y": m.get("revenueGrowth3Y"),
                        "dividendYield": m.get("dividendYieldIndicatedAnnual"),
                    }
                
                profiles.append({**profile, **metrics})
            
            rate_limit(1.1)  # Stay under 60/min
            
        except Exception as e:
            print(f"    ⚠ {ticker_str}: {e}")
    
    if profiles:
        df = pd.DataFrame(profiles)
        df.to_csv(RAW_DIR / "equities" / "finnhub_profiles.csv", index=False)
        print(f"\n✅ Finnhub data saved: {len(df)} companies")
        return df
    
    return pd.DataFrame()


# Uncomment to run:
# finnhub_data = collect_finnhub_data(all_equity_tickers[:20], FINNHUB_KEY)


# %% [markdown]
# ---
# ## 10. Synthetic Labeled Dataset for the Recommendation Layer
#
# This is the **most critical step** for the ML model. Since no public dataset
# maps (asset features → recommended valuation method), we build one using
# expert rules derived from Hull's framework and IFRS 13.

# %%
# ═══════════════════════════════════════════════════════════════════════════════
# CELL 10 — Synthetic Labeled Dataset: Asset → Valuation Method Mapping
# ═══════════════════════════════════════════════════════════════════════════════

def build_valuation_method_labels():
    """
    Build a labeled dataset mapping asset characteristics to the recommended
    valuation method. This encodes the expert decision matrix from Hull + IFRS 13.
    
    Labels (target variable):
        - "DCF"           : Bonds, dividend-paying stocks, fixed income
        - "DDM"           : Dividend-paying equities
        - "Relative"      : Equities with comparable peers
        - "Black-Scholes" : European options
        - "Binomial-Tree" : American options, early exercise
        - "Monte-Carlo"   : Exotic options, complex payoffs
        - "Cost-of-Carry" : Commodities, FX forwards
        - "Mark-to-Market": Liquid assets with observable prices (IFRS Level 1)
        - "Credit-Model"  : Corporate bonds with default risk, CDS
        - "Forward-Pricing": FX forwards, futures contracts
    """
    
    np.random.seed(42)
    records = []
    
    # ── Rule 1: Government Bonds → DCF ───────────────────────────────────
    for _ in range(500):
        records.append({
            "asset_class": "Bond",
            "asset_subclass": "Government Bond",
            "has_market_price": np.random.choice([True, False], p=[0.8, 0.2]),
            "has_cash_flows": True,
            "has_options_features": False,
            "is_exchange_traded": np.random.choice([True, False], p=[0.7, 0.3]),
            "liquidity": np.random.choice(["High", "Medium", "Low"], p=[0.6, 0.3, 0.1]),
            "maturity_years": np.random.uniform(0.25, 30),
            "has_credit_risk": False,
            "has_early_exercise": False,
            "is_path_dependent": False,
            "data_availability": np.random.choice(["Full", "Partial", "Sparse"], p=[0.7, 0.2, 0.1]),
            "volatility_available": np.random.choice([True, False], p=[0.5, 0.5]),
            "ifrs_level": np.random.choice([1, 2], p=[0.7, 0.3]),
            "recommended_method": "DCF",
        })
    
    # ── Rule 2: Corporate Bonds → DCF or Credit-Model ───────────────────
    for _ in range(400):
        has_default_risk = np.random.choice([True, False], p=[0.6, 0.4])
        records.append({
            "asset_class": "Bond",
            "asset_subclass": "Corporate Bond",
            "has_market_price": np.random.choice([True, False], p=[0.5, 0.5]),
            "has_cash_flows": True,
            "has_options_features": False,
            "is_exchange_traded": np.random.choice([True, False], p=[0.4, 0.6]),
            "liquidity": np.random.choice(["High", "Medium", "Low"], p=[0.2, 0.4, 0.4]),
            "maturity_years": np.random.uniform(1, 30),
            "has_credit_risk": has_default_risk,
            "has_early_exercise": False,
            "is_path_dependent": False,
            "data_availability": np.random.choice(["Full", "Partial", "Sparse"], p=[0.3, 0.4, 0.3]),
            "volatility_available": np.random.choice([True, False], p=[0.3, 0.7]),
            "ifrs_level": np.random.choice([2, 3], p=[0.5, 0.5]),
            "recommended_method": "Credit-Model" if has_default_risk else "DCF",
        })
    
    # ── Rule 3: Dividend Equities → DDM ──────────────────────────────────
    for _ in range(400):
        records.append({
            "asset_class": "Equity",
            "asset_subclass": "Dividend Stock",
            "has_market_price": True,
            "has_cash_flows": True,
            "has_options_features": False,
            "is_exchange_traded": True,
            "liquidity": np.random.choice(["High", "Medium"], p=[0.7, 0.3]),
            "maturity_years": np.nan,  # perpetual
            "has_credit_risk": False,
            "has_early_exercise": False,
            "is_path_dependent": False,
            "data_availability": "Full",
            "volatility_available": True,
            "ifrs_level": 1,
            "recommended_method": "DDM",
        })
    
    # ── Rule 4: Growth Equities → DCF or Relative ────────────────────────
    for _ in range(400):
        has_peers = np.random.choice([True, False], p=[0.6, 0.4])
        records.append({
            "asset_class": "Equity",
            "asset_subclass": "Growth Stock",
            "has_market_price": True,
            "has_cash_flows": True,
            "has_options_features": False,
            "is_exchange_traded": True,
            "liquidity": np.random.choice(["High", "Medium", "Low"], p=[0.5, 0.3, 0.2]),
            "maturity_years": np.nan,
            "has_credit_risk": False,
            "has_early_exercise": False,
            "is_path_dependent": False,
            "data_availability": np.random.choice(["Full", "Partial"], p=[0.7, 0.3]),
            "volatility_available": True,
            "ifrs_level": 1,
            "recommended_method": "Relative" if has_peers else "DCF",
        })
    
    # ── Rule 5: European Options → Black-Scholes ─────────────────────────
    for _ in range(500):
        records.append({
            "asset_class": "Option",
            "asset_subclass": "European Option",
            "has_market_price": np.random.choice([True, False], p=[0.6, 0.4]),
            "has_cash_flows": False,
            "has_options_features": True,
            "is_exchange_traded": np.random.choice([True, False], p=[0.7, 0.3]),
            "liquidity": np.random.choice(["High", "Medium", "Low"], p=[0.4, 0.3, 0.3]),
            "maturity_years": np.random.uniform(0.02, 2),
            "has_credit_risk": False,
            "has_early_exercise": False,
            "is_path_dependent": False,
            "data_availability": np.random.choice(["Full", "Partial"], p=[0.6, 0.4]),
            "volatility_available": True,
            "ifrs_level": np.random.choice([1, 2], p=[0.5, 0.5]),
            "recommended_method": "Black-Scholes",
        })
    
    # ── Rule 6: American Options → Binomial Tree ─────────────────────────
    for _ in range(400):
        records.append({
            "asset_class": "Option",
            "asset_subclass": "American Option",
            "has_market_price": np.random.choice([True, False], p=[0.5, 0.5]),
            "has_cash_flows": False,
            "has_options_features": True,
            "is_exchange_traded": True,
            "liquidity": np.random.choice(["High", "Medium", "Low"], p=[0.3, 0.4, 0.3]),
            "maturity_years": np.random.uniform(0.02, 2),
            "has_credit_risk": False,
            "has_early_exercise": True,
            "is_path_dependent": False,
            "data_availability": np.random.choice(["Full", "Partial"], p=[0.5, 0.5]),
            "volatility_available": True,
            "ifrs_level": np.random.choice([1, 2], p=[0.4, 0.6]),
            "recommended_method": "Binomial-Tree",
        })
    
    # ── Rule 7: Exotic Options → Monte Carlo ─────────────────────────────
    for _ in range(300):
        records.append({
            "asset_class": "Option",
            "asset_subclass": np.random.choice(["Asian Option", "Barrier Option",
                                                  "Lookback Option", "Digital Option"]),
            "has_market_price": False,
            "has_cash_flows": False,
            "has_options_features": True,
            "is_exchange_traded": False,
            "liquidity": np.random.choice(["Low", "Medium"], p=[0.7, 0.3]),
            "maturity_years": np.random.uniform(0.1, 5),
            "has_credit_risk": False,
            "has_early_exercise": np.random.choice([True, False]),
            "is_path_dependent": True,
            "data_availability": np.random.choice(["Partial", "Sparse"], p=[0.4, 0.6]),
            "volatility_available": np.random.choice([True, False], p=[0.6, 0.4]),
            "ifrs_level": 3,
            "recommended_method": "Monte-Carlo",
        })
    
    # ── Rule 8: Commodities → Cost-of-Carry ──────────────────────────────
    for _ in range(400):
        records.append({
            "asset_class": "Commodity",
            "asset_subclass": np.random.choice(["Precious Metal", "Energy",
                                                  "Agriculture", "Industrial Metal"]),
            "has_market_price": True,
            "has_cash_flows": False,
            "has_options_features": False,
            "is_exchange_traded": True,
            "liquidity": np.random.choice(["High", "Medium"], p=[0.6, 0.4]),
            "maturity_years": np.random.uniform(0.08, 2),
            "has_credit_risk": False,
            "has_early_exercise": False,
            "is_path_dependent": False,
            "data_availability": "Full",
            "volatility_available": True,
            "ifrs_level": 1,
            "recommended_method": "Cost-of-Carry",
        })
    
    # ── Rule 9: FX Forwards → Forward Pricing ────────────────────────────
    for _ in range(300):
        records.append({
            "asset_class": "Currency",
            "asset_subclass": "FX Forward",
            "has_market_price": np.random.choice([True, False], p=[0.6, 0.4]),
            "has_cash_flows": False,
            "has_options_features": False,
            "is_exchange_traded": False,
            "liquidity": np.random.choice(["High", "Medium"], p=[0.7, 0.3]),
            "maturity_years": np.random.uniform(0.02, 1),
            "has_credit_risk": False,
            "has_early_exercise": False,
            "is_path_dependent": False,
            "data_availability": "Full",
            "volatility_available": True,
            "ifrs_level": 2,
            "recommended_method": "Forward-Pricing",
        })
    
    # ── Rule 10: Highly liquid exchange-traded → Mark-to-Market ──────────
    for _ in range(300):
        records.append({
            "asset_class": np.random.choice(["Equity", "ETF", "Commodity"]),
            "asset_subclass": "Liquid Exchange-Traded",
            "has_market_price": True,
            "has_cash_flows": np.random.choice([True, False]),
            "has_options_features": False,
            "is_exchange_traded": True,
            "liquidity": "High",
            "maturity_years": np.nan,
            "has_credit_risk": False,
            "has_early_exercise": False,
            "is_path_dependent": False,
            "data_availability": "Full",
            "volatility_available": True,
            "ifrs_level": 1,
            "recommended_method": "Mark-to-Market",
        })
    
    # ── Rule 11: Swaps → DCF (swap variant) ──────────────────────────────
    for _ in range(250):
        records.append({
            "asset_class": "Derivative",
            "asset_subclass": np.random.choice(["Interest Rate Swap",
                                                  "Currency Swap", "CDS"]),
            "has_market_price": False,
            "has_cash_flows": True,
            "has_options_features": False,
            "is_exchange_traded": False,
            "liquidity": np.random.choice(["Medium", "Low"], p=[0.5, 0.5]),
            "maturity_years": np.random.uniform(1, 30),
            "has_credit_risk": True,
            "has_early_exercise": False,
            "is_path_dependent": False,
            "data_availability": np.random.choice(["Partial", "Sparse"], p=[0.5, 0.5]),
            "volatility_available": False,
            "ifrs_level": np.random.choice([2, 3], p=[0.4, 0.6]),
            "recommended_method": "DCF",
        })
    
    # ── Assemble & Save ──────────────────────────────────────────────────
    df = pd.DataFrame(records)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Encode boolean columns
    bool_cols = ["has_market_price", "has_cash_flows", "has_options_features",
                 "is_exchange_traded", "has_credit_risk", "has_early_exercise",
                 "is_path_dependent", "volatility_available"]
    for col in bool_cols:
        df[col] = df[col].astype(int)
    
    # Save
    df.to_parquet(PROCESSED_DIR / "labeled_valuation_dataset.parquet")
    df.to_csv(PROCESSED_DIR / "labeled_valuation_dataset.csv", index=False)
    
    print("\n" + "=" * 60)
    print("📊 SYNTHETIC LABELED DATASET SUMMARY")
    print("=" * 60)
    print(f"Total samples: {len(df):,}")
    print(f"\nTarget distribution (recommended_method):")
    print(df["recommended_method"].value_counts().to_string())
    print(f"\nAsset class distribution:")
    print(df["asset_class"].value_counts().to_string())
    print(f"\nIFRS Level distribution:")
    print(df["ifrs_level"].value_counts().sort_index().to_string())
    print(f"\nSaved to: {PROCESSED_DIR / 'labeled_valuation_dataset.csv'}")
    
    return df


labeled_dataset = build_valuation_method_labels()


# %% [markdown]
# ---
# ## 11. Master Collection Runner
#
# Run all data collection functions in sequence. Set your API keys above,
# then uncomment and execute this cell.

# %%
# ═══════════════════════════════════════════════════════════════════════════════
# CELL 11 — MASTER RUNNER: Collect Everything
# ═══════════════════════════════════════════════════════════════════════════════

def run_full_collection():
    """
    Execute the full data collection pipeline.
    Estimated time: ~30-45 minutes depending on API rate limits.
    """
    print("🚀 STARTING FULL DATA COLLECTION PIPELINE")
    print("=" * 60)
    start = time.time()
    
    # 1. FinanceDatabase catalog (no API key needed)
    print("\n\n" + "━" * 60)
    print("STEP 1/9: FinanceDatabase Instrument Catalog")
    print("━" * 60)
    catalog = collect_financedatabase_catalog()
    
    # 2. Equity historical data & fundamentals
    print("\n\n" + "━" * 60)
    print("STEP 2/9: Equity Historical Prices & Fundamentals")
    print("━" * 60)
    eq_hist, eq_fund = collect_equity_data(all_equity_tickers)
    
    # 3. Options chains
    print("\n\n" + "━" * 60)
    print("STEP 3/9: Options Chains with IV & Greeks")
    print("━" * 60)
    options = collect_options_data(OPTIONS_TICKERS)
    
    # 4. FRED macro & rates data
    print("\n\n" + "━" * 60)
    print("STEP 4/9: FRED Treasury Yields & Macro Data")
    print("━" * 60)
    fred = collect_fred_data(FRED_KEY)
    
    # 5. Bond ETF proxies
    print("\n\n" + "━" * 60)
    print("STEP 5/9: Bond ETF Data (Fixed Income Proxies)")
    print("━" * 60)
    bonds = collect_bond_etf_data()
    
    # 6. Commodities
    print("\n\n" + "━" * 60)
    print("STEP 6/9: Commodity Futures & Spot Data")
    print("━" * 60)
    commodities = collect_commodity_data()
    
    # 7. Forex
    print("\n\n" + "━" * 60)
    print("STEP 7/9: Forex Data")
    print("━" * 60)
    forex = collect_forex_data()
    
    # 8. Alpha Vantage technical indicators
    print("\n\n" + "━" * 60)
    print("STEP 8/9: Alpha Vantage Technical Indicators")
    print("━" * 60)
    av = collect_alpha_vantage_data(["AAPL", "MSFT", "JPM"], ALPHA_VANTAGE_KEY)
    
    # 9. Finnhub company data
    print("\n\n" + "━" * 60)
    print("STEP 9/9: Finnhub Company Profiles")
    print("━" * 60)
    fh = collect_finnhub_data(all_equity_tickers[:15], FINNHUB_KEY)
    
    # Summary
    elapsed = time.time() - start
    print("\n\n" + "=" * 60)
    print("🎉 COLLECTION COMPLETE")
    print("=" * 60)
    print(f"⏱  Total time: {elapsed/60:.1f} minutes")
    print(f"\n📁 Data directory: {BASE_DIR.resolve()}")
    print(f"   raw/equities/     — Historical prices, fundamentals")
    print(f"   raw/options/      — Options chains with IV")
    print(f"   raw/bonds/        — Bond ETF data, yield curves")
    print(f"   raw/commodities/  — Commodity futures & spot")
    print(f"   raw/forex/        — FX pair data")
    print(f"   raw/macro/        — FRED rates, spreads, macro")
    print(f"   catalogs/         — FinanceDatabase 300k+ catalog")
    print(f"   processed/        — Labeled training dataset")


# ═══════════════════════════════════════════════════════════════════════════════
# TO RUN EVERYTHING:
#   1. Set your API keys in Cell 0 (ALPHA_VANTAGE_KEY, FINNHUB_KEY, FRED_KEY)
#   2. Uncomment the line below and run this cell
# ═══════════════════════════════════════════════════════════════════════════════

# run_full_collection()


# %% [markdown]
# ---
# ## 12. Data Inventory Report
#
# Quick verification: list all collected files and their sizes.

# %%
# ═══════════════════════════════════════════════════════════════════════════════
# CELL 12 — Data Inventory
# ═══════════════════════════════════════════════════════════════════════════════

def print_data_inventory():
    """Print a summary of all collected data files."""
    print("\n📦 DATA INVENTORY")
    print("=" * 70)
    
    total_size = 0
    for root, dirs, files in os.walk(BASE_DIR):
        for f in sorted(files):
            filepath = Path(root) / f
            size = filepath.stat().st_size
            total_size += size
            rel = filepath.relative_to(BASE_DIR)
            size_str = f"{size/1024:.1f} KB" if size < 1024*1024 else f"{size/1024/1024:.1f} MB"
            print(f"  {str(rel):<55} {size_str:>10}")
    
    print(f"\n{'Total':.<55} {total_size/1024/1024:.1f} MB")

print_data_inventory()


# %% [markdown]
# ---
# ## 📋 Summary of Data Sources
#
# | # | Source | Data Type | API Key? | Rate Limit | Coverage |
# |---|--------|-----------|----------|------------|----------|
# | 1 | **FinanceDatabase** | 300k+ instrument classification | No | None | Equities, ETFs, Funds, Indices, Crypto, FX |
# | 2 | **yfinance** | OHLCV, fundamentals, options chains | No | ~2000/hr | Equities, Options, ETFs, Commodities, Crypto, FX |
# | 3 | **FRED** | Treasury yields, rates, credit spreads, macro | Free key | 120/min | Bonds, Interest Rates, Economic Indicators |
# | 4 | **Alpha Vantage** | Technical indicators, fundamentals | Free key | 25/day | Equities, Forex, Commodities |
# | 5 | **Finnhub** | Company profiles, financial metrics, earnings | Free key | 60/min | Global equities, 30+ years fundamentals |
# | 6 | **Synthetic Rules** | Labeled (asset → valuation method) dataset | N/A | N/A | All asset classes, 4,150 samples |
#
# ### Datasets NOT Used (and why):
# - **Reuters / Bloomberg**: Paywalled, no free programmatic access
# - **SeekingAlpha**: Limited free API, primarily editorial content
# - **Investopedia**: Educational articles, not structured data
# - **The-FinAI/FinData**: NLP classification dataset (useful for term taxonomy, not pricing data)
#
# ### Recommended Next Steps:
# 1. **Run this notebook** with API keys set to collect all data
# 2. **Augment** the synthetic dataset with real labeled examples from VERMEG's workflow
# 3. **Feature engineering**: Compute volatility, Greeks, duration, credit metrics from raw data
# 4. **Proceed to Chapter 3** (Feature Engineering & Dataset Construction)
