import numpy as np
import pandas as pd

from .config import (
    best_model, le_target, FEATURE_NAMES, get_shap_values,
    AC_LOOKUP, SC_LOOKUP, AC_REVERSE, CALIBRATED_DEFAULTS
)
from .engines import VALUATION_ENGINES, ENGINE_SIGNATURES
from .ifrs import apply_ifrs_constraints_v3


def encode_asset(asset_class, asset_subclass=None):
    ac_enc = AC_LOOKUP.get(asset_class, -1)
    if ac_enc == -1:
        for name, idx in AC_LOOKUP.items():
            if name.lower() == asset_class.lower():
                ac_enc = idx
                break
    sc_enc = 0
    if asset_subclass:
        sc_enc = SC_LOOKUP.get(asset_subclass, -1)
        if sc_enc == -1:
            sub_lower = asset_subclass.lower()
            for name, idx in SC_LOOKUP.items():
                if sub_lower in name.lower() or name.lower() in sub_lower:
                    sc_enc = idx
                    break
            if sc_enc == -1:
                sc_enc = 0
    return ac_enc, sc_enc


def _build_feature_defaults(features):
    ac_enc = features.get("asset_class_encoded", -1)
    ac_name = AC_REVERSE.get(ac_enc)
    defaults = {}
    if ac_name and ac_name in CALIBRATED_DEFAULTS:
        for feat, stats in CALIBRATED_DEFAULTS[ac_name].items():
            defaults[feat] = stats["median"]
    if not features.get("has_options_features", 0):
        for f in ["implied_volatility_atm", "iv_skew", "avg_delta", "avg_gamma", "avg_vega", "avg_theta"]:
            defaults.setdefault(f, 0)
    if not features.get("has_cash_flows", 0):
        defaults.setdefault("dividend_yield", 0)
    if not features.get("has_credit_risk", 0):
        for f in ["credit_spread_asset", "duration_estimate"]:
            defaults.setdefault(f, 0)
    return defaults


def valuate_asset(asset_features, valuation_params=None):
    defaults = _build_feature_defaults(asset_features)
    for feat in FEATURE_NAMES:
        if feat not in asset_features or asset_features[feat] is None:
            asset_features[feat] = defaults.get(feat, 0)
    X = pd.DataFrame([asset_features])
    for col in FEATURE_NAMES:
        if col not in X.columns:
            X[col] = 0
    X = X[FEATURE_NAMES].fillna(0)

    pred = best_model.predict(X)[0]
    proba = best_model.predict_proba(X)[0]
    ml_method = le_target.inverse_transform([pred])[0]
    confidence = float(proba[pred])
    top3_idx = np.argsort(proba)[-3:][::-1]
    alternatives = [{"method": le_target.inverse_transform([i])[0],
                     "probability": round(float(proba[i]), 4)} for i in top3_idx]

    y_arr = np.array([pred])
    y_ifrs, _, details = apply_ifrs_constraints_v3(y_arr, X, le_target)
    final_method = le_target.inverse_transform([y_ifrs[0]])[0]
    ifrs_override = final_method != ml_method

    drivers = []
    try:
        sv = get_shap_values(X)
        if sv is not None:
            sv_class = sv[pred][0] if isinstance(sv, list) else sv[0, :, pred]
            importance = pd.Series(np.abs(sv_class), index=FEATURE_NAMES).sort_values(ascending=False)
            for feat, imp in importance.head(5).items():
                drivers.append({"feature": feat, "value": round(float(X[feat].iloc[0]), 4),
                               "shap_impact": round(float(sv_class[FEATURE_NAMES.index(feat)]), 4)})
    except Exception:
        pass

    val_result = None
    if valuation_params is not None:
        pk = set(valuation_params.keys())
        sig = ENGINE_SIGNATURES.get(final_method, {}).get("required", set())
        if sig.issubset(pk):
            try:
                val_result = VALUATION_ENGINES[final_method](**valuation_params)
            except Exception as e:
                val_result = {"method": final_method, "error": str(e)}
        else:
            for cand, spec in ENGINE_SIGNATURES.items():
                if spec["required"] and spec["required"].issubset(pk):
                    try:
                        val_result = VALUATION_ENGINES[cand](**valuation_params)
                        val_result["note_dispatch"] = f"Calculated via {cand} (compatible params)"
                        break
                    except Exception:
                        continue
            if val_result is None:
                label = ENGINE_SIGNATURES.get(final_method, {}).get("label", "?")
                val_result = {"method": final_method,
                              "error": f"Insufficient params. Required: {label}. Got: {pk}"}

    parts = [f"{final_method} is recommended with {confidence:.0%} confidence."]
    if confidence < 0.5:
        parts.append("Warning: low confidence, manual verification recommended.")
    if drivers:
        parts.append(f"Top factors: {', '.join([d['feature'].replace('_', ' ') for d in drivers[:3]])}.")
    if ifrs_override:
        parts.append(f"IFRS 13 note: ML prediction ({ml_method}) corrected to {final_method}.")

    return {
        "recommendation": {"method": final_method, "confidence": round(confidence, 4),
                           "ml_prediction": ml_method, "ifrs_override": ifrs_override,
                           "ifrs_rule": details[0]["rule"] if details else None},
        "alternatives": alternatives,
        "explanation": {"top_drivers": drivers, "natural_language": " ".join(parts)},
        "valuation": val_result,
    }
