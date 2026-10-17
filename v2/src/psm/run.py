"""Reproduce every table, figure and reported number: ``python -m psm.run``."""

from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path

import numpy as np
import pandas as pd

from psm import figures, report
from psm.config import (
    ARCHIVED_REPORTED_FILE,
    FULL_SAMPLE,
    HORIZONS,
    OOS_FIRST_ORIGIN,
    OUTPUT_DIR,
    SEED,
    THESIS_SAMPLE,
)
from psm.data import audit_archived_leads, load_raw
from psm.features import (
    FEATURE_LABELS,
    FORECAST_FEATURES,
    ORIGINAL_FEATURES,
    build_features,
    real_price_index,
    real_returns,
    standardize,
)
from psm.forecast import BEAR_MODELS, bear_forecasts, fit_vintage_regimes, regime_prob_forecasts
from psm.labels import episodes, label_series
from psm.metrics import auc, brier, clark_west, diebold_mariano, log_loss
from psm.regimes import fit_regimes
from psm.regressions import fit_beta, fit_binary, fit_ols
from psm.replication import (
    ARCHIVED_HORIZONS,
    archived_frame,
    archived_in_sample,
    archived_mspe,
    fit_archived_regimes,
)
from psm.tables import fmt, write_table

ORIGINAL_KEYS = [f.key for f in ORIGINAL_FEATURES]
FORECAST_KEYS = [f.key for f in FORECAST_FEATURES]
FIGURE_MODELS = ("logit_all", "logit_dy", "ms", "persist")


def log(msg: str, _t0: list[float] = [time.time()]) -> None:  # noqa: B006
    print(f"[{time.time() - _t0[0]:7.1f}s] {msg}", flush=True)


def _num(x: float, digits: int = 3) -> str:
    return fmt(float(x), digits)


def oos_metrics(fc: pd.DataFrame) -> pd.DataFrame:
    """Brier, skill, log loss, AUC and DM tests for every (horizon, model)."""
    rows = []
    for h, sub in fc.groupby("horizon"):
        wide_p = sub.pivot(index="origin", columns="model", values="p")
        y = sub[sub.model == "uncond"].set_index("origin")["y"].reindex(wide_p.index).to_numpy()
        loss = (wide_p.sub(y, axis=0)) ** 2
        b_unc = loss["uncond"].mean()
        for m in BEAR_MODELS:
            p = wide_p[m].to_numpy()
            rows.append(
                {
                    "horizon": h,
                    "model": m,
                    "n": len(y),
                    "bear_share": y.mean(),
                    "brier": brier(p, y),
                    "bss": 1 - loss[m].mean() / b_unc,
                    "log_loss": log_loss(p, y),
                    "auc": auc(p, y),
                    "p_uncond": diebold_mariano(loss[m].to_numpy(), loss["uncond"].to_numpy(), h)[1],
                    "p_persist": diebold_mariano(loss[m].to_numpy(), loss["persist"].to_numpy(), h)[1],
                }
            )
    return pd.DataFrame(rows).set_index(["horizon", "model"])


