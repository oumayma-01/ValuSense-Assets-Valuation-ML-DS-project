import streamlit as st
import pandas as pd
import numpy as np
from valusense.core import valuate_asset_v2, encode_asset
from valusense.engines import ENGINE_SIGNATURES, VALUATION_ENGINES
from valusense.config import TARGET_CLASSES, AC_REVERSE, FEATURE_NAMES
from components.asset_form import render_asset_form, validate_features
from utils.history import add_to_history, get_history_df
from utils.export import result_to_json, results_to_csv
from utils.theme import (
    inject_theme_css,
    theme_sidebar,
    page_header,
    section_header,
    render_stat_cards,
    badge,
    render_table,
    empty_state,
    hairline,
    is_full_detail,
)

st.set_page_config(page_title="Recommend", page_icon="🎯", layout="wide")

with st.sidebar:
    theme_sidebar()

inject_theme_css()

page_header(
    "Valuation Method Recommendation",
    "Describe an asset and ValuSense will tell you the most defensible way to value it, and why.",
    kicker="Recommendation · IFRS 13 · SHAP",
)

if "prediction_result" not in st.session_state:
    st.session_state.prediction_result = None
if "predicted_method" not in st.session_state:
    st.session_state.predicted_method = None

def _ifrs_rule_explanation(rule, ml_pred, final_method):
    if rule and "->" in rule:
        mapping = {
            "Black-Scholes->Binomial-Tree": (
                "This option allows **early exercise** (e.g. an American option). Black-Scholes assumes you "
                "can only exercise at maturity, so it would misprice it. A Binomial Tree handles early exercise correctly."
            ),
            "->Mark-to-Market": (
                f"IFRS 13 (Level 1) says: if an asset trades with an observable, liquid market price, you **must** "
                f"use that market price. The model suggested {ml_pred}, but the regulations require the observed price."
            ),
            "DDM->Relative": (
                "This equity pays **no dividend**, so a dividend-discount model has nothing to discount. "
                "For a high-growth stock, IFRS guidance points to relative valuation against peers."
            ),
            "Mark-to-Market->Relative": (
                "This is a high-growth equity with no dividend. The market-price route doesn't fit a "
                "growth valuation, so the model's Mark-to-Market pick was corrected to a peer-multiples approach."
            ),
            "DCF->Credit-Model": (
                "This bond carries **credit risk**, so a plain discounted-cash-flow price would ignore the "
                "probability of default. A credit model explicitly prices that risk."
            ),
        }
        for key, text in mapping.items():
            if key in rule:
                return text
        return f"IFRS 13 overrode {ml_pred} → {final_method}: the regulatory rule `{rule}` was applied."
    return f"The regulatory rule `{rule or 'n/a'}` was applied to guarantee IFRS 13 compliance."


tab1, tab2, tab3 = st.tabs(["New Recommendation", "History", "Export"])

