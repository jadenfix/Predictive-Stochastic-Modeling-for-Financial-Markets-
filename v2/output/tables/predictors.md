**Out-of-sample Brier skill (%) of individual predictors and combinations**

|  | h = 1 | h = 3 | h = 6 | h = 12 | AUC, h = 1 |
|---|---:|---:|---:|---:|---:|
| *Baseline* | | | | | |
| Persistence | 17.6\*\*\* | 10.0\*\*\* | 3.9\*\* | −0.2 | 0.707 |
| *Univariate logits: main predictors* | | | | | |
| Log dividend yield | 18.3\*\*\* | 13.4\*\*\* | 8.2\*\* | 1.4 | 0.646 |
| Log CAPE | 13.9\*\*\* | 8.3\*\*\* | 2.7\* | −3.9 | 0.668 |
| CPI inflation, 12-month | 5.0\*\*\* | 3.6\*\*\* | 1.9\* | 0.2 | 0.775 |
| 12-month change in 10-year yield | 0.8 | −0.4 | −0.9 | −0.5 | 0.664 |
| 12-month real price change | 23.2\*\*\* | 12.2\*\*\* | 4.6\*\* | 0.0 | 0.831 |
| 12-month realized volatility | 2.2\*\* | 0.5 | −0.9 | −1.1 | 0.614 |
| *Univariate logits: additional predictors* | | | | | |
| Excess CAPE yield | 0.1 | −2.0 | −3.7 | −5.7 | 0.554 |
| Log payout ratio | 1.3\* | 0.4 | −0.4 | −1.2 | 0.504 |
| 12-month real earnings growth | 0.0 | −0.6 | −1.0 | −1.1 | 0.622 |
| 10-year Treasury yield | −4.7 | −6.0 | −7.4 | −7.8 | 0.562 |
| Drawdown from 12-month high | 26.5\*\*\* | 13.8\*\*\* | 4.4\* | −0.2 | 0.852 |
| *Multi-predictor forecasts* | | | | | |
| Equal-weight combination (11 univariate logits) | 13.0\*\*\* | 7.2\*\*\* | 2.7\*\*\* | −0.7 | 0.783 |
| DMA of the 11 univariate logits | 23.3\*\*\* | 10.6\*\*\* | 2.3 | −4.5 | 0.772 |
| Logit: all 11 predictors | 29.1\*\*\* | 12.8\*\* | −3.0 | −14.4 | 0.787 |

Notes: Real-time expanding-window forecasts with the main dating rule; every model is re-estimated at each origin on data available then. Skill is relative to the unconditional frequency. Stars: one-sided Diebold-Mariano test against the unconditional frequency, * p < 0.10, ** p < 0.05, *** p < 0.01.
