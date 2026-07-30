import streamlit as st
import pandas as pd
import numpy as np
import json
from pathlib import Path

st.set_page_config(page_title="Model Insights", page_icon="chart_with_upwards_trend", layout="wide")
from utils.theme import inject_theme_css
inject_theme_css()
st.title("Model Insights")

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
FIG_DIR = Path(__file__).resolve().parent.parent / "reports" / "figures"

meta = {}
meta_path = MODELS_DIR / "model_metadata.json"
if meta_path.exists():
    with open(meta_path) as f:
        meta = json.load(f)

cal_meta = None
cal_path = MODELS_DIR / "v3_calibrated_metadata.json"
if cal_path.exists():
    with open(cal_path) as f:
        cal_meta = json.load(f)
else:
    cal_path2 = MODELS_DIR / "metadata_calibrated_v3_calibrated.json"
    if cal_path2.exists():
        with open(cal_path2) as f:
            cal_meta = json.load(f)

tab1, tab2, tab3, tab4 = st.tabs([
    "Model Performance & Calibration",
    "SHAP Global",
    "Confusion Matrices",
    "Data Summary",
])

with tab1:
    model_source = st.radio(
        "Model source",
        ["Flat (standard)", "Hierarchical", "Calibrated"],
        horizontal=True,
        help="Flat: single XGBoost classifier. Hierarchical: two-stage (class → method). Calibrated: Platt/Isotonic recalibrated probabilities."
    )

    st.markdown("### Model Performance")

    if model_source in ("Flat (standard)", "Hierarchical"):
        try:
            comp = pd.read_csv(FIG_DIR.parent / "model_comparison.csv", index_col=0)
            st.dataframe(comp.style.highlight_max(axis=0), use_container_width=True)
        except Exception as e:
            st.warning(f"Could not load model comparison: {e}")

    if model_source == "Flat (standard)":
        st.markdown(f"**Best Model:** {meta.get('model', 'XGBoost')}")
        st.json({
            "model": meta.get("model"),
            "best_params": meta.get("best_params", {}),
            "f1_weighted_before_ifrs": meta.get("metrics", {}).get("before_ifrs", {}).get("f1_weighted"),
            "f1_weighted_after_ifrs": meta.get("metrics", {}).get("after_ifrs", {}).get("f1_weighted"),
            "ifrs_overrides": meta.get("ifrs_overrides", 0),
            "domain_violations": meta.get("domain_violations_after_ifrs", 0),
            "training_samples": meta.get("training_samples"),
        })

    elif model_source == "Hierarchical":
        st.info("Hierarchical model: Stage 1 predicts asset class, Stage 2 predicts valuation method within that class.")
        hier = meta.get("hierarchical", {})
        st.json({
            "stage1_accuracy": hier.get("stage1_accuracy"),
            "stage1_model": hier.get("stage1_model", "XGBoost"),
            "stage2_weighted_f1": hier.get("stage2_weighted_f1"),
            "overall_accuracy": hier.get("overall_accuracy"),
        } if hier else {"status": "Hierarchical metadata not available in model_metadata.json"})

    elif model_source == "Calibrated":
        st.markdown("**Calibrated Model** — probabilities adjusted via Platt scaling or isotonic regression for better confidence reliability.")
        if cal_meta:
            st.json({
                "calibration_method": cal_meta.get("calibration_method", "Platt"),
                "base_model": cal_meta.get("base_model", "XGBoost"),
                "ece_before": cal_meta.get("comparison", {}).get("flat", {}).get("ece"),
                "ece_after": cal_meta.get("comparison", {}).get("calibrated", {}).get("ece"),
                "mce_before": cal_meta.get("comparison", {}).get("flat", {}).get("mce"),
                "mce_after": cal_meta.get("comparison", {}).get("calibrated", {}).get("mce"),
            })
        else:
            st.warning("Calibrated metadata not found. Run Notebook 07 first to generate calibration artifacts.")

    st.markdown("---")
    st.subheader("Calibration Quality (Reliability)")
    if cal_meta:
        comp = cal_meta.get("comparison", {})
        c1, c2, c3 = st.columns(3)
        flat = comp.get("flat", {})
        hier = comp.get("hierarchical", {})
        cal = comp.get("calibrated", {})
        c1.metric("Flat ECE", f"{flat.get('ece', 0):.3f}")
        c2.metric("Hierarchical ECE", f"{hier.get('ece', 0):.3f}")
        c3.metric("Calibrated ECE", f"{cal.get('ece', 0):.3f}")

        if model_source == "Calibrated":
            plots = {
                "reliability_original.png": "Flat Model Reliability",
                "reliability_comparison.png": "Reliability Comparison",
                "diagnostic_confiance_baseline.png": "Confidence Diagnostic",
            }
            for fn, caption in plots.items():
                p = FIG_DIR / fn
                if p.exists():
                    st.image(str(p), use_container_width=True, caption=caption)
    else:
        st.info("Calibration metadata not loaded. Run notebook 07 to generate it.")

    other_images = ["top_features_by_method.png", "ifrs_level_methods.png"]
    for fn in other_images:
        p = FIG_DIR / fn
        if p.exists():
            st.image(str(p), use_container_width=True, caption=fn.replace("_", " ").replace(".png", "").title())

