# Predictive Stochastic Modeling for Financial Markets

Can market and macroeconomic indicators forecast bear markets in the S&P 500? This repository
holds my undergraduate thesis on that question, which received the Adam Smith Award, and a
revised edition (v2) that rebuilds the analysis with a corrected data alignment and a real-time
out-of-sample test.

The short answer from v2: a two-regime Markov-switching model describes the market well, and a
bear market is partly recognizable once it has started, but none of the models forecasts bear
markets significantly better than simply knowing whether one is already under way.

![Real S&P 500 with dated bear markets, and the real-time one-month-ahead bear-market probability](v2/output/figures/hero.png)

- **Revised paper (v2):** [v2/paper/Predictive_Stochastic_Modeling_v2.pdf](v2/paper/Predictive_Stochastic_Modeling_v2.pdf)
- **Original award paper (February 2025):** [Predictive_Stochastic_Modeling_for_Financial_Markets.pdf](Predictive_Stochastic_Modeling_for_Financial_Markets.pdf)
- **Original R code:** [code.R](code.R)
- **What changed and why:** [v2/NOTES.md](v2/NOTES.md)

## Key results

Real-time forecasts of a dated bear market, made every month from January 1960 with every model
re-estimated on data available at the time. Brier scores, lower is better; skill in parentheses
is the reduction relative to the unconditional frequency.

| Horizon | Unconditional | Persistence | MS-AR(1) filtered | Logit: dividend yield | Logit: 6 predictors | Best p vs persistence |
|---|---:|---:|---:|---:|---:|---:|
| 1 month | 0.198 | 0.161 (18.9%) | 0.176 (10.9%) | 0.165 (16.5%) | 0.157 (20.8%) | 0.256 |
| 3 months | 0.199 | 0.176 (11.5%) | 0.193 (3.0%) | 0.175 (12.3%) | 0.187 (6.2%) | 0.433 |
| 6 months | 0.200 | 0.190 (4.9%) | 0.205 (−2.5%) | 0.185 (7.9%) | 0.214 (−6.9%) | 0.287 |
| 12 months | 0.202 | 0.201 (0.8%) | 0.209 (−3.5%) | 0.198 (1.9%) | 0.224 (−11.1%) | 0.405 |

*Persistence* is the bear frequency conditional on whether the market is currently in a
confirmed bear market. The last column is the smallest one-sided Diebold-Mariano p-value of any
of the five models against persistence; none of the 20 model-horizon comparisons is significant
at the 5% level. Full table: [v2/output/tables/oos.md](v2/output/tables/oos.md).

- **Regimes.** In the MS-AR(1) model of monthly real returns (1960-2023) the bull regime has a
  mean of 0.84% and volatility of 2.45% per month; the bear regime has a mean of −1.81% and
  volatility of 5.62%. Expected durations are 17.9 and 5.2 months.
- **In sample**, higher inflation and realized volatility, a weak past year and a high dividend
  yield are all associated with bear markets ([logit table](v2/output/tables/logit.md)).
- **Out of sample**, short-horizon gains come mostly from persistence. The dividend-yield logit
  is the most robust single model at three to twelve months, but its gains are small, and at
  twelve months no model is reliably better than the unconditional frequency.

## The data-alignment correction

Rebuilding the code exposed three errors in the award version. Re-running the archived code path
in Python reproduces the published numbers (correlation 1.000 for the OLS coefficients and
R² values, 0.998 for the forecast ratios), which confirms that these errors drove them.

1. **A future price in the regime model.** The column `realpricelag` in `one45.csv` is next
   month's price, not last month's: it matches the following month on 1,490 of 1,490 rows and the
   previous month on 3. The archived Markov-switching model regressed the price on this column, so
   its regime probabilities used future information.
2. **"Ahead" targets that look backwards.** The script built the "k months ahead" target with
   `dplyr::lag`, which shifts a series back in time. The predictive regressions therefore
   explained the regime probability k months *in the past*.
3. **A loss ratio that is not an MSPE.** The reported "MSPE ratio" divided squared mean errors,
   not mean squared errors. For dividends at one month the paper reported 0.004; the true MSPE
   ratio on the same design is 1.154 (worse than the benchmark), and 0.953 after all corrections.

In v2 every predictor at month t uses only data published by the end of month t (CPI lagged one
month, dividends and earnings six months), bear markets are dated with an explicit 20% rule,
filtered rather than smoothed probabilities are used for forecasts, and models are evaluated only
on expanding-window, out-of-sample forecasts. Tests check that no feature or forecast changes
when data after the forecast origin are altered.

## Reproduce

Requires [uv](https://docs.astral.sh/uv/). From the repository root:

```bash
cd v2
uv sync                       # Python 3.12+, numpy, pandas, statsmodels, matplotlib, typst
uv run python -m psm.run      # rebuilds v2/output/ and the paper PDF (about 3-4 minutes)
uv run pytest                 # data, timing, labeling, metrics and no-look-ahead tests
```

The pipeline is deterministic: it uses a fixed grid of starting values for the regime models and
no random sampling. Every number in the paper is read from `v2/output/numbers.json` or the
generated tables when the Typst source is compiled.

## Repository layout

```
one45.csv                         archived Shiller data extract (unchanged)
code.R, run_*.R, *.R              original R code and checked fitting lanes (unchanged)
Predictive_Stochastic_Modeling_for_Financial_Markets.pdf   original award paper (unchanged)
v2/
  src/psm/
    data.py          loading, date validation, audit of the archived lead columns
    features.py      past-only predictors with publication lags
    labels.py        bull and bear market dating, real-time state, vintage labels
    regimes.py       Markov-switching models (statsmodels), filtered and smoothed probabilities
    regressions.py   OLS and beta regressions, logit and probit, Newey-West errors
    forecast.py      real-time expanding-window forecasting engine
    metrics.py       Brier, log loss, AUC, calibration, Diebold-Mariano, Clark-West
    replication.py   the archived specification, errors included, for comparison
    tables.py        regression-table generator (Typst and Markdown)
    report.py        table builders
    figures.py       figures (300-dpi PNG and SVG)
    run.py           single entry point
    paper.py         compiles the Typst paper
  tests/             pytest suite
  data/archived_reported.csv   values transcribed from the award PDF
  output/            tables, figures, result CSVs, numbers.json
  paper/             main.typ and the compiled PDF
  NOTES.md           what the original did, what was wrong, what v2 changes
```

## Original R workflow

The award-version code is preserved as it was. With R installed:

```bash
Rscript install_dependencies.R
Rscript run_research.R            # runs code.R on one45.csv
Rscript test_temporal.R           # past-only alignment checks
Rscript run_regime_core.R         # archived regime models
Rscript run_regime_core.R --past-only
```

These scripts reproduce the archived models, including the timing issues described above; use
v2 for any forecasting conclusions.

## Data

Robert Shiller, *U.S. Stock Markets and CAPE Ratio* (Yale Department of Economics), monthly
1900-2024, as archived in `one45.csv`. The analysis uses observations through December 2023.

## Author

Jaden Fix. Original thesis advised by Jonathan Kaplan.
