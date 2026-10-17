#figure(
  caption: [Out-of-sample Brier scores (skill relative to the unconditional frequency)],
  kind: table,
  [
    #set text(size: 8.5pt, hyphenate: false)
    #set par(justify: false, first-line-indent: 0em)
    #table(
      columns: (2fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr),
      align: (left, center, center, center, center, center, center),
      stroke: none,
      inset: (x: 3pt, y: 2.4pt),
      table.hline(stroke: 0.9pt),
      table.header(
        [Horizon], [Unconditional frequency], [Persistence (real-time state)], [MS-AR(1) filtered probability], [Logit: dividend yield], [Logit: all predictors], [Best p vs persistence],
      ),
      table.hline(stroke: 0.5pt),
      [1 month], [0.198], [0.161 (18.9%)], [0.176 (10.9%)], [0.165 (16.5%)], [0.157 (20.8%)], [0.256],
      [3 months], [0.199], [0.176 (11.5%)], [0.193 (3.0%)], [0.175 (12.3%)], [0.187 (6.2%)], [0.433],
      [6 months], [0.200], [0.190 (4.9%)], [0.205 (−2.5%)], [0.185 (7.9%)], [0.214 (−6.9%)], [0.287],
      [12 months], [0.202], [0.201 (0.8%)], [0.209 (−3.5%)], [0.198 (1.9%)], [0.224 (−11.1%)], [0.405],
      table.hline(stroke: 0.9pt),
    )
    #block(width: 100%, above: 0.5em)[#set text(size: 7.5pt); #set par(justify: true); #align(left)[_Notes:_ Lower is better. Real-time expanding-window forecasts, targets 1960-2023. The last column is the smallest one-sided Diebold-Mariano p-value of any model against persistence.]]
  ],
) <tab:summary>
