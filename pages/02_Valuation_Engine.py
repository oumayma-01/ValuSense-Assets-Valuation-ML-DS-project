import streamlit as st
from valusense.engines import VALUATION_ENGINES, ENGINE_SIGNATURES
from valusense.config import TARGET_CLASSES
from components.results_card import render_valuation
from utils.theme import (
    inject_theme_css,
    theme_sidebar,
    page_header,
    section_header,
    render_stat_cards,
    hairline,
)

st.set_page_config(page_title="Valuation Engine", page_icon="🧮", layout="wide")

with st.sidebar:
    theme_sidebar()

inject_theme_css()

page_header(
    "Valuation Engine Calculator",
    "Pick a method (it's pre-selected to match your recommendation) and hit "
    "<strong>Calculate</strong>. Defaults are realistic, so you can price an asset in seconds.",
    kicker="Pricing · Numerical engines",
)

METHOD_GUIDANCE = {
    "Black-Scholes": "Best for European options with no early exercise: a plain call or put that can only be exercised at maturity.",
    "Binomial-Tree": "Best for American options that can be exercised early, or for simple options where the tree matches the real exercise flexibility.",
    "Monte-Carlo": "Best for exotic or path-dependent options (for example Asian options) whose payoff depends on the whole price path.",
    "DCF": "Best for bonds or any asset with predictable cash flows: discount the future cash flows back to today.",
    "DDM": "Best for dividend-paying equities. The value comes from the stream of future dividends.",
    "Credit-Model": "Best for corporate bonds or any asset with meaningful credit risk, where default risk is priced explicitly.",
    "Cost-of-Carry": "Best for commodities held or delivered at a future date. The forward price reflects storage cost minus any convenience yield.",
    "Forward-Pricing": "Best for FX forwards, priced from the interest-rate differential between two currencies.",
    "Mark-to-Market": "Best for liquid assets with an observable market price. IFRS 13 Level 1 says use that price directly.",
    "Relative": "Best for growth equities that pay no dividend, valued against comparable peers using the multiples approach.",
}

pending = st.session_state.get("pending_method")
pending_params = st.session_state.get("pending_valuation_params") or {}
pending_idx = TARGET_CLASSES.index(pending) if pending and pending in TARGET_CLASSES else 0
method = st.selectbox("Valuation Method", options=TARGET_CLASSES, index=pending_idx)

last_features = st.session_state.get("last_features")
if not last_features:
    st.caption("No asset analyzed yet. Run a **Recommendation** first and its method will be "
               "pre-selected here. You can still price anything manually below.")
mrk = last_features.get("has_market_price") if last_features else None
if mrk == 1 and method == pending:
    st.info("This asset has a market price. Compare with Mark-to-Market below.")

section_header("Parameters", f"{ENGINE_SIGNATURES[method]['label']}")
st.caption(METHOD_GUIDANCE.get(method, ""))

params = {}
if method == "Black-Scholes":
    c1, c2 = st.columns(2)
    with c1:
        params["S"] = st.number_input("Spot (S, $)", value=pending_params.get("S", 100.0),
                                      help="Current market price of the underlying asset.")
        params["K"] = st.number_input("Strike (K, $)", value=pending_params.get("K", 100.0),
                                      help="The price at which the option can be exercised. Moneyness compares S to K: a call with S above K is in the money.")
        params["T"] = st.number_input("Time to expiry (T, years)", value=pending_params.get("T", 1.0),
                                      help="Years until the option matures.")
    with c2:
        params["r"] = st.number_input("Risk-free rate (r)", value=pending_params.get("r", 0.05),
                                      help="The interest rate you could earn on riskless cash, usually a government yield.")
        params["sigma"] = st.number_input("Volatility (σ, annual)", value=pending_params.get("sigma", 0.25),
                                          help="How much the underlying price is expected to move per year. Higher volatility means a more expensive option.")
        params["option_type"] = st.selectbox("Type", ["call", "put"],
                                            index=0 if pending_params.get("option_type", "call") == "call" else 1)

