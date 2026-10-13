# Resolve original data relative to this runner, including Rscript's --file form.
full_args <- commandArgs()
file_arg <- grep('^--file=',full_args,value=TRUE)
if (length(file_arg)) {
  setwd(dirname(normalizePath(sub('^--file=','',file_arg[[1L]]))))
} else if ('-f' %in% full_args) {
  setwd(dirname(normalizePath(full_args[[match('-f',full_args)+1L]])))
}
source('temporal_inputs.R')
price <- c(10,20,30,40,50,60)
dates <- as.Date(c('2020-01-01','2020-02-01','2020-03-01','2020-04-01','2020-05-01','2020-06-01'))
for (lag in 1:4) {
  x <- past_inputs(price,dates,lag)
  stopifnot(all(x$past==price[seq_len(length(price)-lag)]),all(x$target==price[seq.int(lag+1,length(price))]))
  stopifnot(all(x$predictor_date<x$date),nrow(x)==length(price)-lag)
  # Changing a future target cannot change a prior aligned predictor.
  changed <- price;changed[length(price)] <- 99999
  y <- past_inputs(changed,dates,lag)
  stopifnot(identical(x$past,y$past))
}
failed <- tryCatch({past_inputs(price,rev(dates),1);FALSE},error=function(e) TRUE)
stopifnot(failed)
cat('Past-only alignment and future perturbation checks passed\n')
