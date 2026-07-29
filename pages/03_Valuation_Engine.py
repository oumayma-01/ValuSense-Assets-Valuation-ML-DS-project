import streamlit as st
from valusense.engines import VALUATION_ENGINES, ENGINE_SIGNATURES
from valusense.config import TARGET_CLASSES

st.set_page_config(page_title="Valuation Engine", page_icon="chart_with_upwards_trend", layout="wide")
st.title("Valuation Engine Calculator")

st.markdown("Direct access to any of the 10 valuation engines for standalone calculation.")

method = st.selectbox("Select Valuation Method", options=TARGET_CLASSES)

st.markdown(f"**Required parameters:** {ENGINE_SIGNATURES[method]['label']}")

params = {}
if method == "Black-Scholes":
    c1, c2 = st.columns(2)
    with c1:
        params["S"] = st.number_input("Spot (S)", value=100.0, key="bs_S")
        params["K"] = st.number_input("Strike (K)", value=100.0, key="bs_K")
        params["T"] = st.number_input("Time (T)", value=1.0, key="bs_T")
    with c2:
        params["r"] = st.number_input("Rate (r)", value=0.05, key="bs_r")
        params["sigma"] = st.number_input("Vol (sigma)", value=0.25, key="bs_sigma")
        params["option_type"] = st.selectbox("Type", ["call", "put"], key="bs_type")

elif method == "DCF":
    c1, c2 = st.columns(2)
    with c1:
        n = st.number_input("Number of CFs", min_value=1, value=5, key="dcf_n")
        dr = st.number_input("Discount Rate", value=0.10, key="dcf_dr")
    with c2:
        tg = st.number_input("Terminal Growth", value=0.02, key="dcf_tg")
        bc = st.number_input("Base CF ($)", value=100.0, key="dcf_bc")
    params["cash_flows"] = [bc * (1 + 0.05)**t for t in range(n)]
    params["discount_rate"] = dr
    params["terminal_growth"] = tg

elif method == "DDM":
    c1, c2, c3 = st.columns(3)
    params["dividend_current"] = st.number_input("Current Dividend ($)", value=2.0, key="ddm_d0")
    params["growth_rate"] = st.number_input("Growth Rate", value=0.03, key="ddm_g")
    params["required_return"] = st.number_input("Required Return", value=0.08, key="ddm_r")

elif method == "Monte-Carlo":
    c1, c2 = st.columns(2)
    with c1:
        params["S"] = st.number_input("Spot (S)", value=100.0, key="mc_S")
        params["K"] = st.number_input("Strike (K)", value=100.0, key="mc_K")
        params["T"] = st.number_input("Time (T)", value=1.0, key="mc_T")
    with c2:
        params["r"] = st.number_input("Rate (r)", value=0.05, key="mc_r")
        params["sigma"] = st.number_input("Vol (sigma)", value=0.30, key="mc_sigma")
        params["exotic_type"] = st.selectbox("Exotic", [None, "asian"], key="mc_exotic")
    params["seed"] = 42

elif method == "Binomial-Tree":
    c1, c2 = st.columns(2)
    with c1:
        params["S"] = st.number_input("Spot (S)", value=100.0, key="bt_S")
        params["K"] = st.number_input("Strike (K)", value=100.0, key="bt_K")
        params["T"] = st.number_input("Time (T)", value=1.0, key="bt_T")
    with c2:
        params["r"] = st.number_input("Rate (r)", value=0.05, key="bt_r")
        params["sigma"] = st.number_input("Vol (sigma)", value=0.30, key="bt_sigma")
        params["option_type"] = st.selectbox("Type", ["call", "put"], key="bt_type")

elif method == "Cost-of-Carry":
    c1, c2 = st.columns(2)
    params["S"] = st.number_input("Spot", value=1950.0, key="coc_S")
    params["r"] = st.number_input("Rate", value=0.04, key="coc_r")
    params["T"] = st.number_input("Time", value=0.5, key="coc_T")
    params["storage_cost"] = st.number_input("Storage Cost", value=0.01, key="coc_storage")
    params["convenience_yield"] = st.number_input("Conv. Yield", value=0.005, key="coc_conv")

elif method == "Forward-Pricing":
    c1, c2 = st.columns(2)
    params["S"] = st.number_input("Spot Rate", value=1.085, key="fp_S")
    params["r_domestic"] = st.number_input("Domestic Rate", value=0.045, key="fp_rd")
    params["r_foreign"] = st.number_input("Foreign Rate", value=0.035, key="fp_rf")
    params["T"] = st.number_input("Time", value=0.25, key="fp_T")

elif method == "Mark-to-Market":
    c1, c2 = st.columns(2)
    params["market_price"] = st.number_input("Market Price ($)", value=100.0, key="mtm_mp")
    params["bid"] = st.number_input("Bid ($)", value=99.9, key="mtm_bid")
    params["ask"] = st.number_input("Ask ($)", value=100.1, key="mtm_ask")
    params["volume"] = st.number_input("Volume", value=1000000, key="mtm_vol")

elif method == "Relative":
    c1, c2 = st.columns(2)
    params["earnings"] = st.number_input("Earnings ($)", value=5e9, key="rel_e")
    params["ebitda"] = st.number_input("EBITDA ($)", value=8e9, key="rel_eb")
    params["peer_pe"] = st.number_input("Peer P/E", value=22.0, key="rel_pe")
    params["peer_ev_ebitda"] = st.number_input("Peer EV/EBITDA", value=14.0, key="rel_ev")
    params["shares_outstanding"] = st.number_input("Shares", value=1e9, key="rel_sh")

elif method == "Credit-Model":
    c1, c2 = st.columns(2)
    params["face_value"] = st.number_input("Face Value", value=1000.0, key="cm_fv")
    params["coupon_rate"] = st.number_input("Coupon Rate", value=0.05, key="cm_cr")
    params["maturity_years"] = st.number_input("Maturity", value=5.0, key="cm_mat")
    params["credit_spread"] = st.number_input("Credit Spread", value=0.02, key="cm_cs")
    params["risk_free_rate"] = st.number_input("Risk-Free Rate", value=0.04, key="cm_rfr")

if st.button("Calculate", type="primary"):
    try:
        fn = VALUATION_ENGINES[method]
        result = fn(**params)
        st.markdown("### Result")
        st.json(result)
    except Exception as e:
        st.error(f"Calculation error: {e}")
