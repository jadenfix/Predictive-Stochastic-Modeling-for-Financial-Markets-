**Forecasting the regime probability: unrestricted versus intercept-only models**

|  | OLS h = 1 | OLS h = 3 | OLS h = 6 | OLS h = 12 | Beta regression h = 1 | Beta regression h = 3 | Beta regression h = 6 | Beta regression h = 12 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| *A. Archived design and archived formula (squared mean error ratio)* | | | | | | | | |
| CPI | 0.923 | 0.735 | 0.868 | 0.925 | 0.947 | 0.904 | 0.961 | 0.993 |
| Long-term rate | 0.981 | 0.975 | 1.008 | 0.997 | 0.992 | 0.981 | 1.002 | 0.996 |
| Real bond | 0.818 | 0.862 | 1.077 | 0.948 | 0.960 | 0.949 | 1.014 | 0.959 |
| Real dividend | 0.029 | 0.189 | 0.404 | 0.179 | 0.370 | 0.275 | 0.210 | 0.276 |
| Real total return | 0.006 | 0.921 | 0.942 | 0.982 | 0.564 | 1.019 | 0.956 | 1.021 |
| TR-scaled earnings | 0.363 | 0.474 | 0.759 | 1.365 | 0.819 | 0.837 | 0.894 | 1.222 |
| TR-CAPE | 0.822 | 1.016 | 1.018 | 1.027 | 0.706 | 1.010 | 1.004 | 1.013 |
| *B. Archived design, correct mean squared prediction error ratio* | | | | | | | | |
| CPI | 1.002 | 1.021 | 1.005 | 1.006 | 0.996 | 0.996 | 0.997 | 1.000 |
| Long-term rate | 0.989 | 1.009 | 1.002 | 1.001 | 0.991 | 1.002 | 1.001 | 1.002 |
| Real bond | 0.997 | 1.041 | 1.019 | 1.011 | 0.970 | 1.027 | 1.006 | 1.015 |
| Real dividend | 1.154 | 1.184 | 1.148 | 0.963 | 0.951 | 0.924 | 0.883 | 0.806 |
| Real total return | 1.539 | 1.010 | 1.003 | 1.002 | 0.770 | 1.001 | 1.000 | 0.999 |
| TR-scaled earnings | 0.862 | 0.879 | 0.946 | 0.965 | 0.799 | 0.861 | 0.945 | 1.003 |
| TR-CAPE | 0.720 | 0.994 | 0.998 | 0.990 | 0.664 | 0.996 | 1.000 | 0.994 |
| *C. Corrected design: past-only predictors, true h-month lead, expanding window* | | | | | | | | |
| Inflation (CPI, monthly) | 1.003 | 0.951\*\* | 0.918\*\* | 0.939\*\*\* | 0.976\* | 0.930\*\*\* | 0.920\*\*\* | 0.935\*\*\* |
| Change in 10-year Treasury yield | 1.002 | 1.000 | 0.985 | 1.005 | 1.004 | 0.998 | 0.990 | 1.003 |
| Real 10-year bond return | 1.007 | 1.003 | 0.987 | 1.012 | 1.008 | 0.997 | 0.999 | 1.010 |
| Real dividend growth | 0.953\*\*\* | 0.965\*\* | 0.935\*\*\* | 0.941\*\* | 0.934\*\*\* | 0.943\*\*\* | 0.930\*\*\* | 0.935\*\*\* |
| Real S&P 500 total return | 0.868\*\*\* | 0.931\*\*\* | 0.985\* | 1.005 | 0.844\*\*\* | 0.936\*\*\* | 0.974\*\* | 1.000 |
| Real TR-scaled earnings growth | 0.999 | 1.007 | 1.029 | 1.056 | 0.997 | 1.004 | 1.013 | 1.025 |
| Change in log TR-CAPE | 0.865\*\* | 0.928\*\*\* | 0.983\*\* | 1.009 | 0.851\*\*\* | 0.939\*\*\* | 0.978\*\* | 1.003 |
| Benchmark: regime probability at t | 0.476\*\*\* | 0.872\*\*\* | 1.032 | 1.025 | 0.483\*\*\* | 0.853\*\*\* | 0.985 | 1.004 |

Notes: Entries are ratios of the unrestricted model's loss to the intercept-only model's loss; values below one favor the predictor. Panels A and B re-run the archived code path (target Q(t-k), leaked regime model, single 80/20 split with the test period starting in 2011). Panel A uses the archived formula (mean error)² / (mean error)², which is not a mean squared error. Panel C forecasts Q(t+h) from predictors observable at t with expanding-window refits, origins 2011:04 to 2023:11 for h = 1. The benchmark row uses Q(t) itself as the predictor. Stars in Panel C mark Clark-West (2007) tests of equal accuracy in nested models where the unrestricted model is better: * p < 0.10, ** p < 0.05, *** p < 0.01.
