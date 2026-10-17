#figure(
  caption: [Dated bear markets in the real S&P 500, 1900-2023],
  kind: table,
  [
    #set text(size: 8.5pt)
    #table(
      columns: (auto, 1fr, 1fr, 1fr, 1fr, 1fr),
      align: (left, center, center, center, center, center),
      stroke: none,
      inset: (x: 3pt, y: 2.4pt),
      table.hline(stroke: 0.9pt),
      table.header(
        [Peak], [Trough], [Months], [Decline (%)], [Confirmed], [Months to confirm],
      ),
      table.hline(stroke: 0.5pt),
      [1901-06], [1903-10], [28], [−33.2], [1903-06], [24],
      [1906-09], [1907-11], [14], [−43.4], [1907-03], [6],
      [1911-06], [1914-12], [42], [−34.8], [1913-05], [23],
      [1915-11], [1920-12], [61], [−62.9], [1917-05], [18],
      [1929-09], [1929-11], [2], [−34.2], [1929-11], [2],
      [1930-04], [1932-06], [26], [−76.9], [1930-10], [6],
      [1932-09], [1933-02], [5], [−20.8], [1933-02], [5],
      [1933-07], [1935-03], [20], [−30.6], [1934-07], [12],
      [1937-02], [1938-04], [14], [−45.4], [1937-09], [7],
      [1938-11], [1942-04], [41], [−47.5], [1940-06], [19],
      [1946-04], [1949-06], [38], [−42.4], [1946-09], [5],
      [1956-07], [1957-12], [17], [−20.8], [1957-11], [16],
      [1961-12], [1962-06], [6], [−23.0], [1962-06], [6],
      [1968-12], [1970-07], [19], [−35.1], [1970-01], [13],
      [1973-01], [1974-12], [23], [−53.3], [1973-12], [11],
      [1976-09], [1980-04], [43], [−30.0], [1978-01], [16],
      [1980-11], [1982-08], [21], [−29.7], [1982-01], [14],
      [1987-08], [1987-12], [4], [−27.9], [1987-11], [3],
      [2000-08], [2003-02], [30], [−46.4], [2001-03], [7],
      [2007-10], [2009-03], [17], [−51.7], [2008-07], [9],
      [2021-11], [2022-10], [11], [−25.6], [2022-06], [7],
      table.hline(stroke: 0.9pt),
    )
    #block(width: 100%, above: 0.5em)[#set text(size: 7.5pt); #set par(justify: true); #align(left)[_Notes:_ A bear market runs from a peak to the following trough when the real index falls at least 20% below the peak before rising 20% above the trough. 'Confirmed' is the first month in which the 20% decline had occurred, that is, when the bear market became knowable in real time.]]
  ],
) <tab:episodes>
