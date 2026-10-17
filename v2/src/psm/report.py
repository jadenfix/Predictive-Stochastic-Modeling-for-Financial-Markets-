"""Builders that turn estimation results into `Table` objects."""

from __future__ import annotations

import numpy as np
import pandas as pd

from psm.features import FEATURE_LABELS, FORECAST_FEATURES, ORIGINAL_FEATURES
from psm.forecast import BEAR_MODELS
from psm.regimes import RegimeFit
from psm.regressions import Coef, FitSummary
from psm.replication import ARCHIVED_PREDICTORS
from psm.tables import STAR_NOTE, Row, Section, Table, coef_rows, fmt, fmt_int, stars

TRANSFORMS = {
    "infl_m": ("100 dlog CPI", "1"),
    "d_rate": ("Monthly change", "0"),
    "bond_ret": ("100 dlog real bond index", "0 (CPI 1)"),
    "div_growth": ("100 dlog real dividends", "6"),
    "tr_ret": ("Price return plus D/12P, less inflation", "0 (D 6, CPI 1)"),
    "trse_growth": ("100 dlog real TR-scaled earnings", "6"),
    "d_trcape": ("100 dlog TR price / 10-yr mean earnings", "0 (E 6)"),
    "log_dy": ("log(D / P)", "0 (D 6)"),
    "log_cape": ("log(P / 10-yr mean real earnings)", "0 (E 6)"),
    "infl_yoy": ("100 x 12-month dlog CPI", "1"),
    "d_rate_12": ("12-month change", "0"),
    "mom_12": ("100 x 12-month dlog real price", "0 (CPI 1)"),
    "vol_12": ("sd of monthly real returns x sqrt(12)", "0 (CPI 1)"),
}


def _h(h: int) -> str:
    return f"h = {h}"


def variables_table(features: pd.DataFrame, sample_label: str) -> Table:
    rows = []
    sections = []
    for title, group in (("Monthly-change predictors (archived thesis variables)", ORIGINAL_FEATURES),
                         ("State predictors (bear-market forecasting models)", FORECAST_FEATURES)):
        rows = []
        for f in group:
            s = features[f.key].dropna()
            transform, lag = TRANSFORMS[f.key]
            rows.append(Row(f.label, [transform, f.unit, lag, fmt(s.mean(), 2), fmt(s.std(), 2)]))
        sections.append(Section(title, rows))
    return Table(
        key="variables",
        title="Predictors, transformations and publication lags",
        columns=["Construction", "Units", "Lag (months)", "Mean", "SD"],
        sections=sections,
        notes=[
            f"Statistics over {sample_label}. A forecast is made at the end of month t. Lag gives the "
            "publication lag applied to the inputs: CPI enters with one month, dividends (D) and earnings (E) "
            "with six. Real values are deflated by the CPI available at t. The archived 'realpricelag' "
            "columns (future prices) are never used."
        ],
        stub="Predictor",
        stub_width="1.25fr",
    )


def episodes_table(ep: pd.DataFrame) -> Table:
    rows = [
        Row(
            f"{r.peak:%Y-%m}",
            [f"{r.trough:%Y-%m}", str(r.months), fmt(r.decline_pct, 1), f"{r.confirmed:%Y-%m}",
             str((r.confirmed.year - r.peak.year) * 12 + r.confirmed.month - r.peak.month)],
        )
        for r in ep.itertuples()
    ]
    return Table(
        key="episodes",
        title="Dated bear markets in the real S&P 500, 1900-2023",
        columns=["Trough", "Months", "Decline (%)", "Confirmed", "Months to confirm"],
        sections=[Section(None, rows)],
        notes=[
            "A bear market runs from a peak to the following trough when the real index falls at least 20% "
            "below the peak before rising 20% above the trough. 'Confirmed' is the first month in which "
            "the 20% decline had occurred, that is, when the bear market became knowable in real time."
        ],
        stub="Peak",
    )


