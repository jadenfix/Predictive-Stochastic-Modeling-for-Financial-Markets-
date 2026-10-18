**Block-bootstrap uncertainty of out-of-sample Brier skill**

|  | Skill (%) | 90% interval | Gain over persistence (pp), 90% interval | Share of draws beating persistence |
|---|---:|---:|---:|---:|
| *h = 1* | | | | |
| Persistence (real-time state) | 17.6 | [8.2, 26.5] |  |  |
| MS-AR(1) filtered probability | 9.1 | [3.0, 15.6] | [−17.7, 1.0] | 0.07 |
| TVTP MS-AR(1) | 8.0 | [−1.4, 17.0] | [−19.5, −0.3] | 0.04 |
| Logit: dividend yield | 18.3 | [3.0, 34.4] | [−15.9, 17.3] | 0.57 |
| Logit: 6 main predictors | 25.4 | [12.2, 39.4] | [−5.8, 20.9] | 0.84 |
| Elastic-net logit, rich set | 17.3 | [2.6, 31.5] | [−15.2, 13.7] | 0.52 |
| Gradient boosting, rich set | 26.8 | [14.0, 40.1] | [−4.5, 22.9] | 0.87 |
| DMA: all models | 23.4 | [11.6, 35.5] | [−3.4, 15.5] | 0.86 |
| *h = 3* | | | | |
| Persistence (real-time state) | 10.0 | [3.3, 17.1] |  |  |
| MS-AR(1) filtered probability | 2.7 | [−2.9, 9.0] | [−13.9, −0.8] | 0.03 |
| TVTP MS-AR(1) | 2.8 | [−5.7, 11.0] | [−15.7, 0.0] | 0.05 |
| Logit: dividend yield | 13.4 | [0.9, 26.7] | [−9.8, 16.5] | 0.69 |
| Logit: 6 main predictors | 12.4 | [−1.8, 27.2] | [−10.6, 15.7] | 0.64 |
| Elastic-net logit, rich set | 3.9 | [−10.4, 18.2] | [−19.7, 7.7] | 0.24 |
| Gradient boosting, rich set | 13.0 | [0.0, 27.9] | [−10.0, 16.6] | 0.65 |
| DMA: all models | 9.4 | [−2.3, 22.2] | [−9.8, 9.0] | 0.48 |
| *h = 6* | | | | |
| Persistence (real-time state) | 3.9 | [−1.0, 8.6] |  |  |
| MS-AR(1) filtered probability | −1.4 | [−6.7, 4.4] | [−10.0, −0.9] | 0.03 |
| TVTP MS-AR(1) | −1.3 | [−8.4, 5.6] | [−11.2, 0.5] | 0.07 |
| Logit: dividend yield | 8.2 | [−2.5, 19.1] | [−6.3, 14.2] | 0.76 |
| Logit: 6 main predictors | 1.7 | [−12.2, 16.1] | [−15.1, 10.9] | 0.41 |
| Elastic-net logit, rich set | −1.4 | [−13.6, 10.0] | [−17.3, 5.8] | 0.24 |
| Gradient boosting, rich set | −12.3 | [−28.5, 3.2] | [−31.7, −1.8] | 0.03 |
| DMA: all models | −0.9 | [−10.7, 9.2] | [−12.9, 3.2] | 0.16 |
| *h = 12* | | | | |
| Persistence (real-time state) | −0.2 | [−1.0, 0.7] |  |  |
| MS-AR(1) filtered probability | −1.8 | [−5.0, 1.4] | [−4.7, 1.4] | 0.18 |
| TVTP MS-AR(1) | −3.9 | [−9.0, 1.2] | [−8.7, 1.0] | 0.09 |
| Logit: dividend yield | 1.4 | [−5.9, 9.0] | [−5.6, 9.0] | 0.66 |
| Logit: 6 main predictors | −3.2 | [−16.1, 10.5] | [−15.8, 10.4] | 0.36 |
| Elastic-net logit, rich set | −8.6 | [−20.5, 2.5] | [−20.5, 2.5] | 0.11 |
| Gradient boosting, rich set | −32.1 | [−47.3, −16.3] | [−47.1, −16.2] | 0.00 |
| DMA: all models | −4.5 | [−13.9, 4.7] | [−13.7, 4.5] | 0.24 |

Notes: Circular moving-block bootstrap of target months with blocks of 24 months and 2,000 replications, resampling all models jointly. Intervals are 5th and 95th percentiles. The gain over persistence is the model's skill minus the skill of persistence in the same draw.
