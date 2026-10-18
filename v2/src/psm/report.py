"""Builders that turn estimation results into `Table` objects."""

from __future__ import annotations

import numpy as np
import pandas as pd

from psm.features import EXTRA_FEATURES, FEATURE_LABELS, FORECAST_FEATURES, ORIGINAL_FEATURES
from psm.forecast import BEAR_MODELS
from psm.regimes import RegimeFit
from psm.regressions import Coef, FitSummary
from psm.replication import ARCHIVED_PREDICTORS
from psm.tables import STAR_NOTE, Row, Section, Table, coef_rows, fmt, fmt_int, fmt_p, stars

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
    "ecy": ("100 E10/P less (yield less 10-yr inflation)", "0 (E 6, CPI 1)"),
    "log_payout": ("log(D / E)", "6"),
    "earn_growth_12": ("100 x 12-month dlog real earnings", "6"),
    "rate_level": ("Level", "0"),
    "drawdown": ("100 x log(P / 12-month high)", "0 (CPI 1)"),
}


def _h(h: int) -> str:
    return f"h = {h}"


def variables_table(features: pd.DataFrame, sample_label: str) -> Table:
    sections = []
    for title, group in (("Monthly-change predictors (archived thesis variables)", ORIGINAL_FEATURES),
                         ("State predictors (bear-market forecasting models)", FORECAST_FEATURES),
                         ("Additional state predictors (robustness)", EXTRA_FEATURES)):
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
        stub_width="1.9fr",
        widths=["2.1fr", "1fr", "1fr", "0.6fr", "0.6fr"],
        aligns=["left", "left", "center", "right", "right"],
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
        stub_width="1fr",
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
        stub_width="2.2fr",
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
        stub_width="2.1fr",
        size="8pt",
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
            "Dependent variable: 1 if month t+h lies in a dated bear market. Predictors are "
            f"measured at t and standardized. Newey-West standard errors in parentheses ({lags} lags by horizon). "
            f"Forecast origins {first.start:%Y:%m} to {first.end:%Y:%m} for h = {horizons[0]}. "
            + STAR_NOTE + " In-sample estimates over the whole period, not real-time forecasts."
        ],
        stub_width="2.3fr",
        size="8pt",
    )


