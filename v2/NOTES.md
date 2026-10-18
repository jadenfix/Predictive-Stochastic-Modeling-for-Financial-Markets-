# Notes on the original thesis and the v2 rebuild

These notes record what the award version (February 2025 PDF and `code.R`) did, what was
wrong or unclear, and what v2 changes and why. Figures quoted here for the original come from
the PDF; every v2 number lives in `v2/output/`.

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
| Timing | Forecast origin = end of month t; CPI lagged 1 month, dividends and earnings 6 months; real values deflated by CPI_{t-1} | Every predictor at t must be observable at t |
| Leaked columns | `realpricelag*` never read outside `replication.py` (tested) | Remove look-ahead |
| Predictors | Growth rates instead of differenced index levels; standardized coefficients | Interpretable, scale-free |
| Bear definition | Rule-based dating on the real price: a 20% fall from a peak starts a bear market (backdated to the month after the peak), a 20% rise from the trough ends it | Observable target independent of any model; testable |
| Regime model | statsmodels MS (switching mean and variance) and MS-AR(1), on real returns, deterministic starting-value grid, bear = lower-mean regime | Standard Hamilton (1989) specification on a stationary series |
| Probabilities | Filtered for anything used as a forecast; smoothed only in a labeled retrospective figure | Smoothed probabilities condition on the future |
| Regressions | Original OLS and beta specs with the forward target Q_{t+h} and Newey-West errors; logit and probit for the dated indicator | Correct direction and inference; natural binary benchmark |
| Out of sample | Monthly expanding-window refits from 1960:01; vintage bear labels from prices through the origin; regime model re-estimated each January | Real-time evaluation with no future information |
| Baselines | Unconditional frequency and persistence of the real-time state | Any useful model must beat both |
| Metrics | Brier score and skill, log loss, AUC, calibration; Diebold-Mariano (HLN) and Clark-West tests | Proper scoring rules and tests of equal accuracy |
| Replication | `psm.replication` re-runs the archived code path with its errors | Shows that the errors explain the reported numbers |
| Horizons | 1, 3, 6, 12 months (the original also used 2, 18, 24; the replication keeps all seven) | Fewer, more interpretable horizons |
| Beta regression | Smithson-Verkuilen compression of Q into (0, 1) | betareg requires an open interval |

Design decisions that a reader might question:

* **Real versus nominal dating.** The thesis works with real prices, so v2 dates real bear
  markets. This yields more episodes after 1960 (for example 1976-1980) than nominal dating
  would, and monthly averages miss short drops such as 2020.
* **Training on 1910-1959.** The out-of-sample models train on all data from the first month
  with complete predictors (1910), which gives the first forecasts in 1960 about fifty years of
  history. Pre-1926 dividends and earnings are interpolated from annual figures; this affects
  training rows only, all of which were historical by 1960.
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
* The data are a single archived Shiller extract; they are not real-time vintages.

## 5. Robustness experiments and the professional rewrite (October 2026)

`psm.robustness` adds experiments that each change one design choice and re-run the affected
part of the pipeline; everything flows into `numbers.json` (key `rob`) and into new tables
(`regime_specs`, `dating`, `robust_oos`, `predictors`, `bootstrap`) and `fig8_skill_intervals`.

| Experiment | What is re-run | Headline |
|---|---|---|
| Regime specification: MS-AR(1), MS mean-variance, variance-only, mean-only, three regimes (1960-2023) | ML fits; AUC/correlation of the filtered bear probability with the dated state | MS-AR(1) has the lowest AIC and BIC; mean-only switching picks out crash months; three regimes split bull into calm and rebound, bear regime unchanged |
| Subsample regimes: MS-AR(1) on 1960-1989 and 1990-2023 | ML fits | Bear volatility stable (5.6-5.7%); filtered probability tracks bears far better after 1990 (AUC 0.90 vs 0.73) |
| Dating: 15%, 25% on real prices; 20% on nominal prices | Full real-time run (vintage labels and real-time state re-dated) | Persistence h=1 skill 15.8-24.6%; dividend-yield logit positive at 1-3 months under every rule; multivariate logit negative at 12 months under every rule |
| Rolling 30-year windows | Full real-time run | Lower skill for persistence, MS and dividend-yield logit at every horizon |
| Evaluation period: targets 1960-1989, 1990-2023, excluding 2007:10-2009:06 | Scoring of the main forecasts | Skill concentrated after 1990; excluding the crisis changes little |
| Predictors: 5 more (excess CAPE yield, payout ratio, 12-month earnings growth, 10-year yield level, drawdown from 12-month high); 11 univariate logits, equal-weight combination, 11-predictor logit | Full real-time run | Drawdown is the only forecast that beats persistence (h=1, p=0.008); the other additions add nothing; combination positive to 6 months but below persistence |
| Moving-block bootstrap (24-month blocks, 2,000 draws; 12 and 36 as checks) | Resampling of target months, all models jointly | Persistence h=1 skill 90% interval about [6.6, 30.7]%; logit gain over persistence spans zero |

Across the alternative designs and the predictor experiments, 3 of 136 comparisons with
persistence are significant at 5% (all at one month), no more than chance.

Implementation notes:

* `forecast.bear_forecasts` gained keyword options (`models`, `window`, `decline`/`rise`,
  `univariate`, `combine`); with defaults it reproduces the previous forecasts exactly.
* Logit fits now use a Newton-Raphson solver (`forecast._newton_logit`) with a statsmodels
  fallback; it matches statsmodels to numerical tolerance (tested), every reported number in
  `numbers.json` is unchanged, and it makes the tens of thousands of robustness refits affordable. Variants
  run in parallel processes; a full `python -m psm.run` takes about 12 minutes.
* `drawdown` is measured from the 12-month high (an all-time-high version is dominated by the
  decades-long real drawdowns after 1906 and 1929).
* Three-regime and switching-variance/mean-only fits use statsmodels' own starting values plus
  25 random-search repetitions with a fixed seed.

The paper (`paper/main.typ`) was rewritten end to end around the research question and the
findings. The data-alignment correction is one paragraph in Section 3.1, and the regime-probability
regressions, the replication of the award version and the MSPE comparison moved to Appendix A.
Two references were added and verified against Crossref: Rapach, Strauss and Zhou (2010),
doi:10.1093/rfs/hhp063, and Künsch (1989), doi:10.1214/aos/1176347265 (26 references in total).