with tab1:
    features = render_asset_form()

    input_issues = validate_features(features)
    if input_issues:
        st.error("**Please review the following inputs before running the recommendation:**")
        for issue in input_issues:
            st.markdown(f"- {issue}")

    col_btn, col_status = st.columns([1, 2])
    with col_btn:
        recommend_clicked = st.button("Recommend Method", type="primary", width="stretch")

    if recommend_clicked and not input_issues:
        with st.spinner("Running model prediction + SHAP explanation..."):
            try:
                ac_enc, sc_enc = encode_asset(features["asset_class"], features["asset_subclass"])
                feature_vec = {k: v for k, v in features.items()
                              if k not in ("asset_class", "asset_subclass")}
                feature_vec["asset_class_encoded"] = ac_enc
                feature_vec["asset_subclass_encoded"] = sc_enc
                result = valuate_asset_v2(feature_vec, None)
            except Exception as e:
                st.error("**Model unavailable.** The recommendation engine could not run. "
                         f"Check that the model artifacts are present in `models/` and the "
                         f"dependencies are installed. ({e})")
                st.stop()
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

        hairline()
        conf_tone = "success" if confidence >= 0.8 else "warning"
        conf_label = ("High Confidence" if confidence >= 0.8
                      else ("Medium Confidence" if confidence >= 0.6 else "Low Confidence"))
        render_stat_cards([
            {"label": "Recommended method", "value": method, "tone": "accent"},
            {"label": "Confidence", "value": f"{confidence:.1%}", "tone": conf_tone,
             "caption": conf_label},
        ], columns=2)
        st.caption(
            "Confidence = how sure the model is. Above 80% → trust it. "
            "60–80% → check the alternatives. Below 60% → we show the closest similar "
            "asset from the training set to sanity-check the call."
        )

        c_left, c_right = st.columns([1, 1])
        with c_left:
            st.markdown(badge(f"ML prediction: {ml_pred}", tone="neutral"), unsafe_allow_html=True)
        with c_right:
            st.markdown(
                badge("IFRS 13 ✓ compliant" if not ifrs_override else "IFRS 13 override applied",
                      tone="success" if not ifrs_override else "warning"),
                unsafe_allow_html=True,
            )

        c1, c2 = st.columns([1, 1])
        with c1:
            if ifrs_override:
                st.error(f"**Regulatory override applied:** the model chose **{ml_pred}**, but IFRS 13 rules "
                         f"require **{method}**. Rule: `{ifrs_rule}`")
                with st.expander("Why was this overridden? (plain language)"):
                    st.markdown(_ifrs_rule_explanation(ifrs_rule, ml_pred, method))
            else:
                st.success("No IFRS 13 override needed. The model's pick is regulatory-compliant.")
                with st.expander("What does 'no override' mean?"):
                    st.markdown(
                        "The method the model recommends already satisfies IFRS 13 fair-value rules. "
                        "No correction was necessary. The full rule set is on the **About** page."
                    )

            if is_low:
                st.warning("**Uncertain prediction.** Treat this as a flag, not a verdict. "
                           "See the alternatives above and the closest known example below.")
                nn = result.get("nearest_neighbor")
                if nn:
                    with st.expander("Closest known example (nearest neighbor)", expanded=True):
                        st.markdown(f"**Label:** {nn['label']}  |  **Distance:** `{nn['distance']:.4f}`")
                        st.caption(
                            "When confidence is low, we find the most similar asset in the training set "
                            "and show what method it was labelled with. A quick reality check on the prediction."
                        )

        with c2:
            section_header("Alternatives")
            for alt in result.get("alternatives", []):
                prob = alt["probability"]
                st.markdown(f"**{alt['method']}**")
                st.progress(prob, text=f"{prob:.1%}")

        if result.get("explanation", {}).get("natural_language"):
            section_header("Explanation")
            st.info(result["explanation"]["natural_language"])

        drivers = result.get("explanation", {}).get("top_drivers", [])
        if drivers:
            with st.expander(
                "SHAP Waterfall: Top Drivers",
                expanded=is_full_detail(),
            ):
                st.markdown(
                    "SHAP shows *why* the model picked this method: each feature below either pushed the "
                    "prediction up (▲) or down (▼) toward this method. This is how ValuSense stays auditable for IFRS 13."
                )
                driver_df = pd.DataFrame([
                    {"Feature": d["feature"], "Value": d["value"], "SHAP impact": d["shap_impact"]}
                    for d in drivers
                ])
                render_table(driver_df)

        hairline()
        st.session_state.pending_method = method
        st.session_state.pending_asset_features = st.session_state.last_features

        col_send, col_pdf = st.columns(2)
        with col_send:
            if st.button("Send to Valuation Engine →", type="secondary", use_container_width=True):
                add_to_history(st.session_state.last_asset_class or "Asset", st.session_state.last_result)
                st.switch_page("pages/02_Valuation_Engine.py")
        with col_pdf:
            if st.button("Generate Report (PDF)", type="primary", use_container_width=True):
                st.info(
                    "PDF report export is coming soon. In the meantime, use the **Export** "
                    "tab to download this session as a CSV."
                )

        with st.expander("Developer details", expanded=False):
            st.caption(
                "Raw model output kept here for debugging and internal auditing. "
                "It is not part of the client-facing result."
            )
            st.code(result_to_json(result), language="json")

with tab2:
    df = get_history_df()
    if df.empty:
        empty_state("No recommendations yet",
                    "Run a recommendation in the first tab. Your past results will appear here.")
    else:
        render_table(df)
        if st.button("Clear History"):
            st.session_state.valuation_history = []
            st.session_state.prediction_result = None
            st.rerun()

with tab3:
    df = get_history_df()
    if df.empty:
        empty_state("No data to export",
                    "Run a recommendation first. Then you can download it as a CSV.")
    else:
        csv_data = results_to_csv([r for r in st.session_state.valuation_history])
        st.download_button(
            "Download CSV", data=csv_data, file_name="valusense_history.csv",
            mime="text/csv", width="stretch",
        )
