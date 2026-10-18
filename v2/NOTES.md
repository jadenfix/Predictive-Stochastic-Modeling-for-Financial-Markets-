# Notes on the original thesis and the v2 rebuild

These notes record what the award version (February 2025 PDF and `code.R`) did, what was
wrong or unclear, and what v2 changes and why. Figures quoted here for the original come from
the PDF; every v2 number lives in `v2/output/` and is produced by `v2/thesis.py`.

## 1. What the original did

**Research question.** Do financial and macroeconomic indicators forecast bear-market regimes
in the S&P 500? The paper frames a rejection of "beta = 0" as evidence against the semi-strong
efficient market hypothesis.

**Data.** `one45.csv`, an extract of Shiller's "U.S. Stock Markets and CAPE Ratio" workbook,
monthly 1900:01-2024:03 plus one trailing footnote row. `code.R` keeps rows 720-1488
(1959:12-2023:12), first-differences seven predictors and drops the first row, giving 768
months labeled 1960:01-2023:12.

Columns (recovered from the values; several names are misleading):

| Column | Content |
|---|---|
| `spprice` | S&P Composite, monthly average of daily closes (nominal) |
| `dividend`, `earnings` | Annualized dividends and earnings per share (nominal, interpolated from quarterly, annual before 1926) |
| `infl` | CPI **level**, not an inflation rate |
| `lrir10` | 10-year Treasury yield, percent |
| `realprice` | Real price (deflated by same-month CPI) |
| `realpricelag`..`realpricelag4` | **Leads**: the real price 1-4 months *ahead* |
| `realdividend`, `realearnings`, `realtrscaledearnings` | Real dividends, earnings, total-return-scaled earnings |
| `realtotalreturn` | Real total-return price index |
| `CAPE`, `TRCAPE`, `excessCAPE` | CAPE, total-return CAPE, excess CAPE yield |
| `bond`, `realbond` | Gross monthly 10-year bond return; real bond total-return index |
| `dp`, `ep` | Price/dividend and price/earnings ratios (names are inverted) |
| `dy`, `de` | Dividend yield (%), payout ratio (%) |

**Transforms in `code.R`.** `realprice` and the four "lag" columns become `100 * log(level)`.
`infl`, `lrir10`, `realdividend`, `realtrscaledearnings`, `TRCAPE`, `realbond` and
`realtotalreturn` are first-differenced in levels (so "Total Return" is the monthly change in a
total-return index measured in index points, and "CPI" is the change in the CPI level).

**Bear-market definition.** There is no explicit dating rule. A "bear market" is regime 1 of a
two-state Markov-switching model, and the dependent variable of the predictive regressions is its
filtered probability `Q`.

**Regime model.** `msmFit(lm(realprice ~ realpricelag), k = 2, sw = rep(TRUE, 3))` (MSwM): a
regression of 100 ln P_t on the "lag" column with switching intercept, slope and variance. The
paper writes it as `r_t = alpha_S + mu_S + eps_S` with `r_t = 100 ln(price)`, and reports the
transition matrix (bear stay 0.833, bull stay 0.945). Lags 2-4 were also fit; model 1 was kept.

**Predictive regressions.** For each of seven predictors and k in {1, 2, 3, 6, 12, 18, 24},
univariate OLS (`lm`) and beta regression (`betareg`) of the "k months ahead" probability on the
differenced predictor, classical standard errors. Tables were produced with stargazer and pasted
into the PDF as images.

**Out-of-sample tests.** A single 80/20 split (training 1960 to early 2011, test 2011-2023) and a
"back-casting" split (reverse order). Each univariate model is compared with an intercept-only
model through an "MSPE ratio"; ratios below one are reported as forecasting gains (for example
0.004 for dividends at k = 1).

**Conclusions claimed.** Dividend "yields" and total-return-scaled earnings, inflation and
long-term rates "robustly forecast" bear-market probabilities, and the unrestricted models
"significantly outperform" at short horizons.

## 2. What was wrong or unclear

1. **Look-ahead in the regime model.** `realpricelag` is the next month's price (1,490 of 1,490
   comparable rows match P_{t+1}; 3 match P_{t-1}; see `output/results/archived_lead_audit.csv`).
   Filtered probabilities from a regression on P_{t+1} use future information.
2. **"Ahead" targets point backwards.** `combined_df$ahead1 <- lag(Q, 1)` runs after
   `library(dplyr)`, so `dplyr::lag` shifts Q *back*: the regressions explain Q_{t-k} with the
   predictor at t. This is confirmed by replication: regressing Q_{t-k} on Δx_t reproduces the
   archived table (correlation 1.000 across 28 coefficients and 42 R² values), while Q_{t+k}
   does not.
