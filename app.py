import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from finance_engine import (COMPANIES, PEER_GROUPS, load_market_data, market_metrics,
    beta_and_capm, get_annual_financials, get_valuation_multiples,
    dcf_valuation, monte_carlo, historical_var)

BG = "#f1f2ef"
PANEL = "#ffffff"
GRID = "#e5e8e1"
TEXT = "#182019"
MUTED = "#788178"
LIME = "#a9e86f"
GREEN = "#159447"
DARK_GREEN = "#164f2b"
RED = "#e94724"
PURPLE = "#7944bd"
PALETTE = [GREEN, PURPLE, "#74b84c", RED, DARK_GREEN]

st.set_page_config(page_title="QIBVT | Market Terminal", page_icon="📈", layout="wide")
st.markdown("""
<style>
:root { color-scheme: light; }
.stApp { background: #f1f2ef; color: #182019; font-family: 'Manrope', sans-serif; }
[data-testid="stHeader"] { background: rgba(241,242,239,.94); }
[data-testid="stSidebar"] { background: #f7f8f5; border-right: 1px solid #e1e5dd; }
h1,h2,h3 { letter-spacing: -.035em; color: #182019; }
h1 { font-size: 1.75rem !important; font-weight: 800 !important; }
h2 { font-size: 1.22rem !important; font-weight: 750 !important; margin-top: .2rem !important; }
[data-testid="stMetric"] { background: #ffffff; border: 1px solid #e5e8e1; border-radius: 18px; padding: 13px 16px; box-shadow: 0 3px 14px rgba(35,55,35,.035); }
[data-testid="stMetricLabel"] { color: #788178 !important; font-size: .72rem !important; text-transform: uppercase; letter-spacing: .09em; }
[data-testid="stMetricValue"] { color: #182019; font-size: 1.35rem !important; }
.terminal-kicker { font: 700 .68rem 'Manrope', sans-serif; letter-spacing: .14em; color: #159447; text-transform: uppercase; }
.terminal-title { font-size: 1.85rem; font-weight: 800; letter-spacing: -.04em; margin: .05rem 0; color: #182019; }
.terminal-sub { color: #788178; font-size: .82rem; }
.section-note { color: #788178; font-size: .8rem; margin: -.45rem 0 1rem; }
.stTabs [data-baseweb="tab-list"] { gap: .4rem; border-bottom: 1px solid #e1e5dd; }
.stTabs [data-baseweb="tab"] { background: transparent; color: #788178; padding: .65rem 1rem; }
.stTabs [aria-selected="true"] { color: #164f2b !important; background: #a9e86f !important; border-radius: 999px !important; }
div[data-testid="stDataFrame"] { border: 1px solid #e5e8e1; border-radius: 14px; overflow: hidden; }
div[data-testid="stVerticalBlockBorderWrapper"] { background: #fff; border-radius: 20px; border-color: #e5e8e1; }
[data-testid="stButton"] button[kind="primary"] { background: #164f2b; border: 0; border-radius: 999px; color: white; }
[data-testid="stButton"] button { border-radius: 999px; }
</style>
""", unsafe_allow_html=True)

def style_fig(fig, height=390):
    fig.update_layout(template="plotly_white", paper_bgcolor=PANEL, plot_bgcolor=PANEL,
        font=dict(family="Manrope, sans-serif", color=TEXT, size=11), height=height,
        margin=dict(l=18, r=18, t=48, b=18), title_font=dict(size=14, color=TEXT),
        legend=dict(orientation="h", y=1.12, x=0, bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="#ffffff", bordercolor=GRID, font=dict(family="Manrope, sans-serif", color=TEXT)))
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=GRID, tickfont_color=MUTED)
    fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False, tickfont_color=MUTED)
    return fig

