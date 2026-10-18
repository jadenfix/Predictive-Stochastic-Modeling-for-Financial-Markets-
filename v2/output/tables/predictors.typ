#figure(
  caption: [Out-of-sample Brier skill (%) of individual predictors and combinations],
  kind: table,
  [
    #set text(size: 8pt, hyphenate: false)
    #set par(justify: false, first-line-indent: 0em)
    #table(
      columns: (2.8fr, 1fr, 1fr, 1fr, 1fr, 1fr),
      align: (left, center, center, center, center, center),
      stroke: none,
      inset: (x: 3pt, y: 2.4pt),
      table.hline(stroke: 0.9pt),
      table.header(
        [], [h = 1], [h = 3], [h = 6], [h = 12], [AUC, h = 1],
      ),
      table.hline(stroke: 0.5pt),
      table.cell(colspan: 6, align: left)[_Baseline_],
      [Persistence], [18.9#super[\*\*\*]], [11.5#super[\*\*\*]], [4.9#super[\*]], [0.8], [0.688],
      table.cell(colspan: 6, inset: (y: 1.5pt))[],
      table.cell(colspan: 6, align: left)[_Univariate logits: main predictors_],
      [Log dividend yield], [16.5#super[\*\*\*]], [12.3#super[\*\*\*]], [7.9#super[\*]], [1.9], [0.627],
      [Log CAPE], [14.4#super[\*\*\*]], [9.0#super[\*\*\*]], [3.3], [−5.1], [0.653],
      [CPI inflation, 12-month], [10.0#super[\*\*\*]], [7.8#super[\*\*\*]], [5.0#super[\*\*\*]], [1.3#super[\*]], [0.769],
      [12-month change in 10-year yield], [2.0], [0.6], [−0.2], [0.2], [0.655],
      [12-month real price change], [23.7#super[\*\*\*]], [12.6#super[\*\*\*]], [4.5#super[\*]], [−0.5], [0.821],
      [12-month realized volatility], [2.5], [−0.1], [−2.4], [−2.3], [0.593],
      table.cell(colspan: 6, inset: (y: 1.5pt))[],
      table.cell(colspan: 6, align: left)[_Univariate logits: additional predictors_],
      [Excess CAPE yield], [0.5], [−3.1], [−6.6], [−12.9], [0.543],
      [Log payout ratio], [−0.5], [−1.5], [−2.3], [−3.0], [0.415],
      [12-month real earnings growth], [0.0], [−0.9], [−1.3], [−1.2], [0.617],
      [10-year Treasury yield], [−4.5], [−6.0], [−7.6], [−8.1], [0.548],
      [Drawdown from 12-month high], [27.7#super[\*\*\*]], [14.9#super[\*\*\*]], [4.3], [−1.1], [0.844],
      table.cell(colspan: 6, inset: (y: 1.5pt))[],
      table.cell(colspan: 6, align: left)[_Multi-predictor forecasts_],
      [Equal-weight combination (11 univariate logits)], [14.4#super[\*\*\*]], [8.2#super[\*\*\*]], [3.2#super[\*\*]], [−1.0], [0.767],
      [Logit: all 11 predictors], [24.7#super[\*\*\*]], [5.7], [−14.5], [−28.9], [0.779],
      table.hline(stroke: 0.9pt),
    )
    #block(width: 100%, above: 0.5em)[#set text(size: 7.5pt); #set par(justify: true); #align(left)[_Notes:_ Real-time expanding-window forecasts with the main dating rule; every model is re-estimated at each origin on data available then. The combination averages the probability forecasts of the univariate logits with equal weights. Skill is relative to the unconditional frequency. Stars: one-sided Diebold-Mariano test against the unconditional frequency, \* p \< 0.10, \*\* p \< 0.05, \*\*\* p \< 0.01.]]
  ],
) <tab:predictors>