elif method == "DCF":
    c1, c2 = st.columns(2)
    with c1:
        n = st.number_input("Number of CFs", min_value=1, value=pending_params.get("n_cf", 5))
        dr_val = pending_params.get("discount_rate", 0.10)
        dr = st.number_input("Discount Rate", value=dr_val)
    with c2:
        tg = st.number_input("Terminal Growth", value=pending_params.get("terminal_growth", 0.02))
        bc = st.number_input("Base CF ($/year)", value=pending_params.get("base_cf", 100.0))
    params["cash_flows"] = [bc * (1 + 0.05)**t for t in range(n)]
    params["discount_rate"] = dr
    params["terminal_growth"] = tg

elif method == "DDM":
    c1, c2, c3 = st.columns(3)
    params["dividend_current"] = st.number_input("Current Dividend ($/yr)", value=pending_params.get("dividend_current", 2.0))
    params["growth_rate"] = st.number_input("Growth Rate", value=pending_params.get("growth_rate", 0.03))
    params["required_return"] = st.number_input("Required Return", value=pending_params.get("required_return", 0.08))

elif method == "Monte-Carlo":
    c1, c2 = st.columns(2)
    with c1:
        params["S"] = st.number_input("Spot (S, $)", value=pending_params.get("S", 100.0),
                                      help="Current market price of the underlying asset.")
        params["K"] = st.number_input("Strike (K, $)", value=pending_params.get("K", 100.0),
                                      help="The price at which the option can be exercised. Moneyness compares S to K: a call with S above K is in the money.")
        params["T"] = st.number_input("Time to expiry (T, years)", value=pending_params.get("T", 1.0),
                                      help="Years until the option matures.")
    with c2:
        params["r"] = st.number_input("Risk-free rate (r)", value=pending_params.get("r", 0.05),
                                      help="The interest rate you could earn on riskless cash, usually a government yield.")
        params["sigma"] = st.number_input("Volatility (σ, annual)", value=pending_params.get("sigma", 0.30),
                                          help="How much the underlying price is expected to move per year. Higher volatility means a more expensive option.")
        params["exotic_type"] = st.selectbox("Exotic", [None, "asian"],
                                            index=0 if not pending_params.get("exotic_type") else 1)
    params["seed"] = 42

elif method == "Binomial-Tree":
    c1, c2 = st.columns(2)
    with c1:
        params["S"] = st.number_input("Spot (S, $)", value=pending_params.get("S", 100.0))
        params["K"] = st.number_input("Strike (K, $)", value=pending_params.get("K", 100.0))
        params["T"] = st.number_input("Time to expiry (T, years)", value=pending_params.get("T", 1.0))
    with c2:
        params["r"] = st.number_input("Risk-free rate (r)", value=pending_params.get("r", 0.05))
        params["sigma"] = st.number_input("Volatility (σ, annual)", value=pending_params.get("sigma", 0.30))
        params["option_type"] = st.selectbox("Type", ["call", "put"],
                                            index=0 if pending_params.get("option_type", "call") == "call" else 1)

elif method == "Cost-of-Carry":
    c1, c2 = st.columns(2)
    params["S"] = st.number_input("Spot (S, $)", value=pending_params.get("S", 1950.0),
                                  help="Current spot price of the commodity.")
    params["r"] = st.number_input("Risk-free rate (r)", value=pending_params.get("r", 0.04),
                                  help="The interest rate you could earn on riskless cash, usually a government yield.")
    params["T"] = st.number_input("Time to delivery (T, years)", value=pending_params.get("T", 0.5),
                                  help="Years until the commodity is delivered.")
    params["storage_cost"] = st.number_input("Storage Cost (%/yr)", value=pending_params.get("storage_cost", 0.01),
                                             help="The annual cost of storing the physical commodity. It raises the forward price.")
    params["convenience_yield"] = st.number_input("Convenience Yield (%/yr)", value=pending_params.get("convenience_yield", 0.005),
                                                  help="The benefit of physically holding the commodity rather than the derivative. Think of it as a yield the holder earns; it lowers the forward price.")

