from __future__ import annotations
import numpy as np
import pandas as pd
import yfinance as yf

TRADING_DAYS = 252

COMPANIES = {
    "Apple": "AAPL", "Microsoft": "MSFT", "NVIDIA": "NVDA",
    "TCS": "TCS.NS", "Reliance Industries": "RELIANCE.NS"
}

PEER_GROUPS = {
    "AAPL": ["MSFT", "DELL", "HPQ"],
    "MSFT": ["ORCL", "GOOGL", "AMZN"],
    "NVDA": ["AMD", "AVGO", "QCOM"],
    "TCS.NS": ["INFY.NS", "WIPRO.NS", "HCLTECH.NS"],
    # Reliance is a diversified conglomerate; these are broad Indian large-cap
    # reference names, NOT clean pure-play comparables. Segment SOTP is preferable.
    "RELIANCE.NS": ["ADANIENT.NS", "ITC.NS", "BHARTIARTL.NS"]
}

def load_market_data(tickers, period="5y"):
    prices, errors = {}, {}
    for ticker in dict.fromkeys([str(t).strip().upper() for t in tickers if str(t).strip()]):
        try:
            hist = yf.Ticker(ticker).history(period=period, auto_adjust=True)
            if hist.empty or "Close" not in hist:
                errors[ticker] = "No price history returned."
                continue
            prices[ticker] = hist["Close"].rename(ticker)
        except Exception as exc:
            errors[ticker] = str(exc)
    if not prices:
        details = "; ".join(f"{ticker}: {message}" for ticker, message in errors.items())
        raise RuntimeError(
            "No market data downloaded. Check network access and ticker symbols."
            + (f" Provider details: {details}" if details else "")
        )
    return pd.concat(prices.values(), axis=1).sort_index().ffill(), errors

def market_metrics(prices):
    returns = prices.pct_change().dropna(how="all")
    rows = []
    for ticker in prices.columns:
        p, r = prices[ticker].dropna(), returns[ticker].dropna()
        if len(p) < 2 or r.empty: continue
        total = p.iloc[-1] / p.iloc[0] - 1
        years = len(r) / TRADING_DAYS
        cagr = (p.iloc[-1] / p.iloc[0]) ** (1 / years) - 1 if years > 0 and p.iloc[-1] > 0 else np.nan
        rows.append({
            "Ticker": ticker, "Last Price": p.iloc[-1], "Total Return": total,
            "CAGR": cagr, "Annualized Volatility": r.std() * np.sqrt(TRADING_DAYS),
            "Sharpe (rf=0)": r.mean() / r.std() * np.sqrt(TRADING_DAYS) if r.std() else np.nan,
            "Max Drawdown": (p / p.cummax() - 1).min()
        })
    return pd.DataFrame(rows).set_index("Ticker"), returns

def beta_and_capm(asset_returns, benchmark_returns, risk_free_rate=0.04):
    aligned = pd.concat([asset_returns.rename("asset"), benchmark_returns.rename("market")], axis=1).dropna()
    if len(aligned) < 30: return np.nan, np.nan
    a, m = aligned["asset"], aligned["market"]
    beta = a.cov(m) / m.var() if m.var() else np.nan
    market_annual = (1 + m.mean()) ** TRADING_DAYS - 1
    return beta, risk_free_rate + beta * (market_annual - risk_free_rate)

