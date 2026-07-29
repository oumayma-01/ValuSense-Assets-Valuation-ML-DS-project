import streamlit as st
import pandas as pd
import numpy as np
import joblib
from pathlib import Path

st.set_page_config(page_title="Model Insights", page_icon="chart_with_upwards_trend", layout="wide")
st.title("Model Insights")

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"

tab1, tab2, tab3, tab4 = st.tabs(["Model Comparison", "SHAP Global", "Confusion Matrices", "Data Summary"])

with tab1:
    st.markdown("### Model Performance Comparison")
    try:
        comp = pd.read_csv(MODELS_DIR.parent / "reports" / "model_comparison.csv", index_col=0)
        st.dataframe(comp.style.highlight_max(axis=0), use_container_width=True)

        st.markdown("#### Best Model: XGBoost (tuned)")
        import json
        with open(MODELS_DIR / "model_metadata.json") as f:
            meta = json.load(f)
        st.json({
            "model": meta["model"],
            "best_params": meta.get("best_params", {}),
            "metrics_before_ifrs": meta.get("metrics", {}).get("before_ifrs", {}),
            "metrics_after_ifrs": meta.get("metrics", {}).get("after_ifrs", {}),
            "ifrs_overrides": meta.get("ifrs_overrides", 0),
            "domain_violations": meta.get("domain_violations_after_ifrs", 0),
            "training_samples": meta.get("training_samples", 0),
            "validation_samples": meta.get("validation_samples", 0),
        })
    except Exception as e:
        st.warning(f"Could not load model comparison: {e}")

with tab2:
    st.markdown("### Global SHAP Feature Importance")
    st.image(str(MODELS_DIR.parent / "reports" / "figures" / "shap_global_importance.png"),
             use_container_width=True, caption="Global SHAP Feature Importance")

    st.markdown("#### Per-Class SHAP Analysis")
    col1, col2 = st.columns(2)
    shap_images = [
        "shap_beeswarm_black_scholes.png", "shap_beeswarm_credit_model.png",
        "shap_beeswarm_dcf.png", "shap_top_features_by_method.png",
    ]
    img_dir = MODELS_DIR.parent / "reports" / "figures"
    for i, img in enumerate(shap_images):
        path = img_dir / img
        if path.exists():
            with (col1 if i % 2 == 0 else col2):
                st.image(str(path), use_container_width=True,
                         caption=img.replace("shap_beeswarm_", "").replace("_", " ").replace(".png", "").title())

    single_shap = img_dir / "shap_waterfall_example.png"
    if single_shap.exists():
        st.image(str(single_shap), use_container_width=True, caption="Single Prediction Waterfall")

with tab3:
    st.markdown("### Confusion Matrices")
    col1, col2 = st.columns(2)
    matrices = [
        "confusion_matrix_xgboost.png", "confusion_matrix_xgboost_tuned.png",
        "confusion_matrix_random_forest.png", "confusion_matrix_catboost.png",
    ]
    img_dir = MODELS_DIR.parent / "reports" / "figures"
    for i, img in enumerate(matrices):
        path = img_dir / img
        if path.exists():
            with (col1 if i % 2 == 0 else col2):
                st.image(str(path), use_container_width=True,
                         caption=img.replace("confusion_matrix_", "").replace(".png", "").replace("_", " ").title())

    st.markdown("#### F1 Score per Class")
    f1_images = [
        "f1_per_class_xgboost.png", "f1_per_class_xgboost_tuned.png",
        "f1_per_class_random_forest.png", "f1_per_class_catboost.png",
    ]
    for i, img in enumerate(f1_images):
        path = img_dir / img
        if path.exists():
            with (col1 if i % 2 == 0 else col2):
                st.image(str(path), use_container_width=True,
                         caption=img.replace("f1_per_class_", "").replace(".png", "").replace("_", " ").title())

with tab4:
    st.markdown("### Training Data Summary")
    try:
        eda = pd.read_csv(MODELS_DIR.parent / "reports" / "eda_summary.csv")
        st.dataframe(eda, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not load EDA summary: {e}")

    st.markdown("#### Dataset Distribution by Method")
    dist = {
        "Method": ["DCF", "Black-Scholes", "Cost-of-Carry", "DDM", "Binomial Tree",
                    "Mark-to-Market", "Forward Pricing", "Monte Carlo", "Relative", "Credit Model"],
        "Samples": [1056, 500, 400, 400, 400, 300, 300, 300, 254, 240],
    }
    st.bar_chart(pd.DataFrame(dist).set_index("Method"))

    st.markdown("#### Feature Set (28 features)")
    try:
        from valusense.config import FEATURE_NAMES, TARGET_CLASSES
        st.markdown(f"**{len(FEATURE_NAMES)} features**")
        col1, col2, col3 = st.columns(3)
        for i, feat in enumerate(FEATURE_NAMES):
            with [col1, col2, col3][i % 3]:
                st.code(feat)
    except Exception as e:
        st.warning(f"Could not load feature names: {e}")
