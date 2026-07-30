import streamlit as st
import pandas as pd
import numpy as np
from valusense.core import valuate_asset_v2, encode_asset
from valusense.engines import ENGINE_SIGNATURES, VALUATION_ENGINES
from valusense.config import TARGET_CLASSES, AC_REVERSE, FEATURE_NAMES
from components.asset_form import render_asset_form, render_valuation_params
from utils.history import add_to_history, get_history_df
from utils.export import result_to_json, results_to_csv

st.set_page_config(page_title="Recommend", page_icon="chart_with_upwards_trend", layout="wide")
from utils.theme import inject_theme_css
inject_theme_css()
st.title("Valuation Method Recommendation")

if "prediction_result" not in st.session_state:
    st.session_state.prediction_result = None
if "predicted_method" not in st.session_state:
    st.session_state.predicted_method = None

tab1, tab2, tab3 = st.tabs(["New Recommendation", "History", "Export"])

with tab1:
    features = render_asset_form()
    col_btn, col_status = st.columns([1, 2])
    with col_btn:
        recommend_clicked = st.button("Recommend Method", type="primary", use_container_width=True)

    if recommend_clicked:
        with st.spinner("Running model prediction + SHAP explanation..."):
            ac_enc, sc_enc = encode_asset(features["asset_class"], features["asset_subclass"])
            feature_vec = {k: v for k, v in features.items()
                          if k not in ("asset_class", "asset_subclass")}
            feature_vec["asset_class_encoded"] = ac_enc
            feature_vec["asset_subclass_encoded"] = sc_enc
            result = valuate_asset_v2(feature_vec, None)
            result["_asset_class"] = features["asset_class"]
            st.session_state.prediction_result = result
            st.session_state.predicted_method = result["recommendation"]["method"]
            st.session_state.last_features = feature_vec
            st.session_state.last_result = result
            st.session_state.last_asset_class = features["asset_class"]
            st.session_state.last_asset_subclass = features["asset_subclass"]
            st.session_state.pending_asset_features = feature_vec
            st.rerun()

    if st.session_state.prediction_result is not None:
        result = st.session_state.prediction_result
        rec = result["recommendation"]
        method = rec["method"]
        confidence = rec["confidence"]
        ml_pred = rec["ml_prediction"]
        ifrs_override = rec["ifrs_override"]
        ifrs_rule = rec.get("ifrs_rule")
        is_low = rec.get("is_low_confidence", False)

        st.markdown("---")
        col1, col2 = st.columns([1, 1])

        with col1:
            badge_color = "green" if confidence >= 0.8 else ("orange" if confidence >= 0.6 else "red")
            badge_label = "High Confidence" if confidence >= 0.8 else ("Medium Confidence" if confidence >= 0.6 else "Low Confidence")
            st.markdown(f"### {method}")
            st.markdown(
                f"<div style='background:{badge_color};color:white;padding:0.5rem 1rem;"
                f"border-radius:0.5rem;text-align:center;font-size:1.5rem;font-weight:bold'>"
                f"{confidence:.1%} — {badge_label}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(f"**ML Prediction:** {ml_pred}")

        with col2:
            st.markdown("### Alternatives")
            for alt in result.get("alternatives", []):
                prob = alt["probability"]
                st.markdown(f"**{alt['method']}**")
                st.progress(prob, text=f"{prob:.1%}")

        if ifrs_override:
            st.error(f"Regulatory Override Applied: ML predicted **{ml_pred}**, but IFRS 13 rules "
                     f"require **{method}**. Rule: `{ifrs_rule}`")
        else:
            st.success("No IFRS 13 override needed — ML prediction is regulatory-compliant.")

        if is_low:
            st.warning("⚠️ **Uncertain prediction** — see alternatives above.")
            nn = result.get("nearest_neighbor")
            if nn:
                with st.expander("Closest Known Example (Nearest Neighbor)", expanded=True):
                    st.markdown(f"**Label:** {nn['label']}  |  **Distance:** {nn['distance']:.4f}")

        if result.get("explanation", {}).get("natural_language"):
            st.markdown("### Explanation")
            st.info(result["explanation"]["natural_language"])

        drivers = result.get("explanation", {}).get("top_drivers", [])
        if drivers:
            with st.expander("SHAP Waterfall — Top Drivers", expanded=False):
                for d in drivers:
                    direction = "▲" if d["shap_impact"] > 0 else "▼"
                    st.markdown(f"- {d['feature']}: `{d['value']}` → SHAP impact **{d['shap_impact']:.4f}** {direction}")

        st.markdown("---")
        st.session_state.pending_method = method
        st.session_state.pending_asset_features = st.session_state.last_features
        if st.button("Send to Valuation Engine →", type="secondary", use_container_width=True):
            add_to_history(st.session_state.last_asset_class or "Asset", st.session_state.last_result)
            st.switch_page("pages/02_Valuation_Engine.py")

        with st.expander("Raw JSON Output"):
            st.code(result_to_json(result), language="json")

with tab2:
    df = get_history_df()
    if df.empty:
        st.info("No recommendations yet.")
    else:
        st.dataframe(df, use_container_width=True)
        if st.button("Clear History"):
            st.session_state.valuation_history = []
            st.session_state.prediction_result = None
            st.rerun()

with tab3:
    df = get_history_df()
    if df.empty:
        st.info("No data to export.")
    else:
        csv_data = results_to_csv([r for r in st.session_state.valuation_history])
        st.download_button(
            "Download CSV", data=csv_data, file_name="valusense_history.csv",
            mime="text/csv", use_container_width=True,
        )
