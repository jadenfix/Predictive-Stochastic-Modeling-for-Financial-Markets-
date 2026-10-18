"""Robustness experiments.

Each experiment changes one design choice of the main analysis and re-runs the
relevant part of the pipeline:

* regime specification: two regimes with switching mean and variance (with and
  without an AR(1) term), switching variance only, switching mean only, and three
  regimes; plus the main MS-AR(1) on 1960-1989 and 1990-2023 separately;
* bear-market dating: 15%, 20% and 25% thresholds on real prices, and 20% on
  nominal prices, each followed by a full real-time forecasting run;
* estimation window: rolling 30-year windows instead of expanding ones;
* evaluation period: 1960-1989, 1990-2023, and the full period without the
  2007-2009 financial crisis;
* predictors: five more state variables built from the same Shiller file, each as
  a univariate logit, plus an equal-weight combination of all univariate forecasts
  and a multivariate logit on all eleven predictors;
* uncertainty: moving-block bootstrap intervals for the Brier skill scores.
"""

from __future__ import annotations

import warnings
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

import numpy as np
import pandas as pd
from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

from psm.forecast import BASELINES, VintageRegimes, bear_forecasts
from psm.labels import episodes, label_series
from psm.metrics import auc, brier, diebold_mariano
from psm.regimes import RegimeFit, fit_regimes

# Models re-run in every forecasting variant.
ROBUST_MODELS: tuple[str, ...] = ("uncond", "persist", "ms", "logit_dy", "logit_all")
ROLLING_WINDOW = 360  # months
BLOCK_LENGTH = 24  # months
BOOT_REPS = 2000
CRISIS = (pd.Timestamp("2007-10-01"), pd.Timestamp("2009-06-01"))


# --------------------------------------------------------------------------- regimes


@dataclass(frozen=True)
class SpecSummary:
    """A fitted regime specification, regimes ordered from highest to lowest mean."""

    name: str
    k: int
    llf: float
    aic: float
    bic: float
    n_params: int
    nobs: int
    means: tuple[float, ...]
    sds: tuple[float, ...]
    stay: tuple[float, ...]
    bear_filtered: pd.Series
    ar: float | None = None

    @property
    def durations(self) -> tuple[float, ...]:
        return tuple(1 / (1 - p) for p in self.stay)


def _fit_markov(returns: pd.Series, k: int, switching_mean: bool, switching_var: bool, seed: int):
    y = returns.dropna().to_numpy(dtype=float)
    model = MarkovRegression(
        y, k_regimes=k, trend="c", switching_trend=switching_mean, switching_variance=switching_var
    )
    best = None
    for reps in (0, 25):
        np.random.seed(seed)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                res = model.fit(search_reps=reps, disp=False, maxiter=500)
            except (np.linalg.LinAlgError, ValueError):
                continue
        if np.isfinite(res.llf) and (best is None or res.llf > best.llf + 1e-9):
            best = res
    if best is None:
        raise RuntimeError("Markov-switching estimation failed")
    return best


def fit_spec(name: str, returns: pd.Series, k: int, switching_mean: bool, switching_var: bool,
             seed: int = 20250201) -> SpecSummary:
    """Fit a Markov-switching mean/variance model and order regimes by mean (then variance)."""
    returns = returns.dropna()
    res = _fit_markov(returns, k, switching_mean, switching_var, seed)
    p = dict(zip(res.model.param_names, np.asarray(res.params)))
    means = np.array([p.get(f"const[{r}]", p.get("const")) for r in range(k)], dtype=float)
    var = np.array([p.get(f"sigma2[{r}]", p.get("sigma2")) for r in range(k)], dtype=float)
    order = np.lexsort((var, -means))  # by mean descending, ties by variance ascending
    stay = np.diag(res.regime_transition[:, :, 0])
    filt = np.asarray(res.filtered_marginal_probabilities)[:, order[-1]]
    return SpecSummary(
        name=name,
        k=k,
        llf=float(res.llf),
        aic=float(res.aic),
        bic=float(res.bic),
        n_params=len(res.params),
        nobs=int(res.nobs),
        means=tuple(float(means[i]) for i in order),
        sds=tuple(float(np.sqrt(var[i])) for i in order),
        stay=tuple(float(stay[i]) for i in order),
        bear_filtered=pd.Series(filt, index=returns.index[len(returns) - int(res.nobs):]),
    )