def section(title, note=None):
    st.subheader(title)
    if note: st.markdown(f'<div class="section-note">{note}</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="terminal-kicker">QIBVT / workspace</div>', unsafe_allow_html=True)
    st.header("Market setup")
    tickers = st.multiselect("Watchlist", list(COMPANIES.values()), default=list(COMPANIES.values()))
    period = st.selectbox("Price history", ["1y", "2y", "5y", "10y"], index=2)
    st.caption("Benchmarks are matched by listing market.")
    us_bench = st.text_input("US benchmark", "SPY")
    india_bench = st.text_input("India benchmark", "^NSEI")
    st.divider()
    st.markdown('<div class="terminal-kicker">Valuation / scenario</div>', unsafe_allow_html=True)
    selected_dcf = st.selectbox("Company", tickers or list(COMPANIES.values()))
    revenue = st.number_input("Revenue (millions)", min_value=1.0, value=100000.0)
    ebit_margin = st.slider("EBIT margin", 0.0, .60, .20, .01)
    tax_rate = st.slider("Tax rate", 0.0, .50, .25, .01)
    da_pct = st.slider("D&A / revenue", 0.0, .20, .04, .005)
    capex_pct = st.slider("CapEx / revenue", 0.0, .30, .06, .005)
    nwc_pct = st.slider("NWC / revenue", -.10, .30, .05, .005)
    wacc = st.slider("WACC", .04, .25, .10, .005)
    terminal_growth = st.slider("Terminal growth", 0.0, .06, .03, .005)
    growth = [st.slider(f"Revenue growth Y{i}", -.20, .40, v, .01) for i, v in enumerate([.12,.10,.08,.06,.04], 1)]
    shares = st.number_input("Diluted shares (millions)", min_value=1.0, value=1000.0)
    net_debt = st.number_input("Net debt (millions)", value=0.0)
    run = st.button("↻  Refresh terminal", type="primary", use_container_width=True)

st.markdown('<div class="terminal-kicker">Quantitative investment banking & valuation terminal</div><div class="terminal-title">Market overview</div><div class="terminal-sub">Live market data · interactive research workspace · educational use</div>', unsafe_allow_html=True)
st.markdown(" ")
all_tickers = list(dict.fromkeys((tickers or []) + [us_bench, india_bench]))
if run or "loaded_prices" not in st.session_state:
    if not run:
        st.info("Choose a watchlist and click **Refresh terminal** to load market data and build the workspace.")
        st.stop()
    with st.spinner("Loading prices, fundamentals and peer data..."):
        try:
            prices, errors = load_market_data(all_tickers, period)
            st.session_state["loaded_prices"] = prices
            st.session_state["loaded_errors"] = errors
            st.session_state["loaded_universe"] = list(tickers)
            st.session_state["loaded_period"] = period
        except RuntimeError as exc:
            st.error(str(exc))
            st.info("The dashboard needs a connection to its Yahoo Finance data provider. Check internet access, then click **Refresh terminal** to retry.")
            st.stop()
else:
    prices = st.session_state["loaded_prices"]
    errors = st.session_state.get("loaded_errors", {})
if errors: st.warning("Unavailable symbols: " + " | ".join(f"{k}: {v}" for k, v in errors.items()))
universe = [t for t in st.session_state.get("loaded_universe", tickers) if t in prices.columns]
if not universe: st.error("No selected companies loaded."); st.stop()
metrics, returns = market_metrics(prices[universe])

# Compact quote strip, calculated directly from the loaded price series.
quote_cols = st.columns(min(len(universe), 5))
for col, ticker in zip(quote_cols, universe[:5]):
    series = prices[ticker].dropna()
    change = series.iloc[-1] / series.iloc[-2] - 1 if len(series) > 1 else np.nan
    col.metric(ticker, f"{series.iloc[-1]:,.2f}", f"{change:+.2%} 1D" if pd.notna(change) else None,
               delta_color="normal")
st.caption("Delayed or provider-supplied prices. Cross-market prices remain in their local currencies.")

