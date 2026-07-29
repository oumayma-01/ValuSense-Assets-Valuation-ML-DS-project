import streamlit as st
from valusense.core import valuate_asset, encode_asset
from valusense.engines import ENGINE_SIGNATURES, VALUATION_ENGINES
from components.asset_form import render_asset_form, render_valuation_params
from components.results_card import render_recommendation, render_valuation
from utils.history import init_history, add_to_history, get_history_df
from utils.export import result_to_json, results_to_csv

st.set_page_config(page_title="Recommend Method", page_icon="chart_with_upwards_trend", layout="wide")
st.title("Valuation Method Recommendation")

init_history()

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

            result = valuate_asset(feature_vec, None)
            result["_asset_class"] = features["asset_class"]
            st.session_state.prediction_result = result
            st.session_state.predicted_method = result["recommendation"]["method"]
            st.session_state.feature_vec = feature_vec
            st.session_state.asset_name = f"{features['asset_class']} ({features['asset_subclass']})"
            st.rerun()

    if st.session_state.prediction_result is not None:
        result = st.session_state.prediction_result
        method = st.session_state.predicted_method

        st.markdown("---")
        render_recommendation(result)

        if result.get("valuation") and "error" not in result.get("valuation", {}):
            st.markdown("### Valuation Result")
            render_valuation(result.get("valuation"))
        else:
            st.markdown("### Valuation Calculation")
            sig_label = ENGINE_SIGNATURES.get(method, {}).get("label", "?")
            st.info(f"Provide parameters for **{method}** to calculate the fair value.")
            with st.expander(f"Enter {method} parameters", expanded=True):
                val_params = render_valuation_params(method)

            if st.button("Calculate Valuation", use_container_width=True):
                fn = VALUATION_ENGINES.get(method)
                if fn:
                    val_result = fn(**val_params)
                    result["valuation"] = val_result
                    add_to_history(st.session_state.asset_name, result)
                    st.rerun()

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
        csv_data = results_to_csv(
            [r for r in st.session_state.valuation_history]
        )
        st.download_button(
            "Download CSV",
            data=csv_data,
            file_name="valusense_history.csv",
            mime="text/csv",
            use_container_width=True,
        )
