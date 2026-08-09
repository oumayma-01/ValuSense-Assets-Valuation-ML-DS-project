import streamlit as st
from valusense.config import ASSET_CLASSES, SC_LOOKUP_FULL


def render_asset_form():
    st.markdown("### Asset Description")
    st.markdown("Describe the financial asset to get a valuation method recommendation.")

    col1, col2 = st.columns(2)
    with col1:
        asset_class = st.selectbox(
            "Asset Class",
            options=list(ASSET_CLASSES.keys()),
            index=4,
            help="The broad category of the financial asset"
        )

    with col2:
        sc_options = list(SC_LOOKUP_FULL.keys())
        subclass = st.selectbox(
            "Asset Subclass",
            options=sc_options,
            index=sc_options.index("Large Cap Stock") if "Large Cap Stock" in sc_options else 0,
            help="More specific classification"
        )

    with st.expander("Market & Structural Features", expanded=True):
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            has_market_price = st.checkbox(
                "Has Market Price", value=True,
                help="Whether an observable market price exists. IFRS 13 Level 1 assets must use that price directly.")
            has_cash_flows = st.checkbox(
                "Has Cash Flows", value=False,
                help="Whether the asset produces predictable cash flows (coupons, dividends, lease payments). Needed for DCF and DDM.")
            is_exchange_traded = st.checkbox(
                "Exchange Traded", value=True,
                help="Whether the asset trades on a public exchange. OTC assets lack transparent pricing under IFRS 13.")
        with mc2:
            has_options_features = st.checkbox(
                "Has Options Features", value=False,
                help="Whether the asset behaves like an option (a right, not an obligation). This unlocks the option pricing models.")
            has_credit_risk = st.checkbox(
                "Has Credit Risk", value=False,
                help="Whether the issuer could default. Credit-risky assets are valued with a credit model, not plain DCF.")
            volatility_available = st.checkbox(
                "Volatility Available", value=True,
                help="Whether implied or historical volatility data is available. Black-Scholes requires it.")
        with mc3:
            has_early_exercise = st.checkbox(
                "Early Exercise", value=False,
                help="Whether the option can be exercised before maturity. American options need a Binomial Tree; Black-Scholes cannot handle it.")
            is_path_dependent = st.checkbox(
                "Path Dependent", value=False,
                help="Whether the payoff depends on the price path (for example Asian options). These require Monte-Carlo.")

    with st.expander("Quantitative Features", expanded=True):
        q1, q2 = st.columns(2)
        with q1:
            liquidity = st.slider("Liquidity (0-2)", 0, 2, 2,
                                  help="How easily the asset trades. 0 = illiquid, 2 = highly liquid. Low liquidity downgrades the IFRS level.")
            data_availability = st.slider("Data Availability (0-2)", 0, 2, 2,
                                          help="How much pricing data is available. Poor data forces a Level 3 (model-based) valuation.")
            ifrs_level = st.slider("IFRS 13 Level", 1, 3, 1,
                                   help="Fair-value hierarchy: Level 1 = quoted market prices, Level 2 = observable inputs, Level 3 = unobservable inputs.")
            pe_ratio = st.number_input("P/E Ratio", min_value=0.0, value=20.0, format="%.1f",
                                       help="Price divided by earnings per share. Only relevant for equities.")
            market_cap = st.number_input("Market Cap ($)", min_value=0, value=100_000_000_000,
                                          step=1_000_000_000, format="%d",
                                          help="Total market value of the company's outstanding shares.")
        with q2:
            maturity_years = st.number_input("Maturity (years)", min_value=-1.0, value=5.0,
                                              help="-1 = perpetual/no maturity. Options and bonds need a positive maturity to be valued.")
            dividend_yield = st.number_input("Dividend Yield (%)", min_value=0.0, value=0.0,
                                              format="%.2f",
                                              help="Annual dividends as a percentage of the share price. Enter 0 if the stock pays no dividend.") / 100
            beta = st.number_input("Beta", min_value=0.0, value=1.0, format="%.2f",
                                   help="Sensitivity of the asset to market moves. Used for equities, not for options or bonds.")
            implied_vol = st.number_input("Implied Volatility (%)", min_value=0.0, value=25.0,
                                           format="%.1f",
                                           help="The market's expectation of future price swings, in percent. Options need it to be priced.") / 100

    features = {
        "has_market_price": int(has_market_price),
        "has_cash_flows": int(has_cash_flows),
        "has_options_features": int(has_options_features),
        "is_exchange_traded": int(is_exchange_traded),
        "liquidity": liquidity,
        "maturity_years": maturity_years,
        "has_credit_risk": int(has_credit_risk),
        "has_early_exercise": int(has_early_exercise),
        "is_path_dependent": int(is_path_dependent),
        "data_availability": data_availability,
        "volatility_available": int(volatility_available),
        "ifrs_level": ifrs_level,
        "dividend_yield": dividend_yield,
        "beta": beta,
        "pe_ratio": pe_ratio,
        "market_cap": float(market_cap),
        "implied_volatility_atm": implied_vol,
        "asset_class": asset_class,
        "asset_subclass": subclass,
    }

    return features


