// Predictive Stochastic Modeling for Financial Markets, revised edition.
// Every number in this document is read from ../output/numbers.json or from the generated
// tables in ../output/tables, both produced by `uv run python thesis.py`.

#let n = json("../output/numbers.json")
#let d = n.design
#let s = n.source
#let o = n.oos
#let r = n.rob
#let rv = r.var
#let mur = n.murphy
// A p-value string as "p = 0.123" or "p < 0.001".
#let pv(x) = if x.starts-with("<") [$p < #x.slice(1)$] else [$p = #x$]

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
      This revised edition of the undergraduate thesis that received the Adam Smith Award rebuilds
      the analysis from Robert Shiller's primary data, evaluates bear-market forecasts in real
      time, adds time-varying-transition regime models, machine-learning classifiers, dynamic
      forecast combination and multiple-comparison inference, and reports a broad set of
      robustness experiments. A single script produces every estimate, table and figure. The award
      version (February 2025), its R code and the code for this edition are available at
      #link("https://github.com/jadenfix/Predictive-Stochastic-Modeling-for-Financial-Markets-")[github.com/jadenfix/Predictive-Stochastic-Modeling-for-Financial-Markets-].
    ]
  ]
]

// ------------------------------------------------------------------ abstract
#align(center)[#text(size: 12pt, weight: "bold")[Abstract]]
#block(inset: (x: 0.4in))[
  #set par(first-line-indent: 0em)
  #set text(size: 10pt)
  Can market and macroeconomic indicators forecast bear markets in the S&P 500? Using Robert
  Shiller's monthly data from #d.full_start_year to #s.end, I date #n.data.n_bears bear markets in
  the real index with a #d.decline% threshold rule and evaluate probability forecasts made every
  month from #o.first_origin to #o.last_origin, with every model re-estimated on the information
  available at the forecast origin. Returns alternate between a calm bull regime (mean
  #n.ms.bull_mean% a month, expected duration #n.ms.dur_bull months) and a volatile bear regime
  (mean #n.ms.bear_mean%, #n.ms.dur_bear months). Letting the regime transition probabilities
  depend on inflation, valuation, volatility and recent drawdowns improves the in-sample fit by the
  likelihood ratio (#n.tvtp.all.lr, #pv(n.tvtp.all.p)), though not by BIC, and does not improve
  out-of-sample accuracy. At one month, a logit on
  six state variables reduces the Brier score by #o.logit_all.h1.bss% relative
  to the unconditional bear frequency, against #o.persist.h1.bss% for simply knowing whether a
  confirmed bear market is under way; gradient boosting (#o.gbt_rich.h1.bss%) and dynamic model
  averaging (#o.dma_all.h1.bss%) do about as well. These gains over persistence do not survive a
  realistic account of uncertainty: loss differences are strongly autocorrelated, Hansen's test
  for superior predictive ability across the #d.n_challengers competing models gives
  #pv(n.spa.h1.p_c) at one month and #n.spa.joint.p_c across all horizons, and persistence
  remains in the model confidence set at every horizon. Beyond six months no model reliably beats
  the base rate. Bear markets are partly recognizable in real time; with these data they are not
  predictable months in advance.
]

= Introduction

Bear markets destroy a large share of household and institutional wealth in a short time, and
whether they can be anticipated is a direct test of how much public information stock prices
already contain. Two literatures bear on the question. One finds that equity returns alternate
between persistent bull and bear regimes (Hamilton, 1989; Maheu and McCurdy, 2000; Ang and
Timmermann, 2012). The other finds that valuation ratios and macroeconomic conditions carry
information about future returns and downturns (Campbell and Shiller, 1988; Fama and French,
1988; Chen, 2009). If regimes are persistent and their onset is related to observable conditions,
bear markets should be at least partly forecastable.

This paper asks how much of that forecastability survives a strict real-time test. A forecast may
use only information that was published when it was made, every model is re-estimated at every
forecast origin, and accuracy is measured out of sample against two baselines: the unconditional
frequency of bear markets and the persistence of the current, observable market state. The
second baseline is the demanding one. A bear market dated from its peak is only recognized once
prices have fallen far enough, so a model that merely notices an ongoing decline will look
skillful against the base rate without telling an investor anything new.

The analysis proceeds in five steps. First, I date bear markets in Shiller's real S&P 500 series
from #d.full_start_year to #d.end_year with an explicit threshold rule in the spirit of Lunde and
Timmermann (2004), so that the forecast target is an observable event rather than a model output.
Second, I estimate Markov-switching models of real returns, including a model whose transition
probabilities depend on lagged predictors (Diebold, Lee and Weinbach, 1994; Filardo, 1994).
Third, I estimate logit and probit models (Estrella and Mishkin, 1998; Chen, 2009), an elastic-net
logit and gradient-boosted trees in the spirit of Gu, Kelly and Xiu (2020), and equal-weight and
dynamic combinations of the individual forecasts (Rapach, Strauss and Zhou, 2010; Raftery, Kárný
and Ettler, 2010). Fourth, I evaluate the real-time forecasts over #o.period at horizons of
#d.horizons months with proper scoring rules, the Murphy (1973) decomposition, and inference that
accounts for the number of models compared: the test for superior predictive ability of Hansen
(2005), the model confidence set of Hansen, Lunde and Nason (2011) and the conditional test of
Giacomini and White (2006). Fifth, I vary the dating rule, the regime specification, the
estimation window, the evaluation period and the predictor set.

The evidence supports four findings. Regime structure in returns is strong: a calm bull regime and
a short, volatile bear regime appear in every specification and subsample, and time-varying
transition probabilities fit the data better in sample. Inflation, the dividend yield and weak
recent returns are associated with bear markets in sample, and real-time models beat the
unconditional frequency at horizons of one to three months. Much of that short-horizon skill comes
from recognizing a bear market that has already begun; the best models improve on persistence by
several points of Brier skill at one month, mainly through better calibration, but the improvement
is within sampling error once the dependence of the forecast errors and the number of models are
taken into account. Beyond six months nothing reliably improves on the base rate, and the
flexible models do worst there.

The paper proceeds as follows. @sec-lit reviews related work, @sec-data describes the data and
the dating rule, @sec-methods the models, the real-time design and the inference, @sec-results
the main results and @sec-robust the robustness experiments. @sec-limits discusses limitations
and @sec-concl concludes.

= Related literature <sec-lit>

Regime-switching models in the tradition of Hamilton (1989) describe the stock market as moving
between a high-return, low-volatility state and a low-return, high-volatility state. Maheu and
McCurdy (2000) identify bull and bear markets this way, and Ang and Timmermann (2012) survey the
evidence that regime changes are a pervasive feature of financial markets. Diebold, Lee and
Weinbach (1994) and Filardo (1994) let the transition probabilities depend on observable
variables, which turns a descriptive regime model into a potential forecasting model. Rule-based
dating is the main alternative to model-based regimes: Pagan and Sossounov (2003) adapt
business-cycle turning-point algorithms to equity prices, and Lunde and Timmermann (2004) define
bull and bear markets by threshold movements from the latest peak or trough. Chen (2009) and Chen,
Chen and Chou (2017) use such dates as the dependent variable in probit models and find that
macroeconomic and credit variables help predict bear markets.

On the predictor side, Campbell and Shiller (1988) and Fama and French (1988) document that
dividend yields forecast long-horizon returns, while Goetzmann and Jorion (1993), Stambaugh (1999)
and Lewellen (1999) show that inference with persistent, price-scaled predictors is delicate.
Pontiff and Schall (1998) report related evidence for book-to-market ratios, and Hammerschmid and
Lohre (2018) find that return predictability itself varies across regimes. Welch and Goyal (2008)
show that many predictors that look strong in sample fail out of sample, Rapach, Strauss and Zhou
(2010) find that combining forecasts delivers more reliable gains than any single predictor, and
Gu, Kelly and Xiu (2020) show that regularized and tree-based machine-learning methods can extract
more predictive information from many signals than linear regressions. A study that compares many
models also needs inference that accounts for the search: White's (2000) Reality Check, Hansen's
(2005) test for superior predictive ability and the model confidence set of Hansen, Lunde and Nason
(2011) are designed for that problem. This paper applies these out-of-sample standards to the
prediction of bear markets rather than of average returns.

= Data <sec-data>

== Source, vintage and timing

The data are Robert Shiller's monthly U.S. stock market series (Shiller, 2015), the workbook
"U.S. Stock Markets 1871-Present and CAPE Ratio" linked from his Yale data page and distributed at
#link(s.page)[shillerdata.com]. I downloaded the file `ie_data.xls` on #s.downloaded (the server
reported it as last modified on #s.last_modified\; #s.megabytes MB; the SHA-256 hash is given in
@app-data). Every number in this paper is computed from the "#s.sheet" sheet of this file: the
S&P Composite price (a monthly average of daily closes), dividends and earnings per share, the
consumer price index, the long-term interest rate, Shiller's real total-return-scaled earnings and
his real total return index of ten-year Treasury bonds. The workbook runs from #s.first to
#s.last_row, but dividends and earnings end earlier and the most recent price, CPI and yield
observations are provisional (the sheet notes: "#s.footnote"). The sample therefore ends in
#s.end, the last month in which every series is reported, and contains #s.n_months monthly
returns from #s.sample_start.

The award version of this thesis used `one45.csv`, an extract of an earlier vintage of the same
workbook covering 1900 to early 2024. On the #s.compare_months overlapping months the two files
agree to the archived file's two decimals except for #s.compare_n_cells observations, all in the
archived file's final months (#s.compare_first_diff onward), where it held estimates that Shiller
has since revised by at most #s.compare_max_pct% (@app-data). The substantive change is that the
current vintage adds the years 1871 to 1899 and 2024 to #d.end_year.

I treat the end of month $t$ as the forecast origin and impose publication lags on everything that
is not known then: the consumer price index enters with a lag of #d.cpi_lag month, and dividends
and earnings, which Shiller interpolates from quarterly reports (annual before 1926), enter with a
lag of #d.fund_lag months. Real values are obtained by deflating with the CPI available at $t$.
Shiller's monthly bond return for month $t$ uses the following month's yield, so it is never used
directly; his real bond index at $t$ compounds only earlier returns, which the code verifies.
@tab:variables lists the predictors, their construction and their publication lags.

The award version's regime model and forecast targets relied on columns of `one45.csv` that held
future rather than past prices (the column labeled `realpricelag` equals the following month's
real price on #n.data.audit_future of #n.data.audit_pairs comparable rows) and on "ahead" targets
that were shifted backward in time. This edition builds every predictor from data dated at or
before the forecast origin and verifies with automated tests that no predictor or forecast
changes when data after its origin are altered; @app-original relates the award version's
estimates to the ones reported here.

#include "../output/tables/variables.typ"

== Dating bear markets <sec-dating>

I date bear markets on the real price index with a symmetric threshold rule in the spirit of
Lunde and Timmermann (2004). Starting from a bull state, the running maximum is a candidate peak;
when the index falls #d.decline% below it, the peak is confirmed and a bear market begins in the
following month. In the bear state the running minimum is a candidate trough; when the index
rises #d.rise% above it, the trough is confirmed and the bear market ends at the trough month. The
rule yields #n.data.n_bears bear markets since #d.full_start_year, #n.data.n_bears_main of them
beginning after #d.main_start_year (@tab:episodes, @fig:price); the most recent ran from
#n.data.last_peak to #n.data.last_trough. The median bear market lasts #n.data.median_bear_months
months with a median peak-to-trough decline of #n.data.median_decline%. Bear months account for
#n.data.bear_share_full% of the full sample and #n.data.bear_share_main% of the months since
#d.main_start_year.

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

== Markov-switching models of returns

Let $r_t = 100 dot Delta ln P_t$ be the monthly real return. The main regime model is a two-state
Markov-switching autoregression with switching mean and variance (Hamilton, 1989):
$
  r_t - mu_(S_t) = phi (r_(t-1) - mu_(S_(t-1))) + sigma_(S_t) epsilon_t, quad
  epsilon_t tilde.op N(0, 1), quad S_t in {"bull", "bear"},
$ <eq:msar>
where $S_t$ follows a first-order Markov chain with transition probabilities
$p_(i j) = Pr(S_t = j | S_(t-1) = i)$. Setting $phi = 0$ gives the switching mean-variance model.
The bear regime is the one with the lower mean, and the expected duration of regime $i$ is
$1 \/ (1 - p_(i i))$. The Hamilton filter delivers the filtered probability
$Q_t = Pr(S_t = "bear" | r_1, dots, r_t)$, which uses only returns through $t$ and is a legitimate
real-time quantity once the parameters are fixed. The smoothed probability conditions on the
whole sample and is used only for description. An $h$-step regime forecast is
$Pr(S_(t+h) = "bear" | r_1, dots, r_t) = [1 - Q_t, Q_t] bold(P)^h e_2$, where $bold(P)$ is the
transition matrix.

*Time-varying transition probabilities.* Following Diebold, Lee and Weinbach (1994) and Filardo
(1994), the TVTP model replaces the constant transition probabilities by
$
  Pr(S_t = "bull" | S_(t-1) = i, z_(t-1)) = Lambda(z_(t-1)^top b_i), quad i in {"bull", "bear"},
$ <eq:tvtp>
where $Lambda$ is the logistic function and $z_(t-1)$ contains a constant and standardized
predictors observed at $t - 1$: the log dividend yield, twelve-month inflation, twelve-month
realized volatility and the drawdown from the twelve-month high. The model nests the
fixed-transition MS-AR(1), so the likelihood-ratio test of zero slopes is chi-squared with two
degrees of freedom per predictor. An #box[$h$-step] forecast from $t$ applies the transition matrix
implied by $z_t$ $h$ times, because later values of the predictors are unknown at $t$.

== Binary models for dated bear markets

The dated bear indicator $y_(t+h)$ is the forecast target. The binary regression
$
  Pr(y_(t+h) = 1 | x_t) = F(alpha + x_t^top beta)
$ <eq:logit>
uses the logistic (logit) or standard normal (probit) distribution function $F$. The
#d.n_forecast_features main predictors in $x_t$ are the log dividend yield, the log CAPE ratio with
lagged earnings, twelve-month CPI inflation, the twelve-month change in the ten-year yield, the
twelve-month real price change and twelve-month realized volatility. In-sample estimates use Newey
and West (1987) standard errors, since overlapping horizons make the errors serially correlated.

== Machine learning

Two classifiers in the spirit of Gu, Kelly and Xiu (2020) estimate the same conditional
probability with more flexible functional forms. The elastic-net logit (Zou and Hastie, 2005)
penalizes a mixture of the absolute and squared coefficients, with inverse penalty
$C in {#d.enet_c}$ and mixing weight in ${#d.enet_l1}$ (#d.n_enet_grid combinations).
Gradient-boosted classification trees (Friedman, 2001) use depths ${#d.gbt_depth}$ and
${#d.gbt_iter}$ boosting rounds with a learning rate of #d.gbt_lr (#d.n_gbt_grid combinations).
Hyperparameters are chosen without looking outside the training window: the last
#d.ml_validation_years years of training origins form a validation block, the estimation block ends
$h$ months before it so that no estimation target falls in the validation period, and the
combination with the lowest validation Brier score is refit on the whole window. Each method is
applied to the six main predictors and to a rich set that adds the #d.n_extra_features additional
predictors of @sec-robust and the real-time bear state.

== Forecast combination

The equal-weight combination averages the probability forecasts of univariate logits on each of
the #d.n_all_features predictors (Rapach, Strauss and Zhou, 2010). Dynamic model averaging (Raftery,
Kárný and Ettler, 2010) instead weights forecasts by their recent accuracy. With a fixed set of
member forecasts, the DMA recursion, which flattens the previous weights by a forgetting factor
$alpha$ and then multiplies them by each member's predictive likelihood, gives weights
$
  w_(k, t) prop exp(sum_s alpha^(t - h - s) ln p_k (y_(s+h))),
$ <eq:dma>
where the sum runs over earlier forecasts whose outcomes $y_(s+h)$ are known at $t$, scored against
the vintage labels available at $t$. I use $alpha = #d.dma_alpha$ and report
$alpha in {#d.dma_alphas}$ as a check; $alpha = 1$ is recursive Bayesian model averaging. DMA is
applied to the univariate logits and to the main model set.

== Real-time design <sec-oos-design>

Forecasts are made at every month-end from #o.first_origin to #o.last_origin for horizons of
#d.horizons months. At each origin $t$ every model is re-estimated on an expanding window using only
(i) predictors dated $s <= t$; (ii) vintage bear labels from dating the price history through $t$,
so that a training pair $(x_s, y_(s+h))$ requires $s + h <= t$; and (iii) for the regime models,
parameters re-estimated each January on all returns from #d.full_start_year through the origin
(#o.n_refits estimations of each model) with filtered probabilities from those parameters. The logits and probits are re-estimated
every month. The elastic net and the boosted trees are re-estimated, with hyperparameter selection,
each January and applied to the current predictors every month, which keeps their cost modest.
Training starts in #n.data.first_valid, when all predictors are first available. The two baselines
are the *unconditional frequency*, the training-sample share of bear months $h$ months ahead, and
*persistence*, the training-sample frequency of a bear market $h$ months ahead conditional on the
current real-time state (in a confirmed bear market or not). The regime-model forecasts are logit
recalibrations of the $h$-step regime forecast, which map the regime probability into the
probability of a dated bear market on training data only.

== Evaluation and inference

Accuracy is measured by the Brier score (Brier, 1950), the log loss (with probabilities truncated
to $[#d.floor, 1 - #d.floor]$), the area under the ROC curve (AUC) and calibration curves. Brier
skill is the percentage reduction in the Brier score relative to the unconditional frequency. The
Murphy (1973) decomposition splits the Brier score into reliability (miscalibration, lower is
better), resolution (how much the outcome frequency varies with the forecast, higher is better) and
the uncertainty of the outcome, using #d.murphy_bins equal-width forecast bins.

Pairwise differences in Brier score are tested with the Diebold and Mariano (1995) statistic with
the small-sample correction of Harvey, Leybourne and Newbold (1997). The conventional Bartlett
window of $h - 1$ lags (implemented as $max(h - 1, 1)$, so one lag at one month) is too short here: bear markets last many months, so a model's advantage
over persistence persists too: at one month the first-order autocorrelation of the loss differences
against persistence has a median of #n.acf.h1.median across models. I therefore report the tests with the conventional window and
with #(int(d.block) - 1) lags. Because many models and horizons are compared, three further
procedures control for the search. Hansen's (2005) test for superior predictive ability (SPA) asks
whether any model beats persistence, with White's (2000) Reality Check as its conservative bound;
the joint version treats every model-horizon pair as a separate forecast. The model confidence set
(MCS) of Hansen, Lunde and Nason (2011) is the set of models that cannot be distinguished from the
best at the 10% level. The conditional predictive ability test of Giacomini and White (2006) asks
whether the best model's advantage over persistence depends on the real-time bear state. All
bootstrap procedures resample target months in circular blocks of #d.block months (Künsch, 1989)
with #d.reps draws, jointly for all models.

#place.flush()

= Results <sec-results>

== Returns have two persistent regimes

@tab:regimes reports the fixed-transition regime models. In the MS-AR(1) model for #d.main_sample,
the bull regime has a mean real return of #n.ms.bull_mean% per month with a standard deviation of
#n.ms.bull_sd%, while the bear regime has a mean of #n.ms.bear_mean% and a standard deviation of
#n.ms.bear_sd%. Both regimes are persistent ($p_("bull,bull") = #n.ms.p_bull$,
$p_("bear,bear") = #n.ms.p_bear$), implying expected durations of #n.ms.dur_bull months for bull
regimes and #n.ms.dur_bear months for bear regimes. The autoregressive term ($phi = #n.ms.ar$)
partly reflects the time averaging of monthly prices and lowers the AIC from #n.ms.aic_mv to
#n.ms.aic_ar, so the MS-AR(1) is the main specification. On the full #d.full_start_year to
#d.end_year sample the bull regime is more persistent (expected duration #n.ms.full_dur_bull
months) and the bear regime more volatile (standard deviation #n.ms.full_bear_sd%).

#include "../output/tables/regimes.typ"

@fig:regimes contrasts the filtered and smoothed bear-regime probabilities. The smoothed series
marks the dated bear markets more cleanly (AUC #n.ms.auc_smoothed_now against
#n.ms.auc_filtered_now for the contemporaneous dated state), but that advantage comes from
conditioning on later returns. The filtered series is noisier, reacting to individual volatile
months such as October 1987 and early 2020, and it is the only one a forecaster could have used.

#figure(
  image("../output/figures/fig2_regime_probabilities.png", width: 100%),
  caption: [Filtered and smoothed bear-regime probabilities from the MS-AR(1) model, with dated
    bear markets shaded. Only the filtered probability is used for forecasting.],
) <fig:regimes>

== Time-varying transitions fit better in sample

@tab:tvtp lets the transition probabilities depend on lagged predictors. Inflation is the
clearest single driver: higher inflation lowers the probability of staying in the bull regime
(slope #n.tvtp.infl_yoy.stay_infl_yoy on the logit scale), the likelihood ratio against fixed
transitions is #n.tvtp.infl_yoy.lr (#pv(n.tvtp.infl_yoy.p)), and the regimes keep their meaning. The drawdown
improves the likelihood more (#n.tvtp.drawdown.lr) but changes what the regimes describe: with it,
the low-mean regime becomes short-lived (staying probability #n.tvtp.drawdown.p_bear at the
average drawdown) and captures volatile months after a fall rather than whole bear markets. The
dividend yield and volatility alone do not improve the fit significantly (#pv(n.tvtp.log_dy.p)
and #n.tvtp.vol_12.p). With all four predictors the likelihood ratio is #n.tvtp.all.lr on
#n.tvtp.all.df degrees of freedom and the AIC falls from #n.tvtp.fixed_aic to #n.tvtp.all.aic, but
the BIC, which penalizes the eight extra parameters more heavily, prefers fixed transitions
(#n.tvtp.fixed_bic against #n.tvtp.all.bic); only #n.tvtp.n_bic_better of the five TVTP models beat
the fixed model on BIC. As with the drawdown alone, the joint model's low-mean regime is
short-lived (mean #n.tvtp.all.bear_mean% a month, staying probability #n.tvtp.all.p_bear at the
predictors' means), so its regimes are not the bull and bear regimes of the fixed model. The filtered bear probability of the joint model tracks the dated bear
markets better in sample (AUC #n.tvtp.all.auc against #n.tvtp.fixed_auc). @fig:tvtp shows why: the
implied probability of leaving the bull regime swings between #n.tvtp.pbb_min and
#n.tvtp.pbb_max, against a constant #n.tvtp.pbb_fixed with fixed transitions, and it is high
during and shortly after declines.

#include "../output/tables/tvtp.typ"

#figure(
  image("../output/figures/fig9_tvtp.png", width: 100%),
  caption: [Probability of switching from the bull to the bear regime implied by the TVTP model
    with all four predictors (in sample, #d.main_sample), against the constant probability of the
    fixed-transition model. Dated bear markets shaded.],
) <fig:tvtp>

== Inflation, valuation and weak returns are associated with bear markets

@tab:logit reports full-sample binary models for the dated bear indicator, estimated on all
origins from #n.logit.start, and @fig:forest plots the logit coefficients. A higher dividend yield
(#n.logit.log_dy_h1 at one month) and higher inflation (#n.logit.infl_yoy_h1) raise the probability
of a bear market at every horizon. A strong past year lowers the short-horizon probability
(#n.logit.mom_12_h1 at one month), which captures persistence: a low twelve-month return usually
means a decline is already under way. Realized volatility matters mainly at long horizons
(#n.logit.vol_12_h12 at twelve months). Because the dividend yield divides lagged dividends by the
current price, it rises when prices fall, so part of its coefficient reflects an ongoing decline
rather than cheapness; the dividend yield and the CAPE ratio are strongly negatively correlated, so
their conditional coefficients should not be read separately. The pseudo-$R^2$ falls from
#n.logit.r2_h1 at one month to #n.logit.r2_h12 at twelve months.

#include "../output/tables/logit.typ"

#figure(
  image("../output/figures/fig6_logit_forest.png", width: 100%),
  caption: [Full-sample logit coefficients per one-standard-deviation change in each predictor,
    with 95% Newey-West confidence intervals, by forecast horizon.],
) <fig:forest>

== In real time, models beat the base rate; their edge over persistence is fragile

@tab:oos is the central result. At the one-month horizon every model in the table beats the unconditional
frequency (Brier #o.uncond.h1.brier). Persistence alone reaches #o.persist.h1.brier (skill
#o.persist.h1.bss%). The logit on the six main predictors reaches #o.logit_all.h1.brier (skill
#o.logit_all.h1.bss%, AUC #o.logit_all.h1.auc), and the probit and the logit that adds the
real-time state are almost identical. With the conventional Diebold-Mariano window these gains
over persistence look significant (#pv(o.logit_all.h1.p_per) for the logit), but with a window
that covers the autocorrelation of the loss differences the $p$-value rises to
#o.logit_all.h1.p_per_long. The MS-AR(1) forecast ranks months reasonably (AUC #o.ms.h1.auc) but
is less accurate than persistence (skill #o.ms.h1.bss%). Against the unconditional frequency the window
matters less at one month, where the number of models with a gain significant at the 5% level
falls from #o.h1.n_sig_unc with the conventional window to #o.h1.n_sig_unc_long with
#(int(d.block) - 1) lags, than at three months, where it falls from #o.h3.n_sig_unc to
#o.h3.n_sig_unc_long.

#include "../output/tables/oos.typ"

The block bootstrap in @tab:bootstrap and @fig:intervals puts these differences in perspective.
The 90% interval for the one-month skill of persistence is \[#r.boot.persist.h1.lo,
#r.boot.persist.h1.hi\]% and that of the six-predictor logit \[#r.boot.logit_all.h1.lo,
#r.boot.logit_all.h1.hi\]%; both exclude zero. The logit's gain over persistence, however, ranges
from #r.boot.logit_all.h1.glo to #r.boot.logit_all.h1.ghi percentage points, and the logit beats
persistence in a share of #r.boot.logit_all.h1.share of the bootstrap draws. With blocks of 12 or
36 months instead of #d.block the interval for persistence becomes \[#r.boot_sens.b12.persist.lo,
#r.boot_sens.b12.persist.hi\]% or \[#r.boot_sens.b36.persist.lo, #r.boot_sens.b36.persist.hi\]%.

#figure(
  image("../output/figures/fig8_skill_intervals.png", width: 100%),
  caption: [Out-of-sample Brier skill relative to the unconditional frequency, with 90%
    moving-block bootstrap intervals. The dashed line is the unconditional frequency.],
) <fig:intervals>

#include "../output/tables/bootstrap.typ"

== Skill fades with the horizon

At three months the single-variable dividend-yield logit (skill #o.logit_dy.h3.bss%) and the
six-predictor logit (#o.logit_all.h3.bss%) remain ahead of persistence (#o.persist.h3.bss%), but
by margins that no test can distinguish from zero (#pv(o.logit_dy.h3.p_per_long) and
#o.logit_all.h3.p_per_long with the long window). At six months only the dividend-yield logit
retains a sizable gain (skill #o.logit_dy.h6.bss%, against #o.persist.h6.bss% for persistence),
and even that gain is not significant (#pv(o.logit_dy.h6.p_per_long) with the long window); the
multivariate models are near zero. At twelve months no model is reliably better than the
unconditional frequency: the best skill is #o.logit_dy.h12.bss% and the six-predictor logit has an
AUC of #o.logit_all.h12.auc, below the 0.5 of an uninformative forecast.

@fig:oos shows why. The model probabilities rise sharply once a decline is under way and fall when
the market recovers, so at short horizons they track bear markets well, mostly with a lag. The
calibration curves in @fig:calibration show that the short-horizon forecasts are directionally
right, while at twelve months the curves are flat, and the ROC curves in @fig:roc lie close to the
diagonal.

#figure(
  image("../output/figures/fig3_oos_forecasts.png", width: 100%),
  caption: [Real-time forecast probabilities, plotted at the target month, with dated bear markets
    shaded. Each forecast uses only data available at its origin.],
) <fig:oos>

#figure(
  image("../output/figures/fig4_calibration.png", width: 72%),
  caption: [Calibration of out-of-sample forecasts: observed bear frequency against the mean
    forecast within six forecast-quantile bins. The dotted line is perfect calibration.],
) <fig:calibration>

#figure(
  image("../output/figures/fig5_roc.png", width: 72%),
  caption: [ROC curves of out-of-sample forecasts by horizon, with areas under the curve.],
) <fig:roc>

== Time-varying transitions, machine learning and combinations

@tab:modern evaluates the newer methods in the same real-time design. The TVTP model ranks months
better than the fixed-transition model (one-month AUC #o.tvtp.h1.auc against #o.ms.h1.auc) but its
probabilities are worse calibrated, and its Brier skill (#o.tvtp.h1.bss%) is no higher than that
of the fixed model (#o.ms.h1.bss%) and below persistence at every horizon. Its in-sample advantage
does not carry over to forecasting.

The machine-learning models do not change the picture either. Gradient boosting on the rich
predictor set is the most accurate of them at one month (skill #o.gbt_rich.h1.bss%, AUC
#o.gbt_rich.h1.auc), essentially tied with the six-predictor logit, but it deteriorates sharply as
the horizon lengthens (#o.gbt_rich.h6.bss% at six months and #o.gbt_rich.h12.bss% at twelve): with
only a handful of bear markets in each training window, flexible models fit episodes rather than
regularities. The elastic net is less accurate than the unpenalized six-predictor logit
(#o.enet.h1.bss% against #o.logit_all.h1.bss% at one month); part of this gap may reflect the
annual rather than monthly re-estimation of the machine-learning models, which updates their
training labels only once a year. The time-series
validation most often chose the weakest penalty for the elastic net on the main predictors
(#n.ml.enet.top, #n.ml.enet.top_share% of the #n.ml.enet.n_fits fits) and the shallowest, shortest
boosting schedule for both predictor sets (#n.ml.gbt_rich.top, #n.ml.gbt_rich.top_share% of fits
on the rich set).

#include "../output/tables/modern.typ"

Combinations are stable rather than spectacular (@tab:combination). Dynamic model averaging of
the main models reaches a one-month skill of #o.dma_all.h1.bss%, below the best individual model in
hindsight (#o.logit_ext.h1.bss% for the logit on all #d.n_all_features predictors) but without having to know in
advance which model that is; it inherits the weakness of its
members beyond three months (#o.dma_all.h12.bss% at twelve). The equal-weight average of the
univariate logits is more conservative (#o.combo.h1.bss% at one month, #o.combo.h6.bss% at six).
The forgetting factor is not innocuous: with $alpha$ between 0.95 and 1 the one-month skill of DMA
on all models ranges from #n.comb.dma_all_10.h1% to #n.comb.dma_all_095.h1%, a spread comparable to
the gain of the best models over persistence, and for DMA on all models the fastest forgetting is
the most accurate at every horizon. Because that ranking is only known in hindsight, the main
results keep $alpha = #d.dma_alpha$.

#include "../output/tables/combination.typ"

== Where the skill comes from

The Murphy decomposition in @tab:murphy and @fig:murphy separates calibration from
discrimination. At one month persistence already has about as much resolution as the
six-predictor logit (#mur.persist.h1.res against #mur.logit_all.h1.res, times 100) but is worse
calibrated (reliability #mur.persist.h1.rel against #mur.logit_all.h1.rel). The logit's advantage
over persistence is therefore mostly better calibration of the same information, not new
information. The univariate drawdown logit has the highest resolution at one month, which is
consistent with its role as an early measure of a decline already in progress. At twelve months
resolution is small for the main models (#mur.logit_all.h12.res for the logit and
#mur.persist.h12.res for persistence), and the forecasts with more resolution, such as boosting on
the rich set, pay for it with much worse reliability (#mur.gbt_rich.h12.res against
#mur.gbt_rich.h12.rel).

#include "../output/tables/murphy.typ"

#figure(
  image("../output/figures/fig10_murphy.png", width: 100%),
  caption: [Murphy decomposition of out-of-sample Brier scores: resolution against reliability for
    selected models, by horizon.],
) <fig:murphy>

== Accounting for the number of models compared

The main design compares #d.n_challengers distinct non-baseline forecasts with persistence at four
horizons, #o.n_tests comparisons in all (the univariate dividend-yield logit is the dividend-yield
logit of @tab:oos and is counted once). With the conventional Diebold-Mariano window, #o.n_sig_persist of
them are significant at the 5% level (#o.n_sig_persist_h1 at one month); with the
#(int(d.block) - 1)-lag window #o.n_sig_persist_long remains (#o.min_p_long_model, #pv(o.min_p_persist_long)). The tests in
@tab:spa and @tab:mcs settle the question formally. Hansen's SPA test cannot reject that no model
beats persistence: the consistent $p$-value is #n.spa.h1.p_c at one month, #n.spa.h3.p_c at three,
and #n.spa.joint.p_c when all #n.spa.joint.n model-horizon pairs are considered jointly (Reality
Check #n.spa.joint.p_rc\; #n.spa.b12_p_c with 12-month blocks). Persistence belongs to the 90% model
confidence set at every horizon (MCS $p$-values #n.mcs.h1.persist_p, #n.mcs.h3.persist_p,
#n.mcs.h6.persist_p and #n.mcs.h12.persist_p), whereas the unconditional frequency is excluded at one
month (#pv(n.mcs.h1.uncond_p)). At one month #n.mcs.h1.n_in of the #n.mcs.h1.n_models models are
in the set; at longer horizons almost all are, because the data cannot rank them.

#include "../output/tables/spa.typ"

#include "../output/tables/mcs.typ"

The Giacomini-White test asks whether the advantage of the most accurate model at each horizon
depends on whether a bear market is under way. At one month it does not (#pv(n.gw.h1.p)): the best model
(#n.gw.h1.model) is ahead of persistence by a similar margin in both states. At three months
there is weak evidence (#pv(n.gw.h3.p)) that the drawdown logit helps in bull states (mean loss
difference #n.gw.h3.bull, times 1,000) and hurts in confirmed bear markets (#n.gw.h3.bear), which
fits its role as an early-warning measure of declines in progress.

= Robustness <sec-robust>

== Regime specification and sample

@tab:regime_specs compares the main model with four alternatives on #d.main_sample and with the main
model estimated on two subsamples. The MS-AR(1) has the lowest AIC (#r.spec.ar1.aic) and BIC
(#r.spec.ar1.bic) in the first group. Letting only the variance switch gives a high-volatility
regime (standard deviation #r.spec.var_only.bear_sd% against #r.spec.var_only.bull_sd%) that tracks
dated bear markets less well (AUC #r.spec.var_only.auc against #r.spec.ar1.auc). Letting only the
mean switch picks out crash months rather than bear markets: the low-mean regime averages
#r.spec.mean_only.bear_mean% a month and lasts #r.spec.mean_only.dur_bear months. A three-regime
model splits the bull state into a calm regime (mean #r.spec.three.mid_mean%, duration
#r.spec.three.dur_mid months) and a short rebound regime (mean #r.spec.three.bull_mean%, duration
#r.spec.three.dur_bull months), while its bear regime (mean #r.spec.three.bear_mean%, standard
deviation #r.spec.three.bear_sd%) resembles the two-regime one and tracks dated bear markets better
(AUC #r.spec.three.auc); its extra parameters do not pay for themselves by AIC (#r.spec.three.aic).
Across subsamples the bear regime's volatility is stable (#r.spec.pre.bear_sd% before #d.split,
#r.spec.post.bear_sd% after), whereas the bull regime became more persistent (expected duration
#r.spec.pre.dur_bull months before, #r.spec.post.dur_bull after) and the filtered probability became
a much better real-time marker of bear markets (AUC #r.spec.pre.auc before, #r.spec.post.auc after).

#include "../output/tables/regime_specs.typ"

== Dating rule

@tab:dating shows how the set of episodes depends on the rule. A 15% threshold dates
#r.dating.real15.n bear markets since #d.full_start_year and a 25% threshold #r.dating.real25.n,
against #r.dating.main.n for the main rule. Dating nominal prices yields #r.dating.nominal20.n_since
episodes since #d.main_start_year, because inflation in the 1970s turned long real declines into
flat nominal prices; the bear share falls to #r.dating.nominal20.share%. @tab:robust_oos re-runs the
entire real-time exercise under each rule. The six-predictor logit has a one-month skill between
#rv.real15.logit_all.h1.bss% and #rv.nominal20.logit_all.h1.bss% under every rule, persistence
between #rv.real25.persist.h1.bss% (25%) and #rv.real15.persist.h1.bss% (15%), and the multivariate
logit has negative skill at twelve months under both real-price rules
(#rv.real15.logit_all.h12.bss% and #rv.real25.logit_all.h12.bss%). The SPA test against persistence
does not reject under any alternative rule or window (smallest consistent $p$-value
#n.spa.min_variant_p, @tab:spa).

#include "../output/tables/dating.typ"

== Estimation window and evaluation period

Rolling #d.rolling_years\-year windows reduce the skill of persistence, the regime model and the
dividend-yield logit at every horizon (for example #rv.rolling.logit_dy.h1.bss% for the
dividend-yield logit at one month, against #rv.main.logit_dy.h1.bss%), and the multivariate logit
deteriorates sharply at long horizons (#rv.rolling.logit_all.h12.bss% at twelve months). The
longer history in the expanding window is valuable, which is expected for a rare event: thirty
years contain only a handful of bear markets.

The evaluation-period rows of @tab:robust_oos show that forecastability is concentrated in the
later part of the sample. For targets from #d.split onward, persistence reaches a one-month skill
of #rv.post.persist.h1.bss% and the multivariate logit #rv.post.logit_all.h1.bss%; for earlier
targets the corresponding figures are #rv.pre.persist.h1.bss% and #rv.pre.logit_all.h1.bss%. The
long real bear markets of 1968 to 1982 were confirmed slowly, 11 to 16 months after their peaks
(@tab:episodes), while the declines of 2000 to 2002 and 2007 to 2009 were confirmed within 7 and 9
months. Excluding the 2007-2009 crisis (#d.crisis) changes little (one-month skill
#rv.nocrisis.persist.h1.bss% for persistence and #rv.nocrisis.logit_all.h1.bss% for the logit).

#include "../output/tables/robust_oos.typ"

== Additional predictors

@tab:predictors evaluates each of the #d.n_all_features predictors as a univariate logit. The
strongest single predictors at one month are price-based: the drawdown from the twelve-month high
(skill #o.uni_drawdown.h1.bss%, AUC #o.uni_drawdown.h1.auc) and the twelve-month real price change
(#o.uni_mom_12.h1.bss%). The drawdown measures how far a decline has already gone before the
#d.decline% threshold is crossed, so it recognizes the same ongoing bear markets slightly earlier
than the real-time state; at three months its advantage over persistence is no longer
significant (#pv(o.uni_drawdown.h3.p_per_long) with the long window). The additional valuation and macroeconomic predictors add
nothing at one month: the excess CAPE yield (#o.uni_ecy.h1.bss%), the payout ratio
(#o.uni_log_payout.h1.bss%), earnings growth (#o.uni_earn_growth_12.h1.bss%) and the level of the
ten-year yield (#o.uni_rate_level.h1.bss%). At six and twelve months the dividend yield remains the
best single predictor (#o.uni_log_dy.h6.bss% and #o.uni_log_dy.h12.bss%). The logit on all
#d.n_all_features predictors is the most accurate model at one month (#o.logit_ext.h1.bss%) and
overfits at twelve (#o.logit_ext.h12.bss%).

#include "../output/tables/predictors.typ"

= Limitations <sec-limits>

The sample contains #n.data.n_bears_main bear markets since #d.main_start_year, so the
out-of-sample evaluation rests on few independent episodes, and the overlapping monthly forecasts
are strongly dependent. The block bootstrap and the HAC-based tests account for this dependence
only approximately, and the wide intervals are an honest summary of how little a sample of this
size can resolve. Monthly average prices understate intra-month declines: the 2020 decline, for
example, reaches only #n.data.decline_2020% in monthly averages and is not dated as a bear market. Publication lags are imposed
conservatively, but the Shiller series are themselves revised and partly interpolated, and this
paper uses a single vintage, so the exercise is quasi-real-time rather than a true vintage
analysis; the comparison with the archived extract suggests that revisions are small and confined
to the most recent months. The machine-learning models are re-estimated once a year with small
hyperparameter grids to keep the computation modest, and richer specifications might do
differently. The predictor set is limited to what Shiller's workbook contains; credit spreads and
the term structure, which Chen (2009) and Chen, Chen and Chou (2017) find useful, are not in it.

= Conclusion <sec-concl>

The regime-switching description of the S&P 500 is robust: real returns alternate between a long,
calm bull regime and a short, volatile bear regime in every specification and subsample examined
here, and the switching probabilities move with inflation and recent drawdowns. The claim that
market and macroeconomic indicators forecast bear markets is much weaker once forecasts are made in
real time. The information that best predicts a bear market next month is that one has already
begun. Logit models, machine-learning classifiers and forecast combinations built on valuation,
inflation, momentum and volatility improve on that persistence benchmark by several points of
Brier skill at one month, mostly through better calibration, but the improvement is not distinguishable
from chance once the dependence of forecast errors and the number of models are taken into
account. Beyond a few months, the dividend yield retains a small and imprecise advantage over the
unconditional frequency, and the flexible models do worse than the base rate. These conclusions
survive changes to the dating rule, the regime model, the estimation window, the
evaluation period and the predictor set. They are consistent with a market in which downturns are
difficult to anticipate from public information, and they suggest that the useful contribution of
these models is faster recognition of a bear market, not advance warning of one.

#place.flush()

#heading(numbering: none)[References]

#set par(first-line-indent: 0em, hanging-indent: 1.5em, spacing: 0.7em)
#set text(size: 10pt)

Ang, A. and Timmermann, A. (2012). Regime changes and financial markets. _Annual Review of
Financial Economics_, 4(1), 313-337.

Brier, G. W. (1950). Verification of forecasts expressed in terms of probability. _Monthly Weather
Review_, 78(1), 1-3.

Campbell, J. Y. and Shiller, R. J. (1988). The dividend-price ratio and expectations of future
dividends and discount factors. _Review of Financial Studies_, 1(3), 195-228.

Chen, N.-K., Chen, S.-S. and Chou, Y.-H. (2017). Further evidence on bear market predictability:
The role of the external finance premium. _International Review of Economics & Finance_, 50,
106-121.

Chen, S.-S. (2009). Predicting the bear stock market: Macroeconomic variables as leading
indicators. _Journal of Banking & Finance_, 33(2), 211-223.

Clark, T. E. and West, K. D. (2007). Approximately normal tests for equal predictive accuracy in
nested models. _Journal of Econometrics_, 138(1), 291-311.

Diebold, F. X., Lee, J.-H. and Weinbach, G. C. (1994). Regime switching with time-varying
transition probabilities. In C. P. Hargreaves (Ed.), _Nonstationary Time Series Analysis and
Cointegration_ (pp. 283-302). Oxford University Press.

Diebold, F. X. and Mariano, R. S. (1995). Comparing predictive accuracy. _Journal of Business &
Economic Statistics_, 13(3), 253-263.

Estrella, A. and Mishkin, F. S. (1998). Predicting U.S. recessions: Financial variables as leading
indicators. _Review of Economics and Statistics_, 80(1), 45-61.

Fama, E. F. and French, K. R. (1988). Dividend yields and expected stock returns. _Journal of
Financial Economics_, 22(1), 3-25.

Ferrari, S. and Cribari-Neto, F. (2004). Beta regression for modelling rates and proportions.
_Journal of Applied Statistics_, 31(7), 799-815.

Filardo, A. J. (1994). Business-cycle phases and their transitional dynamics. _Journal of Business
& Economic Statistics_, 12(3), 299-308.

Friedman, J. H. (2001). Greedy function approximation: A gradient boosting machine. _Annals of
Statistics_, 29(5), 1189-1232.

Giacomini, R. and White, H. (2006). Tests of conditional predictive ability. _Econometrica_,
74(6), 1545-1578.

Goetzmann, W. N. and Jorion, P. (1993). Testing the predictive power of dividend yields. _Journal
of Finance_, 48(2), 663-679.

Gu, S., Kelly, B. and Xiu, D. (2020). Empirical asset pricing via machine learning. _Review of
Financial Studies_, 33(5), 2223-2273.

Hamilton, J. D. (1989). A new approach to the economic analysis of nonstationary time series and
the business cycle. _Econometrica_, 57(2), 357-384.

Hammerschmid, R. and Lohre, H. (2018). Regime shifts and stock return predictability.
_International Review of Economics & Finance_, 56, 138-160.

Hansen, P. R. (2005). A test for superior predictive ability. _Journal of Business & Economic
Statistics_, 23(4), 365-380.

Hansen, P. R., Lunde, A. and Nason, J. M. (2011). The model confidence set. _Econometrica_, 79(2),
453-497.

Harvey, D., Leybourne, S. and Newbold, P. (1997). Testing the equality of prediction mean squared
errors. _International Journal of Forecasting_, 13(2), 281-291.

Künsch, H. R. (1989). The jackknife and the bootstrap for general stationary observations. _Annals
of Statistics_, 17(3), 1217-1241.

Lewellen, J. (1999). The time-series relations among expected return, risk, and book-to-market.
_Journal of Financial Economics_, 54(1), 5-43.

Lunde, A. and Timmermann, A. (2004). Duration dependence in stock prices: An analysis of bull and
bear markets. _Journal of Business & Economic Statistics_, 22(3), 253-273.

Maheu, J. M. and McCurdy, T. H. (2000). Identifying bull and bear markets in stock returns.
_Journal of Business & Economic Statistics_, 18(1), 100-112.

Murphy, A. H. (1973). A new vector partition of the probability score. _Journal of Applied
Meteorology_, 12(4), 595-600.

Newey, W. K. and West, K. D. (1987). A simple, positive semi-definite, heteroskedasticity and
autocorrelation consistent covariance matrix. _Econometrica_, 55(3), 703-708.

Pagan, A. R. and Sossounov, K. A. (2003). A simple framework for analysing bull and bear markets.
_Journal of Applied Econometrics_, 18(1), 23-46.

Pontiff, J. and Schall, L. D. (1998). Book-to-market ratios as predictors of market returns.
_Journal of Financial Economics_, 49(2), 141-160.

Raftery, A. E., Kárný, M. and Ettler, P. (2010). Online prediction under model uncertainty via
dynamic model averaging: Application to a cold rolling mill. _Technometrics_, 52(1), 52-66.

Rapach, D. E., Strauss, J. K. and Zhou, G. (2010). Out-of-sample equity premium prediction:
Combination forecasts and links to the real economy. _Review of Financial Studies_, 23(2),
821-862.

Shiller, R. J. (2015). _Irrational Exuberance_ (3rd ed.). Princeton University Press. Data: U.S.
Stock Markets 1871-Present and CAPE Ratio, #link("https://shillerdata.com")[shillerdata.com],
downloaded #s.downloaded.

Smithson, M. and Verkuilen, J. (2006). A better lemon squeezer? Maximum-likelihood regression with
beta-distributed dependent variables. _Psychological Methods_, 11(1), 54-71.

Stambaugh, R. F. (1999). Predictive regressions. _Journal of Financial Economics_, 54(3), 375-421.

Welch, I. and Goyal, A. (2008). A comprehensive look at the empirical performance of equity premium
prediction. _Review of Financial Studies_, 21(4), 1455-1508.

White, H. (2000). A reality check for data snooping. _Econometrica_, 68(5), 1097-1126.

Zou, H. and Hastie, T. (2005). Regularization and variable selection via the elastic net. _Journal
of the Royal Statistical Society: Series B_, 67(2), 301-320.

// ------------------------------------------------------------------ appendix
#pagebreak()
#set par(first-line-indent: 1.2em, hanging-indent: 0em, spacing: 0.62em)
#set text(size: 11pt)
#counter(heading).update(0)
#set heading(numbering: "A.1", supplement: [Appendix])

= Regressions of the regime probability and the award version <app-original>

The award version of this thesis forecast the filtered regime probability $Q_t$ rather than a dated
event, with univariate OLS and beta regressions (Ferrari and Cribari-Neto, 2004; Smithson and
Verkuilen, 2006) of $Q_(t+h)$ on each of #n.orig.n_pred monthly-change predictors,
$
  Q_(t+h) = alpha + beta x_t + e_(t+h),
$ <eq:ols>
and an out-of-sample comparison with an intercept-only model. @tab:original_spec re-estimates this
design on the Shiller data with predictors observable at $t$, growth rates in place of index levels
and Newey-West standard errors. The number of predictors significant at the 5% level is
#n.orig.sig5_h1 of #n.orig.n_pred at one month, #n.orig.sig5_h3 at three, #n.orig.sig5_h6 at six and
#n.orig.sig5_h12 at twelve. The largest $R^2$ (#n.orig.max_r2) belongs to the #lower(n.orig.max_r2_label)
at one month (coefficient #n.orig.tr_h1 percentage points), which is close to mechanical because the
filter itself updates on recent returns. Total-return-scaled earnings show no relationship ($R^2$ =
#n.orig.trse_h1_r2). Because $Q_t$ uses full-sample parameters, these are in-sample associations
rather than forecasts.

#include "../output/tables/original_spec.typ"

@tab:mspe reports the out-of-sample comparison. Panel C uses expanding-window refits from
#n.mspe.test_start: #n.mspe.n_below1_ols of #n.mspe.n_cells OLS ratios of mean squared prediction
errors fall below one and #n.mspe.n_cw10_ols are significant at the 10% level by the Clark and West
(2007) test (#n.mspe.n_cw10_ols_long with #(int(d.block) - 1) Bartlett lags), with a best ratio of #n.mspe.min_ratio_ols. The regime probability's own current value
achieves #n.mspe.qnow_h1 at one month and no gain at six months (#n.mspe.qnow_h6).

The award version reached stronger conclusions for three reasons that a replication of its code
path on its own data confirms (@tab:replication, @fig:replication): its regime model was estimated
with the following month's price as a regressor, its "$k$ months ahead" targets were shifted
backward rather than forward in time, and its loss ratio compared squared mean errors rather than
mean squared errors. The replication reproduces the reported transition probabilities
(#n.rep.p_bull_replicated and #n.rep.p_bear_replicated against #n.rep.p_bull_reported and
#n.rep.p_bear_reported) and the reported coefficients (correlation #n.rep.corr_coef). For dividends
at one month the reported ratio of #n.rep.div_ratio_reported becomes #n.rep.div_ratio_true as a true
MSPE ratio on the same design and #n.rep.div_ratio_corrected after all corrections. Panels A and B of
@tab:mspe show the award version's design with its own ratio and with the correct one.

#include "../output/tables/replication.typ"

#include "../output/tables/mspe.typ"

#figure(
  image("../output/figures/fig7_replication.png", width: 100%),
  caption: [Values reported in the award version against a Python replication of its code path on
    its archived data, including its timing errors.],
) <fig:replication>

= Data source and vintage <app-data>

The workbook used here is `ie_data.xls`, downloaded on #s.downloaded from #link(s.url)[the
download link on shillerdata.com] (#s.megabytes MB, server last-modified date #s.last_modified).
Its SHA-256 hash is shown below, and `thesis.py` refuses to run on a file with a different hash,
so a future Shiller update has to be adopted deliberately.

#align(center)[#text(size: 9pt)[#raw(s.sha256)]]

The parser reads the "#s.sheet" sheet, checks each column heading, converts
Shiller's fractional dates (1871.01 is January 1871 and 1871.1 is October), drops the note rows below
the table and leaves blank recent cells missing. @tab:data_comparison compares the archived extract
`one45.csv` with this vintage month by month; a list of every differing observation is in
`output/results/one45_differences.csv`.

#include "../output/tables/data_comparison.typ"
