**Out-of-sample accuracy of real-time bear-market forecasts, targets 1960:02-2026:06**

|  | Brier | Skill (%) | Log loss | AUC | p vs uncond. | p vs persist. | p vs persist., 23 lags |
|---|---:|---:|---:|---:|---:|---:|---:|
| *h = 1 (797 forecasts, bear share 21.8%)* | | | | | | | |
| Unconditional frequency | 0.196 | 0.0 | 0.583 | 0.585 |  |  |  |
| Persistence (real-time state) | 0.161 | 17.6 | 0.506 | 0.707 | <0.001 |  |  |
| MS-AR(1) filtered probability | 0.178 | 9.1 | 0.542 | 0.713 | <0.001 | 0.999 | 0.938 |
| Logit: dividend yield | 0.160 | 18.3 | 0.509 | 0.646 | <0.001 | 0.441 | 0.475 |
| Logit: 6 main predictors | 0.146 | 25.4 | 0.460 | 0.773 | <0.001 | 0.019 | 0.172 |
| Probit: 6 main predictors | 0.146 | 25.3 | 0.463 | 0.772 | <0.001 | 0.021 | 0.177 |
| Logit: 6 predictors + state | 0.148 | 24.6 | 0.464 | 0.772 | <0.001 | 0.022 | 0.171 |
| *h = 3 (795 forecasts, bear share 21.9%)* | | | | | | | |
| Unconditional frequency | 0.196 | 0.0 | 0.584 | 0.569 |  |  |  |
| Persistence (real-time state) | 0.177 | 10.0 | 0.540 | 0.651 | <0.001 |  |  |
| MS-AR(1) filtered probability | 0.191 | 2.7 | 0.570 | 0.635 | 0.137 | 0.999 | 0.967 |
| Logit: dividend yield | 0.170 | 13.4 | 0.529 | 0.607 | <0.001 | 0.202 | 0.338 |
| Logit: 6 main predictors | 0.172 | 12.4 | 0.528 | 0.671 | 0.005 | 0.290 | 0.385 |
| Probit: 6 main predictors | 0.172 | 12.4 | 0.531 | 0.672 | 0.006 | 0.295 | 0.388 |
| Logit: 6 predictors + state | 0.174 | 11.2 | 0.534 | 0.667 | 0.013 | 0.383 | 0.436 |
| *h = 6 (792 forecasts, bear share 22.0%)* | | | | | | | |
| Unconditional frequency | 0.197 | 0.0 | 0.584 | 0.550 |  |  |  |
| Persistence (real-time state) | 0.189 | 3.9 | 0.567 | 0.586 | 0.028 |  |  |
| MS-AR(1) filtered probability | 0.199 | −1.4 | 0.589 | 0.556 | 0.696 | 0.989 | 0.965 |
| Logit: dividend yield | 0.180 | 8.2 | 0.552 | 0.558 | 0.020 | 0.146 | 0.245 |
| Logit: 6 main predictors | 0.193 | 1.7 | 0.577 | 0.550 | 0.388 | 0.660 | 0.606 |
| Probit: 6 main predictors | 0.194 | 1.3 | 0.581 | 0.549 | 0.412 | 0.682 | 0.621 |
| Logit: 6 predictors + state | 0.196 | 0.1 | 0.584 | 0.544 | 0.495 | 0.761 | 0.680 |
| *h = 12 (786 forecasts, bear share 22.1%)* | | | | | | | |
| Unconditional frequency | 0.197 | 0.0 | 0.584 | 0.535 |  |  |  |
| Persistence (real-time state) | 0.197 | −0.2 | 0.585 | 0.498 | 0.625 |  |  |
| MS-AR(1) filtered probability | 0.200 | −1.8 | 0.591 | 0.496 | 0.827 | 0.820 | 0.797 |
| Logit: dividend yield | 0.194 | 1.4 | 0.579 | 0.489 | 0.353 | 0.334 | 0.360 |
| Logit: 6 main predictors | 0.203 | −3.2 | 0.605 | 0.428 | 0.679 | 0.673 | 0.645 |
| Probit: 6 main predictors | 0.205 | −4.3 | 0.611 | 0.419 | 0.726 | 0.721 | 0.686 |
| Logit: 6 predictors + state | 0.204 | −3.8 | 0.609 | 0.423 | 0.706 | 0.700 | 0.669 |

Notes: Expanding-window forecasts made at each month-end origin using only data available then: predictors with publication lags, bear dates obtained from prices through the origin, and models re-estimated on that information. Lower Brier score and log loss are better; skill is the percentage reduction in Brier score relative to the unconditional frequency. Log loss truncates probabilities to [0.001, 0.999]. The p-values are one-sided Diebold-Mariano tests (Harvey-Leybourne-Newbold correction) of equal Brier score against the alternative that the model is more accurate than the baseline, with the conventional max(h - 1, 1) Bartlett lags; the last column uses 23 lags, which allows for the strong autocorrelation of loss differences during long bear markets. Markov-switching parameters are re-estimated each January (filtered probabilities only).
