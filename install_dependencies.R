packages <- c("AER","MSwM","Metrics","betareg","caret","dplyr","ggplot2","lmtest","msm","plotly","randomForest","sandwich","stargazer","tseries","xts")
missing <- setdiff(packages, rownames(installed.packages()))
if (length(missing)) install.packages(missing, repos="https://cloud.r-project.org")