def regime_table(fits: dict[str, RegimeFit]) -> Table:
    names = list(fits)
    cols = list(fits.values())

    def coef_row(label: str, key: str, digits: int = 3, with_stars: bool = True) -> list[Row]:
        return coef_rows(label, [f.coefs.get(key) for f in cols], digits, with_stars)

    def sd_row(label: str, key: str) -> Row:
        return Row(label, [fmt(float(np.sqrt(f.coefs[key].estimate)), 2) for f in cols])

    sections = [
        Section("Mean monthly real return (%)", coef_row("Bull regime", "mean_bull") + coef_row("Bear regime", "mean_bear")),
        Section("Innovation variance", coef_row("Bull regime", "sigma2_bull", 2, False)
                + coef_row("Bear regime", "sigma2_bear", 2, False)
                + [sd_row("Bull volatility (sd, %)", "sigma2_bull"), sd_row("Bear volatility (sd, %)", "sigma2_bear")]),
        Section("Autoregression", coef_row("AR(1) coefficient", "ar")),
        Section("Transitions", coef_row("P(bull to bull)", "p_bull_bull", 3, False)
                + coef_row("P(bear to bear)", "p_bear_bear", 3, False)
                + [Row("Expected bull duration (months)", [fmt(f.durations[0], 1) for f in cols]),
                   Row("Expected bear duration (months)", [fmt(f.durations[1], 1) for f in cols])]),
        Section("Fit", [
            Row("Log-likelihood", [fmt(f.llf, 1) for f in cols]),
            Row("AIC", [fmt(f.aic, 1) for f in cols]),
            Row("BIC", [fmt(f.bic, 1) for f in cols]),
            Row("Observations", [fmt_int(f.nobs) for f in cols]),
            Row("Sample", [f"{f.index[0]:%Y:%m}-{f.index[-1]:%Y:%m}" for f in cols]),
        ]),
    ]
    return Table(
        key="regimes",
        title="Two-regime Markov-switching models of monthly real S&P 500 returns",
        columns=names,
        sections=sections,
        notes=[
            "Maximum-likelihood estimates; standard errors in parentheses from the numerical Hessian. "
            "The bear regime is the regime with the lower mean. Switching mean and variance; the AR(1) "
            "coefficient is common to both regimes. Returns are 100 times the log change in the real price "
            "index. " + STAR_NOTE + " Stars are shown only for tests against zero that are meaningful (means, AR term)."
        ],
        stub_width="1.5fr",
    )


def original_spec_table(ols: dict[tuple[str, int], FitSummary], beta: dict[tuple[str, int], FitSummary],
                        horizons: tuple[int, ...]) -> Table:
    sections = []
    for f in ORIGINAL_FEATURES:
        rows = coef_rows(f.label, [ols[(f.key, h)].coefs[f.key] for h in horizons]
                         + [beta[(f.key, h)].coefs[f.key] for h in horizons])
        rows.append(Row("R² / pseudo-R²", [fmt(ols[(f.key, h)].stats["r2"], 3) for h in horizons]
                        + [fmt(beta[(f.key, h)].stats["pseudo_r2"], 3) for h in horizons]))
        sections.append(Section(None, rows))
    first = ols[(ORIGINAL_FEATURES[0].key, horizons[0])]
    sections.append(Section(None, [
        Row("Observations", [fmt_int(ols[(ORIGINAL_FEATURES[0].key, h)].nobs) for h in horizons]
            + [fmt_int(beta[(ORIGINAL_FEATURES[0].key, h)].nobs) for h in horizons]),
    ]))
    lags = sorted({ols[(ORIGINAL_FEATURES[0].key, h)].stats["nw_lags"] for h in horizons})
    return Table(
        key="original_spec",
        title="Corrected archived specification: regime probability h months ahead on each predictor",
        columns=[_h(h) for h in horizons] * 2,
        groups=[("OLS (percentage points)", len(horizons)), ("Beta regression (logit link)", len(horizons))],
        sections=sections,
        notes=[
            "Each cell is a separate univariate regression of the filtered bear-regime probability "
            "Q(t+h) from the MS-AR(1) model on the predictor at t, which is standardized (coefficients are "
            "per one standard deviation). OLS coefficients are in percentage points of probability. "
            f"Newey-West standard errors in parentheses ({', '.join(str(int(x)) for x in lags)} lags by horizon). "
            f"Forecast origins {first.start:%Y:%m} to {first.end:%Y:%m} for h = {horizons[0]}; the sample "
            "shortens by h months. The beta-regression pseudo-R² is the squared correlation of the linear "
            "predictor with logit(Q). " + STAR_NOTE + " Q is computed with full-sample parameters, so these "
            "are in-sample associations, not forecasts."
        ],
        stub_width="1.45fr",
    )