def get_annual_financials(ticker, years=3):
    """Best-effort annual statements from Yahoo Finance; verify against official filings."""
    obj = yf.Ticker(ticker)
    statements = {
        "income": obj.income_stmt,
        "balance": obj.balance_sheet,
        "cashflow": obj.cashflow
    }
    aliases = {
        "Revenue": ["Total Revenue", "Operating Revenue"],
        "EBIT": ["EBIT", "Operating Income"],
        "Net Income": ["Net Income", "Net Income Common Stockholders"],
        "Total Debt": ["Total Debt", "Long Term Debt And Capital Lease Obligation"],
        "Cash": ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"],
        "Operating Cash Flow": ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"],
        "CapEx": ["Capital Expenditure", "Capital Expenditures"],
        "Diluted Shares": ["Diluted Average Shares", "Diluted Average Shares Outstanding"]
    }
    def get_value(df, names, col):
        if df is None or df.empty or col not in df.columns: return np.nan
        for n in names:
            if n in df.index:
                v = df.loc[n, col]
                if pd.notna(v): return float(v)
        return np.nan
    cols = list(statements["income"].columns[:years]) if statements["income"] is not None and not statements["income"].empty else []
    rows = []
    for col in cols:
        rows.append({
            "Ticker": ticker, "Fiscal Year End": pd.Timestamp(col).date().isoformat(),
            "Revenue": get_value(statements["income"], aliases["Revenue"], col),
            "EBIT": get_value(statements["income"], aliases["EBIT"], col),
            "Net Income": get_value(statements["income"], aliases["Net Income"], col),
            "Total Debt": get_value(statements["balance"], aliases["Total Debt"], col),
            "Cash": get_value(statements["balance"], aliases["Cash"], col),
            "Operating Cash Flow": get_value(statements["cashflow"], aliases["Operating Cash Flow"], col),
            # Yahoo often reports CapEx as a negative cash flow. Store spend as positive.
            "CapEx": abs(get_value(statements["cashflow"], aliases["CapEx"], col)),
            "Diluted Shares": get_value(statements["income"], aliases["Diluted Shares"], col)
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df["EBIT Margin"] = df["EBIT"] / df["Revenue"]
        df["Free Cash Flow"] = df["Operating Cash Flow"] - df["CapEx"]
        df["Net Debt"] = df["Total Debt"] - df["Cash"]
    return df

def get_valuation_multiples(tickers):
    rows = []
    for ticker in dict.fromkeys(tickers):
        try:
            info = yf.Ticker(ticker).info or {}
            rows.append({
                "Ticker": ticker, "Company": info.get("shortName") or info.get("longName") or ticker,
                "Market Cap": info.get("marketCap"), "Enterprise Value": info.get("enterpriseValue"),
                "P/E": info.get("trailingPE"), "Forward P/E": info.get("forwardPE"),
                "P/B": info.get("priceToBook"), "EV/EBITDA": info.get("enterpriseToEbitda"),
                "EV/Revenue": info.get("enterpriseToRevenue"), "Currency": info.get("currency")
            })
        except Exception as exc:
            rows.append({"Ticker": ticker, "Company": ticker, "Data Error": str(exc)})
    return pd.DataFrame(rows)

def dcf_valuation(revenue, ebit_margin, tax_rate, da_pct, capex_pct, nwc_pct,
                  wacc, terminal_growth, growth_rates, shares, net_debt):
    if not (wacc > terminal_growth >= 0):
        raise ValueError("WACC must be greater than terminal growth, and terminal growth non-negative.")
    if shares <= 0 or revenue <= 0: raise ValueError("Revenue and diluted shares must be positive.")
    prev_revenue, prev_nwc, pv_fcff, rows = revenue, revenue*nwc_pct, 0.0, []
    for year, growth in enumerate(growth_rates, start=1):
        rev = prev_revenue * (1 + growth)
        ebit = rev * ebit_margin
        taxes = max(ebit, 0) * tax_rate
        da, capex = rev * da_pct, rev * capex_pct
        nwc = rev * nwc_pct
        fcff = ebit - taxes + da - capex - (nwc - prev_nwc)
        pv = fcff / (1 + wacc) ** year
        rows.append({"Year": year, "Revenue": rev, "EBIT": ebit, "FCFF": fcff, "PV of FCFF": pv})
        pv_fcff += pv
        prev_revenue, prev_nwc = rev, nwc
    tv = rows[-1]["FCFF"] * (1 + terminal_growth) / (wacc - terminal_growth)
    pv_tv = tv / (1 + wacc) ** len(growth_rates)
    ev = pv_fcff + pv_tv
    equity = ev - net_debt
    return {"forecast": pd.DataFrame(rows), "PV Explicit FCFF": pv_fcff,
            "Terminal Value": tv, "PV Terminal Value": pv_tv,
            "Enterprise Value": ev, "Equity Value": equity,
            "Intrinsic Value / Share": equity / shares}

def monte_carlo(prices, simulations=10000, horizon_days=252, seed=42):
    p = prices.dropna()
    s0 = float(p.iloc[-1]); r = p.pct_change().dropna()
    mu, sigma = float(r.mean())*TRADING_DAYS, float(r.std())*np.sqrt(TRADING_DAYS)
    rng = np.random.default_rng(seed)
    z = rng.standard_normal(simulations)
    terminal = s0*np.exp((mu-.5*sigma**2)*(horizon_days/TRADING_DAYS)
                         + sigma*np.sqrt(horizon_days/TRADING_DAYS)*z)
    return terminal, mu, sigma

def historical_var(returns, confidence=.95, portfolio_value=1_000_000):
    return max(0.0, -float(returns.dropna().quantile(1-confidence))*portfolio_value)
