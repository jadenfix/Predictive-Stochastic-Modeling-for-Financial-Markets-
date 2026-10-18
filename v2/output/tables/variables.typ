#figure(
  caption: [Predictors, construction and publication lags],
  kind: table,
  [
    #set text(size: 8.5pt, hyphenate: false)
    #set par(justify: false, first-line-indent: 0em)
    #table(
      columns: (1.9fr, 2.1fr, 1fr, 1fr, 0.6fr, 0.6fr),
      align: (left, left, left, center, right, right),
      stroke: none,
      inset: (x: 3pt, y: 2.4pt),
      table.hline(stroke: 0.9pt),
      table.header(
        [Predictor], [Construction], [Units], [Lag (months)], [Mean], [SD],
      ),
      table.hline(stroke: 0.5pt),
      table.cell(colspan: 6, align: left)[_Monthly-change predictors (award-version variables; appendix)_],
      [CPI inflation, monthly], [100 dlog CPI], [% per month], [1], [0.30], [0.36],
      [Change in 10-year yield], [Monthly change], [pp], [0], [0.00], [0.27],
      [Real bond return], [100 dlog real bond index], [% per month], [0 (CPI 1)], [0.17], [1.97],
      [Real dividend growth], [100 dlog real dividends], [% per month], [6], [0.17], [0.62],
      [Real total return], [Price return plus D/12P, less inflation], [% per month], [0 (D 6, CPI 1)], [0.53], [3.63],
      [TR-scaled earnings growth], [100 dlog real TR-scaled earnings], [% per month], [6], [0.46], [4.75],
      [Change in log TR-CAPE], [100 dlog TR price / 10-yr mean earnings], [% per month], [0 (E 6)], [0.07], [3.64],
      table.cell(colspan: 6, inset: (y: 1.5pt))[],
      table.cell(colspan: 6, align: left)[_State predictors (main bear-market models)_],
      [Log dividend yield], [log(D / P)], [log points], [0 (D 6)], [−3.69], [0.42],
      [Log CAPE], [log(P / 10-yr mean real earnings)], [log points], [0 (E 6)], [3.00], [0.44],
      [CPI inflation, 12-month], [100 x 12-month dlog CPI], [%], [1], [3.64], [2.63],
      [12-month change in 10-year yield], [12-month change], [pp], [0], [0.00], [1.11],
      [12-month real price change], [100 x 12-month dlog real price], [%], [0 (CPI 1)], [3.55], [15.87],
      [12-month realized volatility], [sd of monthly real returns x sqrt(12)], [% annualized], [0 (CPI 1)], [11.23], [4.86],
      table.cell(colspan: 6, inset: (y: 1.5pt))[],
      table.cell(colspan: 6, align: left)[_Additional state predictors (predictor experiments, rich machine-learning set)_],
      [Excess CAPE yield], [100 E10/P less (yield less 10-yr inflation)], [%], [0 (E 6, CPI 1)], [3.25], [2.35],
      [Log payout ratio], [log(D / E)], [log points], [6], [−0.77], [0.30],
      [12-month real earnings growth], [100 x 12-month dlog real earnings], [%], [6], [2.86], [34.66],
      [10-year Treasury yield], [Level], [%], [0], [5.76], [2.91],
      [Drawdown from 12-month high], [100 x log(P / 12-month high)], [%], [0 (CPI 1)], [−6.48], [9.74],
      table.hline(stroke: 0.9pt),
    )
    #block(width: 100%, above: 0.5em)[#set text(size: 7.5pt); #set par(justify: true); #align(left)[_Notes:_ Statistics over January 1960 to June 2026. A forecast is made at the end of month t. Lag gives the publication lag applied to the inputs: CPI enters with one month, dividends (D) and earnings (E) with six. Real values are deflated by the CPI available at t.]]
  ],
) <tab:variables>
