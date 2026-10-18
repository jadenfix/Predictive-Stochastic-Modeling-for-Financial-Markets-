"""Publication figures in one restrained matplotlib style.

Colors follow the Okabe-Ito colorblind-safe palette, assigned to models in a
fixed order; the unconditional baseline is drawn in neutral gray. Each figure is
saved as a 300-dpi PNG and as SVG.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter  # noqa: E402

from psm.forecast import BEAR_MODELS  # noqa: E402
from psm.metrics import calibration, roc_curve  # noqa: E402
from psm.regressions import FitSummary  # noqa: E402

INK = "#1a1a1a"
MUTED = "#5f5f5f"
GRID = "#e3e3e3"
SHADE = "#d4d4d4"
MODEL_COLORS = {
    "logit_state": "#D55E00",
    "logit_all": "#0072B2",
    "ms": "#009E73",
    "persist": "#E69F00",
    "probit_all": "#56B4E9",
    "logit_dy": "#CC79A7",
    "uncond": "#8c8c8c",
}
HORIZON_COLORS = {1: "#0072B2", 3: "#009E73", 6: "#E69F00", 12: "#D55E00"}
SOURCE = "Source: Shiller, U.S. Stock Markets and CAPE Ratio data (archived extract one45.csv); author's calculations."

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.labelsize": 9,
        "axes.edgecolor": MUTED,
        "axes.labelcolor": INK,
        "axes.linewidth": 0.7,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.frameon": False,
        "legend.fontsize": 8,
        "lines.linewidth": 1.4,
        "savefig.dpi": 300,
        "svg.fonttype": "none",
        "svg.hashsalt": "psm-v2",
        "figure.dpi": 100,
    }
)


def _save(fig: plt.Figure, directory: Path, name: str, source: bool = True) -> None:
    if source:
        fig.text(0.01, -0.01, SOURCE, fontsize=6.5, color=MUTED, ha="left", va="top")
    directory.mkdir(parents=True, exist_ok=True)
    fig.savefig(directory / f"{name}.png", bbox_inches="tight", facecolor="white",
                metadata={"Software": None})
    fig.savefig(directory / f"{name}.svg", bbox_inches="tight", facecolor="white",
                metadata={"Date": None, "Creator": None})
    plt.close(fig)


def _spans(labels: pd.Series) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Contiguous runs of label == 1, as (first month, month after last)."""
    spans = []
    start = None
    idx = labels.index
    for i, v in enumerate(labels.to_numpy()):
        if v == 1 and start is None:
            start = idx[i]
        if v != 1 and start is not None:
            spans.append((start, idx[i]))
            start = None
    if start is not None:
        spans.append((start, idx[-1] + pd.DateOffset(months=1)))
    return spans


def shade_bears(ax: plt.Axes, labels: pd.Series) -> None:
    for a, b in _spans(labels):
        ax.axvspan(a, b, color=SHADE, alpha=0.6, lw=0, zorder=0)


def _date_axis(ax: plt.Axes, years: int) -> None:
    ax.xaxis.set_major_locator(mdates.YearLocator(years))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.margins(x=0.005)


def price_history(price: pd.Series, labels: pd.Series, directory: Path) -> None:
    """Real S&P 500 on a log scale with dated bear markets shaded."""
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    shade_bears(ax, labels)
    ax.plot(price.index, price, color=INK, lw=1.0)
    ax.set_yscale("log")
    ax.yaxis.set_major_locator(LogLocator(base=10, subs=(1.0, 2.0, 5.0)))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set_ylabel("Real price index (log scale)")
    ax.set_title("Real S&P 500 and dated bear markets, 1900-2023")
    _date_axis(ax, 10)
    ax.text(0.01, 0.97, "Shaded: bear market (peak-to-trough decline of at least 20%)",
            transform=ax.transAxes, fontsize=7.5, color=MUTED, va="top")
    _save(fig, directory, "fig1_price_bears")


