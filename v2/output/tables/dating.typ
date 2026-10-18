#figure(
  caption: [Bear markets under alternative dating rules],
  kind: table,
  [
    #set text(size: 8.5pt, hyphenate: false)
    #set par(justify: false, first-line-indent: 0em)
    #table(
      columns: (2fr, 1fr, 1fr, 1fr, 1fr),
      align: (left, center, center, center, center),
      stroke: none,
      inset: (x: 3pt, y: 2.4pt),
      table.hline(stroke: 0.9pt),
      table.header(
        [Dating rule], [Bear markets, 1900-2023], [Since 1960], [Bear share since 1960 (%)], [Median decline (%)],
      ),
      table.hline(stroke: 0.5pt),
      [Real prices, 15%], [31], [12], [24.6], [30.0],
      [Real prices, 20% (main)], [21], [9], [22.7], [34.8],
      [Real prices, 25%], [17], [7], [24.6], [42.4],
      [Nominal prices, 20%], [19], [7], [14.1], [32.2],
      table.hline(stroke: 0.9pt),
    )
    #block(width: 100%, above: 0.5em)[#set text(size: 7.5pt); #set par(justify: true); #align(left)[_Notes:_ Symmetric thresholds: a bear market starts when the index falls the stated percentage below its peak and ends when it rises the same percentage above its trough. Nominal dating uses the S&P Composite monthly average price without deflating.]]
  ],
) <tab:dating>
