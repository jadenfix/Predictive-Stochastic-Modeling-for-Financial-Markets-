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
        [], [MS-AR(1)], [Mean and variance], [Variance only], [Mean only], [Three regimes], [MS-AR(1), 1960-1989], [MS-AR(1), 1990-2023],
      ),
      table.hline(stroke: 0.5pt),
      table.cell(colspan: 8, align: left)[_Mean monthly real return (%)_],
      [Bull (highest mean)], [0.84], [0.90], [0.60], [0.67], [3.45], [0.62], [1.05],
      [Middle (three regimes)], [], [], [], [], [0.66], [], [],
      [Bear (lowest mean)], [−1.81], [−1.89], [0.60], [−10.05], [−2.66], [−2.45], [−1.52],
      table.cell(colspan: 8, inset: (y: 1.5pt))[],
      table.cell(colspan: 8, align: left)[_Volatility (sd, %)_],
      [Bull (highest mean)], [2.45], [2.52], [2.56], [3.02], [2.75], [2.57], [2.29],
      [Middle (three regimes)], [], [], [], [], [2.37], [], [],
      [Bear (lowest mean)], [5.62], [5.56], [6.15], [3.02], [5.02], [5.63], [5.68],
      table.cell(colspan: 8, inset: (y: 1.5pt))[],
      table.cell(colspan: 8, align: left)[_Expected duration (months)_],
      [Bull (highest mean)], [17.9], [19.5], [22.7], [35.8], [3.3], [10.8], [19.3],
      [Middle (three regimes)], [], [], [], [], [18.4], [], [],
      [Bear (lowest mean)], [5.2], [5.7], [6.4], [1.4], [6.0], [2.4], [6.4],
      table.cell(colspan: 8, inset: (y: 1.5pt))[],
      table.cell(colspan: 8, align: left)[_Fit_],
      [AR(1) coefficient], [0.194], [], [], [], [], [0.242], [0.138],
      [Parameters], [7], [6], [5], [5], [12], [7], [7],
      [Log-likelihood], [−1,990.3], [−2,007.0], [−2,019.6], [−2,027.9], [−1,991.6], [−935.9], [−1,047.3],
      [AIC], [3,994.5], [4,026.1], [4,049.2], [4,065.9], [4,007.2], [1,885.8], [2,108.6],
      [BIC], [4,027.0], [4,053.9], [4,072.5], [4,089.1], [4,062.9], [1,912.9], [2,136.6],
      [Observations], [767], [768], [768], [768], [768], [359], [407],
      table.cell(colspan: 8, inset: (y: 1.5pt))[],
      table.cell(colspan: 8, align: left)[_Filtered bear probability against the dated bear state_],
      [AUC], [0.799], [0.826], [0.742], [0.769], [0.874], [0.732], [0.899],
      [Correlation], [0.42], [0.46], [0.35], [0.30], [0.55], [0.31], [0.58],
      table.hline(stroke: 0.9pt),
    )
    #block(width: 100%, above: 0.5em)[#set text(size: 7.5pt); #set par(justify: true); #align(left)[_Notes:_ Two-regime models unless stated; monthly real returns. The first five columns use 1960-2023; AIC and BIC are comparable only within that group. 'Mean and variance' is the switching mean-variance model without the AR term; 'Variance only' lets only the variance switch (its regimes share one mean and the bear regime is the high-variance one); 'Mean only' lets only the mean switch. In the three-regime model the bear regime is the one with the lowest mean. The last two columns re-estimate the main MS-AR(1) on each subsample. AUC and correlation compare the filtered bear-regime probability with the contemporaneous dated bear indicator (in sample, full-sample parameters).]]
  ],
) <tab:regime_specs>
