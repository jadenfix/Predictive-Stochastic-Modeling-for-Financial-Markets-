**Out-of-sample accuracy of real-time bear-market forecasts, targets 1960:02-2023:12**

|  | Brier | Skill (%) | Log loss | AUC | p vs uncond. | p vs persist. |
|---|---:|---:|---:|---:|---:|---:|
| *h = 1 (767 forecasts, bear share 22.7%)* | | | | | | |
| Unconditional frequency | 0.198 | 0.0 | 0.587 | 0.563 |  |  |
| Persistence (real-time state) | 0.161 | 18.9 | 0.502 | 0.688 | 0.000 |  |
| MS-AR(1) filtered probability | 0.176 | 10.9 | 0.537 | 0.702 | 0.000 | 0.987 |
| Logit: dividend yield | 0.165 | 16.5 | 0.527 | 0.627 | 0.000 | 0.680 |
| Logit: all predictors | 0.157 | 20.8 | 0.488 | 0.780 | 0.000 | 0.316 |
| Probit: all predictors | 0.155 | 21.5 | 0.487 | 0.779 | 0.000 | 0.256 |
| Logit: all predictors + state | 0.159 | 19.9 | 0.497 | 0.772 | 0.000 | 0.387 |
| *h = 3 (765 forecasts, bear share 22.7%)* | | | | | | |
| Unconditional frequency | 0.199 | 0.0 | 0.589 | 0.547 |  |  |
| Persistence (real-time state) | 0.176 | 11.5 | 0.537 | 0.636 | 0.001 |  |
| MS-AR(1) filtered probability | 0.193 | 3.0 | 0.575 | 0.618 | 0.182 | 0.994 |
| Logit: dividend yield | 0.175 | 12.3 | 0.545 | 0.586 | 0.001 | 0.433 |
| Logit: all predictors | 0.187 | 6.2 | 0.563 | 0.675 | 0.134 | 0.878 |
| Probit: all predictors | 0.185 | 7.0 | 0.561 | 0.676 | 0.099 | 0.838 |
| Logit: all predictors + state | 0.189 | 5.1 | 0.573 | 0.667 | 0.197 | 0.933 |
| *h = 6 (762 forecasts, bear share 22.8%)* | | | | | | |
| Unconditional frequency | 0.200 | 0.0 | 0.592 | 0.528 |  |  |
| Persistence (real-time state) | 0.190 | 4.9 | 0.568 | 0.571 | 0.094 |  |
| MS-AR(1) filtered probability | 0.205 | −2.5 | 0.602 | 0.530 | 0.737 | 0.986 |
| Logit: dividend yield | 0.185 | 7.9 | 0.567 | 0.541 | 0.051 | 0.287 |
| Logit: all predictors | 0.214 | −6.9 | 0.623 | 0.549 | 0.843 | 0.981 |
| Probit: all predictors | 0.213 | −6.3 | 0.621 | 0.548 | 0.826 | 0.977 |
| Logit: all predictors + state | 0.218 | −8.6 | 0.634 | 0.537 | 0.879 | 0.992 |
| *h = 12 (756 forecasts, bear share 23.0%)* | | | | | | |
| Unconditional frequency | 0.202 | 0.0 | 0.595 | 0.513 |  |  |
| Persistence (real-time state) | 0.201 | 0.8 | 0.591 | 0.513 | 0.331 |  |
| MS-AR(1) filtered probability | 0.209 | −3.5 | 0.609 | 0.463 | 0.847 | 0.959 |
| Logit: dividend yield | 0.198 | 1.9 | 0.594 | 0.488 | 0.353 | 0.405 |
| Logit: all predictors | 0.224 | −11.1 | 0.654 | 0.417 | 0.911 | 0.939 |
| Probit: all predictors | 0.226 | −11.8 | 0.659 | 0.411 | 0.924 | 0.949 |
| Logit: all predictors + state | 0.227 | −12.3 | 0.660 | 0.407 | 0.929 | 0.952 |

Notes: Expanding-window forecasts made at each month-end origin using only data available then: predictors with publication lags, bear dates obtained from prices through the origin, and Markov-switching parameters re-estimated each January (filtered probabilities only). Lower Brier score and log loss are better; skill is the percentage reduction in Brier score relative to the unconditional frequency. Log loss truncates probabilities to [0.001, 0.999]. The p-values are one-sided Diebold-Mariano tests (Harvey-Leybourne-Newbold correction, Bartlett HAC variance) of equal Brier score against the alternative that the model is more accurate than the baseline.
