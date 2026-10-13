# Build lagged design rows using past observations only; no archived lead columns.
past_inputs <- function(price,dates,lag) {
  dates <- as.Date(dates)
  if (length(price)!=length(dates) || anyNA(dates) || any(!is.finite(price))) stop('Finite prices and valid dates required')
  if (is.unsorted(dates,strictly=TRUE)) stop('Unique increasing dates required')
  if (length(lag)!=1L || lag<1L || lag!=as.integer(lag) || lag>=length(price)) stop('Lag must be a positive integer shorter than the history')
  rows <- seq.int(lag+1L,length(price))
  aligned <- data.frame(date=dates[rows],predictor_date=dates[rows-lag],target=price[rows],past=price[rows-lag])
  stopifnot(all(aligned$predictor_date < aligned$date))
  aligned
}