def from_regime_fit(name: str, fit: RegimeFit) -> SpecSummary:
    return SpecSummary(
        name=name,
        k=2,
        llf=fit.llf,
        aic=fit.aic,
        bic=fit.bic,
        n_params=len(fit.params),
        nobs=fit.nobs,
        means=fit.means,
        sds=tuple(float(np.sqrt(v)) for v in fit.variances),
        stay=(float(fit.transition[0, 0]), float(fit.transition[1, 1])),
        bear_filtered=fit.filtered,
        ar=fit.ar,
    )


def regime_specs(returns: pd.Series, main: RegimeFit, mean_var: RegimeFit, start: pd.Timestamp,
                 split: pd.Timestamp) -> list[SpecSummary]:
    """The main MS-AR(1), its alternatives on the same sample, and two subsamples."""
    r = returns.loc[start:]
    before = returns.loc[start : split - pd.DateOffset(months=1)]
    after = returns.loc[split:]
    return [
        from_regime_fit("MS-AR(1)", main),
        from_regime_fit("Mean and variance", mean_var),
        fit_spec("Variance only", r, 2, False, True),
        fit_spec("Mean only", r, 2, True, False),
        fit_spec("Three regimes", r, 3, True, True),
        from_regime_fit(f"MS-AR(1), {start:%Y}-{split.year - 1}", fit_regimes(before, "ar1")),
        from_regime_fit(f"MS-AR(1), {split:%Y}-{returns.index[-1]:%Y}", fit_regimes(after, "ar1")),
    ]


def spec_fit_quality(spec: SpecSummary, bear: pd.Series) -> dict[str, float]:
    """How well the filtered bear-regime probability tracks the dated bear state."""
    q = spec.bear_filtered
    y = bear.reindex(q.index)
    return {"auc": auc(q.to_numpy(), y.to_numpy()), "corr": float(np.corrcoef(q, y)[0, 1])}


# ------------------------------------------------------------------- forecast scoring


def score(fc: pd.DataFrame, models: tuple[str, ...] | None = None) -> pd.DataFrame:
    """Brier score, skill vs the unconditional frequency, AUC and DM p-values per (h, model)."""
    rows = []
    for h, sub in fc.groupby("horizon"):
        wide = sub.pivot(index="origin", columns="model", values="p")
        y = sub[sub.model == "uncond"].set_index("origin")["y"].reindex(wide.index).to_numpy()
        loss = wide.sub(y, axis=0) ** 2
        for m in models or tuple(wide.columns):
            if m not in wide:
                continue
            p = wide[m].to_numpy()
            rows.append({
                "horizon": h,
                "model": m,
                "n": len(y),
                "bear_share": float(y.mean()),
                "brier": brier(p, y),
                "bss": 1 - loss[m].mean() / loss["uncond"].mean(),
                "auc": auc(p, y),
                "p_uncond": diebold_mariano(loss[m].to_numpy(), loss["uncond"].to_numpy(), h)[1]
                if m != "uncond" else np.nan,
                "p_persist": diebold_mariano(loss[m].to_numpy(), loss["persist"].to_numpy(), h)[1]
                if m not in BASELINES and "persist" in loss else np.nan,
            })
    return pd.DataFrame(rows).set_index(["horizon", "model"])


def subperiods(fc: pd.DataFrame, split: pd.Timestamp) -> dict[str, pd.DataFrame]:
    """The main forecasts restricted to target months in each evaluation period."""
    t = fc.target_date
    return {
        f"Targets {t.min():%Y}-{split.year - 1}": fc[t < split],
        f"Targets {split:%Y}-{t.max():%Y}": fc[t >= split],
        "Excluding 2007-2009 crisis": fc[(t < CRISIS[0]) | (t > CRISIS[1])],
    }