SECTIONS_B = (
    ("Valuation", ("log_dy", "log_cape")),
    ("Macroeconomic", ("infl_yoy", "d_rate_12")),
    ("Market", ("mom_12", "vol_12")),
)


def logit_table(logit: dict[int, FitSummary], probit: dict[int, FitSummary], horizons: tuple[int, ...]) -> Table:
    fits = [logit[h] for h in horizons] + [probit[h] for h in horizons]
    sections = []
    for title, keys in SECTIONS_B:
        rows = []
        for k in keys:
            rows += coef_rows(FEATURE_LABELS[k], [f.coefs[k] for f in fits], 2)
        sections.append(Section(title, rows))
    sections.append(Section(None, coef_rows("Constant", [f.coefs["const"] for f in fits], 2) + [
        Row("Pseudo-R² (McFadden)", [fmt(f.stats["pseudo_r2"], 3) for f in fits]),
        Row("Log-likelihood", [fmt(f.stats["llf"], 1) for f in fits]),
        Row("AIC", [fmt(f.stats["aic"], 1) for f in fits]),
        Row("Observations", [fmt_int(f.nobs) for f in fits]),
    ]))
    first = fits[0]
    lags = ", ".join(str(int(f.stats["nw_lags"])) for f in fits[: len(horizons)])
    return Table(
        key="logit",
        title="Full-sample logit and probit models of a dated bear market h months ahead",
        columns=[_h(h) for h in horizons] * 2,
        groups=[("Logit", len(horizons)), ("Probit", len(horizons))],
        sections=sections,
        notes=[
            "Dependent variable: 1 if month t+h lies in a dated bear market (Table 2). Predictors are "
            f"measured at t and standardized. Newey-West standard errors in parentheses ({lags} lags by horizon). "
            f"Forecast origins {first.start:%Y:%m} to {first.end:%Y:%m} for h = {horizons[0]}. "
            + STAR_NOTE + " In-sample estimates over the whole period; Table 6 reports real-time forecasts."
        ],
        stub_width="1.5fr",
    )


def oos_table(metrics: pd.DataFrame, horizons: tuple[int, ...], period: str) -> Table:
    sections = []
    for h in horizons:
        rows = []
        for m, name in BEAR_MODELS.items():
            r = metrics.loc[(h, m)]
            rows.append(Row(name, [
                fmt(r.brier, 3), fmt(100 * r.bss, 1), fmt(r.log_loss, 3), fmt(r.auc, 3),
                "" if m == "uncond" else fmt(r.p_uncond, 3),
                "" if m in ("uncond", "persist") else fmt(r.p_persist, 3),
            ]))
        n = int(metrics.loc[(h, "uncond"), "n"])
        share = metrics.loc[(h, "uncond"), "bear_share"]
        sections.append(Section(f"h = {h} ({n} forecasts, bear share {fmt(100 * share, 1)}%)", rows))
    return Table(
        key="oos",
        title=f"Out-of-sample accuracy of real-time bear-market forecasts, {period}",
        columns=["Brier", "Skill (%)", "Log loss", "AUC", "p vs uncond.", "p vs persist."],
        sections=sections,
        notes=[
            "Expanding-window forecasts made at each month-end origin using only data available then: "
            "predictors with publication lags, bear dates obtained from prices through the origin, and "
            "Markov-switching parameters re-estimated each January (filtered probabilities only). Lower "
            "Brier score and log loss are better; skill is the percentage reduction in Brier score relative to "
            "the unconditional frequency. Log loss truncates probabilities to [0.001, 0.999]. The p-values "
            "are one-sided Diebold-Mariano tests (Harvey-Leybourne-Newbold correction, Bartlett HAC variance) "
            "of equal Brier score against the alternative that the model is more accurate than the baseline."
        ],
        stub_width="1.9fr",
    )


