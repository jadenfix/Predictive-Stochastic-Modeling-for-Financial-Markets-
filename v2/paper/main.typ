// Predictive Stochastic Modeling for Financial Markets, revised edition.
// Every number in this document is read from ../output/numbers.json or from
// the generated tables in ../output/tables, both produced by `python -m psm.run`.

#let n = json("../output/numbers.json")
#let d = n.design
#let o = n.oos
#let r = n.rob
#let rv = r.var

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
      This revised edition of the undergraduate thesis that received the Adam Smith Award
      evaluates bear-market forecasts in real time and adds a broad set of robustness
      experiments. All estimates, tables and figures are produced by a single reproducible
      pipeline. The award version (February 2025), its R code and the code for this edition
      are available at
      #link("https://github.com/jadenfix/Predictive-Stochastic-Modeling-for-Financial-Markets-")[github.com/jadenfix/Predictive-Stochastic-Modeling-for-Financial-Markets-].
    ]
  ]
]

// ------------------------------------------------------------------ abstract
#align(center)[#text(size: 12pt, weight: "bold")[Abstract]]
#block(inset: (x: 0.4in))[
  #set par(first-line-indent: 0em)
  #set text(size: 10pt)
  Can market and macroeconomic indicators forecast bear markets in the S&P 500? I date
  #n.data.n_bears bear markets in the real S&P 500 since #d.full_start_year with a threshold
  rule, describe monthly returns with a two-regime Markov-switching model, and evaluate
  probability forecasts made every month from #o.first_origin to #n.data.end, with every model
  re-estimated on data that were available at the forecast origin. Returns alternate between a
  calm bull regime (mean #n.ms.bull_mean% a month, expected duration #n.ms.dur_bull months) and
  a volatile bear regime (mean #n.ms.bear_mean%, expected duration #n.ms.dur_bear months). Out of
  sample, a logit on #d.n_forecast_features state variables reduces the one-month Brier score by
  #o.h1.logit_all.bss% relative to the unconditional bear frequency. Knowing only whether a
  confirmed bear market is under way achieves #o.h1.persist.bss%, and none of the
  #o.n_challengers model-horizon pairs beats this persistence benchmark at the 5% level. Skill
  declines with the horizon; at twelve months no model is reliably better than the base rate.
  The conclusions hold across alternative dating thresholds and nominal prices, five regime
  specifications, rolling estimation windows, subperiods, #r.pred_n_extra additional predictors,
  forecast combination and block-bootstrap inference. The one predictor that beats persistence is
  the drawdown from the twelve-month high at one month, which recognizes a decline already in
  progress slightly earlier than the dating rule. Bear markets are partly identifiable in real
  time; they are not meaningfully predictable months in advance with these data.
]

= Introduction

Bear markets destroy a large share of household and institutional wealth in a short time, and
whether they can be anticipated is a direct test of how much public information stock prices
already contain. Two literatures bear on the question. One finds that equity returns alternate
between persistent bull and bear regimes (Hamilton, 1989; Maheu and McCurdy, 2000; Ang and
Timmermann, 2012). The other finds that valuation ratios and macroeconomic conditions carry
information about future returns and downturns (Campbell and Shiller, 1988; Fama and French,
1988; Chen, 2009). If regimes are persistent and their onset is related to observable
conditions, bear markets should be at least partly forecastable.

This paper asks how much of that forecastability survives a strict real-time test. A forecast
may use only information that was published when it was made, every model is re-estimated at
every forecast origin, and accuracy is measured out of sample against two baselines: the
unconditional frequency of bear markets and the persistence of the current, observable market
state. The second baseline is the demanding one. A bear market dated from its peak is only
recognized once prices have fallen far enough, so a model that merely notices an ongoing decline
will look skillful against the base rate without telling an investor anything new.

The analysis has four parts. First, I date bear markets with an explicit threshold rule in the
spirit of Lunde and Timmermann (2004), so that the forecast target is an observable event rather
than a model output. Second, I estimate two-regime Markov-switching models of real returns and
use their filtered probabilities as one forecast. Third, I estimate logit and probit models, the
natural tools for a binary outcome (Estrella and Mishkin, 1998; Chen, 2009), on valuation,
inflation, interest-rate and market-state predictors, and evaluate their real-time forecasts over
#o.period at horizons of #d.horizons months. Fourth, I subject the results to a robustness program
that varies the dating rule, the regime specification, the estimation window, the evaluation
period and the predictor set, and that quantifies sampling uncertainty with a block bootstrap.

The evidence supports three findings. Regime structure in returns is strong and stable: a calm
bull regime and a short, volatile bear regime appear in every specification and subsample.
Indicators such as inflation, realized volatility and the dividend yield are associated with
bear markets in sample, and real-time models beat the unconditional frequency at horizons of one
to three months. Most of that short-horizon skill, however, comes from recognizing a bear market
that has already begun. No model significantly improves on persistence, and beyond six months
nothing reliably improves on the base rate.

The paper proceeds as follows. @sec-lit reviews related work, @sec-data describes the data and
the dating rule, @sec-methods the models and the real-time design, @sec-results the main results
and @sec-robust the robustness experiments. @sec-limits discusses limitations and @sec-concl
concludes.

= Related literature <sec-lit>

Regime-switching models in the tradition of Hamilton (1989) describe the stock market as moving
between a high-return, low-volatility state and a low-return, high-volatility state. Maheu and
McCurdy (2000) identify bull and bear markets this way, and Ang and Timmermann (2012) survey the
evidence that regime changes are a pervasive feature of financial markets. Rule-based dating is
the main alternative: Pagan and Sossounov (2003) adapt business-cycle turning-point algorithms to
equity prices, and Lunde and Timmermann (2004) define bull and bear markets by threshold
movements from the latest peak or trough. Chen (2009) and Chen, Chen and Chou (2017) use such
dates as the dependent variable in probit models and find that macroeconomic and credit variables
help predict bear markets.

On the predictor side, Campbell and Shiller (1988) and Fama and French (1988) document that
dividend yields forecast long-horizon returns, while Goetzmann and Jorion (1993), Stambaugh (1999)
and Lewellen (1999) show that inference with persistent, price-scaled predictors is delicate.
Pontiff and Schall (1998) report related evidence for book-to-market ratios, and Hammerschmid and
Lohre (2018) find that return predictability itself varies across regimes. Welch and Goyal (2008)
show that many predictors that look strong in sample fail out of sample, and Rapach, Strauss and
Zhou (2010) find that combining individual forecasts delivers more reliable out-of-sample gains
than any single predictor. This paper applies the out-of-sample standard of these studies to
the prediction of bear markets rather than of average returns.

= Data <sec-data>

== Source and timing

The data are the monthly U.S. stock market series compiled by Robert Shiller (Shiller, 2015),
archived in the repository as `one45.csv`. The file covers #n.data.first to #n.data.last_raw\; I use
observations through #n.data.end, the last month with complete dividend and earnings data. The
S&P Composite price is a monthly average of daily closes, so it is known at the end of each
month. I treat the end of month $t$ as the forecast origin and impose publication lags on
everything else: the consumer price index enters with a lag of #d.cpi_lag month, and dividends
and earnings, which Shiller interpolates from quarterly reports, enter with a lag of #d.fund_lag
months. Real values are obtained by deflating with the CPI available at $t$. @tab:variables
lists the predictors, their construction and their publication lags.

The construction differs from the award version in one respect that matters for timing. The
archived file contains columns labeled `realpricelag` to `realpricelag4` that hold future rather
than past prices (the first matches the following month's real price on #n.data.audit_future of
#n.data.audit_pairs comparable rows), and the award version's regime model and forecast targets
inherited this alignment. This edition never reads those columns, builds every predictor from
data dated at or before the forecast origin, and verifies with an automated test that no
predictor changes when data after its origin are altered. @app-original summarizes how the
award version's estimates relate to the ones reported here.

#include "../output/tables/variables.typ"

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

#figure(
  image("../output/figures/fig1_price_bears.png", width: 100%),
  caption: [Real S&P 500 price index (log scale) with dated bear markets shaded.],
) <fig:price>

The dated labels are ex post: a peak is only known to have been a peak once the #d.decline%
decline has occurred, which took a median of #n.data.median_confirm_lag months. The same rule run
on data through month $t$ gives the real-time state, which is observable at $t$, and "vintage"
labels for all earlier months. The out-of-sample exercise trains every model on vintage labels
only.

#[
  #set figure(placement: top)
  #include "../output/tables/episodes.typ"
]


