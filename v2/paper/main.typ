// Predictive Stochastic Modeling for Financial Markets, revised edition.
// Every number in this document is read from ../output/numbers.json or from
// the generated tables in ../output/tables, both produced by `python -m psm.run`.

#let n = json("../output/numbers.json")
#let d = n.design
#let o = n.oos

#set document(title: "Predictive Stochastic Modeling for Financial Markets (Revised Edition)", author: "Jaden Fix", date: none)
#set page(paper: "us-letter", margin: (x: 1in, y: 1in), numbering: "1", number-align: center)
#set text(font: ("New Computer Modern", "Libertinus Serif"), size: 11pt, lang: "en")
#set par(justify: true, leading: 0.62em, first-line-indent: 1.2em, spacing: 0.62em)
#set heading(numbering: "1.1")
#show heading: set block(above: 1.4em, below: 0.8em)
#show heading.where(level: 1): set text(size: 13pt)
#show heading.where(level: 2): set text(size: 11pt)
#set math.equation(numbering: "(1)")
#show figure.where(kind: table): set figure.caption(position: top)
#show figure: set block(breakable: false)
#show figure.caption: set text(size: 9.5pt)
#set figure(gap: 0.8em, placement: auto)
#show link: set text(fill: rgb("#1f4e79"))

// ------------------------------------------------------------------ title page
#page(numbering: none)[
  #v(1.6in)
  #align(center)[
    #text(size: 20pt, weight: "bold")[Predictive Stochastic Modeling\ for Financial Markets]
    #v(0.6em)
    #text(size: 13pt)[Revised edition]
    #v(2.2em)
    #text(size: 13pt)[Jaden Fix]
    #v(0.4em)
    #text(size: 11pt)[Original thesis advisor: Jonathan Kaplan]
    #v(3em)
    #block(width: 80%)[
      #set par(justify: true, first-line-indent: 0em)
      #set text(size: 10pt)
      This is a revised edition of the undergraduate thesis that received the Adam Smith Award.
      It re-estimates the original models with a corrected data alignment, adds a real-time
      out-of-sample evaluation, and rewrites the paper around what the evidence supports. The
      original award version (February 2025) and its R code are preserved unchanged in the
      repository: #link("https://github.com/jadenfix/Predictive-Stochastic-Modeling-for-Financial-Markets-")[github.com/jadenfix/Predictive-Stochastic-Modeling-for-Financial-Markets-].
    ]
  ]
]

// ------------------------------------------------------------------ abstract
#align(center)[#text(size: 12pt, weight: "bold")[Abstract]]
#block(inset: (x: 0.4in))[
  #set par(first-line-indent: 0em)
  #set text(size: 10pt)
  Can market and macroeconomic indicators forecast bear markets in the S&P 500? The award
  version of this thesis answered yes, but its evidence rested on three timing errors: the
  Markov-switching model conditioned on next month's price, the "k months ahead" regressions
  actually explained the regime probability k months in the past, and the out-of-sample
  "MSPE ratio" divided squared mean errors instead of mean squared errors. I replicate the
  archived results almost exactly (correlation #n.rep.corr_coef across the reported
  coefficients), correct each error, and evaluate real-time forecasts made from #o.first_origin
  onward with every model re-estimated using only data available at the forecast origin. A
  two-regime MS-AR(1) model of real returns still separates a calm bull regime from a short,
  volatile bear regime (expected durations #n.ms.dur_bull and #n.ms.dur_bear months). Out of
  sample, a logit on #d.n_forecast_features state variables reduces the one-month Brier score by
  #o.h1.logit_all.bss% relative to the unconditional frequency, but simply knowing whether the
  market is currently in a confirmed bear market achieves #o.h1.persist.bss%, and none of the
  #o.n_challengers model-horizon pairs beats that persistence benchmark at the 5% level. Beyond
  three months the predictors add little: at twelve months no model is reliably better than the
  unconditional frequency. The dividend yield is the most robust single predictor, but its
  gains are modest. Bear markets are partly identifiable in real time; they are not
  meaningfully predictable months in advance with these data.
]

