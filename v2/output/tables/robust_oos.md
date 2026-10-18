**Robustness of out-of-sample Brier skill (%) to dating, estimation window and evaluation period**

|  | h = 1 | h = 3 | h = 6 | h = 12 |
|---|---:|---:|---:|---:|
| *Persistence* | | | | |
| Main (real prices, 20%, expanding) | 18.9\*\*\* | 11.5\*\*\* | 4.9\* | 0.8 |
| Dating threshold 15% | 24.6\*\*\* | 13.7\*\*\* | 6.6\*\* | 0.1 |
| Dating threshold 25% | 17.1\*\*\* | 10.0\*\*\* | 3.6 | −1.3 |
| Nominal prices, 20% | 15.8\*\*\* | 9.9\*\*\* | 4.8\* | 0.9 |
| Rolling 30-year window | 10.6\*\* | 2.9 | −3.3 | −5.8 |
| Targets 1960-1989 | 7.9\* | 2.1 | −2.3 | −1.8 |
| Targets 1990-2023 | 32.1\*\*\* | 22.6\*\*\* | 13.5\*\*\* | 3.7\* |
| Excluding 2007-2009 crisis | 20.0\*\*\* | 12.6\*\*\* | 6.1\* | 1.3 |
| *MS-AR(1)* | | | | |
| Main (real prices, 20%, expanding) | 10.9\*\*\* | 3.0 | −2.5 | −3.5 |
| Dating threshold 15% | 10.1\*\*\* | 2.3 | −2.5 | −2.6 |
| Dating threshold 25% | 11.1\*\*\* | 4.9\* | −0.3 | −2.6 |
| Nominal prices, 20% | 16.9\*\*\* | 8.0\*\* | −0.5 | −3.1 |
| Rolling 30-year window | 7.6\*\* | −0.7 | −4.5 | −5.1 |
| Targets 1960-1989 | 1.9 | −6.4 | −9.3 | −7.7 |
| Targets 1990-2023 | 21.8\*\*\* | 14.3\*\*\* | 5.6 | 1.5 |
| Excluding 2007-2009 crisis | 10.7\*\*\* | 2.7 | −2.2 | −3.3 |
| *Logit: dividend yield* | | | | |
| Main (real prices, 20%, expanding) | 16.5\*\*\* | 12.3\*\*\* | 7.9\* | 1.9 |
| Dating threshold 15% | 12.4\*\*\* | 8.4\*\*\* | 4.6 | −2.6 |
| Dating threshold 25% | 11.0\*\*\* | 7.8\*\* | 3.9 | −0.8 |
| Nominal prices, 20% | 8.2\*\* | 5.2\* | 1.4 | −4.8 |
| Rolling 30-year window | 3.7\* | 0.3 | −1.5 | −6.4 |
| Targets 1960-1989 | 11.7\*\*\* | 6.6\*\* | 2.4 | −2.9 |
| Targets 1990-2023 | 22.3\*\*\* | 19.1\*\*\* | 14.4\* | 7.4 |
| Excluding 2007-2009 crisis | 19.8\*\*\* | 15.2\*\*\* | 10.4\*\* | 3.6 |
| *Logit: all predictors* | | | | |
| Main (real prices, 20%, expanding) | 20.8\*\*\* | 6.2 | −6.9 | −11.1 |
| Dating threshold 15% | 23.1\*\*\* | 7.3\* | −5.4 | −9.4 |
| Dating threshold 25% | 26.8\*\*\* | 14.8\*\*\* | 2.3 | −9.7 |
| Nominal prices, 20% | 14.0\*\*\* | 1.0 | −11.8 | −15.0 |
| Rolling 30-year window | 21.0\*\*\* | −2.1 | −24.8 | −48.3 |
| Targets 1960-1989 | 10.0\* | −7.0 | −21.7 | −27.8 |
| Targets 1990-2023 | 33.9\*\*\* | 21.8\*\*\* | 10.6 | 8.3 |
| Excluding 2007-2009 crisis | 22.2\*\*\* | 7.6\* | −4.9 | −9.2 |

Notes: Skill is the percentage reduction in Brier score relative to the unconditional frequency estimated in the same variant. Each dating variant re-dates bear markets (symmetric thresholds) and re-runs the complete real-time exercise, including the vintage labels and the real-time state. The rolling variant estimates every model on the most recent 30 years of training data. The evaluation-period rows score the main forecasts on subsets of target months; the crisis excluded is 2007:10-2009:06. Stars: one-sided Diebold-Mariano test against the unconditional frequency, * p < 0.10, ** p < 0.05, *** p < 0.01.
