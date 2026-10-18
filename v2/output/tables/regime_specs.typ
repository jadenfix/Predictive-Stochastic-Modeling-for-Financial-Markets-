#figure(
  caption: [Robustness of the regime model: specification and sample],
  kind: table,
  [
    #set text(size: 7.5pt, hyphenate: false)
    #set par(justify: false, first-line-indent: 0em)
    #table(
      columns: (1.9fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr),
      align: (left, center, center, center, center, center, center, center),
      stroke: none,
      inset: (x: 3pt, y: 2.4pt),
      table.hline(stroke: 0.9pt),
      table.header(
        [], [MS-AR(1)], [Mean and variance], [Variance only], [Mean only], [Three regimes], [MS-AR(1), 1960-1989], [MS-AR(1), 1990-2026],
      ),
      table.hline(stroke: 0.5pt),
      table.cell(colspan: 8, align: left)[_Mean monthly real return (%)_],
      [Bull (highest mean)], [0.88], [0.95], [0.65], [0.71], [3.58], [0.62], [1.10],
      [Middle (three regimes)], [], [], [], [], [0.72], [], [],
      [Bear (lowest mean)], [−1.75], [−1.84], [0.65], [−9.81], [−2.63], [−2.45], [−1.48],
      table.cell(colspan: 8, inset: (y: 1.5pt))[],
      table.cell(colspan: 8, align: left)[_Volatility (sd, %)_],
      [Bull (highest mean)], [2.41], [2.49], [2.54], [3.01], [2.71], [2.57], [2.24],
      [Middle (three regimes)], [], [], [], [], [2.33], [], [],
      [Bear (lowest mean)], [5.57], [5.51], [6.12], [3.01], [4.91], [5.63], [5.63],
      table.cell(colspan: 8, inset: (y: 1.5pt))[],
      table.cell(colspan: 8, align: left)[_Expected duration (months)_],
      [Bull (highest mean)], [16.6], [18.1], [21.4], [35.2], [3.1], [10.8], [17.7],
      [Middle (three regimes)], [], [], [], [], [17.1], [], [],
      [Bear (lowest mean)], [5.0], [5.5], [6.1], [1.4], [5.8], [2.4], [5.9],
      table.cell(colspan: 8, inset: (y: 1.5pt))[],
      table.cell(colspan: 8, align: left)[_Fit_],
      [AR(1) coefficient], [0.196], [], [], [], [], [0.242], [0.143],
      [Parameters], [7], [6], [5], [5], [12], [7], [7],
      [Log-likelihood], [−2,063.5], [−2,081.2], [−2,094.8], [−2,104.1], [−2,064.1], [−935.9], [−1,119.9],
      [AIC], [4,141.0], [4,174.3], [4,199.6], [4,218.1], [4,152.2], [1,885.8], [2,253.8],
      [BIC], [4,173.7], [4,202.4], [4,223.0], [4,241.5], [4,208.4], [1,913.0], [2,282.4],
      [Observations], [797], [798], [798], [798], [798], [359], [437],
      table.cell(colspan: 8, inset: (y: 1.5pt))[],
      table.cell(colspan: 8, align: left)[_Filtered bear probability against the dated bear state_],
      [AUC], [0.802], [0.830], [0.747], [0.771], [0.879], [0.732], [0.900],
      [Correlation], [0.42], [0.46], [0.35], [0.30], [0.56], [0.31], [0.56],
      table.hline(stroke: 0.9pt),
    )
    #block(width: 100%, above: 0.5em)[#set text(size: 7.5pt); #set par(justify: true); #align(left)[_Notes:_ Two-regime models unless stated; monthly real returns. The first five columns use January 1960 to June 2026; AIC and BIC are comparable only within that group. 'Mean and variance' is the switching mean-variance model without the AR term; 'Variance only' lets only the variance switch (the bear regime is the high-variance one); 'Mean only' lets only the mean switch. In the three-regime model the bear regime has the lowest mean. The last two columns re-estimate the main MS-AR(1) on each subsample. AUC and correlation compare the filtered bear-regime probability with the contemporaneous dated bear indicator (in sample).]]
  ],
) <tab:regime_specs>
