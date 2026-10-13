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

# At h=2, a nominal 50% split would let an April training label cross the
# first March test origin. The overlapping row must be purged.
split <- chronological_split(aligned, 0.5)
stopifnot(
  split$split_index == 2L,
  nrow(split$train) == 1L,
  nrow(split$purged) == 1L,
  nrow(split$test) == 2L,
  split$train$predictor_date == dates[1],
  split$train$target_date == dates[3],
  split$purged$predictor_date == dates[2],
  split$purged$target_date == dates[4],
  split$test$predictor_date[1] == dates[3],
  max(split$train$target_date) <= min(split$test$predictor_date)
)

# Each horizon gets its own boundary. For fixed horizons, h-1 nominal training
# rows cross the first test origin and are purged.
long_dates <- seq.Date(as.Date("2020-01-01"), by = "month", length.out = 12)
long_predictors <- data.frame(signal = seq_along(long_dates))
long_target <- seq_along(long_dates) * 10
for (horizon in 1:4) {
  horizon_data <- forward_horizon_inputs(long_dates, long_predictors, long_target, horizon)
  split <- chronological_split(horizon_data, 0.5)
  stopifnot(
    nrow(horizon_data) == length(long_dates) - horizon,
    nrow(split$purged) == horizon - 1L,
    nrow(split$train) + nrow(split$purged) == split$split_index,
    nrow(split$test) == nrow(horizon_data) - split$split_index,
    max(split$train$target_date) <= min(split$test$predictor_date),
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
bad_target_order <- aligned
bad_target_order$target_date[c(2, 3)] <- bad_target_order$target_date[c(3, 2)]
must_fail(chronological_split(bad_target_order, 0.5))
must_fail(chronological_split(aligned[c("signal", "target")], 0.5))
short_horizon_four <- forward_horizon_inputs(dates, predictors, target, 4)
must_fail(chronological_split(short_horizon_four, 0.5))

cat("Forward alignment, purged chronological split, and true MSPE checks passed\n")
