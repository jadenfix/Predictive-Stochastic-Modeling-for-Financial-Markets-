# Resolve files relative to this script when invoked outside the repository.
full_args <- commandArgs()
file_arg <- grep("^--file=", full_args, value = TRUE)
if (length(file_arg)) {
  setwd(dirname(normalizePath(sub("^--file=", "", file_arg[[1L]]))))
} else if ("-f" %in% full_args) {
  setwd(dirname(normalizePath(full_args[[match("-f", full_args) + 1L]])))
}
source("forecast_evaluation.R")

dates <- as.Date(c(
  "2020-01-01", "2020-02-01", "2020-03-01",
  "2020-04-01", "2020-05-01", "2020-06-01"
))
predictors <- data.frame(signal = c(4, 7, 2, 8, 5, 9))
target <- c(10, 20, 30, 40, 50, 60)

# At h=2, x(t) must be paired with y(t+2), never y(t-2).
aligned <- forward_horizon_inputs(dates, predictors, target, 2)
stopifnot(
  nrow(aligned) == 4L,
  identical(aligned$predictor_date, dates[1:4]),
  identical(aligned$target_date, dates[3:6]),
  identical(aligned$signal, predictors$signal[1:4]),
  identical(aligned$target, target[3:6]),
  all(aligned$predictor_date < aligned$target_date)
)

# A later target change cannot alter predictor rows or earlier aligned targets.
changed_target <- target
changed_target[6] <- 99999
changed <- forward_horizon_inputs(dates, predictors, changed_target, 2)
stopifnot(
  identical(aligned[c("predictor_date", "target_date", "signal")],
            changed[c("predictor_date", "target_date", "signal")]),
  identical(aligned$target[1:3], changed$target[1:3]),
  changed$target[4] == 99999
)

# Each horizon receives its own split index based on its own aligned row count.
expected_rows <- length(dates) - 1:4
for (horizon in 1:4) {
  horizon_data <- forward_horizon_inputs(dates, predictors, target, horizon)
  split <- chronological_split(horizon_data, 0.5)
  expected_train <- max(1L, min(floor(expected_rows[horizon] * 0.5), expected_rows[horizon] - 1L))
  stopifnot(
    nrow(horizon_data) == expected_rows[horizon],
    nrow(split$train) == expected_train,
    nrow(split$test) == expected_rows[horizon] - expected_train,
    max(split$train$predictor_date) < min(split$test$predictor_date)
  )
}

# Hand-calculable cancellation case: squared mean error is zero, true MSPE is not.
actual <- c(0.5, 0.5)
prediction <- c(1, 0)
benchmark <- c(1.5, 1.5)
stopifnot(
  mean(prediction - actual)^2 == 0,
  mean_squared_prediction_error(prediction, actual) == 0.25,
  mean_squared_prediction_error(benchmark, actual) == 1,
  mspe_ratio(prediction, benchmark, actual) == 0.25
)

must_fail <- function(expression) {
  failed <- tryCatch({ force(expression); FALSE }, error = function(e) TRUE)
  stopifnot(failed)
}
must_fail(forward_horizon_inputs(rev(dates), predictors, target, 1))
must_fail(forward_horizon_inputs(dates, predictors, target, 0))
must_fail(forward_horizon_inputs(dates, predictors, target, length(dates)))
must_fail(forward_horizon_inputs(dates, predictors[-1, , drop = FALSE], target, 1))
must_fail(mean_squared_prediction_error(c(1, NA), c(1, 2)))
must_fail(mspe_ratio(c(1, 2), c(1, 2), c(1, 2)))
must_fail(chronological_split(aligned, 1))

cat("Forward alignment, chronological split, and true MSPE checks passed\n")
