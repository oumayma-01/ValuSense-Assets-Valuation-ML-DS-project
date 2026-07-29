import numpy as np
from scipy.stats import norm


def black_scholes(S, K, T, r, sigma, option_type="call", **kw):
    if T <= 0:
        intrinsic = max(S - K, 0) if option_type == "call" else max(K - S, 0)
        d = (1.0 if S > K else 0.0) if option_type == "call" else (-1.0 if K > S else 0.0)
        return {"method": "Black-Scholes", "price": round(intrinsic, 4),
                "greeks": {"delta": d, "gamma": 0, "vega": 0, "theta": 0, "rho": 0},
                "inputs": {"S": S, "K": K, "T": T, "r": r, "sigma": sigma, "type": option_type}}
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if option_type == "call":
        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        delta = norm.cdf(d1); rs = 1
    else:
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        delta = norm.cdf(d1) - 1; rs = -1
    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    vega = S * norm.pdf(d1) * np.sqrt(T) / 100
    theta = (-(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
             - rs * r * K * np.exp(-r * T) * norm.cdf(rs * d2)) / 365
    rho = rs * K * T * np.exp(-r * T) * norm.cdf(rs * d2) / 100
    return {"method": "Black-Scholes", "price": round(float(price), 4),
            "greeks": {"delta": round(float(delta), 4), "gamma": round(float(gamma), 6),
                       "vega": round(float(vega), 4), "theta": round(float(theta), 4),
                       "rho": round(float(rho), 4)},
            "inputs": {"S": S, "K": K, "T": T, "r": r, "sigma": sigma, "type": option_type}}


def dcf_valuation(cash_flows, discount_rate, terminal_growth=0.02, **kw):
    if discount_rate <= terminal_growth:
        return {"method": "DCF", "error": "Discount rate must be > terminal growth rate"}
    n = len(cash_flows)
    pv_cfs, total_pv = [], 0
    for t, cf in enumerate(cash_flows, 1):
        pv = cf / (1 + discount_rate) ** t
        pv_cfs.append({"year": t, "cf": cf, "pv": round(pv, 2)})
        total_pv += pv
    tv_cf = cash_flows[-1] * (1 + terminal_growth)
    tv = tv_cf / (discount_rate - terminal_growth)
    pv_tv = tv / (1 + discount_rate) ** n
    fv = total_pv + pv_tv
    return {"method": "DCF", "fair_value": round(fv, 2), "pv_cash_flows": round(total_pv, 2),
            "terminal_value": round(pv_tv, 2), "terminal_pct": round(pv_tv / fv * 100, 1),
            "details": pv_cfs, "inputs": {"discount_rate": discount_rate, "terminal_growth": terminal_growth}}


def ddm_gordon(dividend_current, growth_rate=0.03, required_return=0.08, **kw):
    if required_return <= growth_rate:
        return {"method": "DDM", "error": "Required return must be > growth rate"}
    d1 = dividend_current * (1 + growth_rate)
    fv = d1 / (required_return - growth_rate)
    return {"method": "DDM (Gordon)", "fair_value": round(fv, 2), "next_dividend": round(d1, 4),
            "implied_dividend_yield": round(d1 / fv * 100, 2),
            "inputs": {"D0": dividend_current, "g": growth_rate, "r": required_return}}


def monte_carlo_option(S, K, T, r, sigma, option_type="call", n_simulations=50000,
                        exotic_type=None, seed=None, **kw):
    rng = np.random.default_rng(seed if seed is not None else 42)
    if exotic_type == "asian":
        n_steps = 252; dt = T / n_steps
        paths = np.zeros((n_simulations, n_steps)); paths[:, 0] = S
        for t in range(1, n_steps):
            Z = rng.standard_normal(n_simulations)
            paths[:, t] = paths[:, t-1] * np.exp((r - 0.5*sigma**2)*dt + sigma*np.sqrt(dt)*Z)
        avg = paths.mean(axis=1)
        payoffs = np.maximum(avg - K, 0) if option_type == "call" else np.maximum(K - avg, 0)
    else:
        Z = rng.standard_normal(n_simulations)
        ST = S * np.exp((r - 0.5*sigma**2)*T + sigma*np.sqrt(T)*Z)
        payoffs = np.maximum(ST - K, 0) if option_type == "call" else np.maximum(K - ST, 0)
    price = np.exp(-r*T) * payoffs.mean()
    se = np.exp(-r*T) * payoffs.std() / np.sqrt(n_simulations)
    return {"method": f"Monte-Carlo ({exotic_type or 'vanilla'})", "price": round(float(price), 4),
            "std_error": round(float(se), 4),
            "confidence_95": [round(float(price-1.96*se), 4), round(float(price+1.96*se), 4)],
            "n_simulations": n_simulations, "inputs": {"S": S, "K": K, "T": T, "r": r, "sigma": sigma}}


def binomial_tree(S, K, T, r, sigma, option_type="call", n_steps=100, american=True, **kw):
    dt = T / n_steps; u = np.exp(sigma * np.sqrt(dt)); d = 1 / u
    p = (np.exp(r * dt) - d) / (u - d); disc = np.exp(-r * dt)
    prices = S * u**np.arange(n_steps, -1, -1) * d**np.arange(0, n_steps+1)
    values = np.maximum(prices - K, 0) if option_type == "call" else np.maximum(K - prices, 0)
    ee = 0
    for step in range(n_steps-1, -1, -1):
        ps = S * u**np.arange(step, -1, -1) * d**np.arange(0, step+1)
        cont = disc * (p*values[:step+1] + (1-p)*values[1:step+2])
        if american:
            ex = np.maximum(ps - K, 0) if option_type == "call" else np.maximum(K - ps, 0)
            ee += int((ex > cont).sum()); values = np.maximum(cont, ex)
        else:
            values = cont
    return {"method": f"Binomial Tree ({'American' if american else 'European'})",
            "price": round(float(values[0]), 4), "n_steps": n_steps,
            "early_exercise_optimal": ee > 0 if american else False,
            "inputs": {"S": S, "K": K, "T": T, "r": r, "sigma": sigma, "type": option_type},
            "tree_params": {"u": round(float(u), 6), "d": round(float(d), 6), "p": round(float(p), 6)}}


def cost_of_carry(S, r, T, storage_cost=0, convenience_yield=0, **kw):
    F = S * np.exp((r + storage_cost - convenience_yield) * T)
    return {"method": "Cost-of-Carry", "forward_price": round(float(F), 4), "spot_price": S,
            "basis": round(float(F-S), 4),
            "inputs": {"S": S, "r": r, "T": T, "u": storage_cost, "y": convenience_yield}}


def forward_pricing(S, r_domestic=0, r_foreign=0, T=1, **kw):
    F = S * np.exp((r_domestic - r_foreign) * T)
    return {"method": "Forward-Pricing (CIP)", "forward_rate": round(float(F), 6), "spot_rate": S,
            "forward_points": round(float((F-S)*10000), 2),
            "inputs": {"S": S, "r_domestic": r_domestic, "r_foreign": r_foreign, "T": T}}


def mark_to_market(market_price=None, bid=None, ask=None, volume=None, **kw):
    if market_price is None and bid is not None and ask is not None:
        market_price = (bid + ask) / 2
    result = {"method": "Mark-to-Market",
              "fair_value": round(float(market_price), 4) if market_price else None,
              "source": "Observed market price (IFRS 13, Level 1)"}
    if bid is not None and ask is not None:
        result["bid"] = round(float(bid), 4)
        result["ask"] = round(float(ask), 4)
        result["spread_pct"] = round((ask-bid)/market_price*100, 4) if market_price else None
    if volume is not None:
        result["volume"] = volume
    if market_price is None:
        result["error"] = "Market price required (market_price or bid/ask)"
    return result


def relative_valuation(earnings=None, ebitda=None, revenue=None, peer_pe=None,
                        peer_ev_ebitda=None, peer_ps=None, net_debt=0,
                        shares_outstanding=1, **kw):
    vals = []
    if earnings and peer_pe:
        eq = earnings * peer_pe
        vals.append({"multiple": "P/E", "peer_value": peer_pe,
                     "equity_value": round(eq, 2), "per_share": round(eq/shares_outstanding, 2)})
    if ebitda and peer_ev_ebitda:
        ev = ebitda * peer_ev_ebitda; eq = ev - net_debt
        vals.append({"multiple": "EV/EBITDA", "peer_value": peer_ev_ebitda,
                     "enterprise_value": round(ev, 2), "equity_value": round(eq, 2),
                     "per_share": round(eq/shares_outstanding, 2)})
    if revenue and peer_ps:
        eq = revenue * peer_ps
        vals.append({"multiple": "P/S", "peer_value": peer_ps,
                     "equity_value": round(eq, 2), "per_share": round(eq/shares_outstanding, 2)})
    if not vals:
        return {"method": "Relative", "error": "Provide at least one (metric, peer_multiple) pair"}
    avg = np.mean([v["per_share"] for v in vals])
    return {"method": "Relative (Multiples)", "fair_value_per_share": round(float(avg), 2),
            "valuations": vals, "n_multiples_used": len(vals)}


def credit_model_valuation(face_value=1000, coupon_rate=0.05, maturity_years=5,
                            credit_spread=0.02, recovery_rate=0.4, risk_free_rate=0.04,
                            pd_annual=None, lgd=None, ead=None, **kw):
    dr = risk_free_rate + credit_spread
    n = int(maturity_years * 2); c = face_value * coupon_rate / 2
    pv_c = sum(c / (1+dr/2)**t for t in range(1, n+1))
    pv_p = face_value / (1+dr/2)**n
    price = pv_c + pv_p
    pv_rf = sum(c / (1+risk_free_rate/2)**t for t in range(1, n+1))
    pv_rf += face_value / (1+risk_free_rate/2)**n
    cva = pv_rf - price
    if pd_annual is None:
        pd_annual = credit_spread / (1 - recovery_rate)
    cum_pd = 1 - (1 - pd_annual)**maturity_years
    _lgd = lgd if lgd else (1 - recovery_rate)
    el = cum_pd * _lgd * (ead if ead else face_value)
    return {"method": "Credit-Model", "fair_value": round(price, 2),
            "pv_coupons": round(pv_c, 2), "pv_principal": round(pv_p, 2),
            "risk_free_value": round(pv_rf, 2), "credit_value_adjustment": round(cva, 2),
            "expected_loss": round(el, 2), "implied_pd_annual": round(pd_annual*100, 2),
            "price_per_100": round(price/face_value*100, 2), "discount_rate_pct": round(dr*100, 2),
            "inputs": {"face_value": face_value, "coupon_rate": coupon_rate,
                       "maturity": maturity_years, "credit_spread": credit_spread,
                       "recovery_rate": recovery_rate, "risk_free_rate": risk_free_rate}}


VALUATION_ENGINES = {
    "Black-Scholes": black_scholes, "DCF": dcf_valuation, "DDM": ddm_gordon,
    "Monte-Carlo": monte_carlo_option, "Binomial-Tree": binomial_tree,
    "Cost-of-Carry": cost_of_carry, "Forward-Pricing": forward_pricing,
    "Mark-to-Market": mark_to_market, "Relative": relative_valuation,
    "Credit-Model": credit_model_valuation,
}

ENGINE_SIGNATURES = {
    "Black-Scholes":   {"required": {"S","K","T","r","sigma"}, "label": "S, K, T, r, sigma"},
    "DCF":             {"required": {"cash_flows","discount_rate"}, "label": "cash_flows, discount_rate"},
    "DDM":             {"required": {"dividend_current"}, "label": "dividend_current, [growth_rate, required_return]"},
    "Monte-Carlo":     {"required": {"S","K","T","r","sigma"}, "label": "S, K, T, r, sigma, [exotic_type]"},
    "Binomial-Tree":   {"required": {"S","K","T","r","sigma"}, "label": "S, K, T, r, sigma"},
    "Cost-of-Carry":   {"required": {"S","r","T"}, "label": "S, r, T, [storage_cost, convenience_yield]"},
    "Forward-Pricing": {"required": {"S","T"}, "label": "S, T, r_domestic, r_foreign"},
    "Mark-to-Market":  {"required": set(), "label": "market_price (or bid+ask)"},
    "Relative":        {"required": set(), "label": "earnings+peer_pe, ebitda+peer_ev_ebitda"},
    "Credit-Model":    {"required": set(), "label": "face_value, coupon_rate, credit_spread"},
}