def mspe_summary(fc: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (h, key), g in fc.groupby(["horizon", "predictor"]):
        for model in ("OLS", "Beta"):
            col = model.lower()
            r_pred, u_pred = g[f"{col}_restricted"].to_numpy(), g[col].to_numpy()
            a = g["actual"].to_numpy()
            stat, p = clark_west(a, r_pred, u_pred, h)
            rows.append(
                {
                    "model": model,
                    "predictor": key,
                    "k": h,
                    "mspe_ratio": np.mean((u_pred - a) ** 2) / np.mean((r_pred - a) ** 2),
                    "cw_stat": stat,
                    "cw_p": p,
                    "n": len(a),
                }
            )
    return pd.DataFrame(rows)


def main(out: Path = OUTPUT_DIR, clean: bool = True) -> None:
    np.random.seed(SEED)
    if clean and out.exists():
        shutil.rmtree(out)
    tables, figs, res = out / "tables", out / "figures", out / "results"
    for d in (tables, figs, res):
        d.mkdir(parents=True, exist_ok=True)
    numbers: dict = {}

    # ------------------------------------------------------------------ data
    raw_data = load_raw()
    audit = audit_archived_leads(raw_data.frame)
    audit.to_csv(res / "archived_lead_audit.csv", index=False)
    raw = raw_data.frame.loc[: FULL_SAMPLE.end]
    price = real_price_index(raw).dropna()
    idx = price.index
    returns = real_returns(raw).reindex(idx)
    feats = build_features(raw).reindex(idx)
    labels = label_series(price)
    ep = episodes(price)
    pd.concat([price, returns, labels, feats], axis=1).to_csv(res / "panel.csv", index_label="date")
    ep.to_csv(res / "episodes.csv", index=False)
    a1 = audit.iloc[0]
    post = labels.loc[THESIS_SAMPLE.start :]
    numbers["data"] = {
        "first": f"{raw_data.frame.index[0]:%B %Y}",
        "last_raw": f"{raw_data.frame.index[-1]:%B %Y}",
        "end": f"{FULL_SAMPLE.end:%B %Y}",
        "months": str(len(idx)),
        "dropped_rows": str(len(raw_data.dropped_rows)),
        "audit_future": f"{int(a1.match_future):,}",
        "audit_pairs": f"{int(a1.pairs_future):,}",
        "audit_past": str(int(a1.match_past)),
        "n_bears": str(len(ep)),
        "n_bears_thesis": str(int((ep.peak >= THESIS_SAMPLE.start).sum())),
        "bear_share_full": _num(100 * labels.bear.mean(), 1),
        "bear_share_thesis": _num(100 * post.bear.mean(), 1),
        "median_bear_months": _num(ep.months.median(), 0),
        "median_decline": _num(-ep.decline_pct.median(), 1),
        "median_confirm_lag": _num(
            np.median([(c.year - p.year) * 12 + c.month - p.month for p, c in zip(ep.peak, ep.confirmed)]), 0
        ),
    }
    write_table(report.variables_table(feats.loc[THESIS_SAMPLE.start :], THESIS_SAMPLE.label()), tables)
    write_table(report.episodes_table(ep), tables)
    log("data, features and bear dating")

    # --------------------------------------------------------------- regimes
    fits = {
        "MS, 1960-2023": fit_regimes(returns.loc[THESIS_SAMPLE.start :], "mean_var"),
        "MS-AR(1), 1960-2023": fit_regimes(returns.loc[THESIS_SAMPLE.start :], "ar1"),
        "MS, 1900-2023": fit_regimes(returns, "mean_var"),
        "MS-AR(1), 1900-2023": fit_regimes(returns, "ar1"),
    }
    write_table(report.regime_table(fits), tables)
    main_fit = fits["MS-AR(1), 1960-2023"]
    mv_fit = fits["MS, 1960-2023"]
    q = main_fit.filtered
    pd.DataFrame({"filtered": main_fit.filtered, "smoothed": main_fit.smoothed}).to_csv(
        res / "regime_probabilities.csv", index_label="date"
    )
    lab_q = labels.bear.reindex(q.index)
    numbers["ms"] = {
        "bull_mean": _num(main_fit.means[0], 2),
        "bear_mean": _num(main_fit.means[1], 2),
        "bull_sd": _num(np.sqrt(main_fit.variances[0]), 2),
        "bear_sd": _num(np.sqrt(main_fit.variances[1]), 2),
        "p_bull": _num(main_fit.transition[0, 0], 3),
        "p_bear": _num(main_fit.transition[1, 1], 3),
        "dur_bull": _num(main_fit.durations[0], 1),
        "dur_bear": _num(main_fit.durations[1], 1),
        "ar": _num(main_fit.ar, 3),
        "aic_ar": _num(main_fit.aic, 1),
        "aic_mv": _num(mv_fit.aic, 1),
        "mv_p_bull": _num(mv_fit.transition[0, 0], 3),
        "mv_p_bear": _num(mv_fit.transition[1, 1], 3),
        "filtered_mean": _num(100 * q.mean(), 1),
        "corr_filtered_bear": _num(np.corrcoef(q, lab_q)[0, 1], 2),
        "corr_smoothed_bear": _num(np.corrcoef(main_fit.smoothed, lab_q)[0, 1], 2),
        "auc_filtered_now": _num(auc(q.to_numpy(), lab_q.to_numpy()), 3),
        "auc_smoothed_now": _num(auc(main_fit.smoothed.to_numpy(), lab_q.to_numpy()), 3),
        "full_dur_bull": _num(fits["MS-AR(1), 1900-2023"].durations[0], 1),
        "full_dur_bear": _num(fits["MS-AR(1), 1900-2023"].durations[1], 1),
    }
    log("regime models")

    # ------------------------------------- corrected archived specification
    orig = standardize(feats.loc[q.index, ORIGINAL_KEYS])
    ols, beta = {}, {}
    for key in ORIGINAL_KEYS:
        for h in HORIZONS:
            ols[(key, h)] = fit_ols(q, orig[[key]], h, scale=100)
            beta[(key, h)] = fit_beta(q, orig[[key]], h)
    write_table(report.original_spec_table(ols, beta, HORIZONS), tables)
    pd.DataFrame(
        [
            {"model": m, "predictor": k, "h": h, "coef": f.coefs[k].estimate, "se": f.coefs[k].se,
             "p": f.coefs[k].pvalue, "nobs": f.nobs, **f.stats}
            for m, d in (("OLS", ols), ("Beta", beta)) for (k, h), f in d.items()
        ]
    ).to_csv(res / "original_spec_in_sample.csv", index=False)
    sig5 = {h: sum(ols[(k, h)].coefs[k].pvalue < 0.05 for k in ORIGINAL_KEYS) for h in HORIZONS}
    numbers["orig"] = {
        **{f"sig5_h{h}": str(v) for h, v in sig5.items()},
        "n_pred": str(len(ORIGINAL_KEYS)),
        "max_r2": _num(max(f.stats["r2"] for f in ols.values()), 3),
        "max_r2_label": FEATURE_LABELS[max(ols, key=lambda kh: ols[kh].stats["r2"])[0]],
        "div_h1": report.coef_cell(ols[("div_growth", 1)].coefs["div_growth"], 2),
        "tr_h1": report.coef_cell(ols[("tr_ret", 1)].coefs["tr_ret"], 2),
        "tr_h1_r2": _num(ols[("tr_ret", 1)].stats["r2"], 3),
        "trse_h1": report.coef_cell(ols[("trse_growth", 1)].coefs["trse_growth"], 2),
        "trse_h1_r2": _num(ols[("trse_growth", 1)].stats["r2"], 3),
    }
    log("corrected archived specification, in sample")

    # ------------------------------------------------- replication (archived)
    adf = archived_frame(raw_data.frame)
    arch = fit_archived_regimes(adf)
    arch_is = archived_in_sample(adf, arch.regime_prob)
    arch_is.to_csv(res / "replication_in_sample.csv", index=False)
    arch_mspe = archived_mspe(adf, arch.regime_prob, HORIZONS)
    arch_mspe_all = archived_mspe(adf, arch.regime_prob, ARCHIVED_HORIZONS)
    arch_mspe_all.to_csv(res / "replication_mspe.csv", index=False)
    reported = pd.read_csv(ARCHIVED_REPORTED_FILE)

    def pairs(table: str, stat: str, source: pd.DataFrame, value: str, model: str | None = None) -> pd.DataFrame:
        rep = reported[(reported.table == table) & (reported.statistic == stat)]
        src = source if model is None else source[source.model == model]
        merged = rep.merge(src, on=["predictor", "k"])
        return pd.DataFrame({"reported": merged["value"], "replicated": merged[value]})

    scatter = {
        "OLS coefficients\n(4 predictors x 7 horizons)": pairs("ols_in_sample", "coef", arch_is, "coef"),
        "OLS R²\n(6 predictors x 7 horizons)": pairs("ols_in_sample", "r2", arch_is, "r2"),
        "Archived 'MSPE ratio', OLS\n(7 predictors x 7 horizons)": pairs("ols_forecast_ratio", "ratio", arch_mspe_all, "archived_ratio", "OLS"),
    }
    figures.replication_scatter(scatter, figs)
    rep_t = reported[reported.table == "transition"].set_index("statistic")["value"]

    def arch_val(pred: str, k: int, col: str) -> float:
        return float(arch_is[(arch_is.predictor == pred) & (arch_is.k == k)][col].iloc[0])

    def reported_val(table: str, pred: str, k: int, stat: str) -> float:
        r = reported[(reported.table == table) & (reported.predictor == pred) & (reported.k == k) & (reported.statistic == stat)]
        return float(r["value"].iloc[0])

    log("replication of archived specification")

    # ------------------------------------- corrected forecasts of Q(t+h)
    first_test = arch_mspe[arch_mspe.k == 1].test_start.iloc[0]
    q_origins = q.index[(q.index >= first_test)]
    q_inputs = feats.loc[q.index, ORIGINAL_KEYS].assign(q_now=q)
    q_fc = regime_prob_forecasts(q, q_inputs, q_origins, HORIZONS, q.index[0])
    q_fc.to_csv(res / "regime_prob_forecasts.csv", index=False)
    corr_mspe = mspe_summary(q_fc)
    corr_mspe.to_csv(res / "regime_prob_mspe.csv", index=False)
    period_c = f"{q_origins[0]:%Y:%m} to {q_origins[-1] - pd.DateOffset(months=1):%Y:%m} for h = 1"
    write_table(report.mspe_table(arch_mspe, corr_mspe, HORIZONS, period_c), tables)

    def mspe_val(df: pd.DataFrame, model: str, pred: str, k: int, col: str) -> float:
        return float(df[(df.model == model) & (df.predictor == pred) & (df.k == k)][col].iloc[0])

    ols_all = corr_mspe[corr_mspe.model == "OLS"]
    ols_c = ols_all[ols_all.predictor != "q_now"]
    q_now = ols_all[ols_all.predictor == "q_now"].set_index("k")
    numbers["mspe"] = {
        "test_start": f"{first_test:%B %Y}",
        "n_below1_ols": str(int((ols_c.mspe_ratio < 1).sum())),
        "n_cells": str(len(ols_c)),
        "n_cw10_ols": str(int((ols_c.cw_p < 0.10).sum())),
        "min_ratio_ols": _num(ols_c.mspe_ratio.min(), 3),
        "min_ratio_label": FEATURE_LABELS[ols_c.loc[ols_c.mspe_ratio.idxmin(), "predictor"]],
        "min_ratio_h": str(int(ols_c.loc[ols_c.mspe_ratio.idxmin(), "k"])),
        "arch_b_below1": str(int((arch_mspe[arch_mspe.model == "OLS"].mspe_ratio < 1).sum())),
        "arch_a_below1": str(int((arch_mspe[arch_mspe.model == "OLS"].archived_ratio < 1).sum())),
        "arch_cells": str(int((arch_mspe.model == "OLS").sum())),
        **{f"qnow_h{h}": _num(q_now.loc[h, "mspe_ratio"], 3) for h in HORIZONS},
    }
    rep_rows = [
        ("P(bull to bull)", _num(rep_t["p_bull_bull"]), _num(arch.transition[0, 0]), _num(main_fit.transition[0, 0])),
        ("P(bear to bear)", _num(rep_t["p_bear_bear"]), _num(arch.transition[1, 1]), _num(main_fit.transition[1, 1])),
        ("Dividend, k = 1: coefficient", _num(reported_val("ols_in_sample", "realdividend", 1, "coef")),
         _num(arch_val("realdividend", 1, "coef")), report.coef_cell(ols[("div_growth", 1)].coefs["div_growth"], 2) + " pp"),
        ("Dividend, k = 6: coefficient", _num(reported_val("ols_in_sample", "realdividend", 6, "coef")),
         _num(arch_val("realdividend", 6, "coef")), report.coef_cell(ols[("div_growth", 6)].coefs["div_growth"], 2) + " pp"),
        ("Dividend, k = 6: R²", _num(reported_val("ols_in_sample", "realdividend", 6, "r2")),
         _num(arch_val("realdividend", 6, "r2")), _num(ols[("div_growth", 6)].stats["r2"])),
        ("Total return, k = 1: R²", _num(reported_val("ols_in_sample", "realtotalreturn", 1, "r2")),
         _num(arch_val("realtotalreturn", 1, "r2")), _num(ols[("tr_ret", 1)].stats["r2"])),
        ("TR-scaled earnings, k = 1: R²", _num(reported_val("ols_in_sample", "realtrscaledearnings", 1, "r2")),
         _num(arch_val("realtrscaledearnings", 1, "r2")), _num(ols[("trse_growth", 1)].stats["r2"])),
        ("Dividend, k = 1: OLS forecast ratio", _num(reported_val("ols_forecast_ratio", "realdividend", 1, "ratio")),
         _num(mspe_val(arch_mspe, "OLS", "realdividend", 1, "archived_ratio")),
         _num(mspe_val(corr_mspe, "OLS", "div_growth", 1, "mspe_ratio"))),
        ("Total return, k = 1: OLS forecast ratio", _num(reported_val("ols_forecast_ratio", "realtotalreturn", 1, "ratio")),
         _num(mspe_val(arch_mspe, "OLS", "realtotalreturn", 1, "archived_ratio")),
         _num(mspe_val(corr_mspe, "OLS", "tr_ret", 1, "mspe_ratio"))),
        ("TR-scaled earnings, k = 1: OLS forecast ratio", _num(reported_val("ols_forecast_ratio", "realtrscaledearnings", 1, "ratio")),
         _num(mspe_val(arch_mspe, "OLS", "realtrscaledearnings", 1, "archived_ratio")),
         _num(mspe_val(corr_mspe, "OLS", "trse_growth", 1, "mspe_ratio"))),
    ]
    rep_df = pd.DataFrame(rep_rows, columns=["label", "reported", "replicated", "corrected"])
    rep_df.to_csv(res / "replication_summary.csv", index=False)
    write_table(report.replication_table(rep_df), tables)
    numbers["rep"] = {
        "p_bull_reported": _num(rep_t["p_bull_bull"]),
        "p_bear_reported": _num(rep_t["p_bear_bear"]),
        "p_bull_replicated": _num(arch.transition[0, 0]),
        "p_bear_replicated": _num(arch.transition[1, 1]),
        "corr_coef": _num(np.corrcoef(*scatter["OLS coefficients\n(4 predictors x 7 horizons)"].T.to_numpy())[0, 1], 3),
        "corr_r2": _num(np.corrcoef(*scatter["OLS R²\n(6 predictors x 7 horizons)"].T.to_numpy())[0, 1], 3),
        "corr_ratio": _num(np.corrcoef(*scatter["Archived 'MSPE ratio', OLS\n(7 predictors x 7 horizons)"].T.to_numpy())[0, 1], 3),
        "div_ratio_reported": _num(reported_val("ols_forecast_ratio", "realdividend", 1, "ratio")),
        "div_ratio_replicated": _num(mspe_val(arch_mspe, "OLS", "realdividend", 1, "archived_ratio")),
        "div_ratio_true": _num(mspe_val(arch_mspe, "OLS", "realdividend", 1, "mspe_ratio")),
        "div_ratio_corrected": _num(mspe_val(corr_mspe, "OLS", "div_growth", 1, "mspe_ratio")),
        "div_k1_reported": _num(reported_val("ols_in_sample", "realdividend", 1, "coef")),
        "div_k1_replicated": _num(arch_val("realdividend", 1, "coef")),
    }
    log("corrected regime-probability forecasts")

    # ------------------------------------------ bear-market models (in sample)
    fx = feats[FORECAST_KEYS]
    valid = fx.dropna().index
    fz = standardize(fx.loc[valid])
    logit = {h: fit_binary(labels.bear, fz, h, "logit") for h in HORIZONS}
    probit = {h: fit_binary(labels.bear, fz, h, "probit") for h in HORIZONS}
    write_table(report.logit_table(logit, probit, HORIZONS), tables)
    figures.forest(logit, FEATURE_LABELS, figs)
    pd.DataFrame(
        [
            {"model": m, "h": h, "term": k, "coef": c.estimate, "se": c.se, "p": c.pvalue, **f.stats}
            for m, d in (("logit", logit), ("probit", probit)) for h, f in d.items() for k, c in f.coefs.items()
        ]
    ).to_csv(res / "bear_in_sample.csv", index=False)
    numbers["logit"] = {
        "start": f"{logit[1].start:%B %Y}",
        **{f"r2_h{h}": _num(logit[h].stats["pseudo_r2"], 3) for h in HORIZONS},
        **{
            f"{k}_h{h}": report.coef_cell(logit[h].coefs[k], 2)
            for k in FORECAST_KEYS for h in HORIZONS
        },
    }
    log("bear-market models, in sample")

    # --------------------------------------- bear-market forecasts (out of sample)
    origins = idx[(idx >= OOS_FIRST_ORIGIN) & (idx < idx[-1])]
    vint = fit_vintage_regimes(returns, origins, "ar1", progress=None)
    fc = bear_forecasts(price, fx, labels.bear_now, labels.bear, returns, vint, origins, HORIZONS)
    fc.to_csv(res / "bear_forecasts.csv", index=False)
    met = oos_metrics(fc)
    met.to_csv(res / "bear_oos_metrics.csv")
    period = f"{fc.target_date.min():%Y:%m}-{fc.target_date.max():%Y:%m}"
    write_table(report.oos_table(met, HORIZONS, "targets " + period), tables)
    numbers["oos"] = {"period": period, "first_origin": f"{origins[0]:%B %Y}", "n_refits": str(len(vint.fits))}
    for h in HORIZONS:
        block = {}
        for m in BEAR_MODELS:
            r = met.loc[(h, m)]
            block[m] = {
                "brier": _num(r.brier, 3),
                "bss": _num(100 * r.bss, 1),
                "ll": _num(r.log_loss, 3),
                "auc": _num(r.auc, 3),
                "p_unc": _num(r.p_uncond, 3),
                "p_per": _num(r.p_persist, 3),
            }
        sub = met.loc[h]
        best = sub.brier.idxmin()
        block["best"] = BEAR_MODELS[best]
        block["best_key"] = best
        block["n"] = str(int(sub.loc["uncond", "n"]))
        block["share"] = _num(100 * sub.loc["uncond", "bear_share"], 1)
        numbers["oos"][f"h{h}"] = block
    beats_persist = [
        h for h in HORIZONS
        if met.loc[(h, "logit_state"), "brier"] < met.loc[(h, "persist"), "brier"]
        and met.loc[(h, "logit_state"), "p_persist"] < 0.05
    ]
    numbers["oos"]["state_beats_persist_5pct"] = ", ".join(str(h) for h in beats_persist) or "none"
    figures.oos_paths(fc, labels.bear, (1, 6, 12), FIGURE_MODELS, figs)
    figures.calibration_curves(fc, HORIZONS, FIGURE_MODELS, figs)
    figures.roc_curves(fc, HORIZONS, FIGURE_MODELS, met, figs)
    log("bear-market forecasts, out of sample")

    # -------------------------------------------------------- other figures
    figures.price_history(price, labels.bear, figs)
    figures.regime_probabilities(main_fit.filtered, main_fit.smoothed, labels.bear, figs)
    hero_h, hero_model = 1, "logit_all"
    figures.hero(price, labels.bear, fc, hero_model, hero_h, figs)
    numbers["hero"] = {"h": str(hero_h), "model": BEAR_MODELS[hero_model]}

    (out / "numbers.json").write_text(json.dumps(numbers, indent=2, ensure_ascii=False) + "\n")
    log(f"done: outputs in {out}")


def cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--keep", action="store_true", help="do not delete the output directory first")
    args = parser.parse_args()
    main(args.out, clean=not args.keep)


if __name__ == "__main__":
    cli()