def mspe_table(archived: pd.DataFrame, corrected: pd.DataFrame, horizons: tuple[int, ...],
               corrected_period: str) -> Table:
    def grid(df: pd.DataFrame, value: str, keys: list[str], labels: dict[str, str], cw: bool) -> list[Row]:
        rows = []
        for key in keys:
            cells = []
            for model in ("OLS", "Beta"):
                for h in horizons:
                    r = df[(df.model == model) & (df.predictor == key) & (df.k == h)].iloc[0]
                    cells.append(fmt(r[value], 3) + (stars(r.cw_p) if cw else ""))
            rows.append(Row(labels[key], cells, "coef" if cw else "stat"))
        return rows

    arch_keys = list(ARCHIVED_PREDICTORS)
    corr_keys = [f.key for f in ORIGINAL_FEATURES] + ["q_now"]
    labels_c = {f.key: f.label for f in ORIGINAL_FEATURES} | {"q_now": "Benchmark: regime probability at t"}
    sections = [
        Section("A. Archived design and archived formula (squared mean error ratio)",
                grid(archived, "archived_ratio", arch_keys, ARCHIVED_PREDICTORS, False)),
        Section("B. Archived design, correct mean squared prediction error ratio",
                grid(archived, "mspe_ratio", arch_keys, ARCHIVED_PREDICTORS, False)),
        Section("C. Corrected design: past-only predictors, true h-month lead, expanding window",
                grid(corrected, "mspe_ratio", corr_keys, labels_c, True)),
    ]
    return Table(
        key="mspe",
        title="Forecasting the regime probability: unrestricted versus intercept-only models",
        columns=[_h(h) for h in horizons] * 2,
        groups=[("OLS", len(horizons)), ("Beta regression", len(horizons))],
        sections=sections,
        notes=[
            "Entries are ratios of the unrestricted model's loss to the intercept-only model's loss; values "
            "below one favor the predictor. Panels A and B re-run the archived code path (target Q(t-k), "
            "leaked regime model, single 80/20 split with the test period starting in 2011). Panel A uses "
            "the archived formula (mean error)² / (mean error)², which is not a mean squared error. "
            f"Panel C forecasts Q(t+h) from predictors observable at t with expanding-window refits, origins "
            f"{corrected_period}. The benchmark row uses Q(t) itself as the predictor. Stars in Panel C mark Clark-West (2007) tests of equal accuracy in nested "
            "models where the unrestricted model is better: * p < 0.10, ** p < 0.05, *** p < 0.01."
        ],
        stub_width="1.45fr",
    )


def replication_table(rep: pd.DataFrame) -> Table:
    rows = [Row(r.label, [r.reported, r.replicated, r.corrected]) for r in rep.itertuples()]
    return Table(
        key="replication",
        title="Archived results, their replication, and the corrected estimates",
        columns=["Archived (reported)", "Replicated", "Corrected"],
        sections=[Section(None, rows)],
        notes=[
            "Archived values are transcribed from the award PDF (v2/data/archived_reported.csv). "
            "'Replicated' re-runs the archived code path in Python, including the future-price regressor, "
            "the backward target Q(t-k) and the archived MSPE formula. 'Corrected' uses the MS-AR(1) "
            "model on returns, past-only predictors, the forward target Q(t+k) and expanding-window "
            "forecasts. Coefficients in the corrected column are per one-standard-deviation change of a "
            "different (growth-rate) transformation and are therefore comparable in sign and significance only."
        ],
        stub_width="2fr",
    )


def coef_cell(c: Coef, digits: int = 3) -> str:
    return f"{fmt(c.estimate, digits)}{stars(c.pvalue)} ({fmt(c.se, digits)})"