def oos_table(metrics: pd.DataFrame, horizons: tuple[int, ...], period: str) -> Table:
    sections = []
    for h in horizons:
        rows = []
        for m, name in BEAR_MODELS.items():
            r = metrics.loc[(h, m)]
            rows.append(Row(name, [
                fmt(r.brier, 3), fmt(100 * r.bss, 1), fmt(r.log_loss, 3), fmt(r.auc, 3),
                "" if m == "uncond" else fmt_p(r.p_uncond),
                "" if m in ("uncond", "persist") else fmt_p(r.p_persist),
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
        stub_width="2.6fr",
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
        stub_width="2.3fr",
        size="8pt",
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
        stub_width="2.6fr",
    )


def coef_cell(c: Coef, digits: int = 3) -> str:
    return f"{fmt(c.estimate, digits)}{stars(c.pvalue)} ({fmt(c.se, digits)})"


SUMMARY_MODELS = ("uncond", "persist", "ms", "logit_dy", "logit_all")


def summary_table(metrics: pd.DataFrame, horizons: tuple[int, ...]) -> Table:
    """Compact Brier-score summary for the README."""
    rows = []
    for h in horizons:
        cells = []
        for m in SUMMARY_MODELS:
            r = metrics.loc[(h, m)]
            cells.append(fmt(r.brier, 3) if m == "uncond" else f"{fmt(r.brier, 3)} ({fmt(100 * r.bss, 1)}%)")
        best_p = min(metrics.loc[(h, m), "p_persist"] for m in BEAR_MODELS if m not in ("uncond", "persist"))
        cells.append(fmt_p(best_p))
        rows.append(Row(f"{h} month{'s' if h > 1 else ''}", cells))
    return Table(
        key="summary",
        title="Out-of-sample Brier scores (skill relative to the unconditional frequency)",
        columns=[BEAR_MODELS[m] for m in SUMMARY_MODELS] + ["Best p vs persistence"],
        sections=[Section(None, rows)],
        notes=[
            "Lower is better. Real-time expanding-window forecasts, targets 1960-2023. The last column is "
            "the smallest one-sided Diebold-Mariano p-value of any model against persistence."
        ],
        stub="Horizon",
    )


# ------------------------------------------------------------------ robustness tables

ROBUST_LABELS = {
    "persist": "Persistence",
    "ms": "MS-AR(1)",
    "logit_dy": "Logit: dividend yield",
    "logit_all": "Logit: all predictors",
}


def _skill_cell(r: pd.Series) -> str:
    """Skill in percent with stars for the one-sided DM test against the unconditional frequency."""
    return fmt(100 * r.bss, 1) + stars(r.p_uncond)


def regime_spec_table(specs: list, quality: list[dict[str, float]]) -> Table:
    names = [s.name for s in specs]

    def per_regime(values: str, digits: int, which: int) -> list[str]:
        out = []
        for s in specs:
            vals = getattr(s, values)
            if s.k == 2:
                out.append(fmt(vals[{0: 0, 1: None, 2: 1}[which]], digits) if which != 1 else "")
            else:
                out.append(fmt(vals[which], digits))
        return out

    def block(title: str, attr: str, digits: int) -> Section:
        return Section(title, [
            Row("Bull (highest mean)", per_regime(attr, digits, 0)),
            Row("Middle (three regimes)", per_regime(attr, digits, 1)),
            Row("Bear (lowest mean)", per_regime(attr, digits, 2)),
        ])

    sections = [
        block("Mean monthly real return (%)", "means", 2),
        block("Volatility (sd, %)", "sds", 2),
        block("Expected duration (months)", "durations", 1),
        Section("Fit", [
            Row("AR(1) coefficient", [fmt(s.ar, 3) if s.ar is not None else "" for s in specs]),
            Row("Parameters", [str(s.n_params) for s in specs]),
            Row("Log-likelihood", [fmt(s.llf, 1) for s in specs]),
            Row("AIC", [fmt(s.aic, 1) for s in specs]),
            Row("BIC", [fmt(s.bic, 1) for s in specs]),
            Row("Observations", [fmt_int(s.nobs) for s in specs]),
        ]),
        Section("Filtered bear probability against the dated bear state", [
            Row("AUC", [fmt(q["auc"], 3) for q in quality]),
            Row("Correlation", [fmt(q["corr"], 2) for q in quality]),
        ]),
    ]
    return Table(
        key="regime_specs",
        title="Robustness of the regime model: specification and sample",
        columns=names,
        sections=sections,
        notes=[
            "Two-regime models unless stated; monthly real returns. The first five columns use 1960-2023; "
            "AIC and BIC are comparable only within that group. 'Mean and variance' is the switching "
            "mean-variance model without the AR term; 'Variance only' lets only the variance switch "
            "(its regimes share one mean and the bear regime is the high-variance one); 'Mean only' lets "
            "only the mean switch. In the three-regime model the bear regime is the one with the lowest "
            "mean. The last two columns re-estimate the main MS-AR(1) on each subsample. AUC and "
            "correlation compare the filtered bear-regime probability with the contemporaneous dated "
            "bear indicator (in sample, full-sample parameters)."
        ],
        stub_width="1.9fr",
        size="7.5pt",
    )


def robust_oos_table(variants: dict[str, pd.DataFrame], labels: dict[str, str], horizons: tuple[int, ...]) -> Table:
    """Brier skill of the main models under each variant, one section per model."""
    sections = []
    for m, name in ROBUST_LABELS.items():
        rows = []
        for key, met in variants.items():
            rows.append(Row(labels[key], [_skill_cell(met.loc[(h, m)]) for h in horizons], "coef"))
        sections.append(Section(name, rows))
    return Table(
        key="robust_oos",
        title="Robustness of out-of-sample Brier skill (%) to dating, estimation window and evaluation period",
        columns=[_h(h) for h in horizons],
        sections=sections,
        notes=[
            "Skill is the percentage reduction in Brier score relative to the unconditional frequency "
            "estimated in the same variant. Each dating variant re-dates bear markets (symmetric "
            "thresholds) and re-runs the complete real-time exercise, including the vintage labels and "
            "the real-time state. The rolling variant estimates every model on the most recent 30 years "
            "of training data. The evaluation-period rows score the main forecasts on subsets of target "
            "months; the crisis excluded is 2007:10-2009:06. Stars: one-sided Diebold-Mariano test "
            "against the unconditional frequency, * p < 0.10, ** p < 0.05, *** p < 0.01."
        ],
        stub_width="2.4fr",
        size="8pt",
    )


def dating_table(summaries: dict[str, dict[str, float]], labels: dict[str, str], since: str) -> Table:
    rows = [
        Row(labels[k], [str(v["n_bears"]), str(v["n_bears_since"]), fmt(100 * v["bear_share_since"], 1),
                        fmt(v["median_decline"], 1)])
        for k, v in summaries.items()
    ]
    return Table(
        key="dating",
        title="Bear markets under alternative dating rules",
        columns=["Bear markets, 1900-2023", f"Since {since}", f"Bear share since {since} (%)",
                 "Median decline (%)"],
        sections=[Section(None, rows)],
        notes=["Symmetric thresholds: a bear market starts when the index falls the stated percentage below "
               "its peak and ends when it rises the same percentage above its trough. Nominal dating uses "
               "the S&P Composite monthly average price without deflating."],
        stub="Dating rule",
        stub_width="2fr",
    )


def predictors_table(met: pd.DataFrame, keys: list[str], horizons: tuple[int, ...]) -> Table:
    def row(label: str, m: str) -> Row:
        return Row(label, [_skill_cell(met.loc[(h, m)]) for h in horizons]
                   + [fmt(met.loc[(horizons[0], m)].auc, 3)], "coef")

    base = [f.key for f in FORECAST_FEATURES]
    extra = [f.key for f in EXTRA_FEATURES]
    sections = [
        Section("Baseline", [row("Persistence", "persist")]),
        Section("Univariate logits: main predictors", [row(FEATURE_LABELS[k], f"uni_{k}") for k in base if k in keys]),
        Section("Univariate logits: additional predictors", [row(FEATURE_LABELS[k], f"uni_{k}") for k in extra if k in keys]),
        Section("Multi-predictor forecasts", [
            row(f"Equal-weight combination ({len(keys)} univariate logits)", "combo"),
            row(f"Logit: all {len(keys)} predictors", "logit_ext"),
        ]),
    ]
    return Table(
        key="predictors",
        title="Out-of-sample Brier skill (%) of individual predictors and combinations",
        columns=[_h(h) for h in horizons] + ["AUC, h = 1"],
        sections=sections,
        notes=[
            "Real-time expanding-window forecasts with the main dating rule; every model is re-estimated "
            "at each origin on data available then. The combination averages the probability forecasts of "
            "the univariate logits with equal weights. Skill is relative to the unconditional frequency. "
            "Stars: one-sided Diebold-Mariano test against the unconditional frequency, * p < 0.10, "
            "** p < 0.05, *** p < 0.01."
        ],
        stub_width="2.8fr",
        size="8pt",
    )


def bootstrap_table(boot: pd.DataFrame, models: tuple[str, ...], horizons: tuple[int, ...], block: int,
                    reps: int) -> Table:
    sections = []
    for h in horizons:
        rows = []
        for m in models:
            r = boot.loc[(h, m)]
            rows.append(Row(BEAR_MODELS.get(m, m), [
                fmt(100 * r.bss, 1),
                f"[{fmt(100 * r.bss_lo, 1)}, {fmt(100 * r.bss_hi, 1)}]",
                "" if m == "persist" else f"[{fmt(100 * r.gain_lo, 1)}, {fmt(100 * r.gain_hi, 1)}]",
                "" if m == "persist" else fmt(r.share_beats_persist, 2),
            ]))
        sections.append(Section(f"h = {h}", rows))
    return Table(
        key="bootstrap",
        title="Block-bootstrap uncertainty of out-of-sample Brier skill",
        columns=["Skill (%)", "90% interval", "Gain over persistence (pp), 90% interval",
                 "Share of draws beating persistence"],
        sections=sections,
        notes=[
            f"Circular moving-block bootstrap of target months with blocks of {block} months and {reps:,} "
            "replications, resampling all models jointly. Intervals are 5th and 95th percentiles. The gain "
            "over persistence is the model's skill minus the skill of persistence in the same draw."
        ],
        stub_width="2.3fr",
        widths=["0.8fr", "1.1fr", "1.5fr", "1.2fr"],
        size="8pt",
    )