tab_market, tab_fund, tab_comps, tab_dcf, tab_risk = st.tabs(["◉  Markets", "▤  Fundamentals", "⇄  Comparables", "⌁  DCF lab", "◌  Risk"])
with tab_market:
    section("Relative performance", "Indexed to 100 at the start of the selected window. Select names in the legend to isolate a series.")
    norm = prices[universe].dropna(how="all").copy()
    norm = norm.div(norm.apply(lambda s: s.dropna().iloc[0] if s.notna().any() else np.nan)).mul(100)
    price_view = st.radio("Chart view", ["Indexed growth", "Daily returns"], horizontal=True, key="price_view")
    display_prices = norm if price_view == "Indexed growth" else prices[universe].pct_change().mul(100)
    fig = go.Figure()
    palette = PALETTE
    for i, ticker in enumerate(universe):
        fig.add_trace(go.Scatter(x=display_prices.index, y=display_prices[ticker], name=ticker, mode="lines",
            line=dict(color=palette[i % len(palette)], width=2), connectgaps=True,
            fill="tozeroy" if price_view == "Indexed growth" else None,
            fillcolor=["rgba(21,148,71,.08)", "rgba(121,68,189,.07)", "rgba(116,184,76,.07)", "rgba(233,71,36,.06)", "rgba(22,79,43,.06)"][i % len(palette)] if price_view == "Indexed growth" else None,
            hovertemplate="%{x|%d %b %Y}<br>%{y:.2f}" + (" index" if price_view == "Indexed growth" else "%") + "<extra>%{fullData.name}</extra>"))
    if price_view == "Indexed growth": fig.add_hline(y=100, line_dash="dot", line_color=GRID)
    else: fig.add_hline(y=0, line_dash="dot", line_color=GRID)
    fig.update_layout(title="Growth of 100" if price_view == "Indexed growth" else "Daily returns", hovermode="x unified", yaxis_title="Indexed value" if price_view == "Indexed growth" else "Daily return (%)", xaxis_rangeslider_visible=True)
    st.plotly_chart(style_fig(fig, 440), use_container_width=True, config={"displaylogo":False, "scrollZoom":True})
    left, right = st.columns([1.45, 1])
    with left:
        section("Drawdown monitor", "Peak-to-trough decline from each asset's running high.")
        dd = prices[universe] / prices[universe].cummax() - 1
        f = px.area(dd, labels={"value":"Drawdown", "index":"Date"}, color_discrete_sequence=palette)
        f.update_yaxes(tickformat=".0%")
        st.plotly_chart(style_fig(f, 310), use_container_width=True, config={"displaylogo":False})
    with right:
        section("Market statistics", "Annualized from observed daily returns.")
        m = metrics.copy()
        st.dataframe(m.style.format({"Last Price":"{:,.2f}","Total Return":"{:+.1%}","CAGR":"{:.1%}","Annualized Volatility":"{:.1%}","Sharpe (rf=0)":"{:.2f}","Max Drawdown":"{:.1%}"}), use_container_width=True, height=310)
    section("Benchmark sensitivity", "Daily asset returns against the local market benchmark; slope is historical beta.")
    beta_asset = st.selectbox("Asset", universe, key="beta_asset")
    beta_bench = us_bench if not beta_asset.endswith(".NS") else india_bench
    if beta_bench in prices:
        aligned = pd.concat([prices[beta_asset].pct_change().rename("Asset"), prices[beta_bench].pct_change().rename("Benchmark")], axis=1).dropna()
        beta, capm = beta_and_capm(aligned["Asset"], aligned["Benchmark"], .04 if beta_bench == us_bench else .07)
        if len(aligned) >= 2 and pd.notna(beta):
            fit_x = np.linspace(aligned.Benchmark.min(), aligned.Benchmark.max(), 50)
            intercept = aligned.Asset.mean() - beta * aligned.Benchmark.mean()
            f = go.Figure(go.Scatter(x=aligned.Benchmark, y=aligned.Asset, mode="markers", name="Daily returns", marker=dict(color=GREEN, opacity=.42, size=5)))
            f.add_trace(go.Scatter(x=fit_x, y=intercept + beta * fit_x, mode="lines", name=f"Regression · β {beta:.2f}", line=dict(color=PURPLE, width=2)))
            f.update_layout(title=f"{beta_asset} vs {beta_bench} · CAPM cost of equity {capm:.1%}", xaxis_title="Benchmark daily return", yaxis_title="Asset daily return", hovermode="closest")
            f.update_xaxes(tickformat=".1%"); f.update_yaxes(tickformat=".1%")
            st.plotly_chart(style_fig(f, 360), use_container_width=True, config={"displaylogo":False})
        else: st.info("Insufficient aligned returns for a benchmark regression.")
    else: st.info(f"Benchmark data unavailable ({beta_bench}).")
    st.download_button("Export market statistics CSV", metrics.to_csv(), "market_metrics.csv", "text/csv")