= Introduction

Bear markets are costly for investors and matter for policy, and whether they can be
anticipated is a direct test of how much public information prices already contain. A long
literature finds that equity returns alternate between persistent bull and bear regimes
(Maheu and McCurdy, 2000; Ang and Timmermann, 2012) and that valuation ratios and macroeconomic
conditions carry some information about future returns and downturns (Campbell and Shiller,
1988; Fama and French, 1988; Chen, 2009). The award version of this thesis combined these ideas:
it estimated a two-state Markov-switching model on the S&P 500, treated the filtered probability
of the bear state as the object to forecast, and related it to lagged market and macroeconomic
indicators with OLS and beta regressions. It reported strong in-sample relationships and
out-of-sample loss ratios against an intercept-only benchmark as low as #n.rep.div_ratio_reported.

This revised edition revisits that analysis with a stricter standard: a forecast may use only
information that was published at the time it is made, and forecasting skill is measured only
out of sample. Rebuilding the code from scratch revealed three errors in the archived workflow,
each of which lets future information or an incorrect loss function flatter the results
(@sec-correction). I first replicate the archived specification including those errors, which
confirms that they explain the reported numbers. I then correct them and extend the analysis in
three ways. First, I date bear markets with an explicit, reproducible rule so that the target is
an observable event rather than a model output. Second, I add logit and probit models, the
natural benchmarks for a binary outcome (Estrella and Mishkin, 1998; Chen, 2009). Third, I
evaluate real-time forecasts over #o.period with expanding-window re-estimation and compare them
with two simple baselines: the unconditional bear frequency and the persistence of the current,
real-time market state.

The corrected evidence is more modest than the original. Regime-switching structure in returns
is strong and stable. Indicators such as inflation, volatility and the dividend yield are
associated with bear markets in sample. In real time, however, most of the short-horizon
forecastability comes from recognizing a bear market that is already under way, and little
survives at horizons of six months or more.

= Related literature

Regime-switching models in the tradition of Hamilton (1989) describe the stock market as moving
between a high-return, low-volatility state and a low-return, high-volatility state. Maheu and
McCurdy (2000) identify bull and bear markets this way, and Ang and Timmermann (2012) survey the
evidence that regime changes are a pervasive feature of financial markets. Rule-based dating is
the main alternative: Pagan and Sossounov (2003) adapt business-cycle turning-point algorithms
to equity prices, and Lunde and Timmermann (2004) define bull and bear markets by threshold
movements from the latest peak or trough. Chen (2009) and Chen, Chen and Chou (2017) use such
dates as the dependent variable in probit models and find that macroeconomic and credit
variables help predict bear markets.

On the predictor side, Campbell and Shiller (1988) and Fama and French (1988) document that
dividend yields forecast long-horizon returns, while Goetzmann and Jorion (1993), Stambaugh (1999)
and Lewellen (1999) show that inference with persistent, price-scaled predictors is delicate.
Pontiff and Schall (1998) report related evidence for book-to-market ratios, and Hammerschmidt
and Lohre (2018) find that return predictability itself varies across regimes. Welch and Goyal
(2008) emphasize that many predictors that look strong in sample fail out of sample, which is
the standard this edition adopts.

= Data <sec-data>

== Source and timing

The data are the monthly U.S. stock market series compiled by Robert Shiller (Shiller, 2015),
archived in the repository as `one45.csv`. The file covers #n.data.first to #n.data.last_raw; I use
observations through #n.data.end, the last month with complete dividend and earnings data. One
trailing row of the file is a text footnote and is dropped. The S&P Composite price is a monthly
average of daily closes, so it is known at the end of each month. I treat the end of month $t$
as the forecast origin and impose publication lags on everything else: the consumer price index
enters with a lag of #d.cpi_lag month, and dividends and earnings, which Shiller interpolates
from quarterly reports, enter with a lag of #d.fund_lag months. Real values are obtained by
deflating with the CPI available at $t$. @tab:variables lists the predictors, their
construction and their publication lags.

