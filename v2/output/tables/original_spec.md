**Corrected archived specification: regime probability h months ahead on each predictor**

|  | OLS (percentage points) h = 1 | OLS (percentage points) h = 3 | OLS (percentage points) h = 6 | OLS (percentage points) h = 12 | Beta regression (logit link) h = 1 | Beta regression (logit link) h = 3 | Beta regression (logit link) h = 6 | Beta regression (logit link) h = 12 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Inflation (CPI, monthly) | 3.643\*\* | 4.065\* | 4.512\*\* | 4.267\*\*\* | 0.155\*\* | 0.200\*\* | 0.180\*\* | 0.171\*\*\* |
|  | (1.824) | (2.282) | (1.760) | (1.530) | (0.076) | (0.095) | (0.071) | (0.061) |
| R² / pseudo-R² | 0.019 | 0.024 | 0.029 | 0.026 | 0.020 | 0.027 | 0.029 | 0.030 |
| Change in 10-year Treasury yield | −0.066 | −1.349 | 3.575\*\*\* | 0.944 | 0.017 | −0.052 | 0.131\*\*\* | 0.036 |
|  | (1.329) | (1.100) | (1.026) | (0.815) | (0.060) | (0.040) | (0.043) | (0.028) |
| R² / pseudo-R² | 0.000 | 0.003 | 0.018 | 0.001 | 0.000 | 0.003 | 0.017 | 0.001 |
| Real 10-year bond return | −0.104 | 1.060 | −3.911\*\*\* | −1.386 | −0.018 | 0.039 | −0.145\*\*\* | −0.052\* |
|  | (1.412) | (1.303) | (1.212) | (0.909) | (0.060) | (0.048) | (0.049) | (0.031) |
| R² / pseudo-R² | 0.000 | 0.002 | 0.022 | 0.003 | 0.000 | 0.001 | 0.021 | 0.003 |
| Real dividend growth | −3.805\*\*\* | −3.337\*\* | −3.395\*\* | −2.808 | −0.122\*\*\* | −0.112\*\* | −0.115\*\* | −0.111 |
|  | (1.329) | (1.344) | (1.388) | (2.034) | (0.047) | (0.044) | (0.047) | (0.073) |
| R² / pseudo-R² | 0.021 | 0.016 | 0.017 | 0.011 | 0.017 | 0.014 | 0.015 | 0.015 |
| Real S&P 500 total return | −9.195\*\*\* | −6.111\*\*\* | −5.763\*\*\* | −1.306 | −0.411\*\*\* | −0.241\*\*\* | −0.218\*\*\* | −0.039 |
|  | (1.118) | (1.099) | (1.295) | (0.981) | (0.045) | (0.047) | (0.052) | (0.032) |
| R² / pseudo-R² | 0.121 | 0.053 | 0.048 | 0.002 | 0.107 | 0.049 | 0.043 | 0.002 |
| Real TR-scaled earnings growth | −0.859 | −1.595 | −2.083 | −2.630\*\* | −0.082 | −0.065 | −0.066 | −0.085\* |
|  | (2.498) | (1.782) | (1.660) | (1.309) | (0.123) | (0.073) | (0.062) | (0.049) |
| R² / pseudo-R² | 0.001 | 0.004 | 0.006 | 0.010 | 0.003 | 0.003 | 0.005 | 0.007 |
| Change in log TR-CAPE | −9.128\*\*\* | −6.109\*\*\* | −5.849\*\*\* | −1.507 | −0.407\*\*\* | −0.242\*\*\* | −0.222\*\*\* | −0.046 |
|  | (1.115) | (1.116) | (1.289) | (1.011) | (0.044) | (0.047) | (0.052) | (0.033) |
| R² / pseudo-R² | 0.120 | 0.053 | 0.049 | 0.003 | 0.106 | 0.049 | 0.045 | 0.002 |
| Observations | 766 | 764 | 761 | 755 | 766 | 764 | 761 | 755 |

Notes: Each cell is a separate univariate regression of the filtered bear-regime probability Q(t+h) from the MS-AR(1) model on the predictor at t, which is standardized (coefficients are per one standard deviation). OLS coefficients are in percentage points of probability. Newey-West standard errors in parentheses (7, 12 lags by horizon). Forecast origins 1960:02 to 2023:11 for h = 1; the sample shortens by h months. The beta-regression pseudo-R² is the squared correlation of the linear predictor with logit(Q). * p < 0.10, ** p < 0.05, *** p < 0.01 (two-sided). Q is computed with full-sample parameters, so these are in-sample associations, not forecasts.
