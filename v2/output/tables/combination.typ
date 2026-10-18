#figure(
  caption: [Forecast combinations: out-of-sample Brier skill (%)],
  kind: table,
  [
    #set text(size: 8pt, hyphenate: false)
    #set par(justify: false, first-line-indent: 0em)
    #table(
      columns: (2.8fr, 1fr, 1fr, 1fr, 1fr),
      align: (left, center, center, center, center),
      stroke: none,
      inset: (x: 3pt, y: 2.4pt),
      table.hline(stroke: 0.9pt),
      table.header(
        [], [h = 1], [h = 3], [h = 6], [h = 12],
      ),
      table.hline(stroke: 0.5pt),
      [Equal-weight combination], [13.0#super[\*\*\*]], [7.2#super[\*\*\*]], [2.7#super[\*\*\*]], [−0.7],
      [DMA, univariate logits, alpha = 0.95], [24.0#super[\*\*\*]], [10.5#super[\*\*\*]], [0.6], [−4.8],
      [DMA, all models, alpha = 0.95], [27.3#super[\*\*\*]], [13.2#super[\*\*\*]], [3.1], [−2.2],
      [DMA, univariate logits, alpha = 0.99], [23.3#super[\*\*\*]], [10.6#super[\*\*\*]], [2.3], [−4.5],
      [DMA, all models, alpha = 0.99], [23.4#super[\*\*\*]], [9.4#super[\*\*]], [−0.9], [−4.5],
      [DMA, univariate logits, alpha = 1], [22.1#super[\*\*\*]], [7.8#super[\*\*]], [−0.9], [−6.3],
      [DMA, all models, alpha = 1], [22.6#super[\*\*\*]], [6.8#super[\*]], [−0.4], [−5.5],
      table.hline(stroke: 0.9pt),
    )
    #block(width: 100%, above: 0.5em)[#set text(size: 7.5pt); #set par(justify: true); #align(left)[_Notes:_ The equal-weight combination averages the univariate logits. Dynamic model averaging (Raftery, Kárný and Ettler, 2010) weights forecasts by their exponentially discounted predictive likelihood, using only outcomes known at the origin; alpha is the forgetting factor (alpha = 1 is recursive Bayesian model averaging). Stars: one-sided Diebold-Mariano test against the unconditional frequency, \* p \< 0.10, \*\* p \< 0.05, \*\*\* p \< 0.01.]]
  ],
) <tab:combination>