with tab2:
    st.markdown("### Global SHAP Feature Importance")
    p = FIG_DIR / "shap_global_importance.png"
    if p.exists():
        st.image(str(p), use_container_width=True, caption="Global SHAP Feature Importance")

    st.markdown("#### Per-Class SHAP")
    col1, col2 = st.columns(2)
    shap_images = ["shap_beeswarm_black_scholes.png", "shap_beeswarm_credit_model.png",
                   "shap_beeswarm_dcf.png", "shap_top_features_by_method.png"]
    for i, img in enumerate(shap_images):
        path = FIG_DIR / img
        if path.exists():
            with (col1 if i % 2 == 0 else col2):
                st.image(str(path), use_container_width=True,
                         caption=img.replace("shap_beeswarm_", "").replace("_", " ").replace(".png", "").title())

    wf = FIG_DIR / "shap_waterfall_example.png"
    if wf.exists():
        st.image(str(wf), use_container_width=True, caption="Single Prediction Waterfall (SHAP)")

with tab3:
    st.markdown("### Confusion Matrices")
    col1, col2 = st.columns(2)
    matrices = ["confusion_matrix_xgboost.png", "confusion_matrix_xgboost_tuned.png",
                "confusion_matrix_random_forest.png", "confusion_matrix_catboost.png"]
    for i, img in enumerate(matrices):
        path = FIG_DIR / img
        if path.exists():
            with (col1 if i % 2 == 0 else col2):
                st.image(str(path), use_container_width=True,
                         caption=img.replace("confusion_matrix_", "").replace(".png", "").replace("_", " ").title())

    st.markdown("#### F1 Score per Class")
    f1_images = ["f1_per_class_xgboost.png", "f1_per_class_xgboost_tuned.png",
                 "f1_per_class_random_forest.png", "f1_per_class_catboost.png"]
    for i, img in enumerate(f1_images):
        path = FIG_DIR / img
        if path.exists():
            with (col1 if i % 2 == 0 else col2):
                st.image(str(path), use_container_width=True,
                         caption=img.replace("f1_per_class_", "").replace(".png", "").replace("_", " ").title())

with tab4:
    st.markdown("### Training Data Summary")
    try:
        eda = pd.read_csv(FIG_DIR.parent / "eda_summary.csv")
        st.dataframe(eda, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not load EDA summary: {e}")

    st.markdown("#### Dataset Distribution by Method")
    dist = pd.DataFrame({
        "Method": ["DCF", "Black-Scholes", "Cost-of-Carry", "DDM", "Binomial Tree",
                   "Mark-to-Market", "Forward Pricing", "Monte Carlo", "Relative", "Credit Model"],
        "Samples": [1056, 500, 400, 400, 400, 300, 300, 300, 254, 240],
    }).set_index("Method")
    st.bar_chart(dist)

    st.markdown("#### Feature Set (28 features)")
    try:
        from valusense.config import FEATURE_NAMES
        st.markdown(f"**{len(FEATURE_NAMES)} features**")
        cols = st.columns(3)
        for i, feat in enumerate(FEATURE_NAMES):
            with cols[i % 3]:
                st.code(feat)
    except Exception as e:
        st.warning(f"Could not load feature names: {e}")
