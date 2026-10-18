#figure(
  caption: [Full-sample logit and probit models of a dated bear market h months ahead],
  kind: table,
  [
    #set text(size: 8pt, hyphenate: false)
    #set par(justify: false, first-line-indent: 0em)
    #table(
      columns: (2.3fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr),
      align: (left, center, center, center, center, center, center, center, center),
      stroke: none,
      inset: (x: 3pt, y: 2.4pt),
      table.hline(stroke: 0.9pt),
      table.header(
        [], table.cell(colspan: 4)[Logit], table.cell(colspan: 4)[Probit],
        table.hline(start: 1, end: 5, stroke: 0.4pt),
        table.hline(start: 5, end: 9, stroke: 0.4pt),
        [], [h = 1], [h = 3], [h = 6], [h = 12], [h = 1], [h = 3], [h = 6], [h = 12],
      ),
      table.hline(stroke: 0.5pt),
      table.cell(colspan: 9, align: left)[_Valuation_],
      [Log dividend yield], [0.98#super[\*\*\*]], [0.99#super[\*\*\*]], [0.98#super[\*\*\*]], [1.01#super[\*\*\*]], [0.58#super[\*\*\*]], [0.59#super[\*\*\*]], [0.58#super[\*\*\*]], [0.60#super[\*\*\*]],
      [], [(0.37)], [(0.37)], [(0.36)], [(0.38)], [(0.21)], [(0.21)], [(0.21)], [(0.22)],
      [Log CAPE], [0.59#super[\*]], [0.65#super[\*\*]], [0.70#super[\*\*]], [0.77#super[\*\*]], [0.35#super[\*]], [0.39#super[\*\*]], [0.42#super[\*\*]], [0.47#super[\*\*]],
      [], [(0.32)], [(0.32)], [(0.32)], [(0.33)], [(0.19)], [(0.19)], [(0.19)], [(0.20)],
      table.cell(colspan: 9, inset: (y: 1.5pt))[],
      table.cell(colspan: 9, align: left)[_Macroeconomic_],
      [CPI inflation, 12-month], [0.55#super[\*\*\*]], [0.52#super[\*\*\*]], [0.46#super[\*\*]], [0.41#super[\*\*]], [0.32#super[\*\*\*]], [0.31#super[\*\*\*]], [0.27#super[\*\*]], [0.25#super[\*\*]],
      [], [(0.21)], [(0.19)], [(0.18)], [(0.18)], [(0.11)], [(0.11)], [(0.11)], [(0.10)],
      [12-month change in 10-year yield], [0.25#super[\*]], [0.24#super[\*]], [0.25#super[\*]], [0.23#super[\*]], [0.15#super[\*\*]], [0.15#super[\*]], [0.15#super[\*]], [0.13#super[\*]],
      [], [(0.13)], [(0.13)], [(0.13)], [(0.13)], [(0.08)], [(0.08)], [(0.08)], [(0.08)],
      table.cell(colspan: 9, inset: (y: 1.5pt))[],
      table.cell(colspan: 9, align: left)[_Market_],
      [12-month real price change], [−0.68#super[\*\*\*]], [−0.33#super[\*]], [−0.09], [0.22], [−0.38#super[\*\*\*]], [−0.20#super[\*\*]], [−0.07], [0.13],
      [], [(0.22)], [(0.19)], [(0.16)], [(0.16)], [(0.11)], [(0.10)], [(0.09)], [(0.10)],
      [12-month realized volatility], [0.17], [0.24], [0.30#super[\*\*]], [0.43#super[\*\*\*]], [0.11], [0.15#super[\*]], [0.18#super[\*\*]], [0.26#super[\*\*\*]],
      [], [(0.19)], [(0.16)], [(0.15)], [(0.14)], [(0.10)], [(0.09)], [(0.09)], [(0.09)],
      table.hline(stroke: 0.3pt),
      [Constant], [−0.86#super[\*\*\*]], [−0.81#super[\*\*\*]], [−0.79#super[\*\*\*]], [−0.78#super[\*\*\*]], [−0.52#super[\*\*\*]], [−0.49#super[\*\*\*]], [−0.48#super[\*\*\*]], [−0.47#super[\*\*\*]],
      [], [(0.16)], [(0.16)], [(0.16)], [(0.17)], [(0.09)], [(0.09)], [(0.09)], [(0.10)],
      [Pseudo-R² (McFadden)], [0.196], [0.130], [0.089], [0.073], [0.196], [0.130], [0.089], [0.073],
      [Log-likelihood], [−890.2], [−961.8], [−1,003.6], [−1,014.9], [−891.0], [−961.4], [−1,003.5], [−1,015.7],
      [Observations], [1,740], [1,738], [1,735], [1,729], [1,740], [1,738], [1,735], [1,729],
      table.hline(stroke: 0.9pt),
    )
    #block(width: 100%, above: 0.5em)[#set text(size: 7.5pt); #set par(justify: true); #align(left)[_Notes:_ Dependent variable: 1 if month t+h lies in a dated bear market. Predictors are measured at t and standardized. Newey-West standard errors in parentheses (10, 10, 10, 12 lags by horizon). Forecast origins 1881:06 to 2026:05 for h = 1. \* p \< 0.10, \*\* p \< 0.05, \*\*\* p \< 0.01 (two-sided). In-sample estimates over the whole period, not real-time forecasts.]]
  ],
) <tab:logit>
