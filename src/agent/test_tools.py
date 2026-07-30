"""
Stage 1 test — direct tool calls, no agent.
Run: python -m src.agent.test_tools
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.agent.tools import classify_asset, check_ifrs_compliance, explain_prediction, run_valuation
from valusense.core import encode_asset


def test_1_european_call_option():
    print("=" * 60)
    print("TEST 1: European Call Option")
    print("=" * 60)
    ac, sc = encode_asset("Option", "European Call")
    features = {
        "asset_class_encoded": ac, "asset_subclass_encoded": sc,
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

    # 1a — classify
    cls = classify_asset(features)
    print("\n[classify_asset]")
    print(json.dumps(cls, indent=2))
    assert "error" not in cls, f"FAIL: {cls['error']}"
    method = cls["predicted_method"]
    print(f"  -> Predicted: {method} (conf={cls['calibrated_confidence']:.2%})")

    # 1b — IFRS check
    ifrs = check_ifrs_compliance(method, features)
    print("\n[check_ifrs_compliance]")
    print(json.dumps(ifrs, indent=2))

    # 1c — explain
    exp = explain_prediction(features)
    print("\n[explain_prediction]")
    print(json.dumps(exp, indent=2))

    # 1d — run valuation (Black-Scholes params)
    val = run_valuation(method, {"S": 195, "K": 200, "T": 0.5, "r": 0.045, "sigma": 0.26, "option_type": "call"})
    print("\n[run_valuation]")
    print(json.dumps(val, indent=2))
    assert "error" not in val, f"FAIL: {val.get('error')}"
    print(f"  -> Fair value: ${val['fair_value']:.4f}")


def test_2_corporate_bond():
    print("\n" + "=" * 60)
    print("TEST 2: Corporate Bond (IG)")
    print("=" * 60)
    ac, sc = encode_asset("Bond", "Corporate Bond (IG)")
    features = {
        "asset_class_encoded": ac, "asset_subclass_encoded": sc,
        "has_market_price": 1, "has_cash_flows": 1, "has_options_features": 0,
        "is_exchange_traded": 1, "liquidity": 1, "maturity_years": 5,
        "has_credit_risk": 1, "has_early_exercise": 0, "is_path_dependent": 0,
        "data_availability": 2, "volatility_available": 0, "ifrs_level": 2,
        "risk_free_rate_3m": 3.83, "yield_10y": 4.46, "yield_curve_slope": 0.27,
        "implied_volatility_atm": 0.0, "iv_skew": 0.0, "beta": 0.0,
        "pe_ratio": 0.0, "dividend_yield": 0.0, "market_cap": 0,
        "debt_to_equity": 50.0, "duration_estimate": 4.3, "credit_spread_asset": 2.1,
        "convenience_yield": 0.0, "storage_cost_pct": 0.0,
    }

    cls = classify_asset(features)
    print("\n[classify_asset]")
    print(json.dumps(cls, indent=2))
    assert "error" not in cls
    method = cls["predicted_method"]

    ifrs = check_ifrs_compliance(method, features)
    print("\n[check_ifrs_compliance]")
    print(json.dumps(ifrs, indent=2))

    val = run_valuation(method, {"face_value": 1000, "coupon_rate": 0.05, "maturity_years": 5,
                                 "credit_spread": 0.021, "risk_free_rate": 0.045})
    print("\n[run_valuation]")
    print(json.dumps(val, indent=2))
    if "error" not in val:
        print(f"  -> Fair value: ${val['fair_value']:.4f}")


def test_3_fx_forward():
    print("\n" + "=" * 60)
    print("TEST 3: FX Forward")
    print("=" * 60)
    ac, sc = encode_asset("Currency", "FX Forward")
    features = {
        "asset_class_encoded": ac, "asset_subclass_encoded": sc,
        "has_market_price": 1, "has_cash_flows": 0, "has_options_features": 0,
        "is_exchange_traded": 0, "liquidity": 2, "maturity_years": 0.25,
        "has_credit_risk": 0, "has_early_exercise": 0, "is_path_dependent": 0,
        "data_availability": 2, "volatility_available": 1, "ifrs_level": 1,
        "risk_free_rate_3m": 3.83, "yield_10y": 4.46, "yield_curve_slope": 0.27,
        "implied_volatility_atm": 0.0, "iv_skew": 0.0, "beta": 0.0,
        "pe_ratio": 0.0, "dividend_yield": 0.0, "market_cap": 0,
        "debt_to_equity": 0.0, "duration_estimate": 0.0, "credit_spread_asset": 0.0,
        "convenience_yield": 0.0, "storage_cost_pct": 0.0,
    }

    cls = classify_asset(features)
    print("\n[classify_asset]")
    print(json.dumps(cls, indent=2))
    assert "error" not in cls
    method = cls["predicted_method"]

    val = run_valuation(method, {"S": 1.085, "r_domestic": 0.045, "r_foreign": 0.035, "T": 0.25})
    print("\n[run_valuation]")
    print(json.dumps(val, indent=2))
    if "error" not in val:
        print(f"  -> Forward rate: {val['fair_value']:.6f}")


def test_4_error_handling():
    print("\n" + "=" * 60)
    print("TEST 4: Error handling — missing params")
    print("=" * 60)
    val = run_valuation("Black-Scholes", {"S": 100})
    print("\n[run_valuation with missing params]")
    print(json.dumps(val, indent=2))
    assert "error" in val
    print("  -> Correctly caught missing params error.")

    val2 = run_valuation("Unknown-Method", {})
    print("\n[run_valuation with unknown method]")
    print(json.dumps(val2, indent=2))
    assert "error" in val2
    print("  -> Correctly caught unknown method error.")


if __name__ == "__main__":
    test_1_european_call_option()
    test_2_corporate_bond()
    test_3_fx_forward()
    test_4_error_handling()
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