= Methodology <sec-methods>

== Markov-switching model of returns

Let $r_t = 100 dot Delta ln P_t$ be the monthly real return. The main regime model is a
two-state Markov-switching autoregression with switching mean and variance (Hamilton, 1989):
$
  r_t - mu_(S_t) = phi (r_(t-1) - mu_(S_(t-1))) + sigma_(S_t) epsilon_t, quad
  epsilon_t tilde.op N(0, 1), quad S_t in {"bull", "bear"},
$ <eq:msar>
where $S_t$ follows a first-order Markov chain with transition probabilities
$p_(i j) = Pr(S_t = j | S_(t-1) = i)$. Setting $phi = 0$ gives the switching mean-variance
model. The bear regime is the one with the lower mean, and the expected duration of regime $i$
is $1 \/ (1 - p_(i i))$. The Hamilton filter delivers the filtered probability
$
  Q_t = Pr(S_t = "bear" | r_1, dots, r_t),
$ <eq:filtered>
which uses only returns through $t$ and is therefore a legitimate real-time quantity once the
parameters are fixed. The smoothed probability $Pr(S_t = "bear" | r_1, dots, r_T)$ conditions on
the whole sample and is used only for description. An $h$-step regime forecast is
$Pr(S_(t+h) = "bear" | r_1, dots, r_t) = [1 - Q_t, Q_t] bold(P)^h e_2$, where $bold(P)$ is the
transition matrix.

