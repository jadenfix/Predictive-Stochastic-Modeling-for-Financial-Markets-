#figure(
  caption: [Model confidence set p-values for out-of-sample Brier loss],
  kind: table,
  [
    #set text(size: 8pt, hyphenate: false)
    #set par(justify: false, first-line-indent: 0em)
    #table(
      columns: (2.6fr, 1fr, 1fr, 1fr, 1fr),
      align: (left, center, center, center, center),
      stroke: none,
      inset: (x: 3pt, y: 2.4pt),
      table.hline(stroke: 0.9pt),
      table.header(
        [], [h = 1], [h = 3], [h = 6], [h = 12],
      ),
      table.hline(stroke: 0.5pt),
      [Unconditional frequency], [0.001], [0.343#super[\*]], [0.960#super[\*]], [0.990#super[\*]],
      [Persistence (real-time state)], [0.833#super[\*]], [0.987#super[\*]], [0.972#super[\*]], [0.990#super[\*]],
      [MS-AR(1) filtered probability], [0.225#super[\*]], [0.670#super[\*]], [0.956#super[\*]], [0.989#super[\*]],
      [TVTP MS-AR(1)], [0.270#super[\*]], [0.729#super[\*]], [0.960#super[\*]], [0.925#super[\*]],
      [Logit: dividend yield], [0.852#super[\*]], [1.000#super[\*]], [1.000#super[\*]], [1.000#super[\*]],
      [Logit: 6 main predictors], [0.940#super[\*]], [1.000#super[\*]], [0.972#super[\*]], [0.990#super[\*]],
      [Probit: 6 main predictors], [0.940#super[\*]], [1.000#super[\*]], [0.972#super[\*]], [0.969#super[\*]],
      [Logit: 6 predictors + state], [0.940#super[\*]], [0.987#super[\*]], [0.960#super[\*]], [0.989#super[\*]],
      [Elastic-net logit], [0.833#super[\*]], [0.770#super[\*]], [0.972#super[\*]], [0.990#super[\*]],
      [Elastic-net logit, rich set], [0.607#super[\*]], [0.688#super[\*]], [0.960#super[\*]], [0.822#super[\*]],
      [Gradient boosting], [0.852#super[\*]], [0.729#super[\*]], [0.952#super[\*]], [0.623#super[\*]],
      [Gradient boosting, rich set], [0.959#super[\*]], [1.000#super[\*]], [0.430#super[\*]], [0.019],
      [Logit: all 11 predictors], [1.000#super[\*]], [1.000#super[\*]], [0.960#super[\*]], [0.632#super[\*]],
      [Equal-weight combination], [0.147#super[\*]], [0.770#super[\*]], [0.972#super[\*]], [0.990#super[\*]],
      [DMA: univariate logits], [0.940#super[\*]], [0.987#super[\*]], [0.972#super[\*]], [0.822#super[\*]],
      [DMA: all models], [0.908#super[\*]], [0.843#super[\*]], [0.960#super[\*]], [0.925#super[\*]],
      table.hline(stroke: 0.9pt),
    )
    #block(width: 100%, above: 0.5em)[#set text(size: 7.5pt); #set par(justify: true); #align(left)[_Notes:_ Hansen, Lunde and Nason (2011) T\_max procedure on squared forecast errors, circular block bootstrap with 24-month blocks and 2,000 draws. A star marks models in the 90% model confidence set (p \>= 0.10): the set of models that cannot be distinguished from the best at the 10% level.]]
  ],
) <tab:mcs>