def validate_features(features):
    """Return a list of human-readable problems with the entered asset description.

    Surfaced as inline validation errors so a contradictory input fails clearly
    instead of silently producing a misleading recommendation.
    """
    issues = []
    ac = features.get("asset_class", "")
    maturity = features.get("maturity_years", 0)

    if features.get("has_market_price") == 1 and features.get("ifrs_level") == 3:
        issues.append(
            "This asset has a market price but IFRS Level 3 is selected. A Level 3 asset is "
            "valued from unobservable inputs; if a market price exists it should typically be "
            "Level 1 or Level 2."
        )

    if maturity < 0 and ac in ("Option", "Bond", "Derivative"):
        issues.append(
            f"'{ac}' is set to have no maturity (maturity = {maturity}). Options, bonds and "
            "derivatives need a positive maturity to be valued."
        )

    if features.get("has_options_features") == 1 and features.get("implied_volatility_atm", 0) <= 0:
        issues.append(
            "This asset has option features but implied volatility is 0%. Option pricing "
            "(Black-Scholes, Binomial Tree) requires a positive volatility."
        )

    if ac == "Bond" and features.get("has_cash_flows") == 0:
        issues.append(
            "A bond usually produces cash flows (coupons). With no cash flows, DCF and DDM "
            "cannot apply and the recommendation may be misleading."
        )

    if features.get("has_early_exercise") == 1 and features.get("is_path_dependent") == 1:
        issues.append(
            "Early exercise and path dependency are both selected. These are unusual to "
            "combine; please check the asset description."
        )

    return issues


