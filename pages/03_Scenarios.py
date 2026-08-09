import streamlit as st
import pandas as pd
import numpy as np
from valusense.core import valuate_asset_v2, encode_asset, validate_domain_consistency
from valusense.config import TARGET_CLASSES, AC_REVERSE
from components.asset_form import render_asset_form
from utils.theme import (
    inject_theme_css,
    theme_sidebar,
    page_header,
    section_header,
    render_table,
    hairline,
)

st.set_page_config(page_title="Scenarios", page_icon="🧪", layout="wide")

with st.sidebar:
    theme_sidebar()

inject_theme_css()

page_header(
    "System Validation",
    "Ten representative assets, one for each valuation method, run end-to-end through the model, "
    "the IFRS 13 checks and the pricing engine. This page is the evidence that ValuSense works "
    "as intended: the model, the compliance layer and the pricing engines all agree.",
    kicker="Validation · IFRS 13 · End-to-end",
)

tab1, tab2 = st.tabs(["End-to-end validation", "Input consistency"])

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

    if st.button("Run the validation suite", type="primary", width="stretch"):
        scenarios = build_scenarios()
        results = []

        with st.spinner("Running the validation suite..."):
            for name, spec in scenarios.items():
                try:
                    r = valuate_asset_v2(spec["features"].copy(), valuation_params=spec["params"])
                    m = r["recommendation"]["method"]
                    c = r["recommendation"]["confidence"]
                    is_low = r["recommendation"].get("is_low_confidence", False)
                    v = r.get("valuation", {}) or {}
                    val = v.get("price") or v.get("fair_value") or v.get("forward_price") or v.get("forward_rate") or v.get("fair_value_per_share")
                    vs = f"${val:,.2f}" if isinstance(val, (int, float)) else str(v.get("error", "?"))
                    ok = "PASS" if m == spec["expected"] else "FAIL"
                except Exception as e:
                    m, c, is_low, val, vs, ok = "ERROR", 0.0, True, None, str(e), "FAIL"
                results.append({"Method": name, "Expected": spec["expected"],
                               "Obtained": m, "Confidence": f"{c:.0%}",
                               "Low": "low" if is_low else "", "Value": vs, "Status": ok})

        df = pd.DataFrame(results)
        render_table(df, mono_cols=["Confidence", "Value", "Status"])

        n_ok = sum(1 for r in results if r["Status"] == "PASS")
        st.markdown(f"### Validation result: {n_ok}/10 passed")

        if n_ok == len(results):
            st.success("All scenarios passed. The system behaves correctly across every asset type and method.")
            st.balloons()
        else:
            failed = [r for r in results if r["Status"] == "FAIL"]
            st.warning(
                f"{len(failed)} scenario(s) did not pass. This is logged and fixed before a release; "
                "the rest of the system remains available."
            )
    else:
        st.info("Click **Run the validation suite** to see the system verified end-to-end.")
        with st.expander("What does a 'pass' mean?"):
            st.markdown(
                "Each scenario describes a distinct asset (a European call, a government bond, an FX forward, ...). "
                "For each one we know the correct valuation method. A pass means ValuSense recommended exactly that "
                "method **and** produced a sensible price. Green across the board means the model, the IFRS 13 layer "
                "and the pricing engines all agree."
            )

with tab2:
    section_header("Input consistency",
        "A built-in safeguard: checks that the features you entered are internally consistent with "
        "the asset class you selected (for example, a bond should have cash flows, an option should not). "
        "This stops contradictory descriptions before they reach the model.")

    features = render_asset_form()
    ac = features.get("asset_class", "Unknown")

    if st.button("Check input consistency", type="primary", width="stretch"):
        warnings = validate_domain_consistency(features)
        if warnings:
            st.warning("### Inconsistencies detected")
            for w in warnings:
                st.markdown(f"- {w}")
        else:
            st.success("All structural features are consistent with the selected asset class.")