with tab_fund:
    section("Fundamentals dashboard", "Annual provider data; missing fields are omitted from charts and remain missing in the table.")
    financials = []
    for t in universe:
        try:
            f = get_annual_financials(t, years=5)
            if not f.empty: financials.append(f)
        except Exception as e: st.warning(f"{t}: {e}")
    if financials:
        fin = pd.concat(financials, ignore_index=True)
        fin["Fiscal Year End"] = pd.to_datetime(fin["Fiscal Year End"])
        c1, c2 = st.columns(2)
        with c1:
            section("Revenue trajectory")
            f = px.line(fin, x="Fiscal Year End", y="Revenue", color="Ticker", markers=True, color_discrete_sequence=palette)
            f.update_yaxes(tickformat="~s", title="Provider units")
            st.plotly_chart(style_fig(f), use_container_width=True, config={"displaylogo":False})
        with c2:
            section("Profitability & cash flow")
            f = make_subplots(specs=[[{"secondary_y":True}]])
            for i, ticker in enumerate(universe):
                subset = fin[fin.Ticker == ticker].sort_values("Fiscal Year End")
                f.add_trace(go.Bar(x=subset["Fiscal Year End"], y=subset["Free Cash Flow"], name=f"{ticker} FCF", marker_color=palette[i % len(palette)], opacity=.72), secondary_y=False)
                f.add_trace(go.Scatter(x=subset["Fiscal Year End"], y=subset["EBIT Margin"], name=f"{ticker} EBIT margin", mode="lines+markers", line=dict(color=palette[i % len(palette)], dash="dot")), secondary_y=True)
            f.update_yaxes(title_text="Free cash flow", tickformat="~s", secondary_y=False)
            f.update_yaxes(title_text="EBIT margin", tickformat=".0%", secondary_y=True, showgrid=False)
            st.plotly_chart(style_fig(f), use_container_width=True, config={"displaylogo":False})
        section("Income statement flow", "Follow revenue into operating costs, EBIT, and net income. Hover over a flow for its reported amount.")
        flow_ticker = st.selectbox("Issuer for income flow", [t for t in universe if t in fin.Ticker.unique()], key="flow_ticker")
        flow_rows = fin[fin.Ticker == flow_ticker].sort_values("Fiscal Year End")
        if not flow_rows.empty:
            row = flow_rows.iloc[-1]
            revenue_flow, ebit_flow, income_flow = [pd.to_numeric(row.get(k), errors="coerce") for k in ["Revenue", "EBIT", "Net Income"]]
            if all(pd.notna(v) and np.isfinite(v) for v in [revenue_flow, ebit_flow, income_flow]) and revenue_flow > 0:
                ebit_flow = max(0, min(float(ebit_flow), float(revenue_flow)))
                income_flow = max(0, min(float(income_flow), ebit_flow))
                cost_flow, below_ebit = revenue_flow - ebit_flow, ebit_flow - income_flow
                f = go.Figure(go.Sankey(
                    arrangement="snap",
                    node=dict(pad=24, thickness=18,
                        label=[f"Revenue<br>{revenue_flow:,.0f}", f"Operating costs<br>{cost_flow:,.0f}", f"EBIT<br>{ebit_flow:,.0f}", f"Tax & other<br>{below_ebit:,.0f}", f"Net income<br>{income_flow:,.0f}"],
                        color=[PURPLE, RED, GREEN, "#f08b70", DARK_GREEN],
                        line=dict(color="#ffffff", width=1.5),
                        hovertemplate="%{label}<extra></extra>"),
                    link=dict(source=[0, 0, 2, 2], target=[1, 2, 3, 4],
                        value=[cost_flow, ebit_flow, below_ebit, income_flow],
                        color=["rgba(233,71,36,.32)", "rgba(21,148,71,.42)", "rgba(233,71,36,.32)", "rgba(22,79,43,.52)"],
                        hovertemplate="%{source.label} → %{target.label}<br>Reported flow: %{value:,.0f}<extra></extra>")))
                f.update_layout(title=f"{flow_ticker} · {row['Fiscal Year End'].year} · {row.get('Currency', 'reported units')}", height=380)
                st.plotly_chart(f, use_container_width=True, config={"displaylogo":False})
                st.caption("The chart groups revenue less EBIT as operating costs and EBIT less net income as tax and other items. Provider units and reporting currency apply.")
            else:
                st.info("Revenue, EBIT, or net income is missing for this issuer, so the income flow cannot be constructed.")
        section("Statement detail")
        fin_show = fin.copy(); fin_show["Fiscal Year End"] = fin_show["Fiscal Year End"].dt.date
        st.dataframe(fin_show, use_container_width=True, height=300)
        st.download_button("Export financial statements CSV", fin_show.to_csv(index=False), "financial_statements.csv", "text/csv")
    else: st.warning("No annual statement rows were returned. Use official annual reports and the project template.")
    st.caption("Yahoo Finance fields vary by issuer and reporting currency. Provider units can differ; do not compare absolute amounts across issuers without checking units and currency.")