3. **The "MSPE ratio" is not an MSPE ratio.** The code computes
   `mean(e_u)^2 / mean(e_r)^2`, a ratio of squared biases. On the same design the true MSPE ratio
   for dividends at k = 1 is above one (the predictor makes forecasts worse).
4. **Variable labels do not match the code.** "Dividend yield" in the text is the first
   difference of real dividends; "Inflation (CPI)" is the change in the CPI level; "Total return"
   is the change in an index level, whose coefficients print as 0.00000.
5. **Publication lags are ignored.** CPI for month t is published in month t+1; Shiller's
   dividends and earnings are interpolated between quarterly (pre-1926: annual) reports.
6. **Smoothed vs filtered.** The archived code uses filtered probabilities, but the paper
   attributes them to "the Kalman filter"; the relevant algorithm is the Hamilton filter.
   Smoothed probabilities must not be used as forecasts (v2 uses them only for description).
7. **Inference.** Classical OLS standard errors on a highly persistent target with overlapping
   horizons overstate significance; no correction for serial correlation was applied.
8. **Evaluation.** One split, no recursive refits, no test of equal accuracy, no comparison with
   persistence, and the regime parameters were estimated on the full sample.
9. **Smaller issues.** The paper says the beta regression forces figures with `[H]` (a LaTeX
   note left in the text); the "back-casting" mean (`meanMSPEbc`) re-uses the forecasting ratios;
   the `ts()` objects label the 768 rows 1960:01-2023:12 while the R rows start a month earlier;
   the reference "Chen, N.-K. (2008)" for the *Journal of Banking & Finance* 33(2) article is
   Chen, S.-S. (Shiu-Sheng Chen) (2009), doi:10.1016/j.jbankfin.2008.07.013 (online 2008, issue
   February 2009), and is cited that way in v2; "Hammerschmidt" is spelled Hammerschmid.


## 3. What v2 changes and why

| Area | v2 choice | Reason |
|---|---|---|
| Data | Shiller's current workbook (`ie_data.xls`, sheet "Data"), pinned by SHA-256, January 1871 to June 2026 | Primary source, longer sample, reproducible vintage |
| Timing | Forecast origin = end of month t; CPI lagged 1 month, dividends and earnings 6 months; real values deflated by CPI_{t-1} | Every predictor at t must be observable at t |
| Leaked columns | `realpricelag*` from `one45.csv` are read only by the replication of the award version | Remove look-ahead |
| Predictors | Growth rates instead of differenced index levels; standardized coefficients | Interpretable, scale-free |
| Bear definition | Rule-based dating on the real price: a 20% fall from a peak starts a bear market (backdated to the month after the peak), a 20% rise from the trough ends it | Observable target independent of any model; testable |
| Regime models | statsmodels MS and MS-AR(1) on real returns, deterministic starting-value grid, bear = lower-mean regime; TVTP MS-AR(1) with lagged predictors | Standard Hamilton (1989) specification; Diebold, Lee and Weinbach (1994) and Filardo (1994) extension |
| Probabilities | Filtered for anything used as a forecast; smoothed only in a labeled retrospective figure | Smoothed probabilities condition on the future |
| Regressions | Award-version OLS and beta specs with the forward target Q_{t+h} and Newey-West errors; logit and probit for the dated indicator | Correct direction and inference; natural binary benchmark |
| Out of sample | Monthly expanding-window refits from 1960:01; vintage bear labels from prices through the origin; regime and ML models re-estimated each January | Real-time evaluation with no future information |
| New forecasts | Elastic-net logit and gradient boosting (hyperparameters by time-series validation inside each window), equal-weight combination and dynamic model averaging | Modern methods under the same real-time protocol |
| Baselines | Unconditional frequency and persistence of the real-time state | Any useful model must beat both |
| Inference | Brier, log loss, AUC, calibration, Murphy decomposition; Diebold-Mariano with conventional and 23-lag windows; Hansen SPA and White Reality Check; model confidence set; Giacomini-White; block bootstrap | Proper scoring rules and inference that accounts for dependence and the number of models |
| Replication | The award version's code path re-run on `one45.csv`, errors included | Shows that the errors explain the reported numbers |
| Horizons | 1, 3, 6, 12 months (the replication keeps the original seven) | Fewer, more interpretable horizons |

Design decisions that a reader might question:

* **Real versus nominal dating.** The thesis works with real prices, so v2 dates real bear
  markets. This yields more episodes after 1960 (for example 1976-1980) than nominal dating
  would, and monthly averages miss short drops such as 2020 (19.6% in monthly averages).
* **Training from 1881.** The out-of-sample models train on all data from the first month with
  complete predictors (June 1881), which gives the first forecasts in 1960 almost eighty years of
  history. Pre-1926 dividends and earnings are interpolated from annual figures; this affects
  training rows only.
