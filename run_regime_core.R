# Resolve original data relative to this runner, including Rscript's --file form.
full_args <- commandArgs()
file_arg <- grep('^--file=',full_args,value=TRUE)
if (length(file_arg)) {
  setwd(dirname(normalizePath(sub('^--file=','',file_arg[[1L]]))))
} else if ('-f' %in% full_args) {
  setwd(dirname(normalizePath(full_args[[match('-f',full_args)+1L]])))
}
# Execute the original archived MS regression core, keeping data and formulas.
# Plotly presentation and later exploratory sections are outside this lane.
args <- commandArgs(trailingOnly=TRUE)
past_only <- '--past-only' %in% args
maxiter <- as.integer(Sys.getenv('RESEARCH_MAX_ITER','100'))
if (is.na(maxiter) || maxiter<1L) stop('RESEARCH_MAX_ITER must be positive')
fit_control <- list(parallelization=FALSE,maxiter=maxiter)
source_file <- "code.R"
library(xts)
library(MSwM)
source('temporal_inputs.R')
outdir <- if (past_only) 'research-output-past-only' else 'research-output'
dir.create(outdir,showWarnings=FALSE)
set.seed(666)
lines <- readLines(source_file, warn=FALSE)
end <- grep("^AIC\\(ms_model1",lines)[1]
if (is.na(end)) stop('Original model boundary not found')
expressions <- parse(text=paste(lines[seq_len(end-1L)],collapse='\n'))
executed <- 0L
for (expression in expressions) {
  rendered <- paste(deparse(expression), collapse=' ')
  if (past_only && grepl('^msmod1 <-',rendered)) break
  if (grepl('plot_ly\\(',rendered) || grepl('library\\((ggplot2|plotly|msm|stargazer|tseries)\\)',rendered)) next
  # Only worker scheduling changes: the existing MSwM objective and defaults
  # are retained, with serial initialization to avoid spawning all host cores.
  modify_call <- function(x) {
    if (!is.call(x)) return(x)
    if (identical(x[[1L]],as.name('msmFit'))) x[['control']] <- fit_control
    for (i in seq_along(x)[-1L]) x[[i]] <- modify_call(x[[i]])
    x
  }
  if (grepl('msmFit',rendered)) cat(paste('Fitting original:',rendered,'\n'))
  eval(modify_call(expression),envir=.GlobalEnv)
  executed <- executed+1L
}
if (past_only) {
  price <- as.numeric(xts$realprice)
  dates <- as.Date(index(xts))
  if (is.unsorted(dates) || anyDuplicated(dates)) stop('Expected unique chronological dates')
  for (lag in 1:4) {
    aligned <- past_inputs(price,dates,lag)
    write.csv(aligned,file.path(outdir,paste0('past-lag',lag,'-inputs.csv')),row.names=FALSE)
    cat(paste('Fitting corrected past lag',lag,'\n'))
    fit <- msmFit(lm(target ~ past,data=aligned),k=2,sw=rep(TRUE,3),control=fit_control)
    assign(paste0('past_model',lag),fit)
  }
}
outdir <- if (past_only) 'research-output-past-only' else 'research-output'
dir.create(outdir,showWarnings=FALSE)
models <- c("ms_model1","ms_model2","ms_model3","ms_model4")
if (past_only) models <- paste0('past_model',1:4)
scores <- data.frame(model=models, AIC=vapply(models,function(n) AIC(get(n)),numeric(1)), observations=vapply(models,function(n) nobs(get(n)@model),integer(1)))
write.csv(scores,file.path(outdir,'model-scores.csv'),row.names=FALSE)
for (name in models) {
  fit <- get(name)
  if (any(!is.finite(fit@Fit@filtProb)) || max(abs(rowSums(fit@Fit@filtProb)-1))>1e-6) stop('Filtered probabilities must be finite and normalized')
  if (any(!is.finite(fit@transMat))) stop('Non-finite transition matrix')
  if (max(abs(colSums(fit@transMat)-1))>1e-6) stop('Transition columns must sum to one')
  write.csv(fit@transMat,file.path(outdir,paste0(name,'-transitions.csv')),row.names=FALSE)
  png(file.path(outdir,paste0(name,'-probabilities.png')),width=1400,height=900,res=140)
  plotProb(fit,which=1)
  dev.off()
  model_path <- file.path(outdir,paste0(name,'.rds'))
  saveRDS(fit,model_path)
  reloaded <- readRDS(model_path)
  stopifnot(identical(reloaded@Coef,fit@Coef),identical(reloaded@transMat,fit@transMat))
}
writeLines(c(paste('Original source:',source_file),paste('Executed original expressions:',executed),paste('Rows:',nrow(xts)),paste('Max EM iterations:',maxiter), if(past_only) 'Scope: separate past-only re-estimation; not reproduction of archived coefficients or validated forecasting performance.' else 'Scope: retrospective archived model reproduction; future-price predictors do not establish forecasting validity.',paste('R:',getRversion()),paste('MSwM:',packageVersion('MSwM'))),file.path(outdir,'execution.txt'))
print(scores)
