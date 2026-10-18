**Forecast combinations: out-of-sample Brier skill (%)**

|  | h = 1 | h = 3 | h = 6 | h = 12 |
|---|---:|---:|---:|---:|
| Equal-weight combination | 13.0\*\*\* | 7.2\*\*\* | 2.7\*\*\* | −0.7 |
| DMA, univariate logits, alpha = 0.95 | 24.0\*\*\* | 10.5\*\*\* | 0.6 | −4.8 |
| DMA, all models, alpha = 0.95 | 27.3\*\*\* | 13.2\*\*\* | 3.1 | −2.2 |
| DMA, univariate logits, alpha = 0.99 | 23.3\*\*\* | 10.6\*\*\* | 2.3 | −4.5 |
| DMA, all models, alpha = 0.99 | 23.4\*\*\* | 9.4\*\* | −0.9 | −4.5 |
| DMA, univariate logits, alpha = 1 | 22.1\*\*\* | 7.8\*\* | −0.9 | −6.3 |
| DMA, all models, alpha = 1 | 22.6\*\*\* | 6.8\* | −0.4 | −5.5 |

Notes: The equal-weight combination averages the univariate logits. Dynamic model averaging (Raftery, Kárný and Ettler, 2010) weights forecasts by their exponentially discounted predictive likelihood, using only outcomes known at the origin; alpha is the forgetting factor (alpha = 1 is recursive Bayesian model averaging). Stars: one-sided Diebold-Mariano test against the unconditional frequency, * p < 0.10, ** p < 0.05, *** p < 0.01.
