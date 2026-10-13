# Produce small, hand-checkable artifacts for the checked evaluation helpers.
# These synthetic outputs demonstrate direction and arithmetic only.
full_args <- commandArgs()
file_arg <- grep("^--file=", full_args, value = TRUE)
if (length(file_arg)) {
  setwd(dirname(normalizePath(sub("^--file=", "", file_arg[[1L]]))))
} else if ("-f" %in% full_args) {
  setwd(dirname(normalizePath(full_args[[match("-f", full_args) + 1L]])))
}
source("forecast_evaluation.R")

outdir <- "evaluation-output"
dir.create(outdir, showWarnings = FALSE)

dates <- as.Date(c(
  "2020-01-01", "2020-02-01", "2020-03-01",
  "2020-04-01", "2020-05-01", "2020-06-01"
))
aligned <- forward_horizon_inputs(
  dates,
  data.frame(signal = c(4, 7, 2, 8, 5, 9)),
  target = c(10, 20, 30, 40, 50, 60),
  horizon = 2
)
write.csv(aligned, file.path(outdir, "forward-horizon-2.csv"), row.names = FALSE)

actual <- c(0.5, 0.5)
prediction <- c(1, 0)
benchmark <- c(1.5, 1.5)
metrics <- data.frame(
  quantity = c(
    "legacy squared mean error",
    "prediction MSPE",
    "benchmark MSPE",
    "MSPE ratio"
  ),
  value = c(
    mean(prediction - actual)^2,
    mean_squared_prediction_error(prediction, actual),
    mean_squared_prediction_error(benchmark, actual),
    mspe_ratio(prediction, benchmark, actual)
  )
)
write.csv(metrics, file.path(outdir, "metric-check.csv"), row.names = FALSE)
writeLines(c(
  "Scope: synthetic temporal-alignment and metric-arithmetic check only.",
  "No regime accuracy, forecasting skill, trading return, or optimizer convergence is claimed."
), file.path(outdir, "LIMITATIONS.txt"))

print(aligned)
print(metrics)
