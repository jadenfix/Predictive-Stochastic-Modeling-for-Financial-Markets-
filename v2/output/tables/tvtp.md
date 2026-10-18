**Markov-switching models with time-varying transition probabilities**

|  | Fixed transitions | Log dividend yield | CPI inflation, 12-month | 12-month realized volatility | Drawdown from 12-month high | All four |
|---|---:|---:|---:|---:|---:|---:|
| *Logit of P(bull to bull): slope on lagged predictor* | | | | | | |
| Log dividend yield |  | −0.60\*\* |  |  |  | 0.67 |
|  |  | (0.28) |  |  |  | (0.43) |
| CPI inflation, 12-month |  |  | −1.28\*\*\* |  |  | −0.95\*\* |
|  |  |  | (0.32) |  |  | (0.40) |
| 12-month realized volatility |  |  |  | −0.30 |  | 0.20 |
|  |  |  |  | (0.27) |  | (0.37) |
| Drawdown from 12-month high |  |  |  |  | 2.39\*\*\* | 2.77\*\* |
|  |  |  |  |  | (0.87) | (1.26) |
| *Logit of P(bear to bull): slope on lagged predictor* | | | | | | |
| Log dividend yield |  | 0.80\*\* |  |  |  | 2.03 |
|  |  | (0.37) |  |  |  | (1.53) |
| CPI inflation, 12-month |  |  | 0.56\* |  |  | 0.65 |
|  |  |  | (0.30) |  |  | (1.03) |
| 12-month realized volatility |  |  |  | 0.60\* |  | 0.71 |
|  |  |  |  | (0.35) |  | (0.92) |
| Drawdown from 12-month high |  |  |  |  | 1.03 | 4.90 |
|  |  |  |  |  | (0.82) | (3.86) |
| *Regimes (transition probabilities at the predictors' sample means)* | | | | | | |
| Bull mean / bear mean (%) | 0.88 / −1.75 | 0.87 / −1.77 | 0.86 / −1.79 | 0.88 / −1.86 | 0.66 / −0.89 | 0.67 / −0.63 |
| Bull sd / bear sd (%) | 2.41 / 5.57 | 2.37 / 5.70 | 2.41 / 5.69 | 2.42 / 5.61 | 2.31 / 5.75 | 2.26 / 5.45 |
| P(bull to bull) | 0.940 | 0.915 | 0.926 | 0.943 | 0.738 | 0.657 |
| P(bear to bear) | 0.798 | 0.699 | 0.703 | 0.856 | 0.214 | 0.038 |
| *Fit* | | | | | | |
| Log-likelihood | −2,063.5 | −2,062.0 | −2,055.7 | −2,062.2 | −2,045.6 | −2,038.0 |
| LR statistic against fixed (df) |  | 3.0 (2) | 15.5 (2) | 2.5 (2) | 35.9 (2) | 51.0 (8) |
| LR p-value |  | 0.228 | <0.001 | 0.283 | <0.001 | <0.001 |
| AIC | 4,141.0 | 4,142.0 | 4,129.5 | 4,142.5 | 4,109.1 | 4,106.0 |
| BIC | 4,173.7 | 4,184.2 | 4,171.6 | 4,184.6 | 4,151.2 | 4,176.2 |
| AUC of filtered bear probability | 0.802 | 0.812 | 0.874 | 0.807 | 0.861 | 0.865 |

Notes: MS-AR(1) models of monthly real returns, 1960:02-2026:06. In the TVTP models the probability of moving from regime i at t - 1 to the bull regime at t is a logistic function of the standardized predictors at t - 1 (Diebold, Lee and Weinbach, 1994; Filardo, 1994). Slopes are per one standard deviation, with standard errors from the numerical Hessian in parentheses. The likelihood-ratio test compares each model with fixed transitions (chi-squared with two degrees of freedom per predictor). AUC compares the filtered bear-regime probability with the dated bear state (in sample). * p < 0.10, ** p < 0.05, *** p < 0.01 (two-sided).
