import streamlit as st
import pandas as pd
from datetime import datetime


def init_history():
    if "valuation_history" not in st.session_state:
        st.session_state.valuation_history = []


def add_to_history(asset_name, result):
    init_history()
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_name": asset_name,
        "asset_class": result.get("_asset_class", ""),
        "recommended_method": result["recommendation"]["method"],
        "confidence": result["recommendation"]["confidence"],
        "ml_prediction": result["recommendation"]["ml_prediction"],
        "ifrs_override": result["recommendation"]["ifrs_override"],
        "valuation_price": _extract_price(result.get("valuation")),
    }
    st.session_state.valuation_history.append(entry)


def _extract_price(val):
    if val is None:
        return None
    for key in ["price", "fair_value", "forward_price", "forward_rate", "fair_value_per_share"]:
        v = val.get(key)
        if v is not None:
            return round(v, 4)
    return None


def get_history_df():
    init_history()
    if not st.session_state.valuation_history:
        return pd.DataFrame()
    return pd.DataFrame(st.session_state.valuation_history)


def clear_history():
    init_history()
    st.session_state.valuation_history = []
