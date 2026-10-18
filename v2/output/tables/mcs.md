**Model confidence set p-values for out-of-sample Brier loss**

|  | h = 1 | h = 3 | h = 6 | h = 12 |
|---|---:|---:|---:|---:|
| Unconditional frequency | 0.001 | 0.343\* | 0.960\* | 0.990\* |
| Persistence (real-time state) | 0.833\* | 0.987\* | 0.972\* | 0.990\* |
| MS-AR(1) filtered probability | 0.225\* | 0.670\* | 0.956\* | 0.989\* |
| TVTP MS-AR(1) | 0.270\* | 0.729\* | 0.960\* | 0.925\* |
| Logit: dividend yield | 0.852\* | 1.000\* | 1.000\* | 1.000\* |
| Logit: 6 main predictors | 0.940\* | 1.000\* | 0.972\* | 0.990\* |
| Probit: 6 main predictors | 0.940\* | 1.000\* | 0.972\* | 0.969\* |
| Logit: 6 predictors + state | 0.940\* | 0.987\* | 0.960\* | 0.989\* |
| Elastic-net logit | 0.833\* | 0.770\* | 0.972\* | 0.990\* |
| Elastic-net logit, rich set | 0.607\* | 0.688\* | 0.960\* | 0.822\* |
| Gradient boosting | 0.852\* | 0.729\* | 0.952\* | 0.623\* |
| Gradient boosting, rich set | 0.959\* | 1.000\* | 0.430\* | 0.019 |
| Logit: all 11 predictors | 1.000\* | 1.000\* | 0.960\* | 0.632\* |
| Equal-weight combination | 0.147\* | 0.770\* | 0.972\* | 0.990\* |
| DMA: univariate logits | 0.940\* | 0.987\* | 0.972\* | 0.822\* |
| DMA: all models | 0.908\* | 0.843\* | 0.960\* | 0.925\* |

Notes: Hansen, Lunde and Nason (2011) T_max procedure on squared forecast errors, circular block bootstrap with 24-month blocks and 2,000 draws. A star marks models in the 90% model confidence set (p >= 0.10): the set of models that cannot be distinguished from the best at the 10% level.