#include "../output/tables/variables.typ"

The archived file also contains columns labeled `realpricelag` to `realpricelag4`. An audit of
the file shows that these are leads, not lags: on #n.data.audit_future of #n.data.audit_pairs
comparable rows, `realpricelag` equals the following month's real price, and it matches the
previous month's price on only #n.data.audit_past rows. The corrected pipeline never reads these
columns, and an automated test confirms that every predictor is unchanged when all data after
its forecast origin are altered.

== Dating bear markets <sec-dating>

I date bear markets on the real price index with a symmetric threshold rule in the spirit of
Lunde and Timmermann (2004). Starting from a bull state, the running maximum is a candidate peak;
when the index falls #d.decline% below it, the peak is confirmed and a bear market begins in the
following month. In the bear state the running minimum is a candidate trough; when the index
rises #d.rise% above it, the trough is confirmed and the bear market ends at the trough month. The
rule yields #n.data.n_bears bear markets since #d.full_start_year, #n.data.n_bears_thesis of them
beginning after #d.thesis_start_year (@tab:episodes, @fig:price). The median bear market lasts
#n.data.median_bear_months months with a median peak-to-trough decline of #n.data.median_decline%.
Bear months account for #n.data.bear_share_full% of the full sample and #n.data.bear_share_thesis%
of #d.thesis_sample.

The dated labels are ex post: a peak is only known to have been a peak once the #d.decline%
decline has occurred, which took a median of #n.data.median_confirm_lag months. The same rule run
on data through month $t$ gives the real-time state, which is observable at $t$, and "vintage"
labels for all earlier months. The out-of-sample exercise trains every model on vintage labels
only.

#figure(
  image("../output/figures/fig1_price_bears.png", width: 100%),
  caption: [Real S&P 500 price index (log scale) with dated bear markets shaded.],
) <fig:price>

#include "../output/tables/episodes.typ"

= Methodology

== Markov-switching model of returns

Let $r_t = 100 dot Delta ln P_t$ be the monthly real return. The main regime model is a
two-state Markov-switching autoregression with switching mean and variance (Hamilton, 1989):
$
  r_t - mu_(S_t) = phi (r_(t-1) - mu_(S_(t-1))) + sigma_(S_t) epsilon_t, quad
  epsilon_t tilde.op N(0, 1), quad S_t in {"bull", "bear"},
$ <eq:msar>
where $S_t$ follows a first-order Markov chain with transition probabilities
$p_(i j) = Pr(S_t = j | S_(t-1) = i)$. Setting $phi = 0$ gives the switching mean-variance
model. The bear regime is the one with the lower mean. The expected duration of regime $i$ is
$1 \/ (1 - p_(i i))$. The Hamilton filter delivers the filtered probability
$
  Q_t = Pr(S_t = "bear" | r_1, dots, r_t),
$ <eq:filtered>
which uses only returns through $t$ and is therefore a legitimate real-time quantity once the
parameters are fixed. The smoothed probability $Pr(S_t = "bear" | r_1, dots, r_T)$ conditions on
the whole sample, so I use it only for retrospective description. An $h$-step regime forecast is
$Pr(S_(t+h) = "bear" | r_1, dots, r_t) = [Q_t^c, Q_t] bold(P)^h e_2$, where $bold(P)$ is the
transition matrix and $Q_t^c = 1 - Q_t$.

== Predictive regressions for the regime probability

Following the original thesis, each predictor $x_t$ enters a separate regression for the regime
probability $h$ months ahead:
$
  Q_(t+h) = alpha + beta x_t + e_(t+h).
$ <eq:ols>
I estimate @eq:ols by OLS with Newey and West (1987) standard errors, since overlapping horizons
and the persistence of $Q_t$ make the errors serially correlated. Because $Q_t$ lies in the unit
interval, I also estimate a beta regression (Ferrari and Cribari-Neto, 2004),
$
  Q_(t+h) tilde.op "Beta"(mu_t phi, (1 - mu_t) phi), quad
  "logit"(mu_t) = alpha + beta x_t,