with tab_comps:
    section("Trading comparables", "Screening references from the configured peer groups. Multiples are not adjusted for accounting or segment mix.")
    comp_tickers = list(dict.fromkeys(universe + [p for t in universe for p in PEER_GROUPS.get(t, [])]))
    with st.spinner("Retrieving valuation multiples..."): comps = get_valuation_multiples(comp_tickers)
    mult = [c for c in ["P/E", "Forward P/E", "P/B", "EV/EBITDA", "EV/Revenue"] if c in comps and comps[c].notna().any()]
    if mult:
        chosen_mult = st.selectbox("Valuation multiple", mult, index=3 if "EV/EBITDA" in mult else 0)
        chart_data = comps.dropna(subset=[chosen_mult]).copy()
        if not chart_data.empty:
            chart_data["Group"] = np.where(chart_data.Ticker.isin(universe), "Selected", "Reference peer")
            f = px.bar(chart_data.sort_values(chosen_mult), x=chosen_mult, y="Ticker", color="Group", orientation="h", text=chosen_mult,
                color_discrete_map={"Selected":GREEN,"Reference peer":"#a6ada4"}, hover_data=["Company", "Currency"] if "Currency" in chart_data else None)
            f.update_traces(texttemplate="%{text:.1f}x", textposition="outside", cliponaxis=False)
            f.update_xaxes(title="Multiple", ticksuffix="x")
            st.plotly_chart(style_fig(f, max(350, 42 * len(chart_data))), use_container_width=True, config={"displaylogo":False})
        else: st.info(f"No values available for {chosen_mult}.")
    st.dataframe(comps, use_container_width=True, height=330)
    st.download_button("Export peer data CSV", comps.to_csv(index=False), "trading_comparables.csv", "text/csv")
    st.caption("Reliance is diversified; a segment-level sum-of-the-parts analysis is generally more defensible than a single peer multiple.")

