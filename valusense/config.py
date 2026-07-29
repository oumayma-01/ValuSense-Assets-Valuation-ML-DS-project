import json
import joblib
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"

best_model = joblib.load(MODELS_DIR / "xgboost_valuation_recommender.pkl")
le_target = joblib.load(MODELS_DIR / "label_encoder_target.pkl")
label_encoders = joblib.load(MODELS_DIR / "feature_label_encoders.pkl")

AC_LOOKUP = {name: i for i, name in enumerate(label_encoders["asset_class"].classes_)}
SC_LOOKUP = {name: i for i, name in enumerate(label_encoders["asset_subclass"].classes_)}
AC_REVERSE = {i: name for name, i in AC_LOOKUP.items()}

FEATURE_NAMES = list(best_model.get_booster().feature_names)
TARGET_CLASSES = list(le_target.classes_)
N_FEATURES = len(FEATURE_NAMES)
N_CLASSES = len(TARGET_CLASSES)
ASSET_CLASSES = AC_LOOKUP

_SHAP_EXPLAINER = None
_SHAP_FAILED = False

def get_shap_explainer():
    global _SHAP_EXPLAINER, _SHAP_FAILED
    if _SHAP_FAILED:
        return None
    if _SHAP_EXPLAINER is None:
        try:
            import shap
            _SHAP_EXPLAINER = shap.TreeExplainer(best_model)
        except Exception:
            _SHAP_FAILED = True
            return None
    return _SHAP_EXPLAINER


def get_shap_values(X):
    explainer = get_shap_explainer()
    if explainer is None:
        return None
    try:
        return explainer.shap_values(X)
    except Exception:
        return None

with open(MODELS_DIR / "calibrated_defaults.json") as f:
    CALIBRATED_DEFAULTS = json.load(f)

with open(MODELS_DIR / "encoder_lookups.json") as f:
    lookups = json.load(f)

SC_LOOKUP_FULL = lookups["sc_lookup"]
AC_LOOKUP_FULL = lookups["ac_lookup"]
