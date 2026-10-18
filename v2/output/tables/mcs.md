**Model confidence set p-values for out-of-sample Brier loss**

|  | h = 1 | h = 3 | h = 6 | h = 12 |
|---|---:|---:|---:|---:|
| Unconditional frequency | 0.002 | 0.370\* | 0.981\* | 0.997\* |
| Persistence (real-time state) | 0.788\* | 0.990\* | 0.992\* | 0.997\* |
| MS-AR(1) filtered probability | 0.204\* | 0.684\* | 0.972\* | 0.993\* |
| TVTP MS-AR(1) | 0.234\* | 0.750\* | 0.981\* | 0.947\* |
| Logit: dividend yield | 0.806\* | 1.000\* | 1.000\* | 1.000\* |
| Logit: 6 main predictors | 0.940\* | 1.000\* | 0.992\* | 0.997\* |
| Probit: 6 main predictors | 0.940\* | 1.000\* | 0.992\* | 0.976\* |
| Logit: 6 predictors + state | 0.940\* | 0.990\* | 0.981\* | 0.993\* |
| Elastic-net logit | 0.788\* | 0.781\* | 0.992\* | 0.997\* |
| Elastic-net logit, rich set | 0.546\* | 0.722\* | 0.981\* | 0.837\* |
| Gradient boosting | 0.806\* | 0.750\* | 0.968\* | 0.638\* |
| Gradient boosting, rich set | 0.959\* | 1.000\* | 0.464\* | 0.021 |
| Logit: all 11 predictors | 1.000\* | 1.000\* | 0.981\* | 0.646\* |
| Equal-weight combination | 0.124\* | 0.781\* | 0.992\* | 0.997\* |
| DMA: univariate logits | 0.940\* | 0.990\* | 0.992\* | 0.837\* |
| DMA: all models | 0.908\* | 0.860\* | 0.981\* | 0.947\* |

Notes: Hansen, Lunde and Nason (2011) T_max procedure on squared forecast errors, circular block bootstrap with 24-month blocks and 2,000 draws. A star marks models in the 90% model confidence set (p >= 0.10): the set of models that cannot be distinguished from the best at the 10% level.
