import numpy as np
import pandas as pd

from valusense.core import (
    valuate_asset_v2, encode_asset, validate_domain_consistency,
)
from valusense.config import (
    TARGET_CLASSES, ASSET_CLASSES, AC_REVERSE,
    FEATURE_NAMES, CALIBRATED_DEFAULTS,
)
from valusense.engines import VALUATION_ENGINES, ENGINE_SIGNATURES
from valusense.ifrs import apply_ifrs_constraints_v3


def _validate_features(features: dict) -> dict:
    ifrs = features.get("ifrs_level")
    if ifrs is not None and ifrs not in (1, 2, 3):
        return {"error": f"ifrs_level must be 1, 2, or 3, got {ifrs}"}
    return {}


_CLASS_DESCRIPTIONS = {
    "Option": "Financial derivative whose value depends on an underlying asset.",
    "Equity": "Ownership shares in a company (stocks).",
    "Bond": "Fixed-income instrument representing a loan to an issuer.",
    "Commodity": "Physical goods like metals, energy, or agricultural products.",
    "Currency": "Foreign exchange (FX) instruments.",
    "Derivative": "General derivative contract (other than plain options).",
}

_VALIDATION_MAP = {
    "Black-Scholes": {"required": {"S", "K", "T", "r", "sigma"},
                      "desc": "S=spot, K=strike, T=time(years), r=rate, sigma=vol"},
    "Binomial-Tree": {"required": {"S", "K", "T", "r", "sigma"},
                      "desc": "S=spot, K=strike, T=time(years), r=rate, sigma=vol, option_type='call'|'put', american=True"},
    "Monte-Carlo":   {"required": {"S", "K", "T", "r", "sigma"},
                      "desc": "S=spot, K=strike, T=time(years), r=rate, sigma=vol, exotic_type='asian'|None"},
    "DCF":           {"required": {"cash_flows", "discount_rate"},
                      "desc": "cash_flows=list of floats, discount_rate=float, terminal_growth=float"},
    "DDM":           {"required": {"dividend_current"},
                      "desc": "dividend_current=float, growth_rate=float, required_return=float"},
    "Cost-of-Carry": {"required": {"S", "r", "T"},
                      "desc": "S=spot, r=rate, T=time, storage_cost=float, convenience_yield=float"},
    "Forward-Pricing": {"required": {"S", "r_domestic", "r_foreign", "T"},
                        "desc": "S=spot_rate, r_domestic=domestic_rate, r_foreign=foreign_rate, T=time"},
    "Mark-to-Market": {"required": set(),
                       "desc": "market_price=float (or bid+ask). No model needed; uses observed price."},
    "Relative":       {"required": set(),
                       "desc": "Provide earnings+peer_pe and/or ebitda+peer_ev_ebitda and shares_outstanding"},
    "Credit-Model":   {"required": {"face_value"},
                       "desc": "face_value=float, coupon_rate=float, maturity_years=float, credit_spread=float, risk_free_rate=float"},
}


def classify_asset(features: dict) -> dict:
    err = _validate_features(features)
    if "error" in err:
        return err

    ac_name = None
    ac = features.get("asset_class_encoded")
    if ac is not None:
        ac_name = AC_REVERSE.get(ac)
    if ac_name is None and features.get("asset_class"):
        ac_name = features["asset_class"]

    sc_name = features.get("asset_subclass", None)

    try:
        result = valuate_asset_v2(features, valuation_params=None)
    except Exception as e:
        return {"error": f"Classification failed: {e}"}

    rec = result["recommendation"]
    return {
        "asset_class": ac_name or "Unknown",
        "asset_subclass": sc_name or "Not specified",
        "predicted_method": rec["method"],
        "calibrated_confidence": round(rec["confidence"], 4),
        "is_low_confidence": rec.get("is_low_confidence", False),
        "ml_raw_prediction": rec["ml_prediction"],
        "ifrs_overridden": rec["ifrs_override"],
        "top_3_alternatives": result.get("alternatives", []),
        "warnings": result.get("explanation", {}).get("top_drivers", []),
    }


