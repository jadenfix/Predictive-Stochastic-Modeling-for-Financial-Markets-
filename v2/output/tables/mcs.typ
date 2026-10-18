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
      [Unconditional frequency], [0.002], [0.370#super[\*]], [0.981#super[\*]], [0.997#super[\*]],
      [Persistence (real-time state)], [0.788#super[\*]], [0.990#super[\*]], [0.992#super[\*]], [0.997#super[\*]],
      [MS-AR(1) filtered probability], [0.204#super[\*]], [0.684#super[\*]], [0.972#super[\*]], [0.993#super[\*]],
      [TVTP MS-AR(1)], [0.234#super[\*]], [0.750#super[\*]], [0.981#super[\*]], [0.947#super[\*]],
      [Logit: dividend yield], [0.806#super[\*]], [1.000#super[\*]], [1.000#super[\*]], [1.000#super[\*]],
      [Logit: 6 main predictors], [0.940#super[\*]], [1.000#super[\*]], [0.992#super[\*]], [0.997#super[\*]],
      [Probit: 6 main predictors], [0.940#super[\*]], [1.000#super[\*]], [0.992#super[\*]], [0.976#super[\*]],
      [Logit: 6 predictors + state], [0.940#super[\*]], [0.990#super[\*]], [0.981#super[\*]], [0.993#super[\*]],
      [Elastic-net logit], [0.788#super[\*]], [0.781#super[\*]], [0.992#super[\*]], [0.997#super[\*]],
      [Elastic-net logit, rich set], [0.546#super[\*]], [0.722#super[\*]], [0.981#super[\*]], [0.837#super[\*]],
      [Gradient boosting], [0.806#super[\*]], [0.750#super[\*]], [0.968#super[\*]], [0.638#super[\*]],
      [Gradient boosting, rich set], [0.959#super[\*]], [1.000#super[\*]], [0.464#super[\*]], [0.021],
      [Logit: all 11 predictors], [1.000#super[\*]], [1.000#super[\*]], [0.981#super[\*]], [0.646#super[\*]],
      [Equal-weight combination], [0.124#super[\*]], [0.781#super[\*]], [0.992#super[\*]], [0.997#super[\*]],
      [DMA: univariate logits], [0.940#super[\*]], [0.990#super[\*]], [0.992#super[\*]], [0.837#super[\*]],
      [DMA: all models], [0.908#super[\*]], [0.860#super[\*]], [0.981#super[\*]], [0.947#super[\*]],
      table.hline(stroke: 0.9pt),
    )
    #block(width: 100%, above: 0.5em)[#set text(size: 7.5pt); #set par(justify: true); #align(left)[_Notes:_ Hansen, Lunde and Nason (2011) T\_max procedure on squared forecast errors, circular block bootstrap with 24-month blocks and 2,000 draws. A star marks models in the 90% model confidence set (p \>= 0.10): the set of models that cannot be distinguished from the best at the 10% level.]]
  ],
) <tab:mcs>
