#figure(
  caption: [Out-of-sample Brier scores (skill relative to the unconditional frequency)],
  kind: table,
  [
    #set text(size: 8.5pt, hyphenate: false)
    #set par(justify: false, first-line-indent: 0em)
    #table(
      columns: (2fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr),
      align: (left, center, center, center, center, center, center, center),
      stroke: none,
      inset: (x: 3pt, y: 2.4pt),
      table.hline(stroke: 0.9pt),
      table.header(
        [Horizon], [Unconditional frequency], [Persistence (real-time state)], [MS-AR(1) filtered probability], [Logit: dividend yield], [Logit: 6 main predictors], [Gradient boosting, rich set], [Best p vs persistence],
      ),
      table.hline(stroke: 0.5pt),
      [1 month], [0.196], [0.161 (17.6%)], [0.178 (9.1%)], [0.160 (18.3%)], [0.146 (25.4%)], [0.143 (26.8%)], [0.033],
      [3 months], [0.196], [0.177 (10.0%)], [0.191 (2.7%)], [0.170 (13.4%)], [0.172 (12.4%)], [0.171 (13.0%)], [0.131],
      [6 months], [0.197], [0.189 (3.9%)], [0.199 (−1.4%)], [0.180 (8.2%)], [0.193 (1.7%)], [0.221 (−12.3%)], [0.245],
      [12 months], [0.197], [0.197 (−0.2%)], [0.200 (−1.8%)], [0.194 (1.4%)], [0.203 (−3.2%)], [0.260 (−32.1%)], [0.350],
      table.hline(stroke: 0.9pt),
    )
    #block(width: 100%, above: 0.5em)[#set text(size: 7.5pt); #set par(justify: true); #align(left)[_Notes:_ Lower is better. Real-time expanding-window forecasts. The last column is the smallest one-sided Diebold-Mariano p-value (23 Bartlett lags) against persistence among the 25 non-baseline models of the main design, not adjusted for multiple comparisons.]]
  ],
) <tab:summary>