with tab_dcf:
    st.warning("Scenario inputs are manually supplied in the sidebar. Values use the selected currency and units; defaults are not company forecasts.")
    try:
        dcf = dcf_valuation(revenue, ebit_margin, tax_rate, da_pct, capex_pct, nwc_pct, wacc, terminal_growth, growth, shares, net_debt)
        a,b,c,d = st.columns(4)
        a.metric("Enterprise value", f"{dcf['Enterprise Value']:,.1f}")
        b.metric("Equity value", f"{dcf['Equity Value']:,.1f}")
        c.metric("Value / share", f"{dcf['Intrinsic Value / Share']:,.2f}")
        d.metric("Terminal value share", f"{dcf['PV Terminal Value']/dcf['Enterprise Value']:.1%}" if dcf['Enterprise Value'] else "—")
        section("Forecast & valuation sensitivity", "Heatmap recalculates intrinsic value per share as WACC and terminal growth change; current case is marked with a star.")
        forecast = dcf["forecast"]
        f = make_subplots(specs=[[{"secondary_y":True}]])
        f.add_trace(go.Bar(x=forecast.Year, y=forecast.Revenue, name="Revenue", marker_color="#31506a"), secondary_y=False)
        f.add_trace(go.Scatter(x=forecast.Year, y=forecast["FCFF"], name="FCFF", mode="lines+markers", line=dict(color=GREEN, width=3)), secondary_y=True)
        f.update_yaxes(title_text="Revenue", tickformat="~s", secondary_y=False)
        f.update_yaxes(title_text="FCFF", tickformat="~s", secondary_y=True, showgrid=False)
        st.plotly_chart(style_fig(f, 300), use_container_width=True, config={"displaylogo":False})
        waccs = sorted(set(round(float(x), 3) for x in np.clip(np.array([wacc-.02,wacc-.01,wacc,wacc+.01,wacc+.02]), .04, .25)))
        grows = sorted(set(round(float(x), 3) for x in np.clip(np.array([terminal_growth-.02,terminal_growth-.01,terminal_growth,terminal_growth+.01,terminal_growth+.02]), 0, .06)))
        z = []
        for g in grows:
            row = []
            for w in waccs:
                try: row.append(dcf_valuation(revenue, ebit_margin, tax_rate, da_pct, capex_pct, nwc_pct, w, g, growth, shares, net_debt)["Intrinsic Value / Share"])
                except Exception: row.append(np.nan)
            z.append(row)
        f = go.Figure(go.Heatmap(x=[f"{x:.1%}" for x in waccs], y=[f"{x:.1%}" for x in grows], z=z, colorscale=[[0,"#632e48"],[.5,"#233c55"],[1,"#1aa88f"]], colorbar=dict(title="/ share", tickfont_color=MUTED), hovertemplate="WACC %{x}<br>Growth %{y}<br>Value %{z:,.2f}<extra></extra>"))
        f.update_layout(title="Intrinsic value / share", xaxis_title="WACC", yaxis_title="Terminal growth")
        st.plotly_chart(style_fig(f, 340), use_container_width=True, config={"displaylogo":False})
        st.dataframe(forecast.style.format({"Revenue":"{:,.2f}","EBIT":"{:,.2f}","FCFF":"{:,.2f}","PV of FCFF":"{:,.2f}"}), use_container_width=True)
    except Exception as e: st.error(f"DCF error: {e}")

with tab_risk:
    risk_ticker = st.selectbox("Risk asset", universe)
    simulations = st.select_slider("Monte Carlo paths", options=[1000, 5000, 10000, 25000], value=10000)
    horizon = st.select_slider("Horizon (trading days)", options=[21, 63, 126, 252], value=252)
    terminal, mu, sigma = monte_carlo(prices[risk_ticker], simulations, horizon)
    var = historical_var(returns[risk_ticker], .95, 1_000_000)
    a,b,c = st.columns(3)
    a.metric("Annualized drift", f"{mu:.1%}")
    b.metric("Annualized volatility", f"{sigma:.1%}")
    c.metric("1 day / 95% VaR on 1m", f"{var:,.0f}")
    section("Scenario distribution", f"{simulations:,} one-factor GBM terminal price simulations over {horizon} trading days. These are model scenarios, not forecasts.")
    f = px.histogram(pd.DataFrame({"Terminal price":terminal}), x="Terminal price", nbins=65, histnorm="probability density", color_discrete_sequence=[GREEN], opacity=.85)
    for q, label, color in [(5,"5th percentile",RED),(50,"Median",PURPLE),(95,"95th percentile",GREEN)]:
        val = np.percentile(terminal, q)
        f.add_vline(x=val, line_dash="dot", line_color=color, annotation_text=f"{label} {val:,.2f}", annotation_position="top")
    f.update_layout(xaxis_title="Terminal price", yaxis_title="Probability density", bargap=.04)
    st.plotly_chart(style_fig(f, 420), use_container_width=True, config={"displaylogo":False})
    st.caption("GBM assumes constant drift and volatility. Historical VaR is a sample quantile and does not describe the maximum possible loss.")

st.markdown("---")
st.caption("QIBVT · Market data and fundamentals from Yahoo Finance · Verify currencies, fiscal periods, units and assumptions against primary sources before formal analysis.")