def regime_probabilities(filtered: pd.Series, smoothed: pd.Series, labels: pd.Series, directory: Path) -> None:
    """Filtered (real-time) and smoothed (retrospective) bear-regime probabilities."""
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 4.6), sharex=True)
    for ax, series, title in (
        (axes[0], filtered, "Filtered probability P(bear regime at t | returns through t): usable in real time"),
        (axes[1], smoothed, "Smoothed probability P(bear regime at t | all returns): retrospective dating only"),
    ):
        shade_bears(ax, labels.reindex(series.index))
        ax.fill_between(series.index, 0, series, color="#0072B2", alpha=0.25, lw=0)
        ax.plot(series.index, series, color="#0072B2", lw=0.8)
        ax.set_ylim(0, 1)
        ax.set_yticks([0, 0.5, 1])
        ax.set_ylabel("Probability")
        ax.set_title(title, fontsize=8.5, fontweight="normal")
    _date_axis(axes[1], 5)
    fig.suptitle("MS-AR(1) bear-regime probability, 1960-2023 (shaded: dated bear markets)",
                 x=0.01, ha="left", fontsize=10, fontweight="bold")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    _save(fig, directory, "fig2_regime_probabilities")


def oos_paths(forecasts: pd.DataFrame, labels: pd.Series, horizons: tuple[int, ...], models: tuple[str, ...], directory: Path, name: str = "fig3_oos_forecasts") -> None:
    """Real-time forecast probabilities, plotted at the target month, against dated bears."""
    fig, axes = plt.subplots(len(horizons), 1, figsize=(7.2, 1.9 * len(horizons) + 0.6), sharex=True)
    axes = np.atleast_1d(axes)
    for ax, h in zip(axes, horizons):
        sub = forecasts[forecasts.horizon == h]
        shade_bears(ax, labels.loc[sub.target_date.min() : sub.target_date.max()])
        for m in models:
            s = sub[sub.model == m].set_index("target_date")["p"]
            ax.plot(s.index, s, color=MODEL_COLORS[m], lw=1.0 if m != "uncond" else 0.9,
                    ls="--" if m == "uncond" else "-", label=BEAR_MODELS[m])
        ax.set_ylim(0, 1)
        ax.set_yticks([0, 0.5, 1])
        ax.set_ylabel("Probability")
        ax.set_title(f"{h}-month-ahead forecast of a bear market", fontsize=8.5, fontweight="normal")
    handles, lbls = axes[0].get_legend_handles_labels()
    _date_axis(axes[-1], 5)
    fig.suptitle("Out-of-sample bear-market probabilities, expanding window (shaded: dated bear markets)",
                 x=0.01, ha="left", fontsize=10, fontweight="bold", y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.935))
    fig.legend(handles, lbls, loc="upper left", bbox_to_anchor=(0.01, 0.968), ncol=len(models), fontsize=7.5,
               handlelength=1.8, columnspacing=1.2)
    _save(fig, directory, name)


def _panel_grid() -> tuple[plt.Figure, np.ndarray]:
    fig, axes = plt.subplots(2, 2, figsize=(6.4, 6.9), sharex=True, sharey=True)
    return fig, axes.ravel()


def _shared_legend(fig: plt.Figure, ax: plt.Axes) -> None:
    handles, lbls = ax.get_legend_handles_labels()
    fig.legend(handles, lbls, loc="upper left", ncol=2, bbox_to_anchor=(0.01, 0.965),
               fontsize=7.5, handlelength=1.8, columnspacing=1.2)


