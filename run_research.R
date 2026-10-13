args <- commandArgs(trailingOnly=TRUE)
script <- if(length(args)) args[[1]] else "code.R"
allowed <- c("code.R")
if (!(script %in% allowed)) stop("Select an original research script in this repository")
inputs <- c("one45.csv")
if(any(!file.exists(inputs))) stop("Missing original data: ", paste(inputs[!file.exists(inputs)], collapse=", "))
source(script)
