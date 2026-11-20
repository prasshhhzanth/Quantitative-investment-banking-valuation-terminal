# QIBVT — Quantitative Investment Banking & Valuation Terminal

An educational investment-banking valuation and market-risk dashboard built with Streamlit. The interactive terminal includes market performance, benchmark sensitivity, financial statement flows, trading comparables, DCF sensitivity, and Monte Carlo scenarios.

## Company universe
- US: Apple (AAPL), Microsoft (MSFT), NVIDIA (NVDA)
- India: TCS (TCS.NS), Reliance Industries (RELIANCE.NS)

## Included
1. Interactive indexed-price, daily-return, drawdown, and beta/CAPM charts
2. Best-effort annual financial statements and income-statement flow visualization from Yahoo Finance
3. Trading-comparable multiple charts for P/E, forward P/E, P/B, EV/EBITDA, and EV/Revenue
4. FCFF DCF with five-year forecast and WACC / terminal-growth sensitivity heatmap
5. Monte Carlo terminal-price distribution and 95% one-day historical VaR
6. Downloadable CSV data exports and a Google Colab notebook starter

## Quick start — Google Colab
1. Open https://colab.research.google.com/
2. Upload `QIBVT_Colab_Notebook.ipynb`.
3. Run cells from top to bottom.
4. The notebook downloads market data and attempts to retrieve financial statements.
5. Download CSV outputs from the Colab Files panel.

## Quick start — Streamlit dashboard
1. Extract this ZIP.
2. Open the extracted folder in VS Code.
3. In terminal run:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   pip install -r requirements.txt
   streamlit run app.py
   ```
4. Select the company universe and click **Refresh terminal**. Use the tabs and chart controls to explore the results.

## Financial data caveats
- Yahoo Finance is a convenient prototype data source, not a substitute for official filings.
- Financial statement line-item labels vary by issuer and may be missing. The code uses best-effort aliases.
- Verify annual figures against SEC filings (US issuers) and company annual reports / NSE filings (Indian issuers).
- Record fiscal year end, reporting currency, units (ones/thousands/millions), and source URL for every manual adjustment.
- Never combine USD and INR amounts in one valuation. Convert consistently if you need cross-company comparisons.
- CapEx is stored as a positive spend amount and subtracted from operating cash flow in the FCF calculation.
- Diluted shares in a DCF must be in the same scale as equity value. If revenue and debt are in millions, shares should be in millions.
- A missing field is not zero.

## Important modelling notes
- DCF uses FCFF = EBIT × (1 − tax) + D&A − CapEx − change in NWC.
- Terminal value uses the Gordon growth formula; WACC must exceed terminal growth.
- The DCF assumptions in the dashboard are manual scenario inputs. Do not interpret default values as company forecasts.
- Comparable sets are screening peers only. A formal deal valuation requires a documented peer-selection rationale and adjusted financials.
- Reliance is a diversified conglomerate. Segment-level sum-of-the-parts valuation is more appropriate than one simple peer group.
- CAPM uses separate benchmarks: SPY for US equities and ^NSEI for Indian equities. The risk-free rates are editable assumptions and should be matched to market/currency.
- Monte Carlo is a simplified geometric Brownian motion model based on historical return moments.
- Historical VaR is a quantile estimate; it is not the worst possible loss.

## Suggested report structure
1. Executive summary and investment question
2. Company and industry overview
3. Data sources, fiscal periods, currency and units
4. Historical market performance
5. Financial statement analysis and cash-flow quality
6. Trading comparables and peer rationale
7. FCFF DCF, WACC, terminal growth and sensitivity
8. CAPM and beta
9. Monte Carlo and VaR
10. Conclusion, limitations and further work

## Official source starting points
- SEC EDGAR company filings: https://www.sec.gov/edgar/search/
- Apple investor relations: https://investor.apple.com/
- Microsoft investor relations: https://www.microsoft.com/en-us/Investor/
- NVIDIA investor relations: https://investor.nvidia.com/
- TCS investor relations: https://www.tcs.com/investor-relations
- Reliance investor relations: https://www.ril.com/investors
- NSE India: https://www.nseindia.com/

Educational use only. Not investment advice.
