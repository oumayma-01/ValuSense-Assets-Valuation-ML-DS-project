import streamlit as st
import pandas as pd
import numpy as np
from valusense.core import valuate_asset_v2, encode_asset, validate_domain_consistency
from valusense.config import TARGET_CLASSES, AC_REVERSE
from components.asset_form import render_asset_form

st.set_page_config(page_title="Scenarios", page_icon="chart_with_upwards_trend", layout="wide")
from utils.theme import inject_theme_css
inject_theme_css()
st.title("Scenarios & Domain Validation")

tab1, tab2 = st.tabs(["Run All (10 Scenarios)", "Domain Validation"])

with tab1:

    def build_scenarios():
        s = {}
        ac, sc = encode_asset("Option", "European Call")
        s["Black-Scholes"] = {"expected": "Black-Scholes",
            "features": {"has_options_features":1,"has_early_exercise":0,"is_path_dependent":0,"has_market_price":1,
                "has_cash_flows":0,"is_exchange_traded":1,"has_credit_risk":0,"volatility_available":1,
                "liquidity":2,"data_availability":2,"ifrs_level":1,"maturity_years":0.5,
                "implied_volatility_atm":0.26,"iv_skew":0.04,
                "asset_class_encoded":ac,"asset_subclass_encoded":sc},
            "params": {"S":195,"K":200,"T":0.5,"r":0.045,"sigma":0.26,"option_type":"call"}}

        ac, sc = encode_asset("Option", "American Put")
        s["Binomial-Tree"] = {"expected": "Binomial-Tree",
            "features": {"has_options_features":1,"has_early_exercise":1,"is_path_dependent":0,"has_market_price":1,
                "has_cash_flows":0,"is_exchange_traded":1,"has_credit_risk":0,"volatility_available":1,
                "liquidity":2,"data_availability":2,"ifrs_level":1,"maturity_years":1.0,
                "implied_volatility_atm":0.32,"iv_skew":0.05,
                "asset_class_encoded":ac,"asset_subclass_encoded":sc},
            "params": {"S":80,"K":100,"T":1.0,"r":0.045,"sigma":0.32,"option_type":"put"}}

        ac, sc = encode_asset("Option", "Asian Option")
        s["Monte-Carlo"] = {"expected": "Monte-Carlo",
            "features": {"has_options_features":1,"has_early_exercise":0,"is_path_dependent":1,"has_market_price":0,
                "has_cash_flows":0,"is_exchange_traded":0,"has_credit_risk":0,"volatility_available":1,
                "liquidity":0,"data_availability":1,"ifrs_level":3,"maturity_years":1.0,
                "implied_volatility_atm":0.35,"iv_skew":0.06,
                "asset_class_encoded":ac,"asset_subclass_encoded":sc},
            "params": {"S":100,"K":100,"T":1.0,"r":0.04,"sigma":0.35,"exotic_type":"asian","seed":42}}

        ac, sc = encode_asset("Bond", "Government Bond")
        s["DCF"] = {"expected": "DCF",
            "features": {"has_options_features":0,"has_early_exercise":0,"is_path_dependent":0,"has_market_price":1,
                "has_cash_flows":1,"is_exchange_traded":1,"has_credit_risk":0,"volatility_available":0,
                "liquidity":2,"data_availability":2,"ifrs_level":1,"maturity_years":10,
                "asset_class_encoded":ac,"asset_subclass_encoded":sc},
            "params": {"cash_flows":[30]*9+[1030],"discount_rate":0.04,"terminal_growth":0}}

        ac, sc = encode_asset("Equity", "Utility Stock")
        s["DDM"] = {"expected": "DDM",
            "features": {"has_options_features":0,"has_early_exercise":0,"is_path_dependent":0,"has_market_price":1,
                "has_cash_flows":1,"is_exchange_traded":1,"has_credit_risk":0,"volatility_available":1,
                "liquidity":2,"data_availability":2,"ifrs_level":1,"maturity_years":-1,
                "dividend_yield":0.045,"beta":0.65,"pe_ratio":12.5,"market_cap":35e9,
                "asset_class_encoded":ac,"asset_subclass_encoded":sc},
            "params": {"dividend_current":1.15,"growth_rate":0.025,"required_return":0.08}}

        ac, sc = encode_asset("Bond", "Corporate Bond (IG)")
        s["Credit-Model"] = {"expected": "Credit-Model",
            "features": {"has_options_features":0,"has_early_exercise":0,"is_path_dependent":0,"has_market_price":1,
                "has_cash_flows":1,"is_exchange_traded":1,"has_credit_risk":1,"volatility_available":0,
                "liquidity":1,"data_availability":2,"ifrs_level":2,"maturity_years":5,
                "duration_estimate":4.3,"credit_spread_asset":2.1,
                "asset_class_encoded":ac,"asset_subclass_encoded":sc},
            "params": {"face_value":1000,"coupon_rate":0.05,"maturity_years":5,"credit_spread":0.021,"risk_free_rate":0.045}}

        ac, sc = encode_asset("Commodity", "Precious Metal")
        s["Cost-of-Carry"] = {"expected": "Cost-of-Carry",
            "features": {"has_options_features":0,"has_early_exercise":0,"is_path_dependent":0,"has_market_price":1,
                "has_cash_flows":0,"is_exchange_traded":1,"has_credit_risk":0,"volatility_available":1,
                "liquidity":2,"data_availability":2,"ifrs_level":1,"maturity_years":0.5,
                "convenience_yield":0.005,"storage_cost_pct":0.01,
                "asset_class_encoded":ac,"asset_subclass_encoded":sc},
            "params": {"S":2350,"r":0.045,"T":0.5,"storage_cost":0.01,"convenience_yield":0.005}}

        ac, sc = encode_asset("Currency", "FX Forward")
        s["Forward-Pricing"] = {"expected": "Forward-Pricing",
            "features": {"has_options_features":0,"has_early_exercise":0,"is_path_dependent":0,"has_market_price":1,
                "has_cash_flows":0,"is_exchange_traded":0,"has_credit_risk":0,"volatility_available":1,
                "liquidity":2,"data_availability":2,"ifrs_level":1,"maturity_years":0.25,
                "asset_class_encoded":ac,"asset_subclass_encoded":sc},
            "params": {"S":1.085,"r_domestic":0.045,"r_foreign":0.035,"T":0.25}}

        ac, sc = encode_asset("Equity", "Index ETF")
        s["Mark-to-Market"] = {"expected": "Mark-to-Market",
            "features": {"has_options_features":0,"has_early_exercise":0,"is_path_dependent":0,"has_market_price":1,
                "has_cash_flows":0,"is_exchange_traded":1,"has_credit_risk":0,"volatility_available":1,
                "liquidity":2,"data_availability":2,"ifrs_level":1,"maturity_years":-1,
                "asset_class_encoded":ac,"asset_subclass_encoded":sc},
            "params": {"market_price":595.50,"bid":595.40,"ask":595.60,"volume":50000000}}

        ac, sc = encode_asset("Equity", "Large Cap Growth")
        s["Relative"] = {"expected": "Relative",
            "features": {"has_options_features":0,"has_early_exercise":0,"is_path_dependent":0,"has_market_price":1,
                "has_cash_flows":1,"is_exchange_traded":1,"has_credit_risk":0,"volatility_available":1,
                "liquidity":2,"data_availability":2,"ifrs_level":1,"maturity_years":-1,
                "dividend_yield":0,"beta":1.3,"pe_ratio":35,"market_cap":200e9,
                "asset_class_encoded":ac,"asset_subclass_encoded":sc},
            "params": {"earnings":6e9,"ebitda":10e9,"peer_pe":30,"peer_ev_ebitda":18,"net_debt":5e9,"shares_outstanding":2e9}}

        return s

    if st.button("Run All Scenarios", type="primary"):
        scenarios = build_scenarios()
        results = []

        with st.spinner("Running 10 scenarios..."):
            for name, spec in scenarios.items():
                r = valuate_asset_v2(spec["features"].copy(), valuation_params=spec["params"])
                m = r["recommendation"]["method"]
                c = r["recommendation"]["confidence"]
                is_low = r["recommendation"].get("is_low_confidence", False)
                v = r.get("valuation", {}) or {}
                val = v.get("price") or v.get("fair_value") or v.get("forward_price") or v.get("forward_rate") or v.get("fair_value_per_share")
                vs = f"${val:,.2f}" if isinstance(val, (int, float)) else str(v.get("error", "?"))
                ok = "✅" if m == spec["expected"] else "❌"
                badge = "⚠" if is_low else ""
                results.append({"Method": name, "Expected": spec["expected"],
                               "Obtained": m, "Confidence": f"{c:.0%}",
                               "Low": badge, "Value": vs, "Status": ok})

        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True, column_config={
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Low": st.column_config.TextColumn("Low", width="small"),
        })

        n_ok = sum(1 for r in results if r["Status"] == "✅")
        st.markdown(f"### {n_ok}/{len(results)} scenarios passed")

        if n_ok == len(results):
            st.balloons()
        else:
            failed = [r for r in results if r["Status"] == "❌"]
            st.warning(f"{len(failed)} scenario(s) failed. Check IFRS rules or model training.")
    else:
        st.info("Click **Run All Scenarios** to execute the 10 predefined test scenarios.")

with tab2:
    st.subheader("Domain Validation")
    st.markdown("Check the consistency between structural features and the selected asset class.")

    features = render_asset_form()
    ac = features.get("asset_class", "Unknown")

    if st.button("Check Domain Consistency", type="primary", use_container_width=True):
        warnings = validate_domain_consistency(features)
        if warnings:
            st.warning("### Inconsistencies Detected")
            for w in warnings:
                st.markdown(f"- {w}")
        else:
            st.success("All structural features are consistent with the selected asset class.")
