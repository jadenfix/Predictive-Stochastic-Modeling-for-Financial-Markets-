#figure(
  caption: [Archived results, their replication, and the corrected estimates],
  kind: table,
  [
    #set text(size: 8.5pt, hyphenate: false)
    #set par(justify: false, first-line-indent: 0em)
    #table(
      columns: (2.6fr, 1fr, 1fr, 1fr),
      align: (left, center, center, center),
      stroke: none,
      inset: (x: 3pt, y: 2.4pt),
      table.hline(stroke: 0.9pt),
      table.header(
        [], [Archived (reported)], [Replicated], [Corrected],
      ),
      table.hline(stroke: 0.5pt),
      [P(bull to bull)], [0.945], [0.950], [0.944],
      [P(bear to bear)], [0.833], [0.833], [0.808],
      [Dividend, k = 1: coefficient], [−0.195], [−0.198], [−3.80\*\*\* (1.33) pp],
      [Dividend, k = 6: coefficient], [−0.325], [−0.320], [−3.40\*\* (1.39) pp],
      [Dividend, k = 6: R²], [0.075], [0.074], [0.017],
      [Total return, k = 1: R²], [0.108], [0.107], [0.121],
      [TR-scaled earnings, k = 1: R²], [0.085], [0.085], [0.001],
      [Dividend, k = 1: OLS forecast ratio], [0.004], [0.029], [0.953],
      [Total return, k = 1: OLS forecast ratio], [0.014], [0.006], [0.868],
      [TR-scaled earnings, k = 1: OLS forecast ratio], [0.390], [0.363], [0.999],
      table.hline(stroke: 0.9pt),
    )
    #block(width: 100%, above: 0.5em)[#set text(size: 7.5pt); #set par(justify: true); #align(left)[_Notes:_ Archived values are transcribed from the award PDF (v2/data/archived\_reported.csv). 'Replicated' re-runs the archived code path in Python, including the future-price regressor, the backward target Q(t-k) and the archived MSPE formula. 'Corrected' uses the MS-AR(1) model on returns, past-only predictors, the forward target Q(t+k) and expanding-window forecasts. Coefficients in the corrected column are per one-standard-deviation change of a different (growth-rate) transformation and are therefore comparable in sign and significance only.]]
  ],
) <tab:replication>
