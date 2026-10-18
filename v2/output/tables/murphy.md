**Murphy decomposition of out-of-sample Brier scores (x 100)**

|  | h = 1 Rel. | h = 1 Res. | h = 3 Rel. | h = 3 Res. | h = 6 Rel. | h = 6 Res. | h = 12 Rel. | h = 12 Res. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Unconditional frequency | 2.77 | 0.10 | 2.72 | 0.02 | 2.67 | 0.00 | 2.54 | 0.00 |
| Persistence (real-time state) | 2.13 | 3.22 | 2.10 | 1.66 | 2.71 | 1.02 | 2.68 | 0.08 |
| MS-AR(1) filtered probability | 2.40 | 1.64 | 2.73 | 0.61 | 3.03 | 0.13 | 2.89 | 0.10 |
| TVTP MS-AR(1) | 4.23 | 3.00 | 3.63 | 1.41 | 4.12 | 1.05 | 4.07 | 0.64 |
| Logit: dividend yield | 1.10 | 2.33 | 1.21 | 1.42 | 1.77 | 0.93 | 2.74 | 0.62 |
| Logit: 6 main predictors | 0.81 | 3.09 | 1.57 | 1.48 | 2.30 | 0.29 | 3.21 | 0.42 |
| Logit: 6 predictors + state | 0.91 | 3.14 | 1.56 | 1.25 | 2.85 | 0.43 | 3.67 | 0.81 |
| Elastic-net logit | 1.46 | 2.83 | 3.60 | 2.67 | 3.74 | 1.70 | 4.22 | 1.26 |
| Elastic-net logit, rich set | 2.56 | 3.47 | 3.75 | 2.01 | 4.02 | 1.18 | 5.15 | 0.83 |
| Gradient boosting | 2.32 | 3.52 | 3.53 | 1.50 | 3.88 | 0.58 | 5.71 | 0.51 |
| Gradient boosting, rich set | 1.08 | 3.76 | 2.15 | 2.20 | 5.14 | 0.34 | 9.35 | 0.99 |
| Equal-weight combination | 2.96 | 2.60 | 2.29 | 0.73 | 2.31 | 0.09 | 2.76 | 0.16 |
| DMA: all models | 0.97 | 2.99 | 1.94 | 1.38 | 3.24 | 0.43 | 4.86 | 1.60 |
| Uncertainty (all models) | 17.07 |  | 17.10 |  | 17.14 |  | 17.24 |  |

Notes: Brier = reliability - resolution + uncertainty (Murphy, 1973), with forecasts grouped into 10 equal-width bins. Reliability (lower is better) measures miscalibration; resolution (higher is better) measures how much the observed bear frequency varies across forecast bins. The remainder due to variation of forecasts within bins is at most 0.44 (x 100) in absolute value.
