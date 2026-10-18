**Out-of-sample Brier skill (%) of individual predictors and combinations**

|  | h = 1 | h = 3 | h = 6 | h = 12 | AUC, h = 1 |
|---|---:|---:|---:|---:|---:|
| *Baseline* | | | | | |
| Persistence | 18.9\*\*\* | 11.5\*\*\* | 4.9\* | 0.8 | 0.688 |
| *Univariate logits: main predictors* | | | | | |
| Log dividend yield | 16.5\*\*\* | 12.3\*\*\* | 7.9\* | 1.9 | 0.627 |
| Log CAPE | 14.4\*\*\* | 9.0\*\*\* | 3.3 | −5.1 | 0.653 |
| CPI inflation, 12-month | 10.0\*\*\* | 7.8\*\*\* | 5.0\*\*\* | 1.3\* | 0.769 |
| 12-month change in 10-year yield | 2.0 | 0.6 | −0.2 | 0.2 | 0.655 |
| 12-month real price change | 23.7\*\*\* | 12.6\*\*\* | 4.5\* | −0.5 | 0.821 |
| 12-month realized volatility | 2.5 | −0.1 | −2.4 | −2.3 | 0.593 |
| *Univariate logits: additional predictors* | | | | | |
| Excess CAPE yield | 0.5 | −3.1 | −6.6 | −12.9 | 0.543 |
| Log payout ratio | −0.5 | −1.5 | −2.3 | −3.0 | 0.415 |
| 12-month real earnings growth | 0.0 | −0.9 | −1.3 | −1.2 | 0.617 |
| 10-year Treasury yield | −4.5 | −6.0 | −7.6 | −8.1 | 0.548 |
| Drawdown from 12-month high | 27.7\*\*\* | 14.9\*\*\* | 4.3 | −1.1 | 0.844 |
| *Multi-predictor forecasts* | | | | | |
| Equal-weight combination (11 univariate logits) | 14.4\*\*\* | 8.2\*\*\* | 3.2\*\* | −1.0 | 0.767 |
| Logit: all 11 predictors | 24.7\*\*\* | 5.7 | −14.5 | −28.9 | 0.779 |

Notes: Real-time expanding-window forecasts with the main dating rule; every model is re-estimated at each origin on data available then. The combination averages the probability forecasts of the univariate logits with equal weights. Skill is relative to the unconditional frequency. Stars: one-sided Diebold-Mariano test against the unconditional frequency, * p < 0.10, ** p < 0.05, *** p < 0.01.
