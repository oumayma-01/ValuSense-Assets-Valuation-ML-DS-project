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

# ---- Calibration & Hierarchical artifacts (optional, v3+) ----
CALIBRATION_META = None
CALIB_TEMPERATURE = 1.0
CALIB_METHOD = None
STAGE1_CLASSIFIER = None
STAGE2_MODELS = None
STAGE2_ENCODERS = None
NEAREST_NEIGHBOR = None
FEATURE_COLS_STAGE1 = [c for c in FEATURE_NAMES if c not in ("asset_class_encoded", "asset_subclass_encoded")]

def load_calibration_artifacts():
    global CALIBRATION_META, CALIB_TEMPERATURE, CALIB_METHOD
    global STAGE1_CLASSIFIER, STAGE2_MODELS, STAGE2_ENCODERS, NEAREST_NEIGHBOR
    try:
        meta_path = MODELS_DIR / "metadata_calibrated_v3_calibrated.json"
        if not meta_path.exists():
            return False
        with open(meta_path) as f:
            CALIBRATION_META = json.load(f)
        CALIB_TEMPERATURE = CALIBRATION_META.get("calibration", {}).get("temperature", 1.0)
        CALIB_METHOD = CALIBRATION_META.get("calibration", {}).get("calibration_method", None)

        if CALIBRATION_META.get("winner") == "hierarchical":
            s1 = MODELS_DIR / "stage1_asset_classifier_v3_calibrated.pkl"
            s2 = MODELS_DIR / "stage2_method_classifiers_v3_calibrated.pkl"
            s2e = MODELS_DIR / "stage2_label_encoders_v3_calibrated.pkl"
            if s1.exists() and s2.exists() and s2e.exists():
                STAGE1_CLASSIFIER = joblib.load(s1)
                STAGE2_MODELS = joblib.load(s2)
                STAGE2_ENCODERS = joblib.load(s2e)

        nn_path = MODELS_DIR / "nearest_neighbor_v3_calibrated.pkl"
        if nn_path.exists():
            NEAREST_NEIGHBOR = joblib.load(nn_path)

        return True
    except Exception:
        return False

CALIBRATION_ENABLED = load_calibration_artifacts()