$ <eq:beta>
after the standard compression of $Q$ into the open interval (Smithson and Verkuilen, 2006),
again with Newey-West standard errors. Predictors are standardized, so $beta$ measures the
effect of a one-standard-deviation change. The test of $beta = 0$ is the test of
no predictability that the original thesis framed in terms of market efficiency.

== Binary models for dated bear markets

The regime probability is itself an estimate. The dated bear indicator $y_(t+h)$ is an
observable target, and the natural model for it is a binary regression,
$
  Pr(y_(t+h) = 1 | x_t) = F(alpha + x_t^top beta),
$ <eq:logit>
with $F$ the logistic (logit) or standard normal (probit) distribution function. The
#d.n_forecast_features predictors in $x_t$ are the log dividend yield, the log CAPE ratio with
lagged earnings, twelve-month CPI inflation, the twelve-month change in the ten-year Treasury
yield, the twelve-month real price change, and twelve-month realized volatility.

== Out-of-sample design <sec-oos-design>

Forecasts are made at every month-end from #o.first_origin onward for horizons of
#d.horizons months. At each origin $t$ every model is re-estimated on an expanding window using
only (i) predictors dated $s <= t$, (ii) vintage bear labels from dating the price history
through $t$, so that a training pair $(x_s, y_(s+h))$ requires $s + h <= t$, and (iii) for the
regime model, parameters re-estimated each January on returns through the origin
(#o.n_refits estimations) and filtered probabilities from those parameters. The training data
start in #n.logit.start, when all predictors are first available. I compare
#d.n_models forecasts:

- *Unconditional frequency*: the training-sample share of bear months $h$ months ahead.
- *Persistence*: the training-sample frequency of a bear market $h$ months ahead, conditional
  on the current real-time state (in a confirmed bear market or not).
- *MS-AR(1)*: a logit recalibration of the $h$-step regime forecast from the filtered
  probability.
- *Logit: dividend yield*, the single predictor emphasized by the original thesis.
- *Logit* and *probit* on all #d.n_forecast_features predictors.
- *Logit: all predictors + state*, which adds the real-time state to test whether the
  predictors add to persistence.

Accuracy is measured by the Brier score (Brier, 1950), the log loss (with probabilities
truncated to $[#d.floor, 1 - #d.floor]$), the area under the ROC curve, and calibration curves.
Brier skill is the percentage reduction in the Brier score relative to the unconditional
frequency. Differences in Brier score are tested with the Diebold and Mariano (1995) statistic
with the small-sample correction of Harvey, Leybourne and Newbold (1997). For forecasts of the
regime probability itself (@eq:ols and @eq:beta), I report ratios of mean squared prediction
errors against the intercept-only model and the Clark and West (2007) test for nested models.

#place.flush()

= In-sample results

== Regimes in real returns

@tab:regimes reports the regime models. The structure is clear and stable across
specifications and samples. In the MS-AR(1) model for #d.thesis_sample, the bull regime has a
mean real return of #n.ms.bull_mean% per month with a standard deviation of #n.ms.bull_sd%,
while the bear regime has a mean of #n.ms.bear_mean% and a standard deviation of
#n.ms.bear_sd%. Both regimes are persistent ($p_("bull,bull") = #n.ms.p_bull$,
$p_("bear,bear") = #n.ms.p_bear$), implying expected durations of #n.ms.dur_bull months for
bull regimes and #n.ms.dur_bear months for bear regimes, close to the estimates in the literature
that the original thesis cited. The autoregressive term ($phi = #n.ms.ar$) partly reflects the
time averaging of Shiller's monthly prices and lowers the AIC from #n.ms.aic_mv to #n.ms.aic_ar,
so the MS-AR(1) is the main specification. On the longer #d.full_start_year to #d.end_year sample
the bull regime is more persistent (expected duration #n.ms.full_dur_bull months) and the bear
regime is more volatile.

#include "../output/tables/regimes.typ"

@fig:regimes contrasts the filtered and smoothed bear-regime probabilities. The smoothed series
marks the dated bear markets more cleanly (AUC #n.ms.auc_smoothed_now against
#n.ms.auc_filtered_now for the contemporaneous dated state), but that advantage comes from
conditioning on later returns. The filtered series is noisier, reacting to individual volatile
months such as October 1987 and early 2020, and it is the only one a forecaster could have
used.

#figure(
  image("../output/figures/fig2_regime_probabilities.png", width: 100%),
  caption: [Filtered and smoothed bear-regime probabilities from the MS-AR(1) model, with
    dated bear markets shaded. Only the filtered probability is used for forecasting.],
) <fig:regimes>

== The corrected archived specification

@tab:original_spec re-estimates the original regressions of the regime probability on the #n.orig.n_pred
original predictors with the timing corrected: the target is $Q_(t+h)$, the predictors are
observable at $t$, and index levels are replaced by growth rates so that coefficients are
interpretable. The number of predictors significant at the 5% level in the OLS regressions is
#n.orig.sig5_h1 of #n.orig.n_pred at one month, #n.orig.sig5_h3 at three, #n.orig.sig5_h6 at six
and #n.orig.sig5_h12 at twelve. The largest $R^2$ (#n.orig.max_r2) belongs to the
predictor "#n.orig.max_r2_label" at one month: a one-standard-deviation higher real return lowers next
month's bear probability by #n.orig.tr_h1 percentage points. This is close to mechanical,
because the filter itself updates on recent returns. Dividend growth (#n.orig.div_h1 at one
month) and inflation have the expected signs. Total-return-scaled earnings, which the award
version singled out, show no meaningful relationship once the timing is corrected
($R^2$ = #n.orig.trse_h1_r2 at one month).

#include "../output/tables/original_spec.typ"

== Logit and probit models of dated bear markets

@tab:logit reports full-sample binary models for the dated bear indicator, and @fig:forest
plots the logit coefficients. Higher inflation (#n.logit.infl_yoy_h1 at one month) and higher
realized volatility (#n.logit.vol_12_h6 at six months) raise the probability of a bear market at
all horizons. A strong past year lowers the short-horizon probability
(#n.logit.mom_12_h1 at one month), which captures persistence: a low twelve-month return
usually means a decline is already under way. The dividend yield enters positively
(#n.logit.log_dy_h6 at six months). Because it divides lagged dividends by the current price, it
rises when prices fall, so part of this coefficient also reflects an ongoing decline rather than
cheapness. The dividend yield and the CAPE ratio are strongly negatively correlated, so their
conditional coefficients should not be read separately. The pseudo-$R^2$ falls from
#n.logit.r2_h1 at one month to #n.logit.r2_h12 at twelve months.

#include "../output/tables/logit.typ"

#figure(
  image("../output/figures/fig6_logit_forest.png", width: 100%),
  caption: [Full-sample logit coefficients per one-standard-deviation change in each predictor,
    with 95% Newey-West confidence intervals, by forecast horizon.],
) <fig:forest>

#place.flush()

= Out-of-sample evaluation <sec-oos>

== Forecasting dated bear markets

@tab:oos is the central result of this edition. At the one-month horizon every model beats the
unconditional frequency (Brier #o.h1.uncond.brier): the multivariate logit reaches
#o.h1.logit_all.brier (skill #o.h1.logit_all.bss%, AUC #o.h1.logit_all.auc) and the probit
#o.h1.probit_all.brier. But persistence alone reaches #o.h1.persist.brier (skill
#o.h1.persist.bss%), and the Diebold-Mariano tests cannot distinguish the multivariate models
from persistence ($p$ = #o.h1.logit_all.p_per for the logit and #o.h1.probit_all.p_per for the
probit). Adding the real-time state to the logit does not help (#o.h1.logit_state.brier). The
MS-AR(1) forecast is informative (AUC #o.h1.ms.auc) but less accurate than persistence (skill
#o.h1.ms.bss%).

At three months the single-variable dividend-yield logit is the most accurate model (Brier
#o.h3.logit_dy.brier, skill #o.h3.logit_dy.bss%), essentially tied with persistence (skill
#o.h3.persist.bss%, $p$ = #o.h3.logit_dy.p_per), while the multivariate logit falls to a skill
of #o.h3.logit_all.bss%. At six months only the dividend-yield logit retains a meaningful gain
(skill #o.h6.logit_dy.bss%, $p$ = #o.h6.logit_dy.p_unc against the unconditional frequency), and
the multivariate models are worse than the unconditional frequency (skill
#o.h6.logit_all.bss%). At twelve months no model is reliably better than the unconditional
frequency: the best skill is #o.h12.logit_dy.bss% ($p$ = #o.h12.logit_dy.p_unc), and the
multivariate logit has an AUC of #o.h12.logit_all.auc, below the 0.5 of an uninformative
forecast. Across all #o.n_challengers comparisons of a model with persistence, #o.n_beat_persist_5pct
are significant at the 5% level (smallest $p$ = #o.min_p_persist).

#include "../output/tables/oos.typ"

@fig:oos shows why. The model probabilities rise sharply once a decline is under way and fall
when the market recovers, so at short horizons they track bear markets well, mostly with a lag.
In the months before the peaks of 1973, 2000 and 2007 the model probabilities were below the
unconditional frequency. The calibration curves
in @fig:calibration show that the short-horizon forecasts are directionally right but
overconfident at the top: months assigned the highest probabilities turned out to be bear months
less often than predicted. At twelve months the curves are flat, and the ROC curves in @fig:roc
lie close to the diagonal.

#figure(
  image("../output/figures/fig3_oos_forecasts.png", width: 100%),
  caption: [Real-time forecast probabilities, plotted at the target month, with dated bear
    markets shaded. Each forecast uses only data available at its origin.],
) <fig:oos>

#figure(
  image("../output/figures/fig4_calibration.png", width: 85%),
  caption: [Calibration of out-of-sample forecasts: observed bear frequency against the mean
    forecast within six forecast-quantile bins. The dotted line is perfect calibration.],
) <fig:calibration>

#figure(
  image("../output/figures/fig5_roc.png", width: 85%),
  caption: [ROC curves of out-of-sample forecasts by horizon, with areas under the curve.],
) <fig:roc>

== Forecasting the regime probability

@tab:mspe revisits the original out-of-sample exercise, in which each predictor forecasts the
regime probability and is compared with an intercept-only model. Panel A reproduces the archived
numbers with the archived code path and formula: #n.mspe.arch_a_below1 of #n.mspe.arch_cells
OLS ratios fall below one. Panel B keeps the archived design but computes true mean squared
errors; only #n.mspe.arch_b_below1 do. Panel C uses the corrected design with expanding-window
refits from #n.mspe.test_start. Here #n.mspe.n_below1_ols of #n.mspe.n_cells OLS ratios fall below
one and #n.mspe.n_cw10_ols are significant at the 10% level by the Clark-West test. The gains are
real but small: the best ratio is #n.mspe.min_ratio_ols, for the predictor "#n.mspe.min_ratio_label" at
#n.mspe.min_ratio_h month. For comparison, the regime probability's own current value achieves a
ratio of #n.mspe.qnow_h1 at one month, but none at six months (#n.mspe.qnow_h6), where inflation
and dividend growth still carry a few percent of information. The intercept-only model is a
weak benchmark for a target as persistent as $Q_t$, and this panel uses full-sample regime
parameters to construct the target, so it describes associations with the regime probability
rather than tradeable forecasts.

#include "../output/tables/mspe.typ"

#place.flush()

= The correction to the archived data alignment <sec-correction>

The award version contains three errors, each verified by replication.

*1. A future price in the regime model.* The archived regime equation regresses
$100 ln P_t$ on the column `realpricelag`, which is $100 ln P_(t+1)$. Every filtered probability
from that model therefore conditions on next month's price.

*2. Backward-looking "ahead" targets.* The archived R script builds the "$k$ months ahead"
target with `lag(Q, k)` after loading `dplyr`, whose `lag` shifts a series back in time. The
regressions therefore relate $Q_(t-k)$, the regime probability $k$ months in the past, to the
predictor's change at $t$. They describe how predictors move after the regime probability,
not before it.

*3. A mislabeled loss ratio.* The archived "MSPE ratio" is
$(overline(e)_u)^2 \/ (overline(e)_r)^2$, the ratio of squared mean errors. Two models with
small average bias can have a ratio near zero even when one has much larger squared errors.

Re-running the archived code path in Python, with all three errors, reproduces the award
results (@fig:replication, @tab:replication). The replicated transition probabilities are
#n.rep.p_bull_replicated and #n.rep.p_bear_replicated against the reported #n.rep.p_bull_reported
and #n.rep.p_bear_reported; the correlation between replicated and reported values is
#n.rep.corr_coef for the OLS coefficients, #n.rep.corr_r2 for the $R^2$ statistics and
#n.rep.corr_ratio for the forecast ratios. The match confirms the diagnosis: the reported dividend
coefficient at $k = 1$ is #n.rep.div_k1_reported and the replication with the backward target
gives #n.rep.div_k1_replicated.

#include "../output/tables/replication.typ"

#figure(
  image("../output/figures/fig7_replication.png", width: 100%),
  caption: [Replication of the archived specification. Each point compares a value reported in
    the award version with the same statistic from the Python replication of the archived code.],
) <fig:replication>

The effect of the corrections is largest for the headline out-of-sample claim. For real
dividends at one month, the award version reported a ratio of #n.rep.div_ratio_reported, which
the replication puts at #n.rep.div_ratio_replicated. The true mean-squared-error ratio on the
same design is #n.rep.div_ratio_true, worse than the intercept-only model, and in the corrected
design it is #n.rep.div_ratio_corrected.


#place.flush()

= Limitations

The sample contains #n.data.n_bears_thesis bear markets since #d.thesis_start_year, so the
out-of-sample evaluation rests on few independent episodes and the overlapping monthly forecasts
are strongly dependent; the Diebold-Mariano and Clark-West tests account for serial correlation
only approximately. The bear-market rule is one reasonable choice among several, and monthly
average prices understate intra-month declines: the 2020 decline, for example, does not reach the
#d.decline% threshold in monthly averages. Publication lags are imposed conservatively, but the
Shiller series are themselves revised and partly interpolated, so this is a quasi-real-time
rather than a true vintage exercise. The predictor set is limited to what the archived file
contains; credit spreads and the term structure, which Chen (2009) and Chen, Chen and Chou (2017)
find useful, are not available in it. Finally, the regime-probability target in @tab:original_spec
and @tab:mspe uses full-sample parameters and should be read as descriptive.

= Conclusion

Correcting the timing of the archived analysis changes its conclusions. The regime-switching
description of the S&P 500 survives: real returns alternate between a long, calm bull regime and
a short, volatile bear regime. The claim that market and macroeconomic indicators forecast bear
markets does not survive in its original form. In real time, the information that best predicts a
bear market next month is that one has already begun, and models built on inflation, valuation,
momentum and volatility do not significantly improve on that persistence benchmark. Beyond a few
months, the dividend yield retains a small and imprecise advantage over the unconditional
frequency, and nothing else does. These results are consistent with a market in which downturns
are difficult to anticipate from public information, and they illustrate how easily look-ahead
in data alignment can create the appearance of predictability.

#place.flush()

#heading(numbering: none)[References]

#set par(first-line-indent: 0em, hanging-indent: 1.5em, spacing: 0.7em)
#set text(size: 10pt)

Ang, A. and Timmermann, A. (2012). Regime changes and financial markets. _Annual Review of
Financial Economics_, 4(1), 313-337.

Brier, G. W. (1950). Verification of forecasts expressed in terms of probability. _Monthly
Weather Review_, 78(1), 1-3.

Campbell, J. Y. and Shiller, R. J. (1988). The dividend-price ratio and expectations of future
dividends and discount factors. _Review of Financial Studies_, 1(3), 195-228.

Chen, N.-K., Chen, S.-S. and Chou, Y.-H. (2017). Further evidence on bear market
predictability: The role of the external finance premium. _International Review of Economics
& Finance_, 50, 106-121.

Chen, S.-S. (2009). Predicting the bear stock market: Macroeconomic variables as leading
indicators. _Journal of Banking & Finance_, 33(2), 211-223.

Clark, T. E. and West, K. D. (2007). Approximately normal tests for equal predictive accuracy in
nested models. _Journal of Econometrics_, 138(1), 291-311.

Diebold, F. X. and Mariano, R. S. (1995). Comparing predictive accuracy. _Journal of Business &
Economic Statistics_, 13(3), 253-263.

Estrella, A. and Mishkin, F. S. (1998). Predicting U.S. recessions: Financial variables as
leading indicators. _Review of Economics and Statistics_, 80(1), 45-61.

Fama, E. F. and French, K. R. (1988). Dividend yields and expected stock returns. _Journal of
Financial Economics_, 22(1), 3-25.

Ferrari, S. and Cribari-Neto, F. (2004). Beta regression for modelling rates and proportions.
_Journal of Applied Statistics_, 31(7), 799-815.

Goetzmann, W. N. and Jorion, P. (1993). Testing the predictive power of dividend yields. _Journal
of Finance_, 48(2), 663-679.

Hamilton, J. D. (1989). A new approach to the economic analysis of nonstationary time series and
the business cycle. _Econometrica_, 57(2), 357-384.

Hammerschmidt, R. and Lohre, H. (2018). Regime shifts and stock return predictability.
_International Review of Economics & Finance_, 56, 138-160.

Harvey, D., Leybourne, S. and Newbold, P. (1997). Testing the equality of prediction mean
squared errors. _International Journal of Forecasting_, 13(2), 281-291.

Lewellen, J. (1999). The time-series relations among expected return, risk, and book-to-market.
_Journal of Financial Economics_, 54(1), 5-43.

Lunde, A. and Timmermann, A. (2004). Duration dependence in stock prices: An analysis of bull and
bear markets. _Journal of Business & Economic Statistics_, 22(3), 253-273.

Maheu, J. M. and McCurdy, T. H. (2000). Identifying bull and bear markets in stock returns.
_Journal of Business & Economic Statistics_, 18(1), 100-112.

Newey, W. K. and West, K. D. (1987). A simple, positive semi-definite, heteroskedasticity and
autocorrelation consistent covariance matrix. _Econometrica_, 55(3), 703-708.

Pagan, A. R. and Sossounov, K. A. (2003). A simple framework for analysing bull and bear
markets. _Journal of Applied Econometrics_, 18(1), 23-46.

Pontiff, J. and Schall, L. D. (1998). Book-to-market ratios as predictors of market returns.
_Journal of Financial Economics_, 49(2), 141-160.

Shiller, R. J. (2015). _Irrational Exuberance_ (3rd ed.). Princeton University Press. Data:
U.S. Stock Markets and CAPE Ratio, Yale Department of Economics.

Smithson, M. and Verkuilen, J. (2006). A better lemon squeezer? Maximum-likelihood regression
with beta-distributed dependent variables. _Psychological Methods_, 11(1), 54-71.

Stambaugh, R. F. (1999). Predictive regressions. _Journal of Financial Economics_, 54(3),
375-421.

Welch, I. and Goyal, A. (2008). A comprehensive look at the empirical performance of equity
premium prediction. _Review of Financial Studies_, 21(4), 1455-1508.
