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
      [Persistence], [17.6#super[\*\*\*]], [10.0#super[\*\*\*]], [3.9#super[\*\*]], [−0.2], [0.707],
      table.cell(colspan: 6, inset: (y: 1.5pt))[],
      table.cell(colspan: 6, align: left)[_Univariate logits: main predictors_],
      [Log dividend yield], [18.3#super[\*\*\*]], [13.4#super[\*\*\*]], [8.2#super[\*\*]], [1.4], [0.646],
      [Log CAPE], [13.9#super[\*\*\*]], [8.3#super[\*\*\*]], [2.7#super[\*]], [−3.9], [0.668],
      [CPI inflation, 12-month], [5.0#super[\*\*\*]], [3.6#super[\*\*\*]], [1.9#super[\*]], [0.2], [0.775],
      [12-month change in 10-year yield], [0.8], [−0.4], [−0.9], [−0.5], [0.664],
      [12-month real price change], [23.2#super[\*\*\*]], [12.2#super[\*\*\*]], [4.6#super[\*\*]], [0.0], [0.831],
      [12-month realized volatility], [2.2#super[\*\*]], [0.5], [−0.9], [−1.1], [0.614],
      table.cell(colspan: 6, inset: (y: 1.5pt))[],
      table.cell(colspan: 6, align: left)[_Univariate logits: additional predictors_],
      [Excess CAPE yield], [0.1], [−2.0], [−3.7], [−5.7], [0.554],
      [Log payout ratio], [1.3#super[\*]], [0.4], [−0.4], [−1.2], [0.504],
      [12-month real earnings growth], [0.0], [−0.6], [−1.0], [−1.1], [0.622],
      [10-year Treasury yield], [−4.7], [−6.0], [−7.4], [−7.8], [0.562],
      [Drawdown from 12-month high], [26.5#super[\*\*\*]], [13.8#super[\*\*\*]], [4.4#super[\*]], [−0.2], [0.852],
      table.cell(colspan: 6, inset: (y: 1.5pt))[],
      table.cell(colspan: 6, align: left)[_Multi-predictor forecasts_],
      [Equal-weight combination (11 univariate logits)], [13.0#super[\*\*\*]], [7.2#super[\*\*\*]], [2.7#super[\*\*\*]], [−0.7], [0.783],
      [DMA of the 11 univariate logits], [23.3#super[\*\*\*]], [10.6#super[\*\*\*]], [2.3], [−4.5], [0.772],
      [Logit: all 11 predictors], [29.1#super[\*\*\*]], [12.8#super[\*\*]], [−3.0], [−14.4], [0.787],
      table.hline(stroke: 0.9pt),
    )
    #block(width: 100%, above: 0.5em)[#set text(size: 7.5pt); #set par(justify: true); #align(left)[_Notes:_ Real-time expanding-window forecasts with the main dating rule; every model is re-estimated at each origin on data available then. Skill is relative to the unconditional frequency. Stars: one-sided Diebold-Mariano test against the unconditional frequency, \* p \< 0.10, \*\* p \< 0.05, \*\*\* p \< 0.01.]]
  ],
) <tab:predictors>