* **Sample end.** The workbook runs to October 2026, but dividends and earnings end in June 2026
  and the latest prices, CPI and yields are provisional, so the sample ends in June 2026.
* **Machine-learning refits.** The elastic net and boosted trees are re-estimated (with
  hyperparameter selection) each January rather than every month, to keep the run time modest;
  this handicaps them slightly relative to the monthly logits.
* **Regime-probability exercise.** Panel C of the MSPE table forecasts Q_{t+h} from the
  full-sample MS-AR(1) model, as the original design did. It is kept for comparability and is
  labeled descriptive; the dated-bear-market exercise is the clean test.

## 4. What I could not do or am unsure about

* The archived R code could not be run (no R on this machine). The replication is a Python
  re-implementation; it matches the reported OLS numbers closely but statsmodels' ML estimates of
  the leaked regime model differ slightly from MSwM's EM estimates (bull stay 0.950 vs 0.945),
  and the beta-regression ratios match less tightly than the OLS ones.
* The transcription of archived values in `v2/data/archived_reported.csv` was done by hand from
  the table images in the PDF.
* The analysis uses one vintage of Shiller's data, not real-time vintages; the comparison with
  `one45.csv` suggests revisions are small and confined to the latest months.
* The pairwise Diebold-Mariano tests with the conventional h - 1 lag window reject persistence
  for nine one-month models, but the loss differences are highly autocorrelated (median
  first-order autocorrelation 0.85 at one month); with a 23-lag window one model remains
  significant at 5%, and the SPA test, which accounts for the 25 models, does not reject. The
  23-lag window and the 24-month bootstrap blocks are judgment calls; 12-month blocks give the
  same conclusion.

## 5. History

* **v2.0 (October 2026, first rebuild).** Python package `v2/src/psm`, data from `one45.csv`
  (1900-2023), seven forecasting models, robustness experiments (alternative regime
  specifications, dating rules, rolling windows, subperiods, five extra predictors, block
  bootstrap).
* **v2.1 (October 2026, this version).** Rebuilt from Shiller's current workbook and consolidated
  into the single script `v2/thesis.py` (the `psm` package was removed); added TVTP regime models,
  elastic-net and gradient-boosting classifiers with in-window validation, dynamic model
  averaging, the Murphy decomposition, Hansen's SPA test and White's Reality Check, the model
  confidence set and the Giacomini-White test; rewrote the paper. Eleven new references were
  verified against Crossref (Diebold, Lee and Weinbach 1994, doi:10.1093/oso/9780198773917.003.0010;
  Filardo 1994, doi:10.1080/07350015.1994.10524545; Friedman 2001, doi:10.1214/aos/1013203451;
  Giacomini and White 2006, doi:10.1111/j.1468-0262.2006.00718.x; Gu, Kelly and Xiu 2020,
  doi:10.1093/rfs/hhaa009; Hansen 2005, doi:10.1198/073500105000000063; Hansen, Lunde and Nason
  2011, doi:10.3982/ECTA5771, authors confirmed on the Econometric Society page; Murphy 1973,
  doi:10.1175/1520-0450(1973)012<0595:ANVPOT>2.0.CO;2; Raftery, Kárný and Ettler 2010,
  doi:10.1198/TECH.2009.08104; White 2000, doi:10.1111/1468-0262.00152; Zou and Hastie 2005,
  doi:10.1111/j.1467-9868.2005.00503.x), giving 37 references.

What moved between v2.0 and v2.1 (same design, new data and sample):

| Quantity | v2.0 (one45.csv, 1900-2023) | v2.1 (Shiller workbook, 1871-2026:06) |
|---|---:|---:|
| Dated bear markets (since 1960) | 21 (9) | 25 (9) |
| MS-AR(1) bull / bear mean, % per month | 0.84 / −1.81 | 0.88 / −1.75 |
| MS-AR(1) expected bull / bear duration, months | 17.9 / 5.2 | 16.6 / 5.0 |
| Logit pseudo-R², h = 1 (training from) | 0.261 (1910) | 0.196 (1881) |
| Brier skill h = 1: persistence / logit 6 predictors | 18.9% / 20.8% | 17.6% / 25.4% |
| Brier skill h = 3: persistence / dividend-yield logit | 11.5% / 12.3% | 10.0% / 13.4% |
| Brier skill h = 12: dividend-yield logit / logit 6 predictors | 1.9% / −11.1% | 1.4% / −3.2% |
| Smallest DM p vs persistence, core models (h − 1 lags) | 0.256 | 0.019 |
| Logit gain over persistence h = 1, 90% bootstrap interval (pp) | [−11.7, 15.4] | [−5.8, 20.9] |

The one-month advantage of the multivariate logit over persistence is larger in v2.1, and its
conventional DM test now rejects at 5%; the HAC window, the bootstrap and the SPA test show that
this is not robust. The qualitative conclusions are unchanged.