elif method == "Forward-Pricing":
    c1, c2 = st.columns(2)
    params["S"] = st.number_input("Spot FX rate (S)", value=pending_params.get("S", 1.085))
    params["r_domestic"] = st.number_input("Domestic Rate", value=pending_params.get("r_domestic", 0.045))
    params["r_foreign"] = st.number_input("Foreign Rate", value=pending_params.get("r_foreign", 0.035))
    params["T"] = st.number_input("Time to delivery (T, years)", value=pending_params.get("T", 0.25))

elif method == "Mark-to-Market":
    c1, c2 = st.columns(2)
    params["market_price"] = st.number_input("Market Price ($)", value=pending_params.get("market_price", 100.0))
    params["bid"] = st.number_input("Bid ($)", value=pending_params.get("bid", 99.9))
    params["ask"] = st.number_input("Ask ($)", value=pending_params.get("ask", 100.1))
    params["volume"] = st.number_input("Volume (shares)", value=pending_params.get("volume", 1000000))

elif method == "Relative":
    c1, c2 = st.columns(2)
    params["earnings"] = st.number_input("Earnings ($)", value=pending_params.get("earnings", 5e9))
    params["ebitda"] = st.number_input("EBITDA ($)", value=pending_params.get("ebitda", 8e9))
    params["peer_pe"] = st.number_input("Peer P/E", value=pending_params.get("peer_pe", 22.0))
    params["peer_ev_ebitda"] = st.number_input("Peer EV/EBITDA", value=pending_params.get("peer_ev_ebitda", 14.0))
    params["shares_outstanding"] = st.number_input("Shares Outstanding", value=pending_params.get("shares_outstanding", 1e9))

elif method == "Credit-Model":
    c1, c2 = st.columns(2)
    params["face_value"] = st.number_input("Face Value ($)", value=pending_params.get("face_value", 1000.0))
    params["coupon_rate"] = st.number_input("Coupon Rate", value=pending_params.get("coupon_rate", 0.05))
    params["maturity_years"] = st.number_input("Maturity (years)", value=pending_params.get("maturity_years", 5.0))
    params["credit_spread"] = st.number_input("Credit Spread", value=pending_params.get("credit_spread", 0.02))
    params["risk_free_rate"] = st.number_input("Risk-Free Rate", value=pending_params.get("risk_free_rate", 0.04))

if st.button("Calculate", type="primary", width="stretch"):
    try:
        fn = VALUATION_ENGINES[method]
        val_result = fn(**params)
        hairline()
        section_header("Result")
        render_valuation(val_result)

        has_mp = st.session_state.get("last_features").get("has_market_price") if st.session_state.get("last_features") else None
        if has_mp == 1 and method != "Mark-to-Market":
            hairline()
            section_header("Mark-to-Market Comparison")
            mtm_fn = VALUATION_ENGINES["Mark-to-Market"]
            mtm_params = {"market_price": pending_params.get("market_price", 100.0),
                          "bid": pending_params.get("bid", 99.9), "ask": pending_params.get("ask", 100.1)}
            mtm_result = mtm_fn(**mtm_params)
            model_val = val_result.get("price") or val_result.get("fair_value") or val_result.get("forward_price") or 0
            mtm_val = mtm_result.get("fair_value") or 0
            diff = model_val - mtm_val if mtm_val else 0
            diff_pct = diff / mtm_val * 100 if mtm_val else 0
            diff_tone = "success" if abs(diff_pct) < 5 else "warning"
            render_stat_cards([
                {"label": "Model value", "value": f"${model_val:,.4f}", "tone": "accent"},
                {"label": "Market value", "value": f"${mtm_val:,.4f}", "tone": "neutral"},
                {"label": "Difference", "value": f"${diff:,.4f}", "tone": diff_tone,
                 "caption": f"{diff_pct:+.2f}% vs market"},
            ], columns=3)
            st.caption("IFRS 13 Level 1 → use Market Price. This comparison is informational.")

    except Exception as e:
        st.error(f"Calculation error: {e}")