== Binary models for dated bear markets

The dated bear indicator $y_(t+h)$ is the forecast target. The binary regression
$
  Pr(y_(t+h) = 1 | x_t) = F(alpha + x_t^top beta)
$ <eq:logit>
uses the logistic (logit) or standard normal (probit) distribution function $F$. The
#d.n_forecast_features predictors in $x_t$ are the log dividend yield, the log CAPE ratio with
lagged earnings, twelve-month CPI inflation, the twelve-month change in the ten-year Treasury
yield, the twelve-month real price change, and twelve-month realized volatility. In-sample
estimates use Newey and West (1987) standard errors, since overlapping horizons make the errors
serially correlated. @app-original also reports regressions of the regime probability $Q_(t+h)$
on each predictor, the design of the award version, estimated by OLS and by beta regression
(Ferrari and Cribari-Neto, 2004; Smithson and Verkuilen, 2006).

== Real-time design <sec-oos-design>

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
- *Logit: dividend yield*, the single valuation predictor emphasized in the literature.
- *Logit* and *probit* on all #d.n_forecast_features predictors.
- *Logit: all predictors + state*, which adds the real-time state to test whether the
  predictors add to persistence.

Accuracy is measured by the Brier score (Brier, 1950), the log loss (with probabilities
truncated to $[#d.floor, 1 - #d.floor]$), the area under the ROC curve (AUC) and calibration
curves. Brier skill is the percentage reduction in the Brier score relative to the unconditional
frequency. Differences in Brier score are tested with the Diebold and Mariano (1995) statistic
with the small-sample correction of Harvey, Leybourne and Newbold (1997) and a Bartlett HAC
variance.

== Robustness design <sec-robust-design>

Each robustness experiment changes one design choice and re-runs the affected part of the
pipeline. (i) *Regime specification*: two regimes with switching mean and variance with and
without the AR(1) term, switching variance only, switching mean only, and three regimes, all on
#d.thesis_sample, plus the main model estimated separately before and after #r.spec.split.
(ii) *Dating rule*: thresholds of 15% and 25% on real prices and 20% on nominal prices, each
followed by a complete real-time forecasting run with re-dated vintage labels and real-time
states. (iii) *Estimation window*: rolling #r.rolling_years\-year windows instead of expanding
ones. (iv) *Evaluation period*: the main forecasts scored on targets before and after
#r.spec.split and without the 2007-2009 financial crisis (#r.crisis). (v) *Predictors*:
#r.pred_n_extra additional state variables from the same file, namely the excess CAPE yield, the
log payout ratio, twelve-month real earnings growth, the level of the ten-year yield and the
drawdown of the real price from its twelve-month high, each as a univariate logit alongside the
six main predictors, together with an equal-weight combination of all #r.pred_n univariate
forecasts (Rapach, Strauss and Zhou, 2010) and a logit on all #r.pred_n predictors.
(vi) *Sampling uncertainty*: a circular moving-block bootstrap (Künsch, 1989) of target months
with #r.boot_block\-month blocks and #r.boot_reps replications, resampling all models jointly,
which gives intervals for each Brier skill and for each model's gain over persistence.

#place.flush()

= Results <sec-results>

== Returns have two persistent regimes

@tab:regimes reports the regime models. In the MS-AR(1) model for #d.thesis_sample, the bull
regime has a mean real return of #n.ms.bull_mean% per month with a standard deviation of
#n.ms.bull_sd%, while the bear regime has a mean of #n.ms.bear_mean% and a standard deviation of
#n.ms.bear_sd%. Both regimes are persistent ($p_("bull,bull") = #n.ms.p_bull$,
$p_("bear,bear") = #n.ms.p_bear$), implying expected durations of #n.ms.dur_bull months for
bull regimes and #n.ms.dur_bear months for bear regimes. The autoregressive term
($phi = #n.ms.ar$) partly reflects the time averaging of monthly prices and lowers the AIC from
#n.ms.aic_mv to #n.ms.aic_ar, so the MS-AR(1) is the main specification. On the longer
#d.full_start_year to #d.end_year sample the bull regime is more persistent (expected duration
#n.ms.full_dur_bull months) and the bear regime is more volatile.

#include "../output/tables/regimes.typ"

@fig:regimes contrasts the filtered and smoothed bear-regime probabilities. The smoothed series
marks the dated bear markets more cleanly (AUC #n.ms.auc_smoothed_now against
#n.ms.auc_filtered_now for the contemporaneous dated state), but that advantage comes from
conditioning on later returns. The filtered series is noisier, reacting to individual volatile
months such as October 1987 and early 2020, and it is the only one a forecaster could have used.

#figure(
  image("../output/figures/fig2_regime_probabilities.png", width: 100%),
  caption: [Filtered and smoothed bear-regime probabilities from the MS-AR(1) model, with
    dated bear markets shaded. Only the filtered probability is used for forecasting.],
) <fig:regimes>

== Inflation, volatility and valuation are associated with bear markets

@tab:logit reports full-sample binary models for the dated bear indicator, and @fig:forest
plots the logit coefficients. Higher inflation (#n.logit.infl_yoy_h1 at one month) and higher
realized volatility (#n.logit.vol_12_h6 at six months) raise the probability of a bear market at
all horizons. A strong past year lowers the short-horizon probability (#n.logit.mom_12_h1 at one
month), which captures persistence: a low twelve-month return usually means a decline is already
under way. The dividend yield enters positively (#n.logit.log_dy_h6 at six months). Because it
divides lagged dividends by the current price, it rises when prices fall, so part of this
coefficient also reflects an ongoing decline rather than cheapness. The dividend yield and the
CAPE ratio are strongly negatively correlated, so their conditional coefficients should not be
read separately. The pseudo-$R^2$ falls from #n.logit.r2_h1 at one month to #n.logit.r2_h12 at
twelve months.

#include "../output/tables/logit.typ"

#figure(
  image("../output/figures/fig6_logit_forest.png", width: 100%),
  caption: [Full-sample logit coefficients per one-standard-deviation change in each predictor,
    with 95% Newey-West confidence intervals, by forecast horizon.],
) <fig:forest>

== In real time, models beat the base rate but not persistence

@tab:oos is the central result. At the one-month horizon every model beats the unconditional
frequency (Brier #o.h1.uncond.brier): the multivariate logit reaches #o.h1.logit_all.brier
(skill #o.h1.logit_all.bss%, AUC #o.h1.logit_all.auc) and the probit #o.h1.probit_all.brier.
Persistence alone reaches #o.h1.persist.brier (skill #o.h1.persist.bss%), and the
Diebold-Mariano tests cannot distinguish the multivariate models from persistence
($p$ = #o.h1.logit_all.p_per for the logit and #o.h1.probit_all.p_per for the probit). Adding the
real-time state to the logit does not help (#o.h1.logit_state.brier). The MS-AR(1) forecast ranks
months well (AUC #o.h1.ms.auc) but is less accurate than persistence (skill #o.h1.ms.bss%).

#include "../output/tables/oos.typ"

The block bootstrap in @tab:bootstrap and @fig:intervals puts these differences in perspective.
The 90% interval for the one-month skill of persistence is \[#r.boot.persist.h1.lo,
#r.boot.persist.h1.hi\]% and that of the multivariate logit \[#r.boot.logit_all.h1.lo,
#r.boot.logit_all.h1.hi\]%; both exclude zero. The logit's gain over persistence, however, ranges
from #r.boot.logit_all.h1.glo to #r.boot.logit_all.h1.ghi percentage points, and the logit beats
persistence in a share of #r.boot.logit_all.h1.share of the bootstrap draws. With blocks of 12
or 36 months instead of #r.boot_block the interval for persistence becomes
\[#r.boot_sens.b12.persist.lo, #r.boot_sens.b12.persist.hi\]% or \[#r.boot_sens.b36.persist.lo,
#r.boot_sens.b36.persist.hi\]%, so the conclusion does not depend on the block length.

#figure(
  image("../output/figures/fig8_skill_intervals.png", width: 100%),
  caption: [Out-of-sample Brier skill relative to the unconditional frequency, with 90%
    moving-block bootstrap intervals. The dashed line is the unconditional frequency.],
) <fig:intervals>

#include "../output/tables/bootstrap.typ"

== Skill fades with the horizon

At three months the single-variable dividend-yield logit is the most accurate model (Brier
#o.h3.logit_dy.brier, skill #o.h3.logit_dy.bss%), essentially tied with persistence (skill
#o.h3.persist.bss%, $p$ = #o.h3.logit_dy.p_per), while the multivariate logit falls to
#o.h3.logit_all.bss%. At six months only the dividend-yield logit retains a meaningful gain
(skill #o.h6.logit_dy.bss%, $p$ = #o.h6.logit_dy.p_unc against the unconditional frequency), and
the multivariate models are worse than the base rate (skill #o.h6.logit_all.bss%). At twelve
months no model is reliably better than the unconditional frequency: the best skill is
#o.h12.logit_dy.bss% ($p$ = #o.h12.logit_dy.p_unc), and the multivariate logit has an AUC of
#o.h12.logit_all.auc, below the 0.5 of an uninformative forecast. Across all #o.n_challengers
comparisons of a model with persistence, #if o.n_beat_persist_5pct == "0" [none is] else [#o.n_beat_persist_5pct are] significant at the 5% level
(smallest $p$ = #o.min_p_persist).

@fig:oos shows why. The model probabilities rise sharply once a decline is under way and fall
when the market recovers, so at short horizons they track bear markets well, mostly with a lag.
In the months before the peaks of 1973, 2000 and 2007 the model probabilities were below the
unconditional frequency. The calibration curves in @fig:calibration show that the short-horizon
forecasts are directionally right but overconfident at the top: months assigned the highest
probabilities turned out to be bear months less often than predicted. At twelve months the
curves are flat, and the ROC curves in @fig:roc lie close to the diagonal.

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

#place.flush()

= Robustness <sec-robust>

== Regime specification and sample

@tab:regime_specs compares the main model with four alternatives on #d.thesis_sample and with
the main model estimated on two subsamples. The MS-AR(1) has the lowest AIC (#r.spec.ar1.aic)
and BIC (#r.spec.ar1.bic) in the first group. Letting only the variance switch gives a
high-volatility regime (standard deviation #r.spec.var_only.bear_sd% against
#r.spec.var_only.bull_sd%) that tracks dated bear markets less well (AUC #r.spec.var_only.auc
against #r.spec.ar1.auc). Letting only the mean switch picks out short crash months rather than
bear markets: the low-mean regime averages #r.spec.mean_only.bear_mean% a month and lasts
#r.spec.mean_only.dur_bear months. A three-regime model splits the bull state into a calm regime
(mean #r.spec.three.mid_mean%, duration #r.spec.three.dur_mid months) and a short rebound regime
(mean #r.spec.three.bull_mean%, duration #r.spec.three.dur_bull months), while its bear regime
(mean #r.spec.three.bear_mean%, standard deviation #r.spec.three.bear_sd%) closely resembles the
two-regime one and tracks dated bear markets better (AUC #r.spec.three.auc). Its extra
parameters do not pay for themselves by AIC (#r.spec.three.aic). Across subsamples the bear
regime's volatility is stable (#r.spec.pre.bear_sd% before #r.spec.split, #r.spec.post.bear_sd%
after), whereas the bull regime became more persistent (expected duration #r.spec.pre.dur_bull
months before, #r.spec.post.dur_bull after) and the filtered probability became a much better
real-time marker of bear markets (AUC #r.spec.pre.auc before, #r.spec.post.auc after).

#include "../output/tables/regime_specs.typ"

== Dating rule

@tab:dating shows how the set of episodes depends on the rule. A 15% threshold dates
#r.dating.real15.n bear markets since #d.full_start_year and a 25% threshold #r.dating.real25.n,
against #r.dating.main.n for the main rule. Dating nominal prices yields only
#r.dating.nominal20.n_since episodes since #d.thesis_start_year, because inflation in the 1970s
turned long real declines into flat nominal prices; the bear share falls to
#r.dating.nominal20.share%. @tab:robust_oos re-runs the entire real-time exercise under each
rule. The pattern is unchanged. Persistence has a one-month skill between
#rv.nominal20.persist.h1.bss% (nominal) and #rv.real15.persist.h1.bss% (15%), the dividend-yield
logit retains positive skill at one and three months under every rule, and the multivariate
logit has negative skill at twelve months under every rule (#rv.real15.logit_all.h12.bss%,
#rv.real25.logit_all.h12.bss% and #rv.nominal20.logit_all.h12.bss%).

#include "../output/tables/dating.typ"

== Estimation window and evaluation period

Rolling #r.rolling_years\-year windows reduce the skill of persistence, the regime model and the
dividend-yield logit at every horizon (for example #rv.rolling.logit_dy.h1.bss% for the
dividend-yield logit at one month, against #rv.main.logit_dy.h1.bss%), and the multivariate logit
deteriorates sharply at long horizons (#rv.rolling.logit_all.h12.bss% at twelve months). The
longer history in the expanding window is valuable, which is expected for a rare event: thirty
years contain only a handful of bear markets.

The evaluation-period rows of @tab:robust_oos show that forecastability is concentrated in the
later part of the sample. For targets from #r.spec.split onward, persistence reaches a one-month
skill of #rv.post.persist.h1.bss% and the multivariate logit #rv.post.logit_all.h1.bss%; for
earlier targets the corresponding figures are #rv.pre.persist.h1.bss% and
#rv.pre.logit_all.h1.bss%. The long real bear markets of 1968-1982 were confirmed slowly, 11 to
16 months after their peaks (@tab:episodes), while the declines of 2000-2002 and 2007-2009 were
confirmed within 7 and 9 months. Excluding
the 2007-2009 crisis changes little (one-month skill #rv.nocrisis.persist.h1.bss% for persistence
and #rv.nocrisis.logit_all.h1.bss% for the logit), so the results are not driven by a single
episode.

#include "../output/tables/robust_oos.typ"

== Additional predictors and forecast combination

@tab:predictors evaluates each of the #r.pred_n predictors as a univariate logit in the
same real-time design. The strongest single predictors at one month are price-based: the
drawdown from the twelve-month high (skill #r.pred.uni_drawdown.h1.bss%, AUC
#r.pred.uni_drawdown.h1.auc) and the twelve-month real price change
(#r.pred.uni_mom_12.h1.bss%). The drawdown is the only forecast in this study that beats
persistence at the 5% level ($p$ = #r.pred.uni_drawdown.h1.p_per), and its advantage disappears
by three months ($p$ = #r.pred.uni_drawdown.h3.p_per). It measures how far a decline has already
gone before the #d.decline% threshold is crossed, so it recognizes the same ongoing bear markets
slightly earlier than the real-time state. The additional valuation and macroeconomic
predictors add nothing: the excess CAPE yield, the payout ratio, earnings growth and the level
of the ten-year yield all have one-month skills between #r.pred.uni_rate_level.h1.bss% and
#r.pred.uni_ecy.h1.bss%. At six and twelve months the dividend yield remains the best single
predictor (#r.pred.uni_log_dy.h6.bss% and #r.pred.uni_log_dy.h12.bss%).

The equal-weight combination is stable but unspectacular: its skill is
#r.pred.combo.h1.bss%, #r.pred.combo.h3.bss%, #r.pred.combo.h6.bss% and #r.pred.combo.h12.bss%
at the four horizons: positive up to six months and close to zero at twelve, but below
persistence at every horizon. The logit on all #r.pred_n predictors overfits as the
horizon lengthens (#r.pred.logit_ext.h12.bss% at twelve months).

Taken together, the alternative designs and the predictor experiments involve
#(int(r.var_alt_tests) + int(r.pred_challengers)) comparisons of a model with persistence, of
which #(int(r.var_alt_beats) + int(r.pred_beats_persist)) are significant at the 5% level, all
at the one-month horizon. That is no more than chance alone would produce.

#include "../output/tables/predictors.typ"

= Limitations <sec-limits>

The sample contains #n.data.n_bears_thesis bear markets since #d.thesis_start_year, so the
out-of-sample evaluation rests on few independent episodes and the overlapping monthly forecasts
are strongly dependent. The block bootstrap and the HAC-based tests account for this dependence
only approximately, and the wide bootstrap intervals are an honest summary of how little a
sample of this size can resolve. Monthly average prices understate intra-month declines: the
2020 decline, for example, does not reach the #d.decline% threshold in monthly averages.
Publication lags are imposed conservatively, but the Shiller series are themselves revised and
partly interpolated, so this is a quasi-real-time rather than a true vintage exercise. The
predictor set is limited to what the archived file contains; credit spreads and the term
structure, which Chen (2009) and Chen, Chen and Chou (2017) find useful, are not available in it.

= Conclusion <sec-concl>

The regime-switching description of the S&P 500 is robust: real returns alternate between a
long, calm bull regime and a short, volatile bear regime in every specification and subsample
examined here. The claim that market and macroeconomic indicators forecast bear markets is much
weaker once forecasts are made in real time. In real time, the information that best predicts a
bear market next month is that one has already begun. Models built on inflation, valuation,
momentum and volatility do not significantly improve on that persistence benchmark; the price
drawdown improves on it only at one month and only by recognizing the decline sooner. Beyond a
few months, the dividend yield retains a small and imprecise advantage over the unconditional
frequency, and nothing else does. These conclusions survive changes to the dating rule, the
regime model, the estimation window, the evaluation period and the predictor set. They are
consistent with a market in which downturns are difficult to anticipate from public
information, and they suggest that the useful contribution of these models is faster
recognition of a bear market, not advance warning of one.

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

Hammerschmid, R. and Lohre, H. (2018). Regime shifts and stock return predictability.
_International Review of Economics & Finance_, 56, 138-160.

Harvey, D., Leybourne, S. and Newbold, P. (1997). Testing the equality of prediction mean
squared errors. _International Journal of Forecasting_, 13(2), 281-291.

Künsch, H. R. (1989). The jackknife and the bootstrap for general stationary observations.
_Annals of Statistics_, 17(3), 1217-1241.

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

Rapach, D. E., Strauss, J. K. and Zhou, G. (2010). Out-of-sample equity premium prediction:
Combination forecasts and links to the real economy. _Review of Financial Studies_, 23(2),
821-862.

Shiller, R. J. (2015). _Irrational Exuberance_ (3rd ed.). Princeton University Press. Data:
U.S. Stock Markets 1871-Present and CAPE Ratio, #link("https://shillerdata.com")[shillerdata.com].

Smithson, M. and Verkuilen, J. (2006). A better lemon squeezer? Maximum-likelihood regression
with beta-distributed dependent variables. _Psychological Methods_, 11(1), 54-71.

Stambaugh, R. F. (1999). Predictive regressions. _Journal of Financial Economics_, 54(3),
375-421.

Welch, I. and Goyal, A. (2008). A comprehensive look at the empirical performance of equity
premium prediction. _Review of Financial Studies_, 21(4), 1455-1508.

// ------------------------------------------------------------------ appendix
#pagebreak()
#set par(first-line-indent: 1.2em, hanging-indent: 0em, spacing: 0.62em)
#set text(size: 11pt)
#counter(heading).update(0)
#set heading(numbering: "A.1", supplement: [Appendix])

= Regressions of the regime probability and the award version <app-original>

The award version of this thesis forecast the filtered regime probability $Q_t$ rather than a
dated event, with univariate OLS and beta regressions of $Q_(t+h)$ on each of #n.orig.n_pred
monthly-change predictors,
$
  Q_(t+h) = alpha + beta x_t + e_(t+h),
$ <eq:ols>
and an out-of-sample comparison with an intercept-only model. @tab:original_spec re-estimates
this design with predictors observable at $t$, growth rates in place of index levels, and
Newey-West standard errors. The number of predictors significant at the 5% level is
#n.orig.sig5_h1 of #n.orig.n_pred at one month, #n.orig.sig5_h3 at three, #n.orig.sig5_h6 at six
and #n.orig.sig5_h12 at twelve. The largest $R^2$ (#n.orig.max_r2) belongs to the real total
return at one month (coefficient #n.orig.tr_h1 percentage points), which is close to mechanical
because the filter itself updates on recent returns. Dividend growth (#n.orig.div_h1 at one
month) and inflation have the expected signs; total-return-scaled earnings show no relationship
($R^2$ = #n.orig.trse_h1_r2). Because $Q_t$ uses full-sample parameters, these are in-sample
associations rather than forecasts.

#include "../output/tables/original_spec.typ"

@tab:mspe reports the out-of-sample comparison. Panel C uses expanding-window refits from
#n.mspe.test_start: #n.mspe.n_below1_ols of #n.mspe.n_cells OLS ratios of mean squared
prediction errors fall below one and #n.mspe.n_cw10_ols are significant at the 10% level by the
Clark and West (2007) test, with a best ratio of #n.mspe.min_ratio_ols. The regime probability's
own current value achieves #n.mspe.qnow_h1 at one month and no gain at six months
(#n.mspe.qnow_h6).

The award version reached stronger conclusions for three reasons that a replication of its code
path confirms (@tab:replication): its regime model was estimated with the following month's
price as a regressor, its "$k$ months ahead" targets were shifted backward rather than forward
in time, and its loss ratio compared squared mean errors rather than mean squared errors. The
replication reproduces the reported transition probabilities (#n.rep.p_bull_replicated and
#n.rep.p_bear_replicated against #n.rep.p_bull_reported and #n.rep.p_bear_reported) and the
reported coefficients (correlation #n.rep.corr_coef). Panels A and B of @tab:mspe show the
archived design with its own ratio and with the correct one.

#include "../output/tables/replication.typ"

#include "../output/tables/mspe.typ"