def render_valuation_params(method):
    st.markdown("### Valuation Parameters")
    st.markdown(f"Provide parameters for **{method}** valuation calculation.")

    if method == "Black-Scholes" or method == "Binomial-Tree":
        c1, c2, c3 = st.columns(3)
        with c1:
            S = st.number_input("Spot Price (S)", value=100.0, format="%.2f")
            K = st.number_input("Strike Price (K)", value=100.0, format="%.2f")
        with c2:
            T = st.number_input("Time to Maturity (T, years)", value=1.0, format="%.2f")
            r = st.number_input("Risk-Free Rate (r)", value=0.045, format="%.3f")
        with c3:
            sigma = st.number_input("Volatility (sigma)", value=0.25, format="%.2f")
            opt_type = st.selectbox("Option Type", ["call", "put"])
        return {"S": S, "K": K, "T": T, "r": r, "sigma": sigma, "option_type": opt_type}

    elif method == "DCF":
        c1, c2 = st.columns(2)
        with c1:
            n_cf = st.number_input("Number of cash flows", min_value=1, value=5)
            discount_rate = st.number_input("Discount Rate", value=0.10, format="%.3f")
        with c2:
            terminal_growth = st.number_input("Terminal Growth Rate", value=0.02, format="%.3f")
            base_cf = st.number_input("Base Cash Flow ($)", value=100.0, format="%.2f")
        cash_flows = [base_cf * (1 + 0.05) ** t for t in range(n_cf)]
        return {"cash_flows": cash_flows, "discount_rate": discount_rate, "terminal_growth": terminal_growth}

    elif method == "DDM":
        c1, c2, c3 = st.columns(3)
        with c1:
            div = st.number_input("Current Dividend ($)", value=2.0, format="%.2f")
        with c2:
            g = st.number_input("Growth Rate", value=0.03, format="%.3f")
        with c3:
            r = st.number_input("Required Return", value=0.08, format="%.3f")
        return {"dividend_current": div, "growth_rate": g, "required_return": r}

    elif method == "Monte-Carlo":
        c1, c2, c3 = st.columns(3)
        with c1:
            S = st.number_input("Spot Price (S)", value=100.0, format="%.2f")
            K = st.number_input("Strike Price (K)", value=100.0, format="%.2f")
        with c2:
            T = st.number_input("Time to Maturity (T)", value=1.0, format="%.2f")
            r = st.number_input("Risk-Free Rate (r)", value=0.05, format="%.3f")
        with c3:
            sigma = st.number_input("Volatility (sigma)", value=0.30, format="%.2f")
            exotic = st.selectbox("Exotic Type", [None, "asian"])
        return {"S": S, "K": K, "T": T, "r": r, "sigma": sigma, "exotic_type": exotic, "seed": 42}

    elif method == "Cost-of-Carry":
        c1, c2 = st.columns(2)
        with c1:
            S = st.number_input("Spot Price", value=1950.0, format="%.2f")
            r = st.number_input("Risk-Free Rate (r)", value=0.04, format="%.3f")
        with c2:
            T = st.number_input("Time (T, years)", value=0.5, format="%.2f")
            storage = st.number_input("Storage Cost (%)", value=0.01, format="%.3f")
            conv = st.number_input("Convenience Yield (%)", value=0.005, format="%.3f")
        return {"S": S, "r": r, "T": T, "storage_cost": storage, "convenience_yield": conv}

    elif method == "Forward-Pricing":
        c1, c2 = st.columns(2)
        with c1:
            S = st.number_input("Spot Rate", value=1.085, format="%.4f")
            rd = st.number_input("Domestic Rate", value=0.045, format="%.3f")
        with c2:
            rf = st.number_input("Foreign Rate", value=0.035, format="%.3f")
            T = st.number_input("Time (T, years)", value=0.25, format="%.2f")
        return {"S": S, "r_domestic": rd, "r_foreign": rf, "T": T}

    elif method == "Mark-to-Market":
        return {}

    elif method == "Relative":
        c1, c2 = st.columns(2)
        with c1:
            earnings = st.number_input("Earnings ($)", value=5e9, format="%.0f")
            ebitda = st.number_input("EBITDA ($)", value=8e9, format="%.0f")
        with c2:
            peer_pe = st.number_input("Peer P/E", value=22.0, format="%.1f")
            peer_ev_ebitda = st.number_input("Peer EV/EBITDA", value=14.0, format="%.1f")
            shares = st.number_input("Shares Outstanding", value=1e9, format="%.0f")
        return {"earnings": earnings, "ebitda": ebitda, "peer_pe": peer_pe,
                "peer_ev_ebitda": peer_ev_ebitda, "shares_outstanding": shares}

    elif method == "Credit-Model":
        c1, c2 = st.columns(2)
        with c1:
            fv = st.number_input("Face Value", value=1000.0, format="%.0f")
            coupon = st.number_input("Coupon Rate", value=0.05, format="%.3f")
        with c2:
            mat = st.number_input("Maturity (years)", value=5.0, format="%.1f")
            spread = st.number_input("Credit Spread", value=0.02, format="%.3f")
            rfr = st.number_input("Risk-Free Rate", value=0.04, format="%.3f")
        return {"face_value": fv, "coupon_rate": coupon, "maturity_years": mat,
                "credit_spread": spread, "risk_free_rate": rfr}

    return {}
