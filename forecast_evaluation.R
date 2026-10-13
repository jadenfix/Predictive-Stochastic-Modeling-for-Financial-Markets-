# Checked primitives for forward-looking evaluation.
#
# This file intentionally stays separate from code.R, which is preserved as the
# archived thesis analysis. These helpers only establish temporal alignment and
# metric arithmetic; they do not establish forecast or trading performance.

validate_numeric_pair <- function(prediction, actual, prediction_name = "prediction") {
  if (!is.numeric(prediction) || !is.numeric(actual)) {
    stop(prediction_name, " and actual must be numeric")
  }
  if (!length(actual) || length(prediction) != length(actual)) {
    stop(prediction_name, " and actual must have the same non-zero length")
  }
  if (any(!is.finite(prediction)) || any(!is.finite(actual))) {
    stop(prediction_name, " and actual must be finite")
  }
}

mean_squared_prediction_error <- function(prediction, actual) {
  validate_numeric_pair(prediction, actual)
  mean((prediction - actual)^2)
}

mspe_ratio <- function(prediction, benchmark, actual) {
  validate_numeric_pair(prediction, actual)
  validate_numeric_pair(benchmark, actual, "benchmark")
  benchmark_mspe <- mean_squared_prediction_error(benchmark, actual)
  if (benchmark_mspe == 0) stop("Benchmark MSPE must be non-zero")
  mean_squared_prediction_error(prediction, actual) / benchmark_mspe
}

forward_horizon_inputs <- function(dates, predictors, target, horizon) {
  dates <- as.Date(dates)
  observations <- length(dates)
  if (!observations || anyNA(dates)) stop("Valid dates are required")
  if (is.unsorted(dates, strictly = TRUE)) {
    stop("Dates must be unique and strictly increasing")
  }
  if (length(horizon) != 1L || !is.numeric(horizon) || !is.finite(horizon) ||
      horizon != as.integer(horizon) || horizon < 1L || horizon >= observations) {
    stop("Horizon must be a positive integer shorter than the history")
  }
  if (length(target) != observations) stop("Target length must match dates")

  if (is.atomic(predictors) && is.null(dim(predictors))) {
    predictors <- data.frame(predictor = predictors)
  } else {
    predictors <- as.data.frame(predictors, stringsAsFactors = FALSE)
  }
  if (nrow(predictors) != observations || ncol(predictors) < 1L) {
    stop("Predictors must have one row per date and at least one column")
  }
  reserved <- c("predictor_date", "target_date", "target")
  if (any(!nzchar(names(predictors))) || anyDuplicated(names(predictors)) ||
      any(names(predictors) %in% reserved)) {
    stop("Predictor names must be unique, non-empty, and not reserved output names")
  }

  horizon <- as.integer(horizon)
  predictor_rows <- seq_len(observations - horizon)
  target_rows <- predictor_rows + horizon
  aligned <- data.frame(
    predictor_date = dates[predictor_rows],
    target_date = dates[target_rows],
    predictors[predictor_rows, , drop = FALSE],
    target = target[target_rows],
    check.names = FALSE
  )
  rownames(aligned) <- NULL
  stopifnot(all(aligned$predictor_date < aligned$target_date))
  aligned
}

chronological_split <- function(aligned, train_fraction = 0.8) {
  aligned <- as.data.frame(aligned)
  if (nrow(aligned) < 2L) stop("At least two aligned observations are required")
  if (length(train_fraction) != 1L || !is.numeric(train_fraction) ||
      !is.finite(train_fraction) || train_fraction <= 0 || train_fraction >= 1) {
    stop("train_fraction must be between zero and one")
  }
  if (all(c("predictor_date", "target_date") %in% names(aligned))) {
    predictor_dates <- as.Date(aligned$predictor_date)
    target_dates <- as.Date(aligned$target_date)
    if (anyNA(predictor_dates) || anyNA(target_dates) ||
        is.unsorted(predictor_dates, strictly = TRUE) ||
        any(predictor_dates >= target_dates)) {
      stop("Aligned rows must be chronological forward pairs")
    }
  }

  split_index <- floor(nrow(aligned) * train_fraction)
  split_index <- max(1L, min(split_index, nrow(aligned) - 1L))
  list(
    train = aligned[seq_len(split_index), , drop = FALSE],
    test = aligned[seq.int(split_index + 1L, nrow(aligned)), , drop = FALSE],
    split_index = split_index
  )
}
