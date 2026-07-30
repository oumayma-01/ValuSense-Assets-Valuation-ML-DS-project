TOOL_DEFINITIONS = [
    {
        "name": "classify_asset",
        "description": "Classify a financial asset and predict the optimal valuation method using the ML model. Returns asset class, predicted method, calibrated confidence score (0-1), and top 3 alternative methods with probabilities. Always call this before run_valuation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "features": {
                    "type": "object",
                    "description": "Dictionary of asset features. At minimum must include: asset_class (string: Option|Equity|Bond|Commodity|Currency|Derivative), asset_subclass (string), ifrs_level (1|2|3), has_market_price (0|1), has_cash_flows (0|1), has_options_features (0|1), is_exchange_traded (0|1), liquidity (0|1|2), maturity_years (float), volatility_available (0|1), data_availability (0|1|2). All 28 features will be auto-defaulted if missing.",
                    "additionalProperties": True,
                }
            },
            "required": ["features"],
        },
    },
    {
        "name": "check_ifrs_compliance",
        "description": "Check whether a predicted valuation method complies with IFRS 13 fair value hierarchy rules. Returns whether an override was applied, the final method, and which IFRS rule fired. Call this after classify_asset to confirm the method is regulatory-compliant.",
        "input_schema": {
            "type": "object",
            "properties": {
                "predicted_method": {
                    "type": "string",
                    "description": "The method name from classify_asset (e.g. 'Black-Scholes', 'DCF', 'DDM', 'Binomial-Tree', 'Monte-Carlo', 'Cost-of-Carry', 'Forward-Pricing', 'Mark-to-Market', 'Relative', 'Credit-Model').",
                },
                "features": {
                    "type": "object",
                    "description": "Same features dict used in classify_asset. Required fields: asset_class_encoded, ifrs_level, has_market_price, has_cash_flows, has_options_features, has_early_exercise, is_path_dependent, has_credit_risk, liquidity, dividend_yield, pe_ratio.",
                },
            },
            "required": ["predicted_method", "features"],
        },
    },
    {
        "name": "explain_prediction",
        "description": "Get SHAP-based explanation for why a specific valuation method was recommended. Returns the top 5 driving features with their values, SHAP impact scores, and direction (positive/negative). Use this when a user asks 'why' a method was chosen.",
        "input_schema": {
            "type": "object",
            "properties": {
                "features": {
                    "type": "object",
                    "description": "Same features dict used in classify_asset.",
                },
                "method": {
                    "type": "string",
                    "description": "Optional. The method to explain. If omitted, explains whatever the model predicted.",
                },
            },
            "required": ["features"],
        },
    },
    {
        "name": "run_valuation",
        "description": "Run a numerical valuation calculation using the specified method and parameters. Returns the fair value amount, currency, and a detailed breakdown. Call classify_asset first to determine the appropriate method. If the user provides params for the wrong method, return a clear error describing what params are needed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "method": {
                    "type": "string",
                    "description": "Valuation method name. Must be one of: Black-Scholes, DCF, DDM, Binomial-Tree, Monte-Carlo, Cost-of-Carry, Forward-Pricing, Mark-to-Market, Relative, Credit-Model.",
                },
                "params": {
                    "type": "object",
                    "description": "Parameters required by the valuation method:\n- Black-Scholes: {S(spot), K(strike), T(time_years), r(rate), sigma(volatility), option_type('call'|'put')}\n- Binomial-Tree: same as Black-Scholes + optional option_type\n- Monte-Carlo: {S, K, T, r, sigma, exotic_type('asian'|None), seed}\n- DCF: {cash_flows(list), discount_rate, terminal_growth}\n- DDM: {dividend_current, growth_rate, required_return}\n- Cost-of-Carry: {S, r, T, storage_cost, convenience_yield}\n- Forward-Pricing: {S(spot_rate), r_domestic, r_foreign, T}\n- Mark-to-Market: {market_price} or {bid, ask}\n- Relative: {earnings, ebitda, peer_pe, peer_ev_ebitda, shares_outstanding}\n- Credit-Model: {face_value, coupon_rate, maturity_years, credit_spread, risk_free_rate}",
                },
            },
            "required": ["method", "params"],
        },
    },
]
