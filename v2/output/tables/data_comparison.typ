#figure(
  caption: [The archived extract one45.csv against the 6 October 2026 Shiller workbook],
  kind: table,
  [
    #set text(size: 8.5pt, hyphenate: false)
    #set par(justify: false, first-line-indent: 0em)
    #table(
      columns: (2.2fr, 1.5fr, 0.7fr, 0.9fr, 1fr, 1.3fr),
      align: (left, center, center, center, center, center),
      stroke: none,
      inset: (x: 3pt, y: 2.4pt),
      table.hline(stroke: 0.9pt),
      table.header(
        [Series], [Overlap], [Months], [Months that differ], [Largest difference (%)], [Months affected],
      ),
      table.hline(stroke: 0.5pt),
      [S&P Composite price], [1900:01-2024:03], [1,491], [1], [0.65], [2024:03-2024:03],
      [Dividends], [1900:01-2023:12], [1,488], [0], [], [],
      [Earnings], [1900:01-2023:12], [1,488], [3], [0.22], [2023:10-2023:12],
      [CPI], [1900:01-2024:03], [1,491], [2], [0.85], [2024:02-2024:03],
      [Long-term interest rate], [1900:01-2024:03], [1,491], [1], [0.95], [2024:03-2024:03],
      [CAPE], [1900:01-2024:03], [1,491], [2], [0.67], [2024:02-2024:03],
      [Total-return CAPE], [1900:01-2024:03], [1,491], [3], [0.47], [2024:01-2024:03],
      [Real price (rescaled)], [1900:01-2024:03], [1,491], [2], [0.35], [2024:02-2024:03],
      [Real TR-scaled earnings (rescaled)], [1900:01-2023:12], [1,488], [3], [0.22], [2023:10-2023:12],
      table.hline(stroke: 0.9pt),
    )
    #block(width: 100%, above: 0.5em)[#set text(size: 7.5pt); #set par(justify: true); #align(left)[_Notes:_ A month differs if the archived value differs from the current value rounded to two decimals by more than 0.01 (levels), or by more than 0.05% after rescaling (real series, which Shiller expresses in dollars of the latest month). 'Largest difference' is the largest absolute percentage difference among the months that differ. All differences fall in the last months of the archived file, which held estimates at the time (see output/results/one45\_differences.csv).]]
  ],
) <tab:data_comparison>
