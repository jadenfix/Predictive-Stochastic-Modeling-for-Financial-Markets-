**Block-bootstrap uncertainty of out-of-sample Brier skill**

|  | Skill (%) | 90% interval | Gain over persistence (pp), 90% interval | Share of draws beating persistence |
|---|---:|---:|---:|---:|
| *h = 1* | | | | |
| Persistence (real-time state) | 18.9 | [6.6, 30.7] |  |  |
| MS-AR(1) filtered probability | 10.9 | [3.0, 19.6] | [−19.6, 3.8] | 0.14 |
| Logit: dividend yield | 16.5 | [0.5, 33.7] | [−20.9, 16.3] | 0.45 |
| Logit: all predictors | 20.8 | [7.3, 35.4] | [−11.7, 15.4] | 0.61 |
| Probit: all predictors | 21.5 | [8.2, 35.8] | [−11.0, 16.1] | 0.65 |
| Logit: all predictors + state | 19.9 | [5.3, 35.2] | [−10.4, 12.6] | 0.58 |
| *h = 3* | | | | |
| Persistence (real-time state) | 11.5 | [1.3, 22.1] |  |  |
| MS-AR(1) filtered probability | 3.0 | [−4.6, 11.6] | [−17.1, 0.1] | 0.05 |
| Logit: dividend yield | 12.3 | [−2.5, 27.7] | [−16.2, 16.0] | 0.55 |
| Logit: all predictors | 6.2 | [−9.1, 22.6] | [−19.4, 7.8] | 0.27 |
| Probit: all predictors | 7.0 | [−8.0, 23.3] | [−18.6, 8.7] | 0.31 |
| Logit: all predictors + state | 5.1 | [−11.1, 22.1] | [−18.9, 5.8] | 0.20 |
| *h = 6* | | | | |
| Persistence (real-time state) | 4.9 | [−3.2, 12.5] |  |  |
| MS-AR(1) filtered probability | −2.5 | [−10.3, 5.3] | [−14.8, −0.5] | 0.03 |
| Logit: dividend yield | 7.9 | [−4.7, 21.6] | [−9.2, 15.3] | 0.67 |
| Logit: all predictors | −6.9 | [−22.8, 8.7] | [−25.1, 1.5] | 0.07 |
| Probit: all predictors | −6.3 | [−21.7, 9.2] | [−24.5, 2.0] | 0.08 |
| Logit: all predictors + state | −8.6 | [−24.8, 7.7] | [−26.3, −0.9] | 0.04 |
| *h = 12* | | | | |
| Persistence (real-time state) | 0.8 | [−2.3, 4.0] |  |  |
| MS-AR(1) filtered probability | −3.5 | [−9.0, 2.3] | [−8.2, −0.3] | 0.03 |
| Logit: dividend yield | 1.9 | [−8.1, 11.8] | [−8.0, 9.9] | 0.60 |
| Logit: all predictors | −11.1 | [−25.6, 4.7] | [−25.2, 2.3] | 0.08 |
| Probit: all predictors | −11.8 | [−26.6, 4.1] | [−26.1, 1.6] | 0.07 |
| Logit: all predictors + state | −12.3 | [−27.3, 3.7] | [−26.8, 1.4] | 0.07 |

Notes: Circular moving-block bootstrap of target months with blocks of 24 months and 2,000 replications, resampling all models jointly. Intervals are 5th and 95th percentiles. The gain over persistence is the model's skill minus the skill of persistence in the same draw.