def calibration_curves(forecasts: pd.DataFrame, horizons: tuple[int, ...], models: tuple[str, ...], directory: Path) -> None:
    """Reliability diagrams on six forecast-quantile bins: observed bear frequency against mean forecast."""
    fig, axes = _panel_grid()
    for ax, h in zip(axes, horizons):
        ax.grid(True, axis="both")
        ax.plot([0, 1], [0, 1], color=MUTED, lw=0.8, ls=":")
        sub = forecasts[forecasts.horizon == h]
        for m in models:
            s = sub[sub.model == m]
            cal = calibration(s.p.to_numpy(), s.y.to_numpy(), bins=6)
            ax.plot(cal.forecast, cal.observed, color=MODEL_COLORS[m], marker="o", ms=4, lw=1.1,
                    label=BEAR_MODELS[m])
        ax.set_title(f"h = {h} month{'s' if h > 1 else ''}", fontsize=9)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
    for ax in axes[2:]:
        ax.set_xlabel("Forecast probability")
    for ax in axes[::2]:
        ax.set_ylabel("Observed bear frequency")
    fig.suptitle("Calibration of out-of-sample forecasts (six forecast-quantile bins)",
                 x=0.01, ha="left", fontsize=10, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    _shared_legend(fig, axes[0])
    _save(fig, directory, "fig4_calibration")


def roc_curves(forecasts: pd.DataFrame, horizons: tuple[int, ...], models: tuple[str, ...], auc_table: pd.DataFrame, directory: Path) -> None:
    """ROC curves by horizon; AUCs are printed in each panel."""
    fig, axes = _panel_grid()
    for ax, h in zip(axes, horizons):
        ax.grid(True, axis="both")
        ax.plot([0, 1], [0, 1], color=MUTED, lw=0.8, ls=":")
        sub = forecasts[forecasts.horizon == h]
        for j, m in enumerate(models):
            s = sub[sub.model == m]
            fpr, tpr = roc_curve(s.p.to_numpy(), s.y.to_numpy())
            ax.plot(fpr, tpr, color=MODEL_COLORS[m], lw=1.2, label=BEAR_MODELS[m], drawstyle="steps-post")
            ax.text(0.97, 0.05 + 0.07 * (len(models) - 1 - j), f"AUC {auc_table.loc[(h, m), 'auc']:.2f}",
                    transform=ax.transAxes, ha="right", fontsize=7.5, color=MODEL_COLORS[m], fontweight="bold")
        ax.set_title(f"h = {h} month{'s' if h > 1 else ''}", fontsize=9)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
    for ax in axes[2:]:
        ax.set_xlabel("False-positive rate")
    for ax in axes[::2]:
        ax.set_ylabel("True-positive rate")
    fig.suptitle("ROC curves of out-of-sample bear-market forecasts",
                 x=0.01, ha="left", fontsize=10, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    _shared_legend(fig, axes[0])
    _save(fig, directory, "fig5_roc")


def forest(fits: dict[int, FitSummary], labels: dict[str, str], directory: Path) -> None:
    """Standardized logit coefficients with 95% Newey-West intervals, by horizon."""
    keys = [k for k in next(iter(fits.values())).coefs if k != "const"]
    fig, ax = plt.subplots(figsize=(7.2, 0.55 * len(keys) + 1.4))
    ax.grid(True, axis="x")
    ax.grid(False, axis="y")
    ax.axvline(0, color=MUTED, lw=0.8)
    n = len(fits)
    offsets = np.linspace(-0.27, 0.27, n)
    for (h, fit), off in zip(fits.items(), offsets):
        y = np.arange(len(keys))[::-1] + off
        est = np.array([fit.coefs[k].estimate for k in keys])
        lo, hi = np.array([fit.coefs[k].ci() for k in keys]).T
        ax.errorbar(est, y, xerr=[est - lo, hi - est], fmt="o", ms=4.5, color=HORIZON_COLORS[h],
                    elinewidth=1.2, capsize=0, label=f"h = {h}")
    ax.set_yticks(np.arange(len(keys))[::-1])
    ax.set_yticklabels([labels[k] for k in keys])
    ax.set_xlabel("Logit coefficient per one-standard-deviation change (95% Newey-West interval)")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=n, fontsize=7.5)
    ax.set_title("Predictors of a bear market h months ahead, full-sample logit", pad=22)
    _save(fig, directory, "fig6_logit_forest")


def replication_scatter(pairs: dict[str, pd.DataFrame], directory: Path) -> None:
    """Archived (reported) values against this replication of the archived code."""
    fig, axes = plt.subplots(1, len(pairs), figsize=(7.2, 2.7))
    for ax, (title, df) in zip(axes, pairs.items()):
        ax.grid(True, axis="both")
        lo = min(df.reported.min(), df.replicated.min())
        hi = max(df.reported.max(), df.replicated.max())
        pad = 0.05 * (hi - lo)
        ax.plot([lo - pad, hi + pad], [lo - pad, hi + pad], color=MUTED, lw=0.8, ls=":")
        ax.scatter(df.reported, df.replicated, s=14, color="#0072B2", edgecolor="white", linewidth=0.5, zorder=3)
        ax.set_title(title, fontsize=8.5, fontweight="normal")
        ax.set_xlabel("Archived (reported)")
        r = np.corrcoef(df.reported, df.replicated)[0, 1]
        ax.text(0.04, 0.95, f"n = {len(df)}, corr = {r:.3f}", transform=ax.transAxes, fontsize=7.5,
                color=INK, va="top")
    axes[0].set_ylabel("Replicated (Python)")
    fig.suptitle("Replication of the archived specification, including its timing errors",
                 x=0.01, ha="left", fontsize=10, fontweight="bold")
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    _save(fig, directory, "fig7_replication")


def hero(price: pd.Series, labels: pd.Series, forecasts: pd.DataFrame, model: str, horizon: int, directory: Path) -> None:
    """README figure: real price with dated bears above the real-time forecast."""
    def path(m: str) -> pd.Series:
        return forecasts[(forecasts.horizon == horizon) & (forecasts.model == m)].set_index("target_date")["p"]

    sub, base = path(model), path("persist")
    p = price.loc[sub.index.min() : sub.index.max()]
    lab = labels.loc[p.index]
    fig, axes = plt.subplots(2, 1, figsize=(8, 4.6), sharex=True, gridspec_kw={"height_ratios": [1.3, 1]})
    shade_bears(axes[0], lab)
    axes[0].plot(p.index, p, color=INK, lw=1.0)
    axes[0].set_yscale("log")
    axes[0].yaxis.set_major_locator(LogLocator(base=10, subs=(1.0, 2.0, 5.0)))
    axes[0].yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    axes[0].yaxis.set_minor_formatter(NullFormatter())
    axes[0].set_ylabel("Real S&P 500 (log)")
    axes[0].set_title("Real S&P 500 with dated bear markets (shaded)", fontsize=9, fontweight="normal")
    shade_bears(axes[1], lab)
    axes[1].plot(sub.index, sub, color=MODEL_COLORS[model], lw=1.1, label=BEAR_MODELS[model], zorder=3)
    axes[1].plot(base.index, base, color=MODEL_COLORS["persist"], lw=0.9, label=BEAR_MODELS["persist"])
    axes[1].set_ylim(0, 1)
    axes[1].set_yticks([0, 0.5, 1])
    axes[1].set_ylabel("Probability")
    axes[1].set_title(f"Real-time {horizon}-month-ahead bear-market probability (out of sample)",
                      fontsize=9, fontweight="normal")
    axes[1].legend(loc="lower right", bbox_to_anchor=(1, 1.0), fontsize=7.5, ncol=2)
    _date_axis(axes[1], 5)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    _save(fig, directory, "hero")


def skill_intervals(boot: pd.DataFrame, models: tuple[str, ...], horizons: tuple[int, ...], block: int,
                    directory: Path) -> None:
    """Out-of-sample Brier skill by horizon with 90% block-bootstrap intervals."""
    fig, ax = plt.subplots(figsize=(7.2, 3.3))
    ax.axhline(0, color=MUTED, lw=0.8, ls="--")
    x = np.arange(len(horizons))
    offsets = np.linspace(-0.24, 0.24, len(models))
    for m, off in zip(models, offsets):
        est = np.array([100 * boot.loc[(h, m), "bss"] for h in horizons])
        lo = np.array([100 * boot.loc[(h, m), "bss_lo"] for h in horizons])
        hi = np.array([100 * boot.loc[(h, m), "bss_hi"] for h in horizons])
        ax.errorbar(x + off, est, yerr=[est - lo, hi - est], fmt="o", ms=4.5, color=MODEL_COLORS[m],
                    elinewidth=1.2, capsize=0, label=BEAR_MODELS[m])
    ax.set_xticks(x)
    ax.set_xticklabels([f"{h} month{'s' if h > 1 else ''}" for h in horizons])
    ax.set_xlabel("Forecast horizon")
    ax.set_ylabel("Brier skill vs unconditional (%)")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=len(models), fontsize=7.5)
    ax.set_title(f"Out-of-sample skill with 90% block-bootstrap intervals ({block}-month blocks)", pad=22)
    _save(fig, directory, "fig8_skill_intervals")
