import streamlit as st


def render_recommendation(result):
    rec = result["recommendation"]
    method = rec["method"]
    confidence = rec["confidence"]
    ml_pred = rec["ml_prediction"]
    ifrs_override = rec["ifrs_override"]
    ifrs_rule = rec.get("ifrs_rule")

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("### Recommendation")
        st.markdown(f"## {method}")

        color = "green" if confidence >= 0.8 else ("orange" if confidence >= 0.6 else "red")
        st.markdown(f"**Confidence:** <span style='color:{color};font-size:1.3em'>{confidence:.1%}</span>",
                    unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(f"**ML Prediction:** {ml_pred}")
        if ifrs_override:
            st.warning(f"IFRS 13 override applied: {ifrs_rule}")
        else:
            st.success("No IFRS 13 override needed")

    with col2:
        st.markdown("### Alternatives")
        for alt in result.get("alternatives", []):
            prob = alt["probability"]
            bar_width = int(prob * 100)
            st.markdown(f"**{alt['method']}**")
            st.progress(prob, text=f"{prob:.1%}")

    if result.get("explanation", {}).get("natural_language"):
        st.markdown("### Explanation")
        st.info(result["explanation"]["natural_language"])

    drivers = result.get("explanation", {}).get("top_drivers", [])
    if drivers:
        st.markdown("### Top Drivers (SHAP)")
        for d in drivers:
            impact = d["shap_impact"]
            direction = "▲" if impact > 0 else "▼"
            st.markdown(f"- {d['feature']}: `{d['value']}` → SHAP impact **{impact:.4f}** {direction}")


def render_valuation(val_result):
    if val_result is None:
        st.info("No valuation parameters provided. Recommend only.")
        return

    st.markdown("### Valuation Result")

    if "error" in val_result:
        st.error(val_result["error"])
        return

    if "note_dispatch" in val_result:
        st.caption(val_result["note_dispatch"])

    price_keys = {"price": "Price", "fair_value": "Fair Value", "forward_price": "Forward Price",
                  "forward_rate": "Forward Rate", "fair_value_per_share": "Fair Value per Share"}

    for key, label in price_keys.items():
        if key in val_result and val_result[key] is not None:
            st.metric(label, f"${val_result[key]:,.4f}")

    if "greeks" in val_result:
        st.markdown("#### Greeks")
        g = val_result["greeks"]
        cols = st.columns(5)
        for i, (k, v) in enumerate(g.items()):
            cols[i].metric(k.capitalize(), f"{v:.4f}")

    if "std_error" in val_result:
        st.caption(f"Standard Error: {val_result['std_error']:.4f}")
        if "confidence_95" in val_result:
            ci = val_result["confidence_95"]
            st.caption(f"95% CI: [{ci[0]:.4f}, {ci[1]:.4f}]")

    if "fair_value" in val_result and "pv_cash_flows" in val_result:
        st.caption(f"PV of Cash Flows: ${val_result['pv_cash_flows']:,.2f}")
        st.caption(f"PV of Terminal Value: ${val_result['terminal_value']:,.2f} ({val_result['terminal_pct']:.1f}%)")

    if "expected_loss" in val_result:
        st.caption(f"Expected Loss: ${val_result['expected_loss']:,.2f}")
        st.caption(f"CVA: ${val_result['credit_value_adjustment']:,.2f}")

    if "implied_dividend_yield" in val_result:
        st.caption(f"Implied Dividend Yield: {val_result['implied_dividend_yield']:.2f}%")