def check_ifrs_compliance(predicted_method: str, features: dict) -> dict:
    if predicted_method not in TARGET_CLASSES:
        return {"error": f"Unknown method '{predicted_method}'. Valid: {TARGET_CLASSES}"}

    try:
        le_target = __import__("valusense.config", fromlist=["le_target"]).le_target
    except Exception as e:
        return {"error": f"Cannot load label encoder: {e}"}

    X = pd.DataFrame([features])
    for col in FEATURE_NAMES:
        if col not in X.columns:
            X[col] = 0
    X = X[FEATURE_NAMES].fillna(0)

    pred_idx = le_target.transform([predicted_method])[0]
    y_arr = np.array([pred_idx])
    y_ifrs, n_overrides, details = apply_ifrs_constraints_v3(y_arr, X, le_target)
    final_method = le_target.inverse_transform([y_ifrs[0]])[0]
    overridden = final_method != predicted_method

    return {
        "final_method": final_method,
        "overridden": overridden,
        "rule_fired": details[0]["rule"] if details else None,
        "rule_explanation": _rule_description(details[0]["rule"]) if details else "No IFRS 13 override needed.",
    }


def _rule_description(rule_str: str) -> str:
    descs = {
        "DDM->Relative": "Equity with high P/E, no dividend, has CFs → IFRS requires Relative valuation.",
        "Mark-to-Market->Relative": "Equity with high growth, no dividend, has CFs → IFRS prefers Relative.",
        "Black-Scholes->Binomial-Tree": "Early exercise feature → IFRS requires Binomial-Tree (handles early exercise).",
    }
    for key, val in descs.items():
        if key in rule_str:
            return val
    if "->" in rule_str:
        return f"IFRS 13 overrides {rule_str.split('->')[0]} → {rule_str.split('->')[1]}."
    return f"Override: {rule_str}."


def explain_prediction(features: dict, method: str = None) -> dict:
    err = _validate_features(features)
    if "error" in err:
        return err

    try:
        result = valuate_asset_v2(features, valuation_params=None)
    except Exception as e:
        return {"error": f"Explanation failed: {e}"}

    drivers = result.get("explanation", {}).get("top_drivers", [])
    if not drivers:
        return {"error": "SHAP explanation unavailable (model may not support it or SHAP failed to load)."}

    formatted = []
    for d in drivers:
        formatted.append({
            "feature": d["feature"],
            "value": d["value"],
            "shap_impact": round(d["shap_impact"], 4),
            "direction": "positive" if d["shap_impact"] > 0 else "negative",
        })

    return {
        "top_5_shap_features": formatted,
        "predicted_method": result["recommendation"]["method"],
        "confidence": result["recommendation"]["confidence"],
        "natural_language_summary": result.get("explanation", {}).get("natural_language", ""),
    }


def run_valuation(method: str, params: dict) -> dict:
    method = method.strip()

    if method not in TARGET_CLASSES:
        return {"error": f"Unknown valuation method '{method}'. Valid methods: {TARGET_CLASSES}"}

    spec = _VALIDATION_MAP.get(method)
    if spec:
        missing = spec["required"] - set(params.keys())
        if missing:
            return {
                "error": f"Missing required parameter(s) for {method}: {sorted(missing)}. "
                         f"Required: {spec['desc']}."
            }

    fn = VALUATION_ENGINES.get(method)
    if fn is None:
        return {"error": f"No engine registered for method '{method}'."}

    try:
        result = fn(**params)
    except TypeError as e:
        arg_err = str(e).replace("()", f"{method}()")
        return {"error": f"Parameter error: {arg_err}. Expected params: {spec['desc'] if spec else 'see documentation'}."}
    except Exception as e:
        return {"error": f"{method} calculation failed: {e}"}

    if "error" in result:
        return {"error": result["error"]}

    price_key = None
    for k in ("price", "fair_value", "forward_price", "forward_rate", "fair_value_per_share"):
        if k in result and result[k] is not None:
            price_key = k
            break

    breakdown = {k: v for k, v in result.items()
                 if k not in ("method", "inputs", price_key) and not isinstance(v, dict)}
    if "inputs" in result:
        breakdown["inputs"] = result["inputs"]

    return {
        "fair_value": result.get(price_key) if price_key else None,
        "currency": "USD",
        "method_used": result.get("method", method),
        "breakdown": breakdown,
    }
