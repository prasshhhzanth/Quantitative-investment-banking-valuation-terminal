# QIBVT — Project Report Template

## Title
Quantitative Investment Banking & Valuation Terminal: Integrated Equity Valuation and Market-Risk Analysis

## Abstract
This project combines fundamental valuation techniques commonly used in investment banking with quantitative analysis of public-market returns and risk. The selected universe comprises Apple, Microsoft, NVIDIA, TCS and Reliance Industries. The prototype calculates market performance and risk metrics, retrieves available annual financial-statement data, screens trading multiples, builds an FCFF DCF scenario, estimates beta and CAPM cost of equity, and performs Monte Carlo and historical VaR analysis.

## 1. Objective and scope
State the research question, company universe, date range and intended user.

## 2. Data and controls
For each source, document:
- Provider / official filing
- URL and retrieval date
- Fiscal year end
- Reporting currency
- Units (ones, thousands or millions)
- Any restatements or manual adjustments

Use SEC EDGAR and issuer investor-relations reports to verify US issuer data. Use issuer annual reports and NSE filings for Indian issuers.

## 3. Market performance
Present total return, CAGR, annualised volatility, Sharpe ratio and maximum drawdown. Explain that CAGR is calculated from observed start/end adjusted prices and elapsed trading days.

## 4. Financial statement analysis
Discuss revenue growth, EBIT margin, net income, debt, cash, operating cash flow and free cash flow. FCF in this project is operating cash flow less positive CapEx spend. Explain missing or inconsistent line items.

## 5. Comparable company analysis
Show P/E, forward P/E, P/B, EV/EBITDA and EV/Revenue where available. Justify peer selection by business model, geography, growth, margins and capital intensity. Explain why Reliance needs segment-level sum-of-the-parts analysis.

## 6. DCF valuation
Document base-year revenue, EBIT margin, tax rate, D&A/revenue, CapEx/revenue, NWC/revenue, five forecast growth rates, WACC, terminal growth, net debt and diluted shares. Show the FCFF forecast, present value of explicit cash flows, terminal value, enterprise value, equity value and value per share. Add sensitivity tables for WACC and terminal growth before treating the model as decision-useful.

## 7. CAPM and beta
Explain the benchmark used for each market, estimation period, risk-free rate, market return and beta. Use SPY for US stocks and Nifty 50 (^NSEI) for Indian stocks; do not mix market/currency inputs.

## 8. Quantitative risk
Explain the GBM assumptions behind the Monte Carlo simulation and report terminal-price percentiles. Explain 95% one-day historical VaR and why VaR is not a maximum-loss measure.

## 9. Findings
Summarise what the data suggests without making unsupported investment recommendations.

## 10. Limitations and next steps
Discuss vendor data gaps, accounting comparability, peer selection, DCF assumption sensitivity, historical-model limitations, FX exposure and the need for official filings.