# ---------------------------------------------------------------- forecast variants


@dataclass(frozen=True)
class Variant:
    key: str
    label: str
    price: pd.Series
    features: pd.DataFrame
    labels: pd.DataFrame
    decline: float
    window: int | None = None
    models: tuple[str, ...] = ROBUST_MODELS
    univariate: tuple[str, ...] = ()
    combine: bool = False


def _run_variant(args) -> tuple[str, pd.DataFrame]:
    v, returns, vint, origins, horizons = args
    fc = bear_forecasts(
        v.price, v.features, v.labels.bear_now, v.labels.bear, returns, vint, origins, horizons,
        models=v.models, window=v.window, decline=v.decline, rise=v.decline,
        univariate=v.univariate, combine=v.combine,
    )
    return v.key, fc


def run_variants(variants: list[Variant], returns: pd.Series, vint: VintageRegimes,
                 origins: pd.DatetimeIndex, horizons: tuple[int, ...], workers: int = 4) -> dict[str, pd.DataFrame]:
    """Real-time forecasting runs for each variant, in parallel processes."""
    jobs = [(v, returns, vint, origins, horizons) for v in variants]
    with ProcessPoolExecutor(max_workers=min(workers, len(jobs))) as pool:
        return dict(pool.map(_run_variant, jobs))


def dating_summary(price: pd.Series, decline: float, since: pd.Timestamp) -> dict[str, float]:
    lab = label_series(price, decline=decline, rise=decline)
    ep = episodes(price, decline=decline, rise=decline)
    return {
        "n_bears": len(ep),
        "n_bears_since": int((ep.peak >= since).sum()),
        "bear_share_since": float(lab.bear.loc[since:].mean()),
        "median_decline": float(-ep.decline_pct.median()),
    }


# ---------------------------------------------------------------------- bootstrap


def block_indices(n: int, block: int, reps: int, rng: np.random.Generator) -> np.ndarray:
    """Circular moving-block bootstrap: (reps, n) resampled positions."""
    n_blocks = -(-n // block)
    starts = rng.integers(0, n, size=(reps, n_blocks))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]) % n
    return idx.reshape(reps, -1)[:, :n]


def bootstrap_skill(fc: pd.DataFrame, models: tuple[str, ...], block: int = BLOCK_LENGTH,
                    reps: int = BOOT_REPS, seed: int = 20250201) -> pd.DataFrame:
    """Block-bootstrap distribution of Brier skill and of the skill gain over persistence.

    Target months are resampled in blocks of `block` consecutive forecasts, jointly
    for all models, which preserves the serial dependence of overlapping forecasts
    and the correlation between models. Returns 90% percentile intervals and the
    share of replications in which each model beats persistence.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for h, sub in fc.groupby("horizon"):
        wide = sub.pivot(index="origin", columns="model", values="p")
        y = sub[sub.model == "uncond"].set_index("origin")["y"].reindex(wide.index).to_numpy()
        loss = (wide.sub(y, axis=0) ** 2)
        idx = block_indices(len(y), block, reps, rng)
        means = {m: loss[m].to_numpy()[idx].mean(axis=1) for m in set(models) | {"uncond", "persist"}}
        skill_p = 1 - means["persist"] / means["uncond"]
        for m in models:
            s = 1 - means[m] / means["uncond"]
            gain = s - skill_p
            rows.append({
                "horizon": h,
                "model": m,
                "bss": 1 - loss[m].mean() / loss["uncond"].mean(),
                "bss_lo": float(np.quantile(s, 0.05)),
                "bss_hi": float(np.quantile(s, 0.95)),
                "gain_lo": float(np.quantile(gain, 0.05)) if m != "persist" else np.nan,
                "gain_hi": float(np.quantile(gain, 0.95)) if m != "persist" else np.nan,
                "share_beats_persist": float((gain > 0).mean()) if m != "persist" else np.nan,
                "share_beats_uncond": float((s > 0).mean()),
            })
    return pd.DataFrame(rows).set_index(["horizon", "model"])
