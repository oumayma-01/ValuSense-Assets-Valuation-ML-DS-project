from .config import AC_LOOKUP, AC_REVERSE


def apply_ifrs_constraints_v3(y_pred, X_df, le_tgt):
    y_c = y_pred.copy(); overrides = []
    BOND = AC_LOOKUP.get("Bond", -1)
    COMM = AC_LOOKUP.get("Commodity", -1)
    CURR = AC_LOOKUP.get("Currency", -1)
    EQUITY = AC_LOOKUP.get("Equity", -1)
    ETF_SUBCLASSES = {24, 39, 43, 11}
    GROWTH_SUBCLASSES = {47, 41, 22, 35, 63}

    for i in range(len(y_c)):
        row = X_df.iloc[i]
        m = le_tgt.inverse_transform([y_c[i]])[0]
        orig = m
        ac = row.get("asset_class_encoded", -1)
        sc = row.get("asset_subclass_encoded", -1)

        if ac == EQUITY and sc in ETF_SUBCLASSES and row.get("has_cash_flows", 0) == 0:
            if row.get("ifrs_level", 0) == 1 and row.get("has_market_price", 0) == 1:
                m = "Mark-to-Market"

        if ac == EQUITY:
            if m == "DDM" and row.get("dividend_yield", 1) == 0:
                m = "Relative" if row.get("pe_ratio", 0) > 25 else "DCF"
            elif m == "Mark-to-Market" and row.get("dividend_yield", 0) == 0 and row.get("pe_ratio", 0) > 25 and row.get("has_cash_flows", 0) == 1:
                m = "Relative"

        if row.get("ifrs_level", 0) == 1 and row.get("has_market_price", 0) == 1 and row.get("liquidity", 0) >= 2:
            valid = {"DDM", "Relative", "DCF", "Mark-to-Market", "Cost-of-Carry",
                     "Forward-Pricing", "Black-Scholes", "Binomial-Tree", "Monte-Carlo"}
            if m not in valid:
                m = "Mark-to-Market"

        if row.get("ifrs_level", 0) == 3 and row.get("has_market_price", 0) == 0 and m == "Mark-to-Market":
            m = "DCF" if row.get("has_cash_flows", 0) else ("Monte-Carlo" if row.get("has_options_features", 0) else "DCF")

        if row.get("has_early_exercise", 0) == 1 and m == "Black-Scholes":
            m = "Binomial-Tree"

        if row.get("is_path_dependent", 0) == 1 and m != "Monte-Carlo":
            m = "Monte-Carlo"

        if ac == BOND and row.get("has_credit_risk", 0) == 1 and m in {"Black-Scholes", "Binomial-Tree", "DCF"}:
            m = "Credit-Model"

        if ac == COMM and m == "DDM":
            m = "Cost-of-Carry"

        if ac == CURR and m == "Cost-of-Carry":
            m = "Forward-Pricing"

        if m != orig:
            y_c[i] = le_tgt.transform([m])[0]
            overrides.append({"idx": i, "from": orig, "to": m, "rule": f"{orig}->{m}"})

    return y_c, len(overrides), overrides
