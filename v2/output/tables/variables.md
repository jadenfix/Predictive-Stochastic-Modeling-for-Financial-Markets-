**Predictors, transformations and publication lags**

| Predictor | Construction | Units | Lag (months) | Mean | SD |
|---|---:|---:|---:|---:|---:|
| *Monthly-change predictors (archived thesis variables)* | | | | | |
| Inflation (CPI, monthly) | 100 dlog CPI | % per month | 1 | 0.31 | 0.36 |
| Change in 10-year Treasury yield | Monthly change | pp | 0 | 0.00 | 0.27 |
| Real 10-year bond return | 100 dlog real bond index | % per month | 0 (CPI 1) | 0.18 | 1.99 |
| Real dividend growth | 100 dlog real dividends | % per month | 6 | 0.17 | 0.63 |
| Real S&P 500 total return | Price return plus D/12P, less inflation | % per month | 0 (D 6, CPI 1) | 0.49 | 3.65 |
| Real TR-scaled earnings growth | 100 dlog real TR-scaled earnings | % per month | 6 | 0.45 | 4.84 |
| Change in log TR-CAPE | 100 dlog TR price / 10-yr mean earnings | % per month | 0 (E 6) | 0.05 | 3.66 |
| *State predictors (bear-market forecasting models)* | | | | | |
| Log dividend yield | log(D / P) | log points | 0 (D 6) | −3.67 | 0.40 |
| Log CAPE | log(P / 10-yr mean real earnings) | log points | 0 (E 6) | 2.98 | 0.43 |
| Inflation (CPI, 12-month) | 100 x 12-month dlog CPI | % | 1 | 3.66 | 2.68 |
| 12-month change in 10-year yield | 12-month change | pp | 0 | −0.01 | 1.13 |
| 12-month real price change | 100 x 12-month dlog real price | % | 0 (CPI 1) | 3.07 | 15.94 |
| 12-month realized volatility | sd of monthly real returns x sqrt(12) | % annualized | 0 (CPI 1) | 11.25 | 4.93 |

Notes: Statistics over 1960:01-2023:12. A forecast is made at the end of month t. Lag gives the publication lag applied to the inputs: CPI enters with one month, dividends (D) and earnings (E) with six. Real values are deflated by the CPI available at t. The archived 'realpricelag' columns (future prices) are never used.
