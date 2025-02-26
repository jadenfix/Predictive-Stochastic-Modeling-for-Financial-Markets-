library(ggplot2)
library(msm)
library(MSwM)
library(stargazer)
data <- read.csv("one45.csv")
head(data)
data$date <- as.Date(data$date, format = "%m/%d/%Y")
df <- data
ncol<-ncol(df)

#
df <- df[-(1:719), ]
head(df)
df <- df[-(770:1492), ]
tail(df)

#df <- df[-(1:492), ]
#df <- df[-(1077:1492), ]


any(is.na(df))
df$spprice <- as.numeric(df$spprice)
df$infl <- as.numeric(df$infl)
df$lrir10 <- as.numeric(df$lrir10)
df$realtotalreturn <- as.numeric(df$realtotalreturn)
df$realtrscaledearnings <- as.numeric(df$realtrscaledearnings)
df$excessCAPE <- as.numeric(df$excessCAPE)
df <- subset(df, select = -c(spprice, dividend, earnings, bond, dp, dy))
#install.packages("xts")
#time series
library(xts)
xts <- xts(df[,-1], order.by = df$date)
ts <- as.ts(xts)
#for stock returns we use: returns=100*pricechange (pricechange=lnrealprice)

xts$realprice <- 100*log(xts$realprice)
xts$realpricelag <- 100*log(xts$realpricelag)
xts$realpricelag2 <- 100*log(xts$realpricelag2)
xts$realpricelag3 <- 100*log(xts$realpricelag3)
xts$realpricelag4 <- 100*log(xts$realpricelag4)
#plots
library(plotly)


#statistical testing: ADF and Phillips Perron 
library(tseries)
#variables <- c("infl", "lrir10", "realprice", "realdividend", "realtrscaledearnings", "TRCAPE", "realbond", "realtotalreturn")
#1st differences
xts$infl <- diff(xts$infl, differences = 1)
xts$lrir10 <- diff(xts$lrir10, differences = 1)
xts$realdividend <- diff(xts$realdividend, differences = 1)
xts$realtrscaledearnings <- diff(xts$realtrscaledearnings, differences = 1)
xts$TRCAPE <- diff(xts$TRCAPE, differences = 1)
xts$realbond <- diff(xts$realbond, differences = 1)
xts$realtotalreturn <-diff(xts$realtotalreturn, differences = 1)
#get rid of 1st NA
xts <- xts[-(1), ]
xtsdataframe <- as.data.frame(xts)

# Plotting
#SPPprice
plot_ly(data = df, x = ~date, y = ~realprice, type = 'scatter', mode = 'lines') %>%
  layout(title = "Log Real S&P 500 Price * 100",
         xaxis = list(title = "Date"),
         yaxis = list(title = "Real USD"))
#Real Dividend 
plot_ly(data = df, x = ~date, y = ~realdividend, type = 'scatter', mode = 'lines') %>%
  layout(title = "Real Dividend",
         xaxis = list(title = "Date"),
         yaxis = list(title = "Real USD"))
#Real TR Scaled Earnings 
plot_ly(data = df, x = ~date, y = ~realtrscaledearnings, type = 'scatter', mode = 'lines') %>%
  layout(title = "Real Total Revenue Scaled Earnings",
         xaxis = list(title = "Date"),
         yaxis = list(title = "Real USD"))
#TR Cape Ratio 
plot_ly(data = df, x = ~date, y = ~TRCAPE, type = 'scatter', mode = 'lines') %>%
  layout(title = "Total Revenue Scaled Cyclically Adjusted Price Earnings Ratio",
         xaxis = list(title = "Date"),
         yaxis = list(title = "Ratio"))
#Real Bond Return
plot_ly(data = df, x = ~date, y = ~realbond, type = 'scatter', mode = 'lines') %>%
  layout(title = "Real Bond Price",
         xaxis = list(title = "Date"),
         yaxis = list(title = "Real USD"))
#inflation 
plot_ly(data = df, x = ~date, y = ~infl, type = 'scatter', mode = 'lines') %>%
  layout(title = "Inflation",
         xaxis = list(title = "Date"),
         yaxis = list(title = "CPI"))
#Long Term Interest Rate 
plot_ly(data = df, x = ~date, y = ~lrir10, type = 'scatter', mode = 'lines') %>%
  layout(title = "Long Range Interest Rates (10 YR)",
         xaxis = list(title = "Date"),
         yaxis = list(title = "Percentage"))
plot_ly(data = df, x = ~date, y = ~realtotalreturn, type = 'scatter', mode = 'lines') %>%
  layout(title = "Real Total Return",
         xaxis = list(title = "Date"),
         yaxis = list(title = "Real USD"))

###########################Data Visualization Stops Here ########### MSM Econometrics Begin 

#MSM################################################################################
library(msm)
library(dplyr)

#Markov model Testing
#Markov model Testing
realpricets <- ts(xts$realprice, start = c(1960, 01), end= c(2023, 12), frequency = 12)
realpricetslag <- ts(xts$realpricelag, start = c(1960, 01), end= c(2023, 12), frequency = 12)
realpricetslag2 <- ts(xts$realpricelag2, start = c(1960, 01), end= c(2023, 12), frequency = 12)
realpricetslag3 <- ts(xts$realpricelag3, start = c(1960, 01), end= c(2023, 12), frequency = 12)
realpricetslag4 <- ts(xts$realpricelag4, start = c(1960, 01), end= c(2023, 12), frequency = 12)



msmod1 <- lm(realpricets ~ realpricetslag)
msmod2 <- lm(realpricets ~ realpricetslag2)
msmod3 <- lm(realpricets ~ realpricetslag3)
msmod4 <- lm(realpricets ~ realpricetslag4)
set.seed(666)
#markov model
ms_model1 <- msmFit(msmod1, k = 2, sw=rep(TRUE,3))
ms_model2 <- msmFit(msmod2, k = 2, sw=rep(TRUE,3))
ms_model3 <- msmFit(msmod3, k = 2, sw=rep(TRUE,3))
ms_model4 <- msmFit(msmod4, k = 2, sw=rep(TRUE,3))

AIC(ms_model1)
AIC(ms_model2)
AIC(ms_model3)
AIC(ms_model4)

ms_model2 <- ms_model1
#transition probabilities 
transition_matrix <- msmProbs(ms_model2)
#ms_model2
par(mar=c(3,3,3,3))
#probs for both 
plotProb(ms_model2, which=1)
#regime 1: recession periods
plotProb(ms_model2, which=2)
#regime 2: expansion periods
plotProb(ms_model2, which=3)
#regime 1 residuals
plotDiag(ms_model2, regime=1, which=1)
#regime 1 QQ plot
plotDiag(ms_model2, regime=1, which=2)
#Regime 1 ACF PACF graphs
plotDiag(ms_model2, regime=1, which=3)
#regime 2 residuals
plotDiag(ms_model2, regime=2, which=1)
#regime 2 QQ plot
plotDiag(ms_model2, regime=2, which=2)
#Regime 2 ACF PACF graphs
plotDiag(ms_model2, regime=2, which=3)

#smooth and filtered probs 
#MS2
#smoothprobms2 <- ms_model2@Fit@smoProb
filterprobms2 <- ms_model2@Fit@filtProb
#convert into dataframes 
#2 regimes
filterprobms2_df <- as.data.frame(filterprobms2)
#smoothprobms2_df <- as.data.frame(smoothprobms2)

#column renaming 2 regime
colnames(filterprobms2_df) <- c("filterprobms2_regime1", "filterprobms2_regime2")
#colnames(smoothprobms2_df) <- c("smoothprobms2_regime1", "smoothprobms2_regime2")

combined_df <- cbind(xtsdataframe, filterprobms2_df)
################################################################################################
################################################################################################
################################################################################################

################################################################################################
################################################################################################
################################################################################################
library(sandwich)
library(Metrics)
library(randomForest)
library(caret)
library(dplyr)
library(lmtest)
library(AER)
set.seed(666)

#1 2 3 6 12 18 24 months ahead 
combined_df$ahead1 <- lag(combined_df$filterprobms2_regime1, 1)
combined_dfahead1 <- combined_df[-(1), ]

combined_df$ahead2 <- lag(combined_df$filterprobms2_regime1, 2)
combined_dfahead2 <- combined_df[-(1:2), ]

combined_df$ahead3 <- lag(combined_df$filterprobms2_regime1, 3)
combined_dfahead3 <- combined_df[-(1:3), ]

combined_df$ahead6 <- lag(combined_df$filterprobms2_regime1, 6)
combined_dfahead6 <- combined_df[-(1:6), ]

combined_df$ahead12 <- lag(combined_df$filterprobms2_regime1, 12)
combined_dfahead12 <- combined_df[-(1:12), ]

combined_df$ahead18 <- lag(combined_df$filterprobms2_regime1, 18)
combined_dfahead18 <- combined_df[-(1:18), ]

combined_df$ahead24 <- lag(combined_df$filterprobms2_regime1, 24)
combined_dfahead24 <- combined_df[-(1:24), ]
#ADF
adfinfl <- adf.test(combined_df$infl)
adfinfl <- adf.test(combined_df$lrir10)
adfinfl <- adf.test(combined_df$realdividend)
adfinfl <- adf.test(combined_df$realtrscaledearnings)
adfinfl <- adf.test(combined_df$TRCAPE)
adfinfl <- adf.test(combined_df$realbond)
adfinfl <- adf.test(combined_df$filterprobms2_regime1)
ppinfl <- pp.test(combined_df$infl)
ppinfl <- pp.test(combined_df$lrir10)
ppinfl <- pp.test(combined_df$realdividend)
ppinfl <- pp.test(combined_df$realtrscaledearnings)
ppinfl <- pp.test(combined_df$TRCAPE)
ppinfl <- pp.test(combined_df$realbond)
ppinfl <- pp.test(combined_df$filterprobms2_regime1)



ts.plot(combined_df$infl)
ts.plot(combined_df$lrir10)
ts.plot(combined_df$realdividend)
ts.plot(combined_df$realtrscaledearnings)
ts.plot(combined_df$TRCAPE)
ts.plot(combined_df$realbond)
ts.plot(combined_df$filterprobms2_regime1)
#IN sample testing
#################################################################################
#################################################################################
#################################################################################
#infl # 
ahead1k2recessionolsinfl <- lm(ahead1~infl, data=combined_dfahead1)
ahead2k2recessionolsinfl <- lm(ahead2~infl, data=combined_dfahead2)
ahead3k2recessionolsinfl <- lm(ahead3~infl, data=combined_dfahead3)
ahead6k2recessionolsinfl <- lm(ahead6~infl, data=combined_dfahead6)
ahead12k2recessionolsinfl <- lm(ahead12~infl, data=combined_dfahead12)
ahead18k2recessionolsinfl <- lm(ahead18~infl, data=combined_dfahead18)
ahead24k2recessionolsinfl <- lm(ahead24~infl, data=combined_dfahead24)
#################################################################################
#################################################################################
#lrir10
ahead1k2recessionolslrir10 <- lm(ahead1~lrir10, data=combined_dfahead1)
ahead2k2recessionolslrir10 <- lm(ahead2~lrir10, data=combined_dfahead2)
ahead3k2recessionolslrir10 <- lm(ahead3~lrir10, data=combined_dfahead3)
ahead6k2recessionolslrir10 <- lm(ahead6~lrir10, data=combined_dfahead6)
ahead12k2recessionolslrir10 <- lm(ahead12~lrir10, data=combined_dfahead12)
ahead18k2recessionolslrir10 <- lm(ahead18~lrir10, data=combined_dfahead18)
ahead24k2recessionolslrir10 <- lm(ahead24~lrir10, data=combined_dfahead24)
#################################################################################
#################################################################################
#realdividend
ahead1k2recessionolsrealdividend <- lm(ahead1~realdividend, data=combined_dfahead1)
ahead2k2recessionolsrealdividend <- lm(ahead2~realdividend, data=combined_dfahead2)
ahead3k2recessionolsrealdividend <- lm(ahead3~realdividend, data=combined_dfahead3)
ahead6k2recessionolsrealdividend <- lm(ahead6~realdividend, data=combined_dfahead6)
ahead12k2recessionolsrealdividend <- lm(ahead12~realdividend, data=combined_dfahead12)
ahead18k2recessionolsrealdividend <- lm(ahead18~realdividend, data=combined_dfahead18)
ahead24k2recessionolsrealdividend <- lm(ahead24~realdividend, data=combined_dfahead24)
#################################################################################
#realtrscaledearnings
ahead1k2recessionolsrealtrscaledearnings <- lm(ahead1~realtrscaledearnings, data=combined_dfahead1)
ahead2k2recessionolsrealtrscaledearnings <- lm(ahead2~realtrscaledearnings, data=combined_dfahead2)
ahead3k2recessionolsrealtrscaledearnings <- lm(ahead3~realtrscaledearnings, data=combined_dfahead3)
ahead6k2recessionolsrealtrscaledearnings <- lm(ahead6~realtrscaledearnings, data=combined_dfahead6)
ahead12k2recessionolsrealtrscaledearnings <- lm(ahead12~realtrscaledearnings, data=combined_dfahead12)
ahead18k2recessionolsrealtrscaledearnings <- lm(ahead18~realtrscaledearnings, data=combined_dfahead18)
ahead24k2recessionolsrealtrscaledearnings <- lm(ahead24~realtrscaledearnings, data=combined_dfahead24)
#################################################################################
#TRCAPE
ahead1k2recessionolsTRCAPE <- lm(ahead1~TRCAPE, data=combined_dfahead1)
ahead2k2recessionolsTRCAPE <- lm(ahead2~TRCAPE, data=combined_dfahead2)
ahead3k2recessionolsTRCAPE <- lm(ahead3~TRCAPE, data=combined_dfahead3)
ahead6k2recessionolsTRCAPE <- lm(ahead6~TRCAPE, data=combined_dfahead6)
ahead12k2recessionolsTRCAPE <- lm(ahead12~TRCAPE, data=combined_dfahead12)
ahead18k2recessionolsTRCAPE <- lm(ahead18~TRCAPE, data=combined_dfahead18)
ahead24k2recessionolsTRCAPE <- lm(ahead24~TRCAPE, data=combined_dfahead24)
#################################################################################
#################################################################################
#realbond
ahead1k2recessionolsrealbond <- lm(ahead1~realbond, data=combined_dfahead1)
ahead2k2recessionolsrealbond <- lm(ahead2~realbond, data=combined_dfahead2)
ahead3k2recessionolsrealbond <- lm(ahead3~realbond, data=combined_dfahead3)
ahead6k2recessionolsrealbond <- lm(ahead6~realbond, data=combined_dfahead6)
ahead12k2recessionolsrealbond <- lm(ahead12~realbond, data=combined_dfahead12)
ahead18k2recessionolsrealbond <- lm(ahead18~realbond, data=combined_dfahead18)
ahead24k2recessionolsrealbond <- lm(ahead24~realbond, data=combined_dfahead24)


#################################################################################
#################################################################################
#################################################################################
#realtotalreturn
ahead1k2recessionolsrealtotalreturn <- lm(ahead1~realtotalreturn, data=combined_dfahead1)
ahead2k2recessionolsrealtotalreturn <- lm(ahead2~realtotalreturn, data=combined_dfahead2)
ahead3k2recessionolsrealtotalreturn <- lm(ahead3~realtotalreturn, data=combined_dfahead3)
ahead6k2recessionolsrealtotalreturn <- lm(ahead6~realtotalreturn, data=combined_dfahead6)
ahead12k2recessionolsrealtotalreturn <- lm(ahead12~realtotalreturn, data=combined_dfahead12)
ahead18k2recessionolsrealtotalreturn <- lm(ahead18~realtotalreturn, data=combined_dfahead18)
ahead24k2recessionolsrealtotalreturn <- lm(ahead24~realtotalreturn, data=combined_dfahead24)

#####################################################################################
#################################################################################
#################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
#################################################################################
library(betareg)
#beta regression
#variance 
# Provide starting values for coefficients and phi parameter
start_values <- c(coefficients = c(0, 0), phi = 1)

# Fit beta regression model with specified starting values
ahead1k2recessionbetareginfl <- betareg(ahead1 ~ infl, data = combined_dfahead1, start = start_values)

# Check the model summary
summary(ahead1k2recessionbetareginfl)


#infl # 
ahead1k2recessionbetareginfl <- betareg(ahead1 ~ infl, data = combined_dfahead1, start = start_values)
ahead2k2recessionbetareginfl <- betareg(ahead2~infl, data=combined_dfahead2, start = start_values)
ahead3k2recessionbetareginfl <- betareg(ahead3~infl, data=combined_dfahead3, start = start_values)
ahead6k2recessionbetareginfl <- betareg(ahead6~infl, data=combined_dfahead6, start = start_values)
ahead12k2recessionbetareginfl <- betareg(ahead12~infl, data=combined_dfahead12, start = start_values)
ahead18k2recessionbetareginfl <- betareg(ahead18~infl, data=combined_dfahead18, start = start_values)
ahead24k2recessionbetareginfl <- betareg(ahead24~infl, data=combined_dfahead24, start = start_values)
#################################################################################
#################################################################################
#lrir10
ahead1k2recessionbetareglrir10 <- betareg(ahead1~lrir10, data=combined_dfahead1, start = start_values)
ahead2k2recessionbetareglrir10 <- betareg(ahead2~lrir10, data=combined_dfahead2, start = start_values)
ahead3k2recessionbetareglrir10 <- betareg(ahead3~lrir10, data=combined_dfahead3, start = start_values)
ahead6k2recessionbetareglrir10 <- betareg(ahead6~lrir10, data=combined_dfahead6, start = start_values)
ahead12k2recessionbetareglrir10 <- betareg(ahead12~lrir10, data=combined_dfahead12, start = start_values)
ahead18k2recessionbetareglrir10 <- betareg(ahead18~lrir10, data=combined_dfahead18, start = start_values)
ahead24k2recessionbetareglrir10 <- betareg(ahead24~lrir10, data=combined_dfahead24, start = start_values)
#################################################################################
#################################################################################
#realdividend
ahead1k2recessionbetaregrealdividend <- betareg(ahead1~realdividend, data=combined_dfahead1, start = start_values)
ahead2k2recessionbetaregrealdividend <- betareg(ahead2~realdividend, data=combined_dfahead2, start = start_values)
ahead3k2recessionbetaregrealdividend <- betareg(ahead3~realdividend, data=combined_dfahead3, start = start_values)
ahead6k2recessionbetaregrealdividend <- betareg(ahead6~realdividend, data=combined_dfahead6, start = start_values)
ahead12k2recessionbetaregrealdividend <- betareg(ahead12~realdividend, data=combined_dfahead12, start = start_values)
ahead18k2recessionbetaregrealdividend <- betareg(ahead18~realdividend, data=combined_dfahead18, start = start_values)
ahead24k2recessionbetaregrealdividend <- betareg(ahead24~realdividend, data=combined_dfahead24, start = start_values)
#################################################################################
#realtrscaledearnings
ahead1k2recessionbetaregrealtrscaledearnings <- betareg(ahead1~realtrscaledearnings, data=combined_dfahead1, start = start_values)
ahead2k2recessionbetaregrealtrscaledearnings <- betareg(ahead2~realtrscaledearnings, data=combined_dfahead2, start = start_values)
ahead3k2recessionbetaregrealtrscaledearnings <- betareg(ahead3~realtrscaledearnings, data=combined_dfahead3, start = start_values)
ahead6k2recessionbetaregrealtrscaledearnings <- betareg(ahead6~realtrscaledearnings, data=combined_dfahead6, start = start_values)
ahead12k2recessionbetaregrealtrscaledearnings <- betareg(ahead12~realtrscaledearnings, data=combined_dfahead12, start = start_values)
ahead18k2recessionbetaregrealtrscaledearnings <- betareg(ahead18~realtrscaledearnings, data=combined_dfahead18, start = start_values)
ahead24k2recessionbetaregrealtrscaledearnings <- betareg(ahead24~realtrscaledearnings, data=combined_dfahead24, start = start_values)
#################################################################################
#TRCAPE
ahead1k2recessionbetaregTRCAPE <- betareg(ahead1~TRCAPE, data=combined_dfahead1, start = start_values)
ahead2k2recessionbetaregTRCAPE <- betareg(ahead2~TRCAPE, data=combined_dfahead2, start = start_values)
ahead3k2recessionbetaregTRCAPE <- betareg(ahead3~TRCAPE, data=combined_dfahead3, start = start_values)
ahead6k2recessionbetaregTRCAPE <- betareg(ahead6~TRCAPE, data=combined_dfahead6, start = start_values)
ahead12k2recessionbetaregTRCAPE <- betareg(ahead12~TRCAPE, data=combined_dfahead12, start = start_values)
ahead18k2recessionbetaregTRCAPE <- betareg(ahead18~TRCAPE, data=combined_dfahead18, start = start_values)
ahead24k2recessionbetaregTRCAPE <- betareg(ahead24~TRCAPE, data=combined_dfahead24, start = start_values)
#################################################################################
#################################################################################
#realbond
ahead1k2recessionbetaregrealbond <- betareg(ahead1~realbond, data=combined_dfahead1, start = start_values)
ahead2k2recessionbetaregrealbond <- betareg(ahead2~realbond, data=combined_dfahead2, start = start_values)
ahead3k2recessionbetaregrealbond <- betareg(ahead3~realbond, data=combined_dfahead3, start = start_values)
ahead6k2recessionbetaregrealbond <- betareg(ahead6~realbond, data=combined_dfahead6, start = start_values)
ahead12k2recessionbetaregrealbond <- betareg(ahead12~realbond, data=combined_dfahead12, start = start_values)
ahead18k2recessionbetaregrealbond <- betareg(ahead18~realbond, data=combined_dfahead18, start = start_values)
ahead24k2recessionbetaregrealbond <- betareg(ahead24~realbond, data=combined_dfahead24, start = start_values)


#################################################################################
#################################################################################
#################################################################################
#realtotalreturn
ahead1k2recessionbetaregrealtotalreturn <- betareg(ahead1~realtotalreturn, data=combined_dfahead1, start = start_values)
ahead2k2recessionbetaregrealtotalreturn <- betareg(ahead2~realtotalreturn, data=combined_dfahead2, start = start_values)
ahead3k2recessionbetaregrealtotalreturn <- betareg(ahead3~realtotalreturn, data=combined_dfahead3, start = start_values)
ahead6k2recessionbetaregrealtotalreturn <- betareg(ahead6~realtotalreturn, data=combined_dfahead6, start = start_values)
ahead12k2recessionbetaregrealtotalreturn <- betareg(ahead12~realtotalreturn, data=combined_dfahead12, start = start_values)
ahead18k2recessionbetaregrealtotalreturn <- betareg(ahead18~realtotalreturn, data=combined_dfahead18, start = start_values)
ahead24k2recessionbetaregrealtotalreturn <- betareg(ahead24~realtotalreturn, data=combined_dfahead24, start = start_values)

##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
#stargazer tables 
resultsinfl <- list(ahead1k2recessionolsinfl,
                    ahead2k2recessionolsinfl,
                    ahead3k2recessionolsinfl,
                    ahead6k2recessionolsinfl,
                    ahead12k2recessionolsinfl,
                    ahead18k2recessionolsinfl,
                    ahead24k2recessionolsinfl)
stargazer(resultsinfl, type="text", out="resultsCPIlols21.html", omit.stat = c("f", "ser"), omit="Constant")
resultsinflbeta <- list(ahead1k2recessionbetareginfl,
                        ahead2k2recessionbetareginfl,
                        ahead3k2recessionbetareginfl,
                        ahead6k2recessionbetareginfl,
                        ahead12k2recessionbetareginfl,
                        ahead18k2recessionbetareginfl,
                        ahead24k2recessionbetareginfl)
stargazer(resultsinflbeta, type="text", out="resultsCPIbeta21.html", omit.stat = c("f", "ser","LL"), omit="Constant")
##
resultslrir10 <- list(ahead1k2recessionolslrir10,
                      ahead2k2recessionolslrir10,
                      ahead3k2recessionolslrir10,
                      ahead6k2recessionolslrir10,
                      ahead12k2recessionolslrir10,
                      ahead18k2recessionolslrir10,
                      ahead24k2recessionolslrir10)
resultslrir10beta <- list(ahead1k2recessionbetareglrir10,
                      ahead2k2recessionbetareglrir10,
                      ahead3k2recessionbetareglrir10,
                      ahead6k2recessionbetareglrir10,
                      ahead12k2recessionbetareglrir10,
                      ahead18k2recessionbetareglrir10,
                      ahead24k2recessionbetareglrir10)
stargazer(resultslrir10, type="text",out="resultsLRIR10ols21.html", omit.stat = c("f", "ser"), omit="Constant")

stargazer(resultslrir10beta, type="text",out="resultsLRIR10beta21.html", omit.stat = c("f", "ser","LL"), omit="Constant")
##
resultsrealdividend <- list(ahead1k2recessionolsrealdividend,
                            ahead2k2recessionolsrealdividend,
                            ahead3k2recessionolsrealdividend,
                            ahead6k2recessionolsrealdividend,
                            ahead12k2recessionolsrealdividend,
                            ahead18k2recessionolsrealdividend,
                            ahead24k2recessionolsrealdividend)
resultsrealdividendbeta <- list(ahead1k2recessionbetaregrealdividend,
                                ahead2k2recessionbetaregrealdividend,
                                ahead3k2recessionbetaregrealdividend,
                                ahead6k2recessionbetaregrealdividend,
                                ahead12k2recessionbetaregrealdividend,
                                ahead18k2recessionbetaregrealdividend,
                                ahead24k2recessionbetaregrealdividend)
stargazer(resultsrealdividend, type="text",out="Resultsrealdividend1021.html", omit.stat = c("f", "ser"), omit="Constant")

stargazer(resultsrealdividendbeta, type="text",out="Resultsrealdividend10beta211.html", omit.stat = c("f", "ser","LL"), omit="Constant")
##
resultsrealtrscaledearnings <- list(ahead1k2recessionolsrealtrscaledearnings,
                                    ahead2k2recessionolsrealtrscaledearnings,
                                    ahead3k2recessionolsrealtrscaledearnings,
                                    ahead6k2recessionolsrealtrscaledearnings,
                                    ahead12k2recessionolsrealtrscaledearnings,
                                    ahead18k2recessionolsrealtrscaledearnings,
                                    ahead24k2recessionolsrealtrscaledearnings)
resultsrealtrscaledearningsbeta <- list(ahead1k2recessionbetaregrealtrscaledearnings,
                                    ahead2k2recessionbetaregrealtrscaledearnings,
                                    ahead3k2recessionbetaregrealtrscaledearnings,
                                    ahead6k2recessionbetaregrealtrscaledearnings,
                                    ahead12k2recessionbetaregrealtrscaledearnings,
                                    ahead18k2recessionbetaregrealtrscaledearnings,
                                    ahead24k2recessionbetaregrealtrscaledearnings)

stargazer(resultsrealtrscaledearnings,type="text", out="Resultsrealtrscaledearnings21.html", omit.stat = c("f", "ser"), omit="Constant")
stargazer(resultsrealtrscaledearningsbeta,type="text", out="Resultsrealtrscaledearningsbeta21.html", omit.stat = c("f", "ser","LL"), omit="Constant")
##
resultsTRCAPE <- list(ahead1k2recessionolsTRCAPE,
                      ahead2k2recessionolsTRCAPE,
                      ahead3k2recessionolsTRCAPE,
                      ahead6k2recessionolsTRCAPE,
                      ahead12k2recessionolsTRCAPE,
                      ahead18k2recessionolsTRCAPE,
                      ahead24k2recessionolsTRCAPE)
resultsTRCAPEbeta <- list(ahead1k2recessionbetaregTRCAPE,
                      ahead2k2recessionbetaregTRCAPE,
                      ahead3k2recessionbetaregTRCAPE,
                      ahead6k2recessionbetaregTRCAPE,
                      ahead12k2recessionbetaregTRCAPE,
                      ahead18k2recessionbetaregTRCAPE,
                      ahead24k2recessionbetaregTRCAPE)

stargazer(resultsTRCAPE, out="TRCAPE21.html",type="text", omit.stat = c("f", "ser"), omit="Constant")
stargazer(resultsTRCAPEbeta,out="TRCAPEbeta2121.html",type="text", omit.stat = c("f", "ser","LL"), omit="Constant")
##
resultsrealbond <- list(ahead1k2recessionolsrealbond,
                        ahead2k2recessionolsrealbond,
                        ahead3k2recessionolsrealbond,
                        ahead6k2recessionolsrealbond,
                        ahead12k2recessionolsrealbond,
                        ahead18k2recessionolsrealbond,
                        ahead24k2recessionolsrealbond)
resultsrealbondbeta <- list(ahead1k2recessionbetaregrealbond,
                        ahead2k2recessionbetaregrealbond,
                        ahead3k2recessionbetaregrealbond,
                        ahead6k2recessionbetaregrealbond,
                        ahead12k2recessionbetaregrealbond,
                        ahead18k2recessionbetaregrealbond,
                        ahead24k2recessionbetaregrealbond)

stargazer(resultsrealbond, out="resultsrealbond21.html",type="text", omit.stat = c("f", "ser"), omit="Constant")
stargazer(resultsrealbondbeta, out="resultsrealbondbeta21.html",type="text", omit.stat = c("f", "ser","LL"), omit="Constant")

##
resultsrealtotalreturn <- list(ahead1k2recessionolsrealtotalreturn,
                               ahead2k2recessionolsrealtotalreturn,
                               ahead3k2recessionolsrealtotalreturn,
                               ahead6k2recessionolsrealtotalreturn,
                               ahead12k2recessionolsrealtotalreturn,
                               ahead18k2recessionolsrealtotalreturn,
                               ahead24k2recessionolsrealtotalreturn)
resultsrealtotalreturnbeta <- list(ahead1k2recessionbetaregrealtotalreturn,
                               ahead2k2recessionbetaregrealtotalreturn,
                               ahead3k2recessionbetaregrealtotalreturn,
                               ahead6k2recessionbetaregrealtotalreturn,
                               ahead12k2recessionbetaregrealtotalreturn,
                               ahead18k2recessionbetaregrealtotalreturn,
                               ahead24k2recessionbetaregrealtotalreturn)
stargazer(resultsrealtotalreturn, out="resultsrealtotalreturn21.html",type="text", omit.stat = c("f", "ser"), omit="Constant")
stargazer(resultsrealtotalreturnbeta, out="resultsrealtotalreturnbeta21.html",type="text", omit.stat = c("f", "ser","LL"), omit="Constant")





##########################################################################################################################################################################
##########################################################################################################################################################################
##########################################################################################################################################################################
##########################################################################################################################################################################
#Forecasting the last 20% (most recent)
# Sort the data by index
combined_dfahead1 <- combined_dfahead1[order(row.names(combined_dfahead1)), ]
combined_dfahead2 <- combined_dfahead2[order(row.names(combined_dfahead2)), ]
combined_dfahead3 <- combined_dfahead3[order(row.names(combined_dfahead3)), ]
combined_dfahead6 <- combined_dfahead6[order(row.names(combined_dfahead6)), ]
combined_dfahead12 <- combined_dfahead12[order(row.names(combined_dfahead12)), ]
combined_dfahead18 <- combined_dfahead18[order(row.names(combined_dfahead18)), ]
combined_dfahead24 <- combined_dfahead24[order(row.names(combined_dfahead24)), ]

# Calculate the index for the first 80%
n <- nrow(combined_dfahead1)
index_80_percent <- round(0.8 * n)

# Select the first 80% of data
ahead1train1 <- combined_dfahead1[1:index_80_percent, ]
ahead2train2 <- combined_dfahead2[1:index_80_percent, ]
ahead3train3 <- combined_dfahead3[1:index_80_percent, ]
ahead6train6 <- combined_dfahead6[1:index_80_percent, ]
ahead12train12 <- combined_dfahead12[1:index_80_percent, ]
ahead18train18 <- combined_dfahead18[1:index_80_percent, ]
ahead24train24 <- combined_dfahead24[1:index_80_percent, ]

ahead1test1 <- combined_dfahead1[-(1:index_80_percent), ]
ahead2test2 <- combined_dfahead2[-(1:index_80_percent), ]
ahead3test3 <- combined_dfahead3[-(1:index_80_percent), ]
ahead6test6 <- combined_dfahead6[-(1:index_80_percent), ]
ahead12test12 <- combined_dfahead12[-(1:index_80_percent), ]
ahead18test18 <- combined_dfahead18[-(1:index_80_percent), ]
ahead24test24 <- combined_dfahead24[-(1:index_80_percent), ]

#out of sample 
intercept1<- lm(ahead1 ~ 1, data=ahead1train1)
intercept2<- lm(ahead2 ~ 1, data=ahead2train2)
intercept3<- lm(ahead3 ~ 1, data=ahead3train3)
intercept6<- lm(ahead6 ~ 1, data=ahead6train6)
intercept12<- lm(ahead12 ~ 1, data=ahead12train12)
intercept18<- lm(ahead18 ~ 1, data=ahead18train18)
intercept24<- lm(ahead24 ~ 1, data=ahead24train24)

infl1<- lm(ahead1 ~ infl, data=ahead1train1)
infl2<- lm(ahead2 ~ infl, data=ahead2train2)
infl3<- lm(ahead3 ~ infl, data=ahead3train3)
infl6<- lm(ahead6 ~ infl, data=ahead6train6)
infl12<- lm(ahead12 ~ infl, data=ahead12train12)
infl18<- lm(ahead18 ~ infl, data=ahead18train18)
infl24<- lm(ahead24 ~ infl, data=ahead24train24)

lrir101<- lm(ahead1 ~ lrir10, data=ahead1train1)
lrir102<- lm(ahead2 ~ lrir10, data=ahead2train2)
lrir103<- lm(ahead3 ~ lrir10, data=ahead3train3)
lrir106<- lm(ahead6 ~ lrir10, data=ahead6train6)
lrir1012<- lm(ahead12 ~ lrir10, data=ahead12train12)
lrir1018<- lm(ahead18 ~ lrir10, data=ahead18train18)
lrir1024<- lm(ahead24 ~ lrir10, data=ahead24train24)

realdividend1<- lm(ahead1 ~ realdividend, data=ahead1train1)
realdividend2<- lm(ahead2 ~ realdividend, data=ahead2train2)
realdividend3<- lm(ahead3 ~ realdividend, data=ahead3train3)
realdividend6<- lm(ahead6 ~ realdividend, data=ahead6train6)
realdividend12<- lm(ahead12 ~ realdividend, data=ahead12train12)
realdividend18<- lm(ahead18 ~ realdividend, data=ahead18train18)
realdividend24<- lm(ahead24 ~ realdividend, data=ahead24train24)

realbond1<- lm(ahead1 ~ realbond, data=ahead1train1)
realbond2<- lm(ahead2 ~ realbond, data=ahead2train2)
realbond3<- lm(ahead3 ~ realbond, data=ahead3train3)
realbond6<- lm(ahead6 ~ realbond, data=ahead6train6)
realbond12<- lm(ahead12 ~ realbond, data=ahead12train12)
realbond18<- lm(ahead18 ~ realbond, data=ahead18train18)
realbond24<- lm(ahead24 ~ realbond, data=ahead24train24)

realtotalreturn1<- lm(ahead1 ~ realtotalreturn, data=ahead1train1)
realtotalreturn2<- lm(ahead2 ~ realtotalreturn, data=ahead2train2)
realtotalreturn3<- lm(ahead3 ~ realtotalreturn, data=ahead3train3)
realtotalreturn6<- lm(ahead6 ~ realtotalreturn, data=ahead6train6)
realtotalreturn12<- lm(ahead12 ~ realtotalreturn, data=ahead12train12)
realtotalreturn18<- lm(ahead18 ~ realtotalreturn, data=ahead18train18)
realtotalreturn24<- lm(ahead24 ~ realtotalreturn, data=ahead24train24)

realtrscaledearnings1<- lm(ahead1 ~ realtrscaledearnings, data=ahead1train1)
realtrscaledearnings2<- lm(ahead2 ~ realtrscaledearnings, data=ahead2train2)
realtrscaledearnings3<- lm(ahead3 ~ realtrscaledearnings, data=ahead3train3)
realtrscaledearnings6<- lm(ahead6 ~ realtrscaledearnings, data=ahead6train6)
realtrscaledearnings12<- lm(ahead12 ~ realtrscaledearnings, data=ahead12train12)
realtrscaledearnings18<- lm(ahead18 ~ realtrscaledearnings, data=ahead18train18)
realtrscaledearnings24<- lm(ahead24 ~ realtrscaledearnings, data=ahead24train24)

TRCAPE1<- lm(ahead1 ~ TRCAPE, data=ahead1train1)
TRCAPE2<- lm(ahead2 ~ TRCAPE, data=ahead2train2)
TRCAPE3<- lm(ahead3 ~ TRCAPE, data=ahead3train3)
TRCAPE6<- lm(ahead6 ~ TRCAPE, data=ahead6train6)
TRCAPE12<- lm(ahead12 ~ TRCAPE, data=ahead12train12)
TRCAPE18<- lm(ahead18 ~ TRCAPE, data=ahead18train18)
TRCAPE24<- lm(ahead24 ~ TRCAPE, data=ahead24train24)
#predictions
restricted1 <- predict(intercept1, newdata=ahead1test1)
restricted2 <- predict(intercept2, newdata=ahead2test2)
restricted3 <- predict(intercept3, newdata=ahead3test3)
restricted6 <- predict(intercept6, newdata=ahead6test6)
restricted12 <- predict(intercept12, newdata=ahead12test12)
restricted18 <- predict(intercept18, newdata=ahead18test18)
restricted24 <- predict(intercept24, newdata=ahead24test24)
#predictions
unrestrictedinfl1 <- predict(infl1, newdata=ahead1test1)
unrestrictedinfl2 <- predict(infl2, newdata=ahead2test2)
unrestrictedinfl3 <- predict(infl3, newdata=ahead3test3)
unrestrictedinfl6 <- predict(infl6, newdata=ahead6test6)
unrestrictedinfl12 <- predict(infl12, newdata=ahead12test12)
unrestrictedinfl18 <- predict(infl18, newdata=ahead18test18)
unrestrictedinfl24 <- predict(infl24, newdata=ahead24test24)
#realdividend
unrestrictedrealdividend1 <- predict(realdividend1, newdata=ahead1test1)
unrestrictedrealdividend2 <- predict(realdividend2, newdata=ahead2test2)
unrestrictedrealdividend3 <- predict(realdividend3, newdata=ahead3test3)
unrestrictedrealdividend6 <- predict(realdividend6, newdata=ahead6test6)
unrestrictedrealdividend12 <- predict(realdividend12, newdata=ahead12test12)
unrestrictedrealdividend18 <- predict(realdividend18, newdata=ahead18test18)
unrestrictedrealdividend24 <- predict(realdividend24, newdata=ahead24test24)
#lrir10
unrestrictedlrir101 <- predict(lrir101, newdata=ahead1test1)
unrestrictedlrir102 <- predict(lrir102, newdata=ahead2test2)
unrestrictedlrir103 <- predict(lrir103, newdata=ahead3test3)
unrestrictedlrir106 <- predict(lrir106, newdata=ahead6test6)
unrestrictedlrir1012 <- predict(lrir1012, newdata=ahead12test12)
unrestrictedlrir1018 <- predict(lrir1018, newdata=ahead18test18)
unrestrictedlrir1024 <- predict(lrir1024, newdata=ahead24test24)
#realdividend
unrestrictedrealdividend1 <- predict(realdividend1, newdata=ahead1test1)
unrestrictedrealdividend2 <- predict(realdividend2, newdata=ahead2test2)
unrestrictedrealdividend3 <- predict(realdividend3, newdata=ahead3test3)
unrestrictedrealdividend6 <- predict(realdividend6, newdata=ahead6test6)
unrestrictedrealdividend12 <- predict(realdividend12, newdata=ahead12test12)
unrestrictedrealdividend18 <- predict(realdividend18, newdata=ahead18test18)
unrestrictedrealdividend24 <- predict(realdividend24, newdata=ahead24test24)
#realbond
unrestrictedrealbond1 <- predict(realbond1, newdata=ahead1test1)
unrestrictedrealbond2 <- predict(realbond2, newdata=ahead2test2)
unrestrictedrealbond3 <- predict(realbond3, newdata=ahead3test3)
unrestrictedrealbond6 <- predict(realbond6, newdata=ahead6test6)
unrestrictedrealbond12 <- predict(realbond12, newdata=ahead12test12)
unrestrictedrealbond18 <- predict(realbond18, newdata=ahead18test18)
unrestrictedrealbond24 <- predict(realbond24, newdata=ahead24test24)
#realtotalreturn
unrestrictedrealtotalreturn1 <- predict(realtotalreturn1, newdata=ahead1test1)
unrestrictedrealtotalreturn2 <- predict(realtotalreturn2, newdata=ahead2test2)
unrestrictedrealtotalreturn3 <- predict(realtotalreturn3, newdata=ahead3test3)
unrestrictedrealtotalreturn6 <- predict(realtotalreturn6, newdata=ahead6test6)
unrestrictedrealtotalreturn12 <- predict(realtotalreturn12, newdata=ahead12test12)
unrestrictedrealtotalreturn18 <- predict(realtotalreturn18, newdata=ahead18test18)
unrestrictedrealtotalreturn24 <- predict(realtotalreturn24, newdata=ahead24test24)
#realtrscaledearnings
unrestrictedrealtrscaledearnings1 <- predict(realtrscaledearnings1, newdata=ahead1test1)
unrestrictedrealtrscaledearnings2 <- predict(realtrscaledearnings2, newdata=ahead2test2)
unrestrictedrealtrscaledearnings3 <- predict(realtrscaledearnings3, newdata=ahead3test3)
unrestrictedrealtrscaledearnings6 <- predict(realtrscaledearnings6, newdata=ahead6test6)
unrestrictedrealtrscaledearnings12 <- predict(realtrscaledearnings12, newdata=ahead12test12)
unrestrictedrealtrscaledearnings18 <- predict(realtrscaledearnings18, newdata=ahead18test18)
unrestrictedrealtrscaledearnings24 <- predict(realtrscaledearnings24, newdata=ahead24test24)
#TRCAPE
unrestrictedTRCAPE1 <- predict(TRCAPE1, newdata=ahead1test1)
unrestrictedTRCAPE2 <- predict(TRCAPE2, newdata=ahead2test2)
unrestrictedTRCAPE3 <- predict(TRCAPE3, newdata=ahead3test3)
unrestrictedTRCAPE6 <- predict(TRCAPE6, newdata=ahead6test6)
unrestrictedTRCAPE12 <- predict(TRCAPE12, newdata=ahead12test12)
unrestrictedTRCAPE18 <- predict(TRCAPE18, newdata=ahead18test18)
unrestrictedTRCAPE24 <- predict(TRCAPE24, newdata=ahead24test24)
#RObustness MSPE 

#MSPE Ratio
#infl
as.numeric(MSPEinfl1ratio <- (((mean(unrestrictedinfl1 - ahead1test1$ahead1))^2) / ((mean(restricted1-ahead1test1$ahead1))^2)))
as.numeric(MSPEinfl2ratio <- (((mean(unrestrictedinfl2 - ahead2test2$ahead2))^2) / ((mean(restricted2-ahead2test2$ahead2))^2)))
as.numeric(MSPEinfl3ratio <- (((mean(unrestrictedinfl3 - ahead3test3$ahead3))^2) / ((mean(restricted3-ahead3test3$ahead3))^2)))
as.numeric(MSPEinfl6ratio <- (((mean(unrestrictedinfl6 - ahead6test6$ahead6))^2) / ((mean(restricted6-ahead6test6$ahead6))^2)))
as.numeric(MSPEinfl12ratio <- (((mean(unrestrictedinfl12 - ahead12test12$ahead12))^2) / ((mean(restricted12-ahead12test12$ahead12))^2)))
as.numeric(MSPEinfl18ratio <- (((mean(unrestrictedinfl18 - ahead18test18$ahead18))^2) / ((mean(restricted18-ahead18test18$ahead18))^2)))
as.numeric(MSPEinfl24ratio <- (((mean(unrestrictedinfl24 - ahead24test24$ahead24))^2) / ((mean(restricted24-ahead24test24$ahead24))^2)))

inflMSPE <- c(MSPEinfl1ratio,MSPEinfl2ratio,MSPEinfl3ratio,MSPEinfl6ratio,
              MSPEinfl12ratio,MSPEinfl18ratio,MSPEinfl24ratio)

#realdividend
as.numeric(MSPErealdividend1ratio <- (((mean(unrestrictedrealdividend1 - ahead1test1$ahead1))^2) / ((mean(restricted1-ahead1test1$ahead1))^2)))
as.numeric(MSPErealdividend2ratio <- (((mean(unrestrictedrealdividend2 - ahead2test2$ahead2))^2) / ((mean(restricted2-ahead2test2$ahead2))^2)))
as.numeric(MSPErealdividend3ratio <- (((mean(unrestrictedrealdividend3 - ahead3test3$ahead3))^2) / ((mean(restricted3-ahead3test3$ahead3))^2)))
as.numeric(MSPErealdividend6ratio <- (((mean(unrestrictedrealdividend6 - ahead6test6$ahead6))^2) / ((mean(restricted6-ahead6test6$ahead6))^2)))
as.numeric(MSPErealdividend12ratio <- (((mean(unrestrictedrealdividend12 - ahead12test12$ahead12))^2) / ((mean(restricted12-ahead12test12$ahead12))^2)))
as.numeric(MSPErealdividend18ratio <- (((mean(unrestrictedrealdividend18 - ahead18test18$ahead18))^2) / ((mean(restricted18-ahead18test18$ahead18))^2)))
as.numeric(MSPErealdividend24ratio <- (((mean(unrestrictedrealdividend24 - ahead24test24$ahead24))^2) / ((mean(restricted24-ahead24test24$ahead24))^2)))

realdividendMSPE <- c(MSPErealdividend1ratio,MSPErealdividend2ratio,MSPErealdividend3ratio,MSPErealdividend6ratio,
                      MSPErealdividend12ratio,MSPErealdividend18ratio,MSPErealdividend24ratio)

as.numeric(MSPElrir101ratio <- (((mean(unrestrictedlrir101 - ahead1test1$ahead1))^2) / ((mean(restricted1-ahead1test1$ahead1))^2)))
as.numeric(MSPElrir102ratio <- (((mean(unrestrictedlrir102 - ahead2test2$ahead2))^2) / ((mean(restricted2-ahead2test2$ahead2))^2)))
as.numeric(MSPElrir103ratio <- (((mean(unrestrictedlrir103 - ahead3test3$ahead3))^2) / ((mean(restricted3-ahead3test3$ahead3))^2)))
as.numeric(MSPElrir106ratio <- (((mean(unrestrictedlrir106 - ahead6test6$ahead6))^2) / ((mean(restricted6-ahead6test6$ahead6))^2)))
as.numeric(MSPElrir1012ratio <- (((mean(unrestrictedlrir1012 - ahead12test12$ahead12))^2) / ((mean(restricted12-ahead12test12$ahead12))^2)))
as.numeric(MSPElrir1018ratio <- (((mean(unrestrictedlrir1018 - ahead18test18$ahead18))^2) / ((mean(restricted18-ahead18test18$ahead18))^2)))
as.numeric(MSPElrir1024ratio <- (((mean(unrestrictedlrir1024 - ahead24test24$ahead24))^2) / ((mean(restricted24-ahead24test24$ahead24))^2)))

lrir10MSPE <- c(MSPElrir101ratio,MSPElrir102ratio,MSPElrir103ratio,MSPElrir106ratio,
                MSPElrir1012ratio,MSPElrir1018ratio,MSPElrir1024ratio)
#realbond
as.numeric(MSPErealbond1ratio <- (((mean(unrestrictedrealbond1 - ahead1test1$ahead1))^2) / ((mean(restricted1-ahead1test1$ahead1))^2)))
as.numeric(MSPErealbond2ratio <- (((mean(unrestrictedrealbond2 - ahead2test2$ahead2))^2) / ((mean(restricted2-ahead2test2$ahead2))^2)))
as.numeric(MSPErealbond3ratio <- (((mean(unrestrictedrealbond3 - ahead3test3$ahead3))^2) / ((mean(restricted3-ahead3test3$ahead3))^2)))
as.numeric(MSPErealbond6ratio <- (((mean(unrestrictedrealbond6 - ahead6test6$ahead6))^2) / ((mean(restricted6-ahead6test6$ahead6))^2)))
as.numeric(MSPErealbond12ratio <- (((mean(unrestrictedrealbond12 - ahead12test12$ahead12))^2) / ((mean(restricted12-ahead12test12$ahead12))^2)))
as.numeric(MSPErealbond18ratio <- (((mean(unrestrictedrealbond18 - ahead18test18$ahead18))^2) / ((mean(restricted18-ahead18test18$ahead18))^2)))
as.numeric(MSPErealbond24ratio <- (((mean(unrestrictedrealbond24 - ahead24test24$ahead24))^2) / ((mean(restricted24-ahead24test24$ahead24))^2)))

realbondMSPE <- c(MSPErealbond1ratio,MSPErealbond2ratio,MSPErealbond3ratio,MSPErealbond6ratio,
                  MSPErealbond12ratio,MSPErealbond18ratio,MSPErealbond24ratio)
#realtotalreturn
as.numeric(MSPErealtotalreturn1ratio <- (((mean(unrestrictedrealtotalreturn1 - ahead1test1$ahead1))^2) / ((mean(restricted1-ahead1test1$ahead1))^2)))
as.numeric(MSPErealtotalreturn2ratio <- (((mean(unrestrictedrealtotalreturn2 - ahead2test2$ahead2))^2) / ((mean(restricted2-ahead2test2$ahead2))^2)))
as.numeric(MSPErealtotalreturn3ratio <- (((mean(unrestrictedrealtotalreturn3 - ahead3test3$ahead3))^2) / ((mean(restricted3-ahead3test3$ahead3))^2)))
as.numeric(MSPErealtotalreturn6ratio <- (((mean(unrestrictedrealtotalreturn6 - ahead6test6$ahead6))^2) / ((mean(restricted6-ahead6test6$ahead6))^2)))
as.numeric(MSPErealtotalreturn12ratio <- (((mean(unrestrictedrealtotalreturn12 - ahead12test12$ahead12))^2) / ((mean(restricted12-ahead12test12$ahead12))^2)))
as.numeric(MSPErealtotalreturn18ratio <- (((mean(unrestrictedrealtotalreturn18 - ahead18test18$ahead18))^2) / ((mean(restricted18-ahead18test18$ahead18))^2)))
as.numeric(MSPErealtotalreturn24ratio <- (((mean(unrestrictedrealtotalreturn24 - ahead24test24$ahead24))^2) / ((mean(restricted24-ahead24test24$ahead24))^2)))

realtotalreturnMSPE <- c(MSPErealtotalreturn1ratio,MSPErealtotalreturn2ratio,MSPErealtotalreturn3ratio,MSPErealtotalreturn6ratio,
                         MSPErealtotalreturn12ratio,MSPErealtotalreturn18ratio,MSPErealtotalreturn24ratio)
#realtrscaledearnings
as.numeric(MSPErealtrscaledearnings1ratio <- (((mean(unrestrictedrealtrscaledearnings1 - ahead1test1$ahead1))^2) / ((mean(restricted1-ahead1test1$ahead1))^2)))
as.numeric(MSPErealtrscaledearnings2ratio <- (((mean(unrestrictedrealtrscaledearnings2 - ahead2test2$ahead2))^2) / ((mean(restricted2-ahead2test2$ahead2))^2)))
as.numeric(MSPErealtrscaledearnings3ratio <- (((mean(unrestrictedrealtrscaledearnings3 - ahead3test3$ahead3))^2) / ((mean(restricted3-ahead3test3$ahead3))^2)))
as.numeric(MSPErealtrscaledearnings6ratio <- (((mean(unrestrictedrealtrscaledearnings6 - ahead6test6$ahead6))^2) / ((mean(restricted6-ahead6test6$ahead6))^2)))
as.numeric(MSPErealtrscaledearnings12ratio <- (((mean(unrestrictedrealtrscaledearnings12 - ahead12test12$ahead12))^2) / ((mean(restricted12-ahead12test12$ahead12))^2)))
as.numeric(MSPErealtrscaledearnings18ratio <- (((mean(unrestrictedrealtrscaledearnings18 - ahead18test18$ahead18))^2) / ((mean(restricted18-ahead18test18$ahead18))^2)))
as.numeric(MSPErealtrscaledearnings24ratio <- (((mean(unrestrictedrealtrscaledearnings24 - ahead24test24$ahead24))^2) / ((mean(restricted24-ahead24test24$ahead24))^2)))

realtrscaledearningsMSPE <- c(MSPErealtrscaledearnings1ratio,MSPErealtrscaledearnings2ratio,MSPErealtrscaledearnings3ratio,MSPErealtrscaledearnings6ratio,
                              MSPErealtrscaledearnings12ratio,MSPErealtrscaledearnings18ratio,MSPErealtrscaledearnings24ratio)
#TRCAPE
as.numeric(MSPETRCAPE1ratio <- (((mean(unrestrictedTRCAPE1 - ahead1test1$ahead1))^2) / ((mean(restricted1-ahead1test1$ahead1))^2)))
as.numeric(MSPETRCAPE2ratio <- (((mean(unrestrictedTRCAPE2 - ahead2test2$ahead2))^2) / ((mean(restricted2-ahead2test2$ahead2))^2)))
as.numeric(MSPETRCAPE3ratio <- (((mean(unrestrictedTRCAPE3 - ahead3test3$ahead3))^2) / ((mean(restricted3-ahead3test3$ahead3))^2)))
as.numeric(MSPETRCAPE6ratio <- (((mean(unrestrictedTRCAPE6 - ahead6test6$ahead6))^2) / ((mean(restricted6-ahead6test6$ahead6))^2)))
as.numeric(MSPETRCAPE12ratio <- (((mean(unrestrictedTRCAPE12 - ahead12test12$ahead12))^2) / ((mean(restricted12-ahead12test12$ahead12))^2)))
as.numeric(MSPETRCAPE18ratio <- (((mean(unrestrictedTRCAPE18 - ahead18test18$ahead18))^2) / ((mean(restricted18-ahead18test18$ahead18))^2)))
as.numeric(MSPETRCAPE24ratio <- (((mean(unrestrictedTRCAPE24 - ahead24test24$ahead24))^2) / ((mean(restricted24-ahead24test24$ahead24))^2)))

TRCAPEMSPE <- c(MSPETRCAPE1ratio,MSPETRCAPE2ratio,MSPETRCAPE3ratio,MSPETRCAPE6ratio,
                MSPETRCAPE12ratio,MSPETRCAPE18ratio,MSPETRCAPE24ratio)

inflMSPE <- round(inflMSPE, digits = 3)
realdividendMSPE <- round(realdividendMSPE, digits=3)
lrir10MSPE <- round(lrir10MSPE, digits=3)
realbondMSPE <- round(realbondMSPE, digits=3)
realtotalreturnMSPE <- round(realtotalreturnMSPE, digits=3)
realtrscaledearningsMSPE <- round(realtrscaledearningsMSPE, digits=3)
TRCAPEMSPE <- round(TRCAPEMSPE, digits=3)

MSPE <- rbind(inflMSPE, realdividendMSPE, lrir10MSPE,realbondMSPE,
              realtotalreturnMSPE,realtrscaledearningsMSPE, TRCAPEMSPE)

meanMSPE <- mean(c(inflMSPE, realdividendMSPE, lrir10MSPE,realbondMSPE,
                 realtotalreturnMSPE,realtrscaledearningsMSPE, TRCAPEMSPE))
print(meanMSPE)
Horizons <- c("k=1","k=2","k=3","k=6","k=12","k=18","k=24")
# Set the column names of the MSPE matrix

MSPE <- rbind(Horizons,inflMSPE, realdividendMSPE, lrir10MSPE,realbondMSPE,
              realtotalreturnMSPE,realtrscaledearningsMSPE, TRCAPEMSPE)
rownames(MSPE) <- c("Horizon","CPI","Real Dividend","Long Range Interest","Real Bond"
                    ,"Real Total Return","TR Scaled Earnings","TR CAPE")
MSPE

stargazer(MSPE, type="text", out = "MSPEOLS.html")


########################################################################################
########################################################################################
########################################################################################
########################################################################################
########################################################################################
########################################################################################

start_values <- c(coefficients = c(0, 0), phi = 1)

bintercept1<- betareg(ahead1 ~ 1, data=ahead1train1)
bintercept2<- betareg(ahead2 ~ 1, data=ahead2train2)
bintercept3<- betareg(ahead3 ~ 1, data=ahead3train3)
bintercept6<- betareg(ahead6 ~ 1, data=ahead6train6)
bintercept12<- betareg(ahead12 ~ 1, data=ahead12train12)
bintercept18<- betareg(ahead18 ~ 1, data=ahead18train18)
bintercept24<- betareg(ahead24 ~ 1, data=ahead24train24)

binfl1<- betareg(ahead1 ~ infl, data=ahead1train1, start = start_values)
binfl2<- betareg(ahead2 ~ infl, data=ahead2train2, start = start_values)
binfl3<- betareg(ahead3 ~ infl, data=ahead3train3, start = start_values)
binfl6<- betareg(ahead6 ~ infl, data=ahead6train6, start = start_values)
binfl12<- betareg(ahead12 ~ infl, data=ahead12train12, start = start_values)
binfl18<- betareg(ahead18 ~ infl, data=ahead18train18, start = start_values)
binfl24<- betareg(ahead24 ~ infl, data=ahead24train24, start = start_values)

blrir101<- betareg(ahead1 ~ lrir10, data=ahead1train1, start = start_values)
blrir102<- betareg(ahead2 ~ lrir10, data=ahead2train2, start = start_values)
blrir103<- betareg(ahead3 ~ lrir10, data=ahead3train3, start = start_values)
blrir106<- betareg(ahead6 ~ lrir10, data=ahead6train6, start = start_values)
blrir1012<- betareg(ahead12 ~ lrir10, data=ahead12train12, start = start_values)
blrir1018<- betareg(ahead18 ~ lrir10, data=ahead18train18, start = start_values)
blrir1024<- betareg(ahead24 ~ lrir10, data=ahead24train24, start = start_values)

brealdividend1<- betareg(ahead1 ~ realdividend, data=ahead1train1, start = start_values)
brealdividend2<- betareg(ahead2 ~ realdividend, data=ahead2train2, start = start_values)
brealdividend3<- betareg(ahead3 ~ realdividend, data=ahead3train3, start = start_values)
brealdividend6<- betareg(ahead6 ~ realdividend, data=ahead6train6, start = start_values)
brealdividend12<- betareg(ahead12 ~ realdividend, data=ahead12train12, start = start_values)
brealdividend18<- betareg(ahead18 ~ realdividend, data=ahead18train18, start = start_values)
brealdividend24<- betareg(ahead24 ~ realdividend, data=ahead24train24, start = start_values)

brealbond1<- betareg(ahead1 ~ realbond, data=ahead1train1, start = start_values)
brealbond2<- betareg(ahead2 ~ realbond, data=ahead2train2, start = start_values)
brealbond3<- betareg(ahead3 ~ realbond, data=ahead3train3, start = start_values)
brealbond6<- betareg(ahead6 ~ realbond, data=ahead6train6, start = start_values)
brealbond12<- betareg(ahead12 ~ realbond, data=ahead12train12, start = start_values)
brealbond18<- betareg(ahead18 ~ realbond, data=ahead18train18, start = start_values)
brealbond24<- betareg(ahead24 ~ realbond, data=ahead24train24, start = start_values)

brealtotalreturn1<- betareg(ahead1 ~ realtotalreturn, data=ahead1train1, start = start_values)
brealtotalreturn2<- betareg(ahead2 ~ realtotalreturn, data=ahead2train2, start = start_values)
brealtotalreturn3<- betareg(ahead3 ~ realtotalreturn, data=ahead3train3, start = start_values)
brealtotalreturn6<- betareg(ahead6 ~ realtotalreturn, data=ahead6train6, start = start_values)
brealtotalreturn12<- betareg(ahead12 ~ realtotalreturn, data=ahead12train12, start = start_values)
brealtotalreturn18<- betareg(ahead18 ~ realtotalreturn, data=ahead18train18, start = start_values)
brealtotalreturn24<- betareg(ahead24 ~ realtotalreturn, data=ahead24train24, start = start_values)

brealtrscaledearnings1<- betareg(ahead1 ~ realtrscaledearnings, data=ahead1train1, start = start_values)
brealtrscaledearnings2<- betareg(ahead2 ~ realtrscaledearnings, data=ahead2train2, start = start_values)
brealtrscaledearnings3<- betareg(ahead3 ~ realtrscaledearnings, data=ahead3train3, start = start_values)
brealtrscaledearnings6<- betareg(ahead6 ~ realtrscaledearnings, data=ahead6train6, start = start_values)
brealtrscaledearnings12<- betareg(ahead12 ~ realtrscaledearnings, data=ahead12train12, start = start_values)
brealtrscaledearnings18<- betareg(ahead18 ~ realtrscaledearnings, data=ahead18train18, start = start_values)
brealtrscaledearnings24<- betareg(ahead24 ~ realtrscaledearnings, data=ahead24train24, start = start_values)

bTRCAPE1<- betareg(ahead1 ~ TRCAPE, data=ahead1train1, start = start_values)
bTRCAPE2<- betareg(ahead2 ~ TRCAPE, data=ahead2train2, start = start_values)
bTRCAPE3<- betareg(ahead3 ~ TRCAPE, data=ahead3train3, start = start_values)
bTRCAPE6<- betareg(ahead6 ~ TRCAPE, data=ahead6train6, start = start_values)
bTRCAPE12<- betareg(ahead12 ~ TRCAPE, data=ahead12train12, start = start_values)
bTRCAPE18<- betareg(ahead18 ~ TRCAPE, data=ahead18train18, start = start_values)
bTRCAPE24<- betareg(ahead24 ~ TRCAPE, data=ahead24train24, start = start_values)
#predictions
brestricted1 <- predict(bintercept1, newdata=ahead1test1)
brestricted2 <- predict(bintercept2, newdata=ahead2test2)
brestricted3 <- predict(bintercept3, newdata=ahead3test3)
brestricted6 <- predict(bintercept6, newdata=ahead6test6)
brestricted12 <- predict(bintercept12, newdata=ahead12test12)
brestricted18 <- predict(bintercept18, newdata=ahead18test18)
brestricted24 <- predict(bintercept24, newdata=ahead24test24)
#predictions
bunrestrictedinfl1 <- predict(binfl1, newdata=ahead1test1)
bunrestrictedinfl2 <- predict(binfl2, newdata=ahead2test2)
bunrestrictedinfl3 <- predict(binfl3, newdata=ahead3test3)
bunrestrictedinfl6 <- predict(binfl6, newdata=ahead6test6)
bunrestrictedinfl12 <- predict(binfl12, newdata=ahead12test12)
bunrestrictedinfl18 <- predict(binfl18, newdata=ahead18test18)
bunrestrictedinfl24 <- predict(binfl24, newdata=ahead24test24)
#realdividend
bunrestrictedrealdividend1 <- predict(brealdividend1, newdata=ahead1test1)
bunrestrictedrealdividend2 <- predict(brealdividend2, newdata=ahead2test2)
bunrestrictedrealdividend3 <- predict(brealdividend3, newdata=ahead3test3)
bunrestrictedrealdividend6 <- predict(brealdividend6, newdata=ahead6test6)
bunrestrictedrealdividend12 <- predict(brealdividend12, newdata=ahead12test12)
bunrestrictedrealdividend18 <- predict(brealdividend18, newdata=ahead18test18)
bunrestrictedrealdividend24 <- predict(brealdividend24, newdata=ahead24test24)
#lrir10
bunrestrictedlrir101 <- predict(blrir101, newdata=ahead1test1)
bunrestrictedlrir102 <- predict(blrir102, newdata=ahead2test2)
bunrestrictedlrir103 <- predict(blrir103, newdata=ahead3test3)
bunrestrictedlrir106 <- predict(blrir106, newdata=ahead6test6)
bunrestrictedlrir1012 <- predict(blrir1012, newdata=ahead12test12)
bunrestrictedlrir1018 <- predict(blrir1018, newdata=ahead18test18)
bunrestrictedlrir1024 <- predict(blrir1024, newdata=ahead24test24)
#realdividend
bunrestrictedrealdividend1 <- predict(brealdividend1, newdata=ahead1test1)
bunrestrictedrealdividend2 <- predict(brealdividend2, newdata=ahead2test2)
bunrestrictedrealdividend3 <- predict(brealdividend3, newdata=ahead3test3)
bunrestrictedrealdividend6 <- predict(brealdividend6, newdata=ahead6test6)
bunrestrictedrealdividend12 <- predict(brealdividend12, newdata=ahead12test12)
bunrestrictedrealdividend18 <- predict(brealdividend18, newdata=ahead18test18)
bunrestrictedrealdividend24 <- predict(brealdividend24, newdata=ahead24test24)
#realbond
bunrestrictedrealbond1 <- predict(brealbond1, newdata=ahead1test1)
bunrestrictedrealbond2 <- predict(brealbond2, newdata=ahead2test2)
bunrestrictedrealbond3 <- predict(brealbond3, newdata=ahead3test3)
bunrestrictedrealbond6 <- predict(brealbond6, newdata=ahead6test6)
bunrestrictedrealbond12 <- predict(brealbond12, newdata=ahead12test12)
bunrestrictedrealbond18 <- predict(brealbond18, newdata=ahead18test18)
bunrestrictedrealbond24 <- predict(brealbond24, newdata=ahead24test24)
#realtotalreturn
bunrestrictedrealtotalreturn1 <- predict(brealtotalreturn1, newdata=ahead1test1)
bunrestrictedrealtotalreturn2 <- predict(brealtotalreturn2, newdata=ahead2test2)
bunrestrictedrealtotalreturn3 <- predict(brealtotalreturn3, newdata=ahead3test3)
bunrestrictedrealtotalreturn6 <- predict(brealtotalreturn6, newdata=ahead6test6)
bunrestrictedrealtotalreturn12 <- predict(brealtotalreturn12, newdata=ahead12test12)
bunrestrictedrealtotalreturn18 <- predict(brealtotalreturn18, newdata=ahead18test18)
bunrestrictedrealtotalreturn24 <- predict(brealtotalreturn24, newdata=ahead24test24)
#realtrscaledearnings
bunrestrictedrealtrscaledearnings1 <- predict(brealtrscaledearnings1, newdata=ahead1test1)
bunrestrictedrealtrscaledearnings2 <- predict(brealtrscaledearnings2, newdata=ahead2test2)
bunrestrictedrealtrscaledearnings3 <- predict(brealtrscaledearnings3, newdata=ahead3test3)
bunrestrictedrealtrscaledearnings6 <- predict(brealtrscaledearnings6, newdata=ahead6test6)
bunrestrictedrealtrscaledearnings12 <- predict(brealtrscaledearnings12, newdata=ahead12test12)
bunrestrictedrealtrscaledearnings18 <- predict(brealtrscaledearnings18, newdata=ahead18test18)
bunrestrictedrealtrscaledearnings24 <- predict(brealtrscaledearnings24, newdata=ahead24test24)
#TRCAPE
bunrestrictedTRCAPE1 <- predict(bTRCAPE1, newdata=ahead1test1)
bunrestrictedTRCAPE2 <- predict(bTRCAPE2, newdata=ahead2test2)
bunrestrictedTRCAPE3 <- predict(bTRCAPE3, newdata=ahead3test3)
bunrestrictedTRCAPE6 <- predict(bTRCAPE6, newdata=ahead6test6)
bunrestrictedTRCAPE12 <- predict(bTRCAPE12, newdata=ahead12test12)
bunrestrictedTRCAPE18 <- predict(bTRCAPE18, newdata=ahead18test18)
bunrestrictedTRCAPE24 <- predict(bTRCAPE24, newdata=ahead24test24)
#RObustness MSPE 

#MSPE Ratio
#infl
as.numeric(bMSPEinfl1ratio <- (((mean(bunrestrictedinfl1 - ahead1test1$ahead1))^2) / ((mean(brestricted1-ahead1test1$ahead1))^2)))
as.numeric(bMSPEinfl2ratio <- (((mean(bunrestrictedinfl2 - ahead2test2$ahead2))^2) / ((mean(brestricted2-ahead2test2$ahead2))^2)))
as.numeric(bMSPEinfl3ratio <- (((mean(bunrestrictedinfl3 - ahead3test3$ahead3))^2) / ((mean(brestricted3-ahead3test3$ahead3))^2)))
as.numeric(bMSPEinfl6ratio <- (((mean(bunrestrictedinfl6 - ahead6test6$ahead6))^2) / ((mean(brestricted6-ahead6test6$ahead6))^2)))
as.numeric(bMSPEinfl12ratio <- (((mean(bunrestrictedinfl12 - ahead12test12$ahead12))^2) / ((mean(brestricted12-ahead12test12$ahead12))^2)))
as.numeric(bMSPEinfl18ratio <- (((mean(bunrestrictedinfl18 - ahead18test18$ahead18))^2) / ((mean(brestricted18-ahead18test18$ahead18))^2)))
as.numeric(bMSPEinfl24ratio <- (((mean(bunrestrictedinfl24 - ahead24test24$ahead24))^2) / ((mean(brestricted24-ahead24test24$ahead24))^2)))

binflMSPE <- c(bMSPEinfl1ratio,bMSPEinfl2ratio,bMSPEinfl3ratio,bMSPEinfl6ratio,
              bMSPEinfl12ratio,bMSPEinfl18ratio,bMSPEinfl24ratio)

#realdividend
as.numeric(bMSPErealdividend1ratio <- (((mean( bunrestrictedrealdividend1 - ahead1test1$ahead1))^2) / ((mean( brestricted1-ahead1test1$ahead1))^2)))
as.numeric(bMSPErealdividend2ratio <- (((mean( bunrestrictedrealdividend2 - ahead2test2$ahead2))^2) / ((mean( brestricted2-ahead2test2$ahead2))^2)))
as.numeric(bMSPErealdividend3ratio <- (((mean( bunrestrictedrealdividend3 - ahead3test3$ahead3))^2) / ((mean( brestricted3-ahead3test3$ahead3))^2)))
as.numeric(bMSPErealdividend6ratio <- (((mean( bunrestrictedrealdividend6 - ahead6test6$ahead6))^2) / ((mean( brestricted6-ahead6test6$ahead6))^2)))
as.numeric(bMSPErealdividend12ratio <- (((mean( bunrestrictedrealdividend12 - ahead12test12$ahead12))^2) / ((mean( brestricted12-ahead12test12$ahead12))^2)))
as.numeric(bMSPErealdividend18ratio <- (((mean( bunrestrictedrealdividend18 - ahead18test18$ahead18))^2) / ((mean( brestricted18-ahead18test18$ahead18))^2)))
as.numeric(bMSPErealdividend24ratio <- (((mean( bunrestrictedrealdividend24 - ahead24test24$ahead24))^2) / ((mean( brestricted24-ahead24test24$ahead24))^2)))

brealdividendMSPE <- c(bMSPErealdividend1ratio,bMSPErealdividend2ratio,bMSPErealdividend3ratio,bMSPErealdividend6ratio,
                      bMSPErealdividend12ratio,bMSPErealdividend18ratio,bMSPErealdividend24ratio)

as.numeric(bMSPElrir101ratio <- (((mean(bunrestrictedlrir101 - ahead1test1$ahead1))^2) / ((mean(brestricted1-ahead1test1$ahead1))^2)))
as.numeric(bMSPElrir102ratio <- (((mean(bunrestrictedlrir102 - ahead2test2$ahead2))^2) / ((mean(brestricted2-ahead2test2$ahead2))^2)))
as.numeric(bMSPElrir103ratio <- (((mean(bunrestrictedlrir103 - ahead3test3$ahead3))^2) / ((mean(brestricted3-ahead3test3$ahead3))^2)))
as.numeric(bMSPElrir106ratio <- (((mean(bunrestrictedlrir106 - ahead6test6$ahead6))^2) / ((mean(brestricted6-ahead6test6$ahead6))^2)))
as.numeric(bMSPElrir1012ratio <- (((mean(bunrestrictedlrir1012 - ahead12test12$ahead12))^2) / ((mean(brestricted12-ahead12test12$ahead12))^2)))
as.numeric(bMSPElrir1018ratio <- (((mean(bunrestrictedlrir1018 - ahead18test18$ahead18))^2) / ((mean(brestricted18-ahead18test18$ahead18))^2)))
as.numeric(bMSPElrir1024ratio <- (((mean(bunrestrictedlrir1024 - ahead24test24$ahead24))^2) / ((mean(brestricted24-ahead24test24$ahead24))^2)))

blrir10MSPE <- c(bMSPElrir101ratio,bMSPElrir102ratio,bMSPElrir103ratio,bMSPElrir106ratio,
                bMSPElrir1012ratio,bMSPElrir1018ratio,bMSPElrir1024ratio)
#realbond
as.numeric(bMSPErealbond1ratio <- (((mean(bunrestrictedrealbond1 - ahead1test1$ahead1))^2) / ((mean(brestricted1-ahead1test1$ahead1))^2)))
as.numeric(bMSPErealbond2ratio <- (((mean(bunrestrictedrealbond2 - ahead2test2$ahead2))^2) / ((mean(brestricted2-ahead2test2$ahead2))^2)))
as.numeric(bMSPErealbond3ratio <- (((mean(bunrestrictedrealbond3 - ahead3test3$ahead3))^2) / ((mean(brestricted3-ahead3test3$ahead3))^2)))
as.numeric(bMSPErealbond6ratio <- (((mean(bunrestrictedrealbond6 - ahead6test6$ahead6))^2) / ((mean(brestricted6-ahead6test6$ahead6))^2)))
as.numeric(bMSPErealbond12ratio <- (((mean(bunrestrictedrealbond12 - ahead12test12$ahead12))^2) / ((mean(brestricted12-ahead12test12$ahead12))^2)))
as.numeric(bMSPErealbond18ratio <- (((mean(bunrestrictedrealbond18 - ahead18test18$ahead18))^2) / ((mean(brestricted18-ahead18test18$ahead18))^2)))
as.numeric(bMSPErealbond24ratio <- (((mean(bunrestrictedrealbond24 - ahead24test24$ahead24))^2) / ((mean(brestricted24-ahead24test24$ahead24))^2)))

brealbondMSPE <- c(bMSPErealbond1ratio,bMSPErealbond2ratio,bMSPErealbond3ratio,bMSPErealbond6ratio,
                  bMSPErealbond12ratio,bMSPErealbond18ratio,bMSPErealbond24ratio)
#realtotalreturn
as.numeric(bMSPErealtotalreturn1ratio <- (((mean(bunrestrictedrealtotalreturn1 - ahead1test1$ahead1))^2) / ((mean(brestricted1-ahead1test1$ahead1))^2)))
as.numeric(bMSPErealtotalreturn2ratio <- (((mean(bunrestrictedrealtotalreturn2 - ahead2test2$ahead2))^2) / ((mean(brestricted2-ahead2test2$ahead2))^2)))
as.numeric(bMSPErealtotalreturn3ratio <- (((mean(bunrestrictedrealtotalreturn3 - ahead3test3$ahead3))^2) / ((mean(brestricted3-ahead3test3$ahead3))^2)))
as.numeric(bMSPErealtotalreturn6ratio <- (((mean(bunrestrictedrealtotalreturn6 - ahead6test6$ahead6))^2) / ((mean(brestricted6-ahead6test6$ahead6))^2)))
as.numeric(bMSPErealtotalreturn12ratio <- (((mean(bunrestrictedrealtotalreturn12 - ahead12test12$ahead12))^2) / ((mean(brestricted12-ahead12test12$ahead12))^2)))
as.numeric(bMSPErealtotalreturn18ratio <- (((mean(bunrestrictedrealtotalreturn18 - ahead18test18$ahead18))^2) / ((mean(brestricted18-ahead18test18$ahead18))^2)))
as.numeric(bMSPErealtotalreturn24ratio <- (((mean(bunrestrictedrealtotalreturn24 - ahead24test24$ahead24))^2) / ((mean(brestricted24-ahead24test24$ahead24))^2)))

brealtotalreturnMSPE <- c(bMSPErealtotalreturn1ratio,bMSPErealtotalreturn2ratio,bMSPErealtotalreturn3ratio,bMSPErealtotalreturn6ratio,
                         bMSPErealtotalreturn12ratio,bMSPErealtotalreturn18ratio,bMSPErealtotalreturn24ratio)
#realtrscaledearnings
as.numeric(bMSPErealtrscaledearnings1ratio <- (((mean(bunrestrictedrealtrscaledearnings1 - ahead1test1$ahead1))^2) / ((mean(brestricted1-ahead1test1$ahead1))^2)))
as.numeric(bMSPErealtrscaledearnings2ratio <- (((mean(bunrestrictedrealtrscaledearnings2 - ahead2test2$ahead2))^2) / ((mean(brestricted2-ahead2test2$ahead2))^2)))
as.numeric(bMSPErealtrscaledearnings3ratio <- (((mean(bunrestrictedrealtrscaledearnings3 - ahead3test3$ahead3))^2) / ((mean(brestricted3-ahead3test3$ahead3))^2)))
as.numeric(bMSPErealtrscaledearnings6ratio <- (((mean(bunrestrictedrealtrscaledearnings6 - ahead6test6$ahead6))^2) / ((mean(brestricted6-ahead6test6$ahead6))^2)))
as.numeric(bMSPErealtrscaledearnings12ratio <- (((mean(bunrestrictedrealtrscaledearnings12 - ahead12test12$ahead12))^2) / ((mean(brestricted12-ahead12test12$ahead12))^2)))
as.numeric(bMSPErealtrscaledearnings18ratio <- (((mean(bunrestrictedrealtrscaledearnings18 - ahead18test18$ahead18))^2) / ((mean(brestricted18-ahead18test18$ahead18))^2)))
as.numeric(bMSPErealtrscaledearnings24ratio <- (((mean(bunrestrictedrealtrscaledearnings24 - ahead24test24$ahead24))^2) / ((mean(brestricted24-ahead24test24$ahead24))^2)))

brealtrscaledearningsMSPE <- c(bMSPErealtrscaledearnings1ratio,bMSPErealtrscaledearnings2ratio,bMSPErealtrscaledearnings3ratio,bMSPErealtrscaledearnings6ratio,
                              bMSPErealtrscaledearnings12ratio,bMSPErealtrscaledearnings18ratio,bMSPErealtrscaledearnings24ratio)
#TRCAPE
as.numeric(bMSPETRCAPE1ratio <- (((mean(bunrestrictedTRCAPE1 - ahead1test1$ahead1))^2) / ((mean(brestricted1-ahead1test1$ahead1))^2)))
as.numeric(bMSPETRCAPE2ratio <- (((mean(bunrestrictedTRCAPE2 - ahead2test2$ahead2))^2) / ((mean(brestricted2-ahead2test2$ahead2))^2)))
as.numeric(bMSPETRCAPE3ratio <- (((mean(bunrestrictedTRCAPE3 - ahead3test3$ahead3))^2) / ((mean(brestricted3-ahead3test3$ahead3))^2)))
as.numeric(bMSPETRCAPE6ratio <- (((mean(bunrestrictedTRCAPE6 - ahead6test6$ahead6))^2) / ((mean(brestricted6-ahead6test6$ahead6))^2)))
as.numeric(bMSPETRCAPE12ratio <- (((mean(bunrestrictedTRCAPE12 - ahead12test12$ahead12))^2) / ((mean(brestricted12-ahead12test12$ahead12))^2)))
as.numeric(bMSPETRCAPE18ratio <- (((mean(bunrestrictedTRCAPE18 - ahead18test18$ahead18))^2) / ((mean(brestricted18-ahead18test18$ahead18))^2)))
as.numeric(bMSPETRCAPE24ratio <- (((mean(bunrestrictedTRCAPE24 - ahead24test24$ahead24))^2) / ((mean(brestricted24-ahead24test24$ahead24))^2)))

bTRCAPEMSPE <- c(bMSPETRCAPE1ratio,bMSPETRCAPE2ratio,bMSPETRCAPE3ratio,bMSPETRCAPE6ratio,
                bMSPETRCAPE12ratio,bMSPETRCAPE18ratio,bMSPETRCAPE24ratio)

binflMSPE <- round(binflMSPE, digits = 3)
brealdividendMSPE <- round(brealdividendMSPE, digits=3)
blrir10MSPE <- round(blrir10MSPE, digits=3)
brealbondMSPE <- round(brealbondMSPE, digits=3)
brealtotalreturnMSPE <- round(brealtotalreturnMSPE, digits=3)
brealtrscaledearningsMSPE <- round(brealtrscaledearningsMSPE, digits=3)
bTRCAPEMSPE <- round(bTRCAPEMSPE, digits=3)

bMSPE <- rbind(binflMSPE, brealdividendMSPE, blrir10MSPE,brealbondMSPE,
              brealtotalreturnMSPE,brealtrscaledearningsMSPE, bTRCAPEMSPE)
meanbMSPE <- mean(c(binflMSPE, brealdividendMSPE, blrir10MSPE,brealbondMSPE,
  brealtotalreturnMSPE,brealtrscaledearningsMSPE, bTRCAPEMSPE))
Horizons <- c("k=1","k=2","k=3","k=6","k=12","k=18","k=24")
# Set the column names of the MSPE matrix

bMSPE <- rbind(Horizons,binflMSPE, brealdividendMSPE, blrir10MSPE,brealbondMSPE,
              brealtotalreturnMSPE,brealtrscaledearningsMSPE, bTRCAPEMSPE)
rownames(bMSPE) <- c("Horizon","CPI","Real Dividend","Long Range Interest","Real Bond"
                    ,"Real Total Return","TR Scaled Earnings","TR CAPE")
bMSPE
print(meanbMSPE)
stargazer(bMSPE, type="text", out = "MSPEBETA101.html")

MSPE
print(meanMSPE)
stargazer(MSPE, type="text", out="MSPEOLS101.html")




###############################################################################################################################################################
###############################################################################################################################################################
###############################################################################################################################################################
###############################################################################################################################################################
###############################################################################################################################################################
###############################################################################################################################################################
###############################################################################################################################################################
##########################################################################################################################################################################
#Backcasting the first 20% (least recent)
# Reverse the order of the dataframes
combined_dfahead1_rev <- combined_dfahead1[nrow(combined_dfahead1):1, ]
combined_dfahead2_rev <- combined_dfahead2[nrow(combined_dfahead2):1, ]
combined_dfahead3_rev <- combined_dfahead3[nrow(combined_dfahead3):1, ]
combined_dfahead6_rev <- combined_dfahead6[nrow(combined_dfahead6):1, ]
combined_dfahead12_rev <- combined_dfahead12[nrow(combined_dfahead12):1, ]
combined_dfahead18_rev <- combined_dfahead18[nrow(combined_dfahead18):1, ]
combined_dfahead24_rev <- combined_dfahead24[nrow(combined_dfahead24):1, ]

# Calculate the index for the last 80%
n <- nrow(combined_dfahead1_rev)
index_80_percent <- round(0.8 * n)

# Select the last 80% of reversed data for training
ahead1train1 <- combined_dfahead1_rev[1:index_80_percent, ]
ahead2train2 <- combined_dfahead2_rev[1:index_80_percent, ]
ahead3train3 <- combined_dfahead3_rev[1:index_80_percent, ]
ahead6train6 <- combined_dfahead6_rev[1:index_80_percent, ]
ahead12train12 <- combined_dfahead12_rev[1:index_80_percent, ]
ahead18train18 <- combined_dfahead18_rev[1:index_80_percent, ]
ahead24train24 <- combined_dfahead24_rev[1:index_80_percent, ]

# Reverse the order of test data
ahead1test1 <- combined_dfahead1_rev[-(1:index_80_percent), ]
ahead2test2 <- combined_dfahead2_rev[-(1:index_80_percent), ]
ahead3test3 <- combined_dfahead3_rev[-(1:index_80_percent), ]
ahead6test6 <- combined_dfahead6_rev[-(1:index_80_percent), ]
ahead12test12 <- combined_dfahead12_rev[-(1:index_80_percent), ]
ahead18test18 <- combined_dfahead18_rev[-(1:index_80_percent), ]
ahead24test24 <- combined_dfahead24_rev[-(1:index_80_percent), ]

#out of sample 
intercept1<- lm(ahead1 ~ 1, data=ahead1train1)
intercept2<- lm(ahead2 ~ 1, data=ahead2train2)
intercept3<- lm(ahead3 ~ 1, data=ahead3train3)
intercept6<- lm(ahead6 ~ 1, data=ahead6train6)
intercept12<- lm(ahead12 ~ 1, data=ahead12train12)
intercept18<- lm(ahead18 ~ 1, data=ahead18train18)
intercept24<- lm(ahead24 ~ 1, data=ahead24train24)

infl1<- lm(ahead1 ~ infl, data=ahead1train1)
infl2<- lm(ahead2 ~ infl, data=ahead2train2)
infl3<- lm(ahead3 ~ infl, data=ahead3train3)
infl6<- lm(ahead6 ~ infl, data=ahead6train6)
infl12<- lm(ahead12 ~ infl, data=ahead12train12)
infl18<- lm(ahead18 ~ infl, data=ahead18train18)
infl24<- lm(ahead24 ~ infl, data=ahead24train24)

lrir101<- lm(ahead1 ~ lrir10, data=ahead1train1)
lrir102<- lm(ahead2 ~ lrir10, data=ahead2train2)
lrir103<- lm(ahead3 ~ lrir10, data=ahead3train3)
lrir106<- lm(ahead6 ~ lrir10, data=ahead6train6)
lrir1012<- lm(ahead12 ~ lrir10, data=ahead12train12)
lrir1018<- lm(ahead18 ~ lrir10, data=ahead18train18)
lrir1024<- lm(ahead24 ~ lrir10, data=ahead24train24)

realdividend1<- lm(ahead1 ~ realdividend, data=ahead1train1)
realdividend2<- lm(ahead2 ~ realdividend, data=ahead2train2)
realdividend3<- lm(ahead3 ~ realdividend, data=ahead3train3)
realdividend6<- lm(ahead6 ~ realdividend, data=ahead6train6)
realdividend12<- lm(ahead12 ~ realdividend, data=ahead12train12)
realdividend18<- lm(ahead18 ~ realdividend, data=ahead18train18)
realdividend24<- lm(ahead24 ~ realdividend, data=ahead24train24)

realbond1<- lm(ahead1 ~ realbond, data=ahead1train1)
realbond2<- lm(ahead2 ~ realbond, data=ahead2train2)
realbond3<- lm(ahead3 ~ realbond, data=ahead3train3)
realbond6<- lm(ahead6 ~ realbond, data=ahead6train6)
realbond12<- lm(ahead12 ~ realbond, data=ahead12train12)
realbond18<- lm(ahead18 ~ realbond, data=ahead18train18)
realbond24<- lm(ahead24 ~ realbond, data=ahead24train24)

realtotalreturn1<- lm(ahead1 ~ realtotalreturn, data=ahead1train1)
realtotalreturn2<- lm(ahead2 ~ realtotalreturn, data=ahead2train2)
realtotalreturn3<- lm(ahead3 ~ realtotalreturn, data=ahead3train3)
realtotalreturn6<- lm(ahead6 ~ realtotalreturn, data=ahead6train6)
realtotalreturn12<- lm(ahead12 ~ realtotalreturn, data=ahead12train12)
realtotalreturn18<- lm(ahead18 ~ realtotalreturn, data=ahead18train18)
realtotalreturn24<- lm(ahead24 ~ realtotalreturn, data=ahead24train24)

realtrscaledearnings1<- lm(ahead1 ~ realtrscaledearnings, data=ahead1train1)
realtrscaledearnings2<- lm(ahead2 ~ realtrscaledearnings, data=ahead2train2)
realtrscaledearnings3<- lm(ahead3 ~ realtrscaledearnings, data=ahead3train3)
realtrscaledearnings6<- lm(ahead6 ~ realtrscaledearnings, data=ahead6train6)
realtrscaledearnings12<- lm(ahead12 ~ realtrscaledearnings, data=ahead12train12)
realtrscaledearnings18<- lm(ahead18 ~ realtrscaledearnings, data=ahead18train18)
realtrscaledearnings24<- lm(ahead24 ~ realtrscaledearnings, data=ahead24train24)

TRCAPE1<- lm(ahead1 ~ TRCAPE, data=ahead1train1)
TRCAPE2<- lm(ahead2 ~ TRCAPE, data=ahead2train2)
TRCAPE3<- lm(ahead3 ~ TRCAPE, data=ahead3train3)
TRCAPE6<- lm(ahead6 ~ TRCAPE, data=ahead6train6)
TRCAPE12<- lm(ahead12 ~ TRCAPE, data=ahead12train12)
TRCAPE18<- lm(ahead18 ~ TRCAPE, data=ahead18train18)
TRCAPE24<- lm(ahead24 ~ TRCAPE, data=ahead24train24)
#predictions
restricted1 <- predict(intercept1, newdata=ahead1test1)
restricted2 <- predict(intercept2, newdata=ahead2test2)
restricted3 <- predict(intercept3, newdata=ahead3test3)
restricted6 <- predict(intercept6, newdata=ahead6test6)
restricted12 <- predict(intercept12, newdata=ahead12test12)
restricted18 <- predict(intercept18, newdata=ahead18test18)
restricted24 <- predict(intercept24, newdata=ahead24test24)
#predictions
unrestrictedinfl1 <- predict(infl1, newdata=ahead1test1)
unrestrictedinfl2 <- predict(infl2, newdata=ahead2test2)
unrestrictedinfl3 <- predict(infl3, newdata=ahead3test3)
unrestrictedinfl6 <- predict(infl6, newdata=ahead6test6)
unrestrictedinfl12 <- predict(infl12, newdata=ahead12test12)
unrestrictedinfl18 <- predict(infl18, newdata=ahead18test18)
unrestrictedinfl24 <- predict(infl24, newdata=ahead24test24)
#realdividend
unrestrictedrealdividend1 <- predict(realdividend1, newdata=ahead1test1)
unrestrictedrealdividend2 <- predict(realdividend2, newdata=ahead2test2)
unrestrictedrealdividend3 <- predict(realdividend3, newdata=ahead3test3)
unrestrictedrealdividend6 <- predict(realdividend6, newdata=ahead6test6)
unrestrictedrealdividend12 <- predict(realdividend12, newdata=ahead12test12)
unrestrictedrealdividend18 <- predict(realdividend18, newdata=ahead18test18)
unrestrictedrealdividend24 <- predict(realdividend24, newdata=ahead24test24)
#lrir10
unrestrictedlrir101 <- predict(lrir101, newdata=ahead1test1)
unrestrictedlrir102 <- predict(lrir102, newdata=ahead2test2)
unrestrictedlrir103 <- predict(lrir103, newdata=ahead3test3)
unrestrictedlrir106 <- predict(lrir106, newdata=ahead6test6)
unrestrictedlrir1012 <- predict(lrir1012, newdata=ahead12test12)
unrestrictedlrir1018 <- predict(lrir1018, newdata=ahead18test18)
unrestrictedlrir1024 <- predict(lrir1024, newdata=ahead24test24)
#realdividend
unrestrictedrealdividend1 <- predict(realdividend1, newdata=ahead1test1)
unrestrictedrealdividend2 <- predict(realdividend2, newdata=ahead2test2)
unrestrictedrealdividend3 <- predict(realdividend3, newdata=ahead3test3)
unrestrictedrealdividend6 <- predict(realdividend6, newdata=ahead6test6)
unrestrictedrealdividend12 <- predict(realdividend12, newdata=ahead12test12)
unrestrictedrealdividend18 <- predict(realdividend18, newdata=ahead18test18)
unrestrictedrealdividend24 <- predict(realdividend24, newdata=ahead24test24)
#realbond
unrestrictedrealbond1 <- predict(realbond1, newdata=ahead1test1)
unrestrictedrealbond2 <- predict(realbond2, newdata=ahead2test2)
unrestrictedrealbond3 <- predict(realbond3, newdata=ahead3test3)
unrestrictedrealbond6 <- predict(realbond6, newdata=ahead6test6)
unrestrictedrealbond12 <- predict(realbond12, newdata=ahead12test12)
unrestrictedrealbond18 <- predict(realbond18, newdata=ahead18test18)
unrestrictedrealbond24 <- predict(realbond24, newdata=ahead24test24)
#realtotalreturn
unrestrictedrealtotalreturn1 <- predict(realtotalreturn1, newdata=ahead1test1)
unrestrictedrealtotalreturn2 <- predict(realtotalreturn2, newdata=ahead2test2)
unrestrictedrealtotalreturn3 <- predict(realtotalreturn3, newdata=ahead3test3)
unrestrictedrealtotalreturn6 <- predict(realtotalreturn6, newdata=ahead6test6)
unrestrictedrealtotalreturn12 <- predict(realtotalreturn12, newdata=ahead12test12)
unrestrictedrealtotalreturn18 <- predict(realtotalreturn18, newdata=ahead18test18)
unrestrictedrealtotalreturn24 <- predict(realtotalreturn24, newdata=ahead24test24)
#realtrscaledearnings
unrestrictedrealtrscaledearnings1 <- predict(realtrscaledearnings1, newdata=ahead1test1)
unrestrictedrealtrscaledearnings2 <- predict(realtrscaledearnings2, newdata=ahead2test2)
unrestrictedrealtrscaledearnings3 <- predict(realtrscaledearnings3, newdata=ahead3test3)
unrestrictedrealtrscaledearnings6 <- predict(realtrscaledearnings6, newdata=ahead6test6)
unrestrictedrealtrscaledearnings12 <- predict(realtrscaledearnings12, newdata=ahead12test12)
unrestrictedrealtrscaledearnings18 <- predict(realtrscaledearnings18, newdata=ahead18test18)
unrestrictedrealtrscaledearnings24 <- predict(realtrscaledearnings24, newdata=ahead24test24)
#TRCAPE
unrestrictedTRCAPE1 <- predict(TRCAPE1, newdata=ahead1test1)
unrestrictedTRCAPE2 <- predict(TRCAPE2, newdata=ahead2test2)
unrestrictedTRCAPE3 <- predict(TRCAPE3, newdata=ahead3test3)
unrestrictedTRCAPE6 <- predict(TRCAPE6, newdata=ahead6test6)
unrestrictedTRCAPE12 <- predict(TRCAPE12, newdata=ahead12test12)
unrestrictedTRCAPE18 <- predict(TRCAPE18, newdata=ahead18test18)
unrestrictedTRCAPE24 <- predict(TRCAPE24, newdata=ahead24test24)
#RObustness MSPE 

#MSPE Ratio
#infl
as.numeric(MSPEinfl1ratio <- (((mean(unrestrictedinfl1 - ahead1test1$ahead1))^2) / ((mean(restricted1-ahead1test1$ahead1))^2)))
as.numeric(MSPEinfl2ratio <- (((mean(unrestrictedinfl2 - ahead2test2$ahead2))^2) / ((mean(restricted2-ahead2test2$ahead2))^2)))
as.numeric(MSPEinfl3ratio <- (((mean(unrestrictedinfl3 - ahead3test3$ahead3))^2) / ((mean(restricted3-ahead3test3$ahead3))^2)))
as.numeric(MSPEinfl6ratio <- (((mean(unrestrictedinfl6 - ahead6test6$ahead6))^2) / ((mean(restricted6-ahead6test6$ahead6))^2)))
as.numeric(MSPEinfl12ratio <- (((mean(unrestrictedinfl12 - ahead12test12$ahead12))^2) / ((mean(restricted12-ahead12test12$ahead12))^2)))
as.numeric(MSPEinfl18ratio <- (((mean(unrestrictedinfl18 - ahead18test18$ahead18))^2) / ((mean(restricted18-ahead18test18$ahead18))^2)))
as.numeric(MSPEinfl24ratio <- (((mean(unrestrictedinfl24 - ahead24test24$ahead24))^2) / ((mean(restricted24-ahead24test24$ahead24))^2)))

inflMSPE <- c(MSPEinfl1ratio,MSPEinfl2ratio,MSPEinfl3ratio,MSPEinfl6ratio,
              MSPEinfl12ratio,MSPEinfl18ratio,MSPEinfl24ratio)

#realdividend
as.numeric(MSPErealdividend1ratio <- (((mean(unrestrictedrealdividend1 - ahead1test1$ahead1))^2) / ((mean(restricted1-ahead1test1$ahead1))^2)))
as.numeric(MSPErealdividend2ratio <- (((mean(unrestrictedrealdividend2 - ahead2test2$ahead2))^2) / ((mean(restricted2-ahead2test2$ahead2))^2)))
as.numeric(MSPErealdividend3ratio <- (((mean(unrestrictedrealdividend3 - ahead3test3$ahead3))^2) / ((mean(restricted3-ahead3test3$ahead3))^2)))
as.numeric(MSPErealdividend6ratio <- (((mean(unrestrictedrealdividend6 - ahead6test6$ahead6))^2) / ((mean(restricted6-ahead6test6$ahead6))^2)))
as.numeric(MSPErealdividend12ratio <- (((mean(unrestrictedrealdividend12 - ahead12test12$ahead12))^2) / ((mean(restricted12-ahead12test12$ahead12))^2)))
as.numeric(MSPErealdividend18ratio <- (((mean(unrestrictedrealdividend18 - ahead18test18$ahead18))^2) / ((mean(restricted18-ahead18test18$ahead18))^2)))
as.numeric(MSPErealdividend24ratio <- (((mean(unrestrictedrealdividend24 - ahead24test24$ahead24))^2) / ((mean(restricted24-ahead24test24$ahead24))^2)))

realdividendMSPE <- c(MSPErealdividend1ratio,MSPErealdividend2ratio,MSPErealdividend3ratio,MSPErealdividend6ratio,
                      MSPErealdividend12ratio,MSPErealdividend18ratio,MSPErealdividend24ratio)

as.numeric(MSPElrir101ratio <- (((mean(unrestrictedlrir101 - ahead1test1$ahead1))^2) / ((mean(restricted1-ahead1test1$ahead1))^2)))
as.numeric(MSPElrir102ratio <- (((mean(unrestrictedlrir102 - ahead2test2$ahead2))^2) / ((mean(restricted2-ahead2test2$ahead2))^2)))
as.numeric(MSPElrir103ratio <- (((mean(unrestrictedlrir103 - ahead3test3$ahead3))^2) / ((mean(restricted3-ahead3test3$ahead3))^2)))
as.numeric(MSPElrir106ratio <- (((mean(unrestrictedlrir106 - ahead6test6$ahead6))^2) / ((mean(restricted6-ahead6test6$ahead6))^2)))
as.numeric(MSPElrir1012ratio <- (((mean(unrestrictedlrir1012 - ahead12test12$ahead12))^2) / ((mean(restricted12-ahead12test12$ahead12))^2)))
as.numeric(MSPElrir1018ratio <- (((mean(unrestrictedlrir1018 - ahead18test18$ahead18))^2) / ((mean(restricted18-ahead18test18$ahead18))^2)))
as.numeric(MSPElrir1024ratio <- (((mean(unrestrictedlrir1024 - ahead24test24$ahead24))^2) / ((mean(restricted24-ahead24test24$ahead24))^2)))

lrir10MSPE <- c(MSPElrir101ratio,MSPElrir102ratio,MSPElrir103ratio,MSPElrir106ratio,
                MSPElrir1012ratio,MSPElrir1018ratio,MSPElrir1024ratio)
#realbond
as.numeric(MSPErealbond1ratio <- (((mean(unrestrictedrealbond1 - ahead1test1$ahead1))^2) / ((mean(restricted1-ahead1test1$ahead1))^2)))
as.numeric(MSPErealbond2ratio <- (((mean(unrestrictedrealbond2 - ahead2test2$ahead2))^2) / ((mean(restricted2-ahead2test2$ahead2))^2)))
as.numeric(MSPErealbond3ratio <- (((mean(unrestrictedrealbond3 - ahead3test3$ahead3))^2) / ((mean(restricted3-ahead3test3$ahead3))^2)))
as.numeric(MSPErealbond6ratio <- (((mean(unrestrictedrealbond6 - ahead6test6$ahead6))^2) / ((mean(restricted6-ahead6test6$ahead6))^2)))
as.numeric(MSPErealbond12ratio <- (((mean(unrestrictedrealbond12 - ahead12test12$ahead12))^2) / ((mean(restricted12-ahead12test12$ahead12))^2)))
as.numeric(MSPErealbond18ratio <- (((mean(unrestrictedrealbond18 - ahead18test18$ahead18))^2) / ((mean(restricted18-ahead18test18$ahead18))^2)))
as.numeric(MSPErealbond24ratio <- (((mean(unrestrictedrealbond24 - ahead24test24$ahead24))^2) / ((mean(restricted24-ahead24test24$ahead24))^2)))

realbondMSPE <- c(MSPErealbond1ratio,MSPErealbond2ratio,MSPErealbond3ratio,MSPErealbond6ratio,
                  MSPErealbond12ratio,MSPErealbond18ratio,MSPErealbond24ratio)
#realtotalreturn
as.numeric(MSPErealtotalreturn1ratio <- (((mean(unrestrictedrealtotalreturn1 - ahead1test1$ahead1))^2) / ((mean(restricted1-ahead1test1$ahead1))^2)))
as.numeric(MSPErealtotalreturn2ratio <- (((mean(unrestrictedrealtotalreturn2 - ahead2test2$ahead2))^2) / ((mean(restricted2-ahead2test2$ahead2))^2)))
as.numeric(MSPErealtotalreturn3ratio <- (((mean(unrestrictedrealtotalreturn3 - ahead3test3$ahead3))^2) / ((mean(restricted3-ahead3test3$ahead3))^2)))
as.numeric(MSPErealtotalreturn6ratio <- (((mean(unrestrictedrealtotalreturn6 - ahead6test6$ahead6))^2) / ((mean(restricted6-ahead6test6$ahead6))^2)))
as.numeric(MSPErealtotalreturn12ratio <- (((mean(unrestrictedrealtotalreturn12 - ahead12test12$ahead12))^2) / ((mean(restricted12-ahead12test12$ahead12))^2)))
as.numeric(MSPErealtotalreturn18ratio <- (((mean(unrestrictedrealtotalreturn18 - ahead18test18$ahead18))^2) / ((mean(restricted18-ahead18test18$ahead18))^2)))
as.numeric(MSPErealtotalreturn24ratio <- (((mean(unrestrictedrealtotalreturn24 - ahead24test24$ahead24))^2) / ((mean(restricted24-ahead24test24$ahead24))^2)))

realtotalreturnMSPE <- c(MSPErealtotalreturn1ratio,MSPErealtotalreturn2ratio,MSPErealtotalreturn3ratio,MSPErealtotalreturn6ratio,
                         MSPErealtotalreturn12ratio,MSPErealtotalreturn18ratio,MSPErealtotalreturn24ratio)
#realtrscaledearnings
as.numeric(MSPErealtrscaledearnings1ratio <- (((mean(unrestrictedrealtrscaledearnings1 - ahead1test1$ahead1))^2) / ((mean(restricted1-ahead1test1$ahead1))^2)))
as.numeric(MSPErealtrscaledearnings2ratio <- (((mean(unrestrictedrealtrscaledearnings2 - ahead2test2$ahead2))^2) / ((mean(restricted2-ahead2test2$ahead2))^2)))
as.numeric(MSPErealtrscaledearnings3ratio <- (((mean(unrestrictedrealtrscaledearnings3 - ahead3test3$ahead3))^2) / ((mean(restricted3-ahead3test3$ahead3))^2)))
as.numeric(MSPErealtrscaledearnings6ratio <- (((mean(unrestrictedrealtrscaledearnings6 - ahead6test6$ahead6))^2) / ((mean(restricted6-ahead6test6$ahead6))^2)))
as.numeric(MSPErealtrscaledearnings12ratio <- (((mean(unrestrictedrealtrscaledearnings12 - ahead12test12$ahead12))^2) / ((mean(restricted12-ahead12test12$ahead12))^2)))
as.numeric(MSPErealtrscaledearnings18ratio <- (((mean(unrestrictedrealtrscaledearnings18 - ahead18test18$ahead18))^2) / ((mean(restricted18-ahead18test18$ahead18))^2)))
as.numeric(MSPErealtrscaledearnings24ratio <- (((mean(unrestrictedrealtrscaledearnings24 - ahead24test24$ahead24))^2) / ((mean(restricted24-ahead24test24$ahead24))^2)))

realtrscaledearningsMSPE <- c(MSPErealtrscaledearnings1ratio,MSPErealtrscaledearnings2ratio,MSPErealtrscaledearnings3ratio,MSPErealtrscaledearnings6ratio,
                              MSPErealtrscaledearnings12ratio,MSPErealtrscaledearnings18ratio,MSPErealtrscaledearnings24ratio)
#TRCAPE
as.numeric(MSPETRCAPE1ratio <- (((mean(unrestrictedTRCAPE1 - ahead1test1$ahead1))^2) / ((mean(restricted1-ahead1test1$ahead1))^2)))
as.numeric(MSPETRCAPE2ratio <- (((mean(unrestrictedTRCAPE2 - ahead2test2$ahead2))^2) / ((mean(restricted2-ahead2test2$ahead2))^2)))
as.numeric(MSPETRCAPE3ratio <- (((mean(unrestrictedTRCAPE3 - ahead3test3$ahead3))^2) / ((mean(restricted3-ahead3test3$ahead3))^2)))
as.numeric(MSPETRCAPE6ratio <- (((mean(unrestrictedTRCAPE6 - ahead6test6$ahead6))^2) / ((mean(restricted6-ahead6test6$ahead6))^2)))
as.numeric(MSPETRCAPE12ratio <- (((mean(unrestrictedTRCAPE12 - ahead12test12$ahead12))^2) / ((mean(restricted12-ahead12test12$ahead12))^2)))
as.numeric(MSPETRCAPE18ratio <- (((mean(unrestrictedTRCAPE18 - ahead18test18$ahead18))^2) / ((mean(restricted18-ahead18test18$ahead18))^2)))
as.numeric(MSPETRCAPE24ratio <- (((mean(unrestrictedTRCAPE24 - ahead24test24$ahead24))^2) / ((mean(restricted24-ahead24test24$ahead24))^2)))

TRCAPEMSPE <- c(MSPETRCAPE1ratio,MSPETRCAPE2ratio,MSPETRCAPE3ratio,MSPETRCAPE6ratio,
                MSPETRCAPE12ratio,MSPETRCAPE18ratio,MSPETRCAPE24ratio)

inflMSPEbc <- round(inflMSPE, digits = 3)
realdividendMSPEbc <- round(realdividendMSPE, digits=3)
lrir10MSPEbc <- round(lrir10MSPE, digits=3)
realbondMSPEbc <- round(realbondMSPE, digits=3)
realtotalreturnMSPEbc <- round(realtotalreturnMSPE, digits=3)
realtrscaledearningsMSPEbc <- round(realtrscaledearningsMSPE, digits=3)
TRCAPEMSPEbc <- round(TRCAPEMSPE, digits=3)

MSPEbc <- rbind(inflMSPEbc, realdividendMSPEbc, lrir10MSPEbc,realbondMSPEbc,
              realtotalreturnMSPEbc,realtrscaledearningsMSPEbc, TRCAPEMSPEbc)

meanMSPEbc <- mean(c(inflMSPE, realdividendMSPE, lrir10MSPE,realbondMSPE,
                   realtotalreturnMSPE,realtrscaledearningsMSPE, TRCAPEMSPE))
print(meanMSPEbc)
Horizons <- c("k=1","k=2","k=3","k=6","k=12","k=18","k=24")
# Set the column names of the MSPE matrix

MSPEbc <- rbind(Horizons,inflMSPEbc, realdividendMSPEbc, lrir10MSPEbc,realbondMSPEbc,
              realtotalreturnMSPEbc,realtrscaledearningsMSPEbc, TRCAPEMSPEbc)
rownames(MSPEbc) <- c("Horizon","CPI","Real Dividend","Long Range Interest","Real Bond"
                    ,"Real Total Return","TR Scaled Earnings","TR CAPE")
MSPEbc

stargazer(MSPEbc, type="text", out = "MSPEOLSbc.html")


########################################################################################
########################################################################################
########################################################################################
########################################################################################
########################################################################################
########################################################################################

start_values <- c(coefficients = c(0, 0), phi = 1)

bintercept1<- betareg(ahead1 ~ 1, data=ahead1train1)
bintercept2<- betareg(ahead2 ~ 1, data=ahead2train2)
bintercept3<- betareg(ahead3 ~ 1, data=ahead3train3)
bintercept6<- betareg(ahead6 ~ 1, data=ahead6train6)
bintercept12<- betareg(ahead12 ~ 1, data=ahead12train12)
bintercept18<- betareg(ahead18 ~ 1, data=ahead18train18)
bintercept24<- betareg(ahead24 ~ 1, data=ahead24train24)

binfl1<- betareg(ahead1 ~ infl, data=ahead1train1, start = start_values)
binfl2<- betareg(ahead2 ~ infl, data=ahead2train2, start = start_values)
binfl3<- betareg(ahead3 ~ infl, data=ahead3train3, start = start_values)
binfl6<- betareg(ahead6 ~ infl, data=ahead6train6, start = start_values)
binfl12<- betareg(ahead12 ~ infl, data=ahead12train12, start = start_values)
binfl18<- betareg(ahead18 ~ infl, data=ahead18train18, start = start_values)
binfl24<- betareg(ahead24 ~ infl, data=ahead24train24, start = start_values)

blrir101<- betareg(ahead1 ~ lrir10, data=ahead1train1, start = start_values)
blrir102<- betareg(ahead2 ~ lrir10, data=ahead2train2, start = start_values)
blrir103<- betareg(ahead3 ~ lrir10, data=ahead3train3, start = start_values)
blrir106<- betareg(ahead6 ~ lrir10, data=ahead6train6, start = start_values)
blrir1012<- betareg(ahead12 ~ lrir10, data=ahead12train12, start = start_values)
blrir1018<- betareg(ahead18 ~ lrir10, data=ahead18train18, start = start_values)
blrir1024<- betareg(ahead24 ~ lrir10, data=ahead24train24, start = start_values)

brealdividend1<- betareg(ahead1 ~ realdividend, data=ahead1train1, start = start_values)
brealdividend2<- betareg(ahead2 ~ realdividend, data=ahead2train2, start = start_values)
brealdividend3<- betareg(ahead3 ~ realdividend, data=ahead3train3, start = start_values)
brealdividend6<- betareg(ahead6 ~ realdividend, data=ahead6train6, start = start_values)
brealdividend12<- betareg(ahead12 ~ realdividend, data=ahead12train12, start = start_values)
brealdividend18<- betareg(ahead18 ~ realdividend, data=ahead18train18, start = start_values)
brealdividend24<- betareg(ahead24 ~ realdividend, data=ahead24train24, start = start_values)

brealbond1<- betareg(ahead1 ~ realbond, data=ahead1train1, start = start_values)
brealbond2<- betareg(ahead2 ~ realbond, data=ahead2train2, start = start_values)
brealbond3<- betareg(ahead3 ~ realbond, data=ahead3train3, start = start_values)
brealbond6<- betareg(ahead6 ~ realbond, data=ahead6train6, start = start_values)
brealbond12<- betareg(ahead12 ~ realbond, data=ahead12train12, start = start_values)
brealbond18<- betareg(ahead18 ~ realbond, data=ahead18train18, start = start_values)
brealbond24<- betareg(ahead24 ~ realbond, data=ahead24train24, start = start_values)

brealtotalreturn1<- betareg(ahead1 ~ realtotalreturn, data=ahead1train1, start = start_values)
brealtotalreturn2<- betareg(ahead2 ~ realtotalreturn, data=ahead2train2, start = start_values)
brealtotalreturn3<- betareg(ahead3 ~ realtotalreturn, data=ahead3train3, start = start_values)
brealtotalreturn6<- betareg(ahead6 ~ realtotalreturn, data=ahead6train6, start = start_values)
brealtotalreturn12<- betareg(ahead12 ~ realtotalreturn, data=ahead12train12, start = start_values)
brealtotalreturn18<- betareg(ahead18 ~ realtotalreturn, data=ahead18train18, start = start_values)
brealtotalreturn24<- betareg(ahead24 ~ realtotalreturn, data=ahead24train24, start = start_values)

brealtrscaledearnings1<- betareg(ahead1 ~ realtrscaledearnings, data=ahead1train1, start = start_values)
brealtrscaledearnings2<- betareg(ahead2 ~ realtrscaledearnings, data=ahead2train2, start = start_values)
brealtrscaledearnings3<- betareg(ahead3 ~ realtrscaledearnings, data=ahead3train3, start = start_values)
brealtrscaledearnings6<- betareg(ahead6 ~ realtrscaledearnings, data=ahead6train6, start = start_values)
brealtrscaledearnings12<- betareg(ahead12 ~ realtrscaledearnings, data=ahead12train12, start = start_values)
brealtrscaledearnings18<- betareg(ahead18 ~ realtrscaledearnings, data=ahead18train18, start = start_values)
brealtrscaledearnings24<- betareg(ahead24 ~ realtrscaledearnings, data=ahead24train24, start = start_values)

bTRCAPE1<- betareg(ahead1 ~ TRCAPE, data=ahead1train1, start = start_values)
bTRCAPE2<- betareg(ahead2 ~ TRCAPE, data=ahead2train2, start = start_values)
bTRCAPE3<- betareg(ahead3 ~ TRCAPE, data=ahead3train3, start = start_values)
bTRCAPE6<- betareg(ahead6 ~ TRCAPE, data=ahead6train6, start = start_values)
bTRCAPE12<- betareg(ahead12 ~ TRCAPE, data=ahead12train12, start = start_values)
bTRCAPE18<- betareg(ahead18 ~ TRCAPE, data=ahead18train18, start = start_values)
bTRCAPE24<- betareg(ahead24 ~ TRCAPE, data=ahead24train24, start = start_values)
#predictions
brestricted1 <- predict(bintercept1, newdata=ahead1test1)
brestricted2 <- predict(bintercept2, newdata=ahead2test2)
brestricted3 <- predict(bintercept3, newdata=ahead3test3)
brestricted6 <- predict(bintercept6, newdata=ahead6test6)
brestricted12 <- predict(bintercept12, newdata=ahead12test12)
brestricted18 <- predict(bintercept18, newdata=ahead18test18)
brestricted24 <- predict(bintercept24, newdata=ahead24test24)
#predictions
bunrestrictedinfl1 <- predict(binfl1, newdata=ahead1test1)
bunrestrictedinfl2 <- predict(binfl2, newdata=ahead2test2)
bunrestrictedinfl3 <- predict(binfl3, newdata=ahead3test3)
bunrestrictedinfl6 <- predict(binfl6, newdata=ahead6test6)
bunrestrictedinfl12 <- predict(binfl12, newdata=ahead12test12)
bunrestrictedinfl18 <- predict(binfl18, newdata=ahead18test18)
bunrestrictedinfl24 <- predict(binfl24, newdata=ahead24test24)
#realdividend
bunrestrictedrealdividend1 <- predict(brealdividend1, newdata=ahead1test1)
bunrestrictedrealdividend2 <- predict(brealdividend2, newdata=ahead2test2)
bunrestrictedrealdividend3 <- predict(brealdividend3, newdata=ahead3test3)
bunrestrictedrealdividend6 <- predict(brealdividend6, newdata=ahead6test6)
bunrestrictedrealdividend12 <- predict(brealdividend12, newdata=ahead12test12)
bunrestrictedrealdividend18 <- predict(brealdividend18, newdata=ahead18test18)
bunrestrictedrealdividend24 <- predict(brealdividend24, newdata=ahead24test24)
#lrir10
bunrestrictedlrir101 <- predict(blrir101, newdata=ahead1test1)
bunrestrictedlrir102 <- predict(blrir102, newdata=ahead2test2)
bunrestrictedlrir103 <- predict(blrir103, newdata=ahead3test3)
bunrestrictedlrir106 <- predict(blrir106, newdata=ahead6test6)
bunrestrictedlrir1012 <- predict(blrir1012, newdata=ahead12test12)
bunrestrictedlrir1018 <- predict(blrir1018, newdata=ahead18test18)
bunrestrictedlrir1024 <- predict(blrir1024, newdata=ahead24test24)
#realdividend
bunrestrictedrealdividend1 <- predict(brealdividend1, newdata=ahead1test1)
bunrestrictedrealdividend2 <- predict(brealdividend2, newdata=ahead2test2)
bunrestrictedrealdividend3 <- predict(brealdividend3, newdata=ahead3test3)
bunrestrictedrealdividend6 <- predict(brealdividend6, newdata=ahead6test6)
bunrestrictedrealdividend12 <- predict(brealdividend12, newdata=ahead12test12)
bunrestrictedrealdividend18 <- predict(brealdividend18, newdata=ahead18test18)
bunrestrictedrealdividend24 <- predict(brealdividend24, newdata=ahead24test24)
#realbond
bunrestrictedrealbond1 <- predict(brealbond1, newdata=ahead1test1)
bunrestrictedrealbond2 <- predict(brealbond2, newdata=ahead2test2)
bunrestrictedrealbond3 <- predict(brealbond3, newdata=ahead3test3)
bunrestrictedrealbond6 <- predict(brealbond6, newdata=ahead6test6)
bunrestrictedrealbond12 <- predict(brealbond12, newdata=ahead12test12)
bunrestrictedrealbond18 <- predict(brealbond18, newdata=ahead18test18)
bunrestrictedrealbond24 <- predict(brealbond24, newdata=ahead24test24)
#realtotalreturn
bunrestrictedrealtotalreturn1 <- predict(brealtotalreturn1, newdata=ahead1test1)
bunrestrictedrealtotalreturn2 <- predict(brealtotalreturn2, newdata=ahead2test2)
bunrestrictedrealtotalreturn3 <- predict(brealtotalreturn3, newdata=ahead3test3)
bunrestrictedrealtotalreturn6 <- predict(brealtotalreturn6, newdata=ahead6test6)
bunrestrictedrealtotalreturn12 <- predict(brealtotalreturn12, newdata=ahead12test12)
bunrestrictedrealtotalreturn18 <- predict(brealtotalreturn18, newdata=ahead18test18)
bunrestrictedrealtotalreturn24 <- predict(brealtotalreturn24, newdata=ahead24test24)
#realtrscaledearnings
bunrestrictedrealtrscaledearnings1 <- predict(brealtrscaledearnings1, newdata=ahead1test1)
bunrestrictedrealtrscaledearnings2 <- predict(brealtrscaledearnings2, newdata=ahead2test2)
bunrestrictedrealtrscaledearnings3 <- predict(brealtrscaledearnings3, newdata=ahead3test3)
bunrestrictedrealtrscaledearnings6 <- predict(brealtrscaledearnings6, newdata=ahead6test6)
bunrestrictedrealtrscaledearnings12 <- predict(brealtrscaledearnings12, newdata=ahead12test12)
bunrestrictedrealtrscaledearnings18 <- predict(brealtrscaledearnings18, newdata=ahead18test18)
bunrestrictedrealtrscaledearnings24 <- predict(brealtrscaledearnings24, newdata=ahead24test24)
#TRCAPE
bunrestrictedTRCAPE1 <- predict(bTRCAPE1, newdata=ahead1test1)
bunrestrictedTRCAPE2 <- predict(bTRCAPE2, newdata=ahead2test2)
bunrestrictedTRCAPE3 <- predict(bTRCAPE3, newdata=ahead3test3)
bunrestrictedTRCAPE6 <- predict(bTRCAPE6, newdata=ahead6test6)
bunrestrictedTRCAPE12 <- predict(bTRCAPE12, newdata=ahead12test12)
bunrestrictedTRCAPE18 <- predict(bTRCAPE18, newdata=ahead18test18)
bunrestrictedTRCAPE24 <- predict(bTRCAPE24, newdata=ahead24test24)
#RObustness MSPE 

#MSPE Ratio
#infl
as.numeric(bMSPEinfl1ratio <- (((mean(bunrestrictedinfl1 - ahead1test1$ahead1))^2) / ((mean(brestricted1-ahead1test1$ahead1))^2)))
as.numeric(bMSPEinfl2ratio <- (((mean(bunrestrictedinfl2 - ahead2test2$ahead2))^2) / ((mean(brestricted2-ahead2test2$ahead2))^2)))
as.numeric(bMSPEinfl3ratio <- (((mean(bunrestrictedinfl3 - ahead3test3$ahead3))^2) / ((mean(brestricted3-ahead3test3$ahead3))^2)))
as.numeric(bMSPEinfl6ratio <- (((mean(bunrestrictedinfl6 - ahead6test6$ahead6))^2) / ((mean(brestricted6-ahead6test6$ahead6))^2)))
as.numeric(bMSPEinfl12ratio <- (((mean(bunrestrictedinfl12 - ahead12test12$ahead12))^2) / ((mean(brestricted12-ahead12test12$ahead12))^2)))
as.numeric(bMSPEinfl18ratio <- (((mean(bunrestrictedinfl18 - ahead18test18$ahead18))^2) / ((mean(brestricted18-ahead18test18$ahead18))^2)))
as.numeric(bMSPEinfl24ratio <- (((mean(bunrestrictedinfl24 - ahead24test24$ahead24))^2) / ((mean(brestricted24-ahead24test24$ahead24))^2)))

binflMSPE <- c(bMSPEinfl1ratio,bMSPEinfl2ratio,bMSPEinfl3ratio,bMSPEinfl6ratio,
               bMSPEinfl12ratio,bMSPEinfl18ratio,bMSPEinfl24ratio)

#realdividend
as.numeric(bMSPErealdividend1ratio <- (((mean( bunrestrictedrealdividend1 - ahead1test1$ahead1))^2) / ((mean( brestricted1-ahead1test1$ahead1))^2)))
as.numeric(bMSPErealdividend2ratio <- (((mean( bunrestrictedrealdividend2 - ahead2test2$ahead2))^2) / ((mean( brestricted2-ahead2test2$ahead2))^2)))
as.numeric(bMSPErealdividend3ratio <- (((mean( bunrestrictedrealdividend3 - ahead3test3$ahead3))^2) / ((mean( brestricted3-ahead3test3$ahead3))^2)))
as.numeric(bMSPErealdividend6ratio <- (((mean( bunrestrictedrealdividend6 - ahead6test6$ahead6))^2) / ((mean( brestricted6-ahead6test6$ahead6))^2)))
as.numeric(bMSPErealdividend12ratio <- (((mean( bunrestrictedrealdividend12 - ahead12test12$ahead12))^2) / ((mean( brestricted12-ahead12test12$ahead12))^2)))
as.numeric(bMSPErealdividend18ratio <- (((mean( bunrestrictedrealdividend18 - ahead18test18$ahead18))^2) / ((mean( brestricted18-ahead18test18$ahead18))^2)))
as.numeric(bMSPErealdividend24ratio <- (((mean( bunrestrictedrealdividend24 - ahead24test24$ahead24))^2) / ((mean( brestricted24-ahead24test24$ahead24))^2)))

brealdividendMSPE <- c(bMSPErealdividend1ratio,bMSPErealdividend2ratio,bMSPErealdividend3ratio,bMSPErealdividend6ratio,
                       bMSPErealdividend12ratio,bMSPErealdividend18ratio,bMSPErealdividend24ratio)

as.numeric(bMSPElrir101ratio <- (((mean(bunrestrictedlrir101 - ahead1test1$ahead1))^2) / ((mean(brestricted1-ahead1test1$ahead1))^2)))
as.numeric(bMSPElrir102ratio <- (((mean(bunrestrictedlrir102 - ahead2test2$ahead2))^2) / ((mean(brestricted2-ahead2test2$ahead2))^2)))
as.numeric(bMSPElrir103ratio <- (((mean(bunrestrictedlrir103 - ahead3test3$ahead3))^2) / ((mean(brestricted3-ahead3test3$ahead3))^2)))
as.numeric(bMSPElrir106ratio <- (((mean(bunrestrictedlrir106 - ahead6test6$ahead6))^2) / ((mean(brestricted6-ahead6test6$ahead6))^2)))
as.numeric(bMSPElrir1012ratio <- (((mean(bunrestrictedlrir1012 - ahead12test12$ahead12))^2) / ((mean(brestricted12-ahead12test12$ahead12))^2)))
as.numeric(bMSPElrir1018ratio <- (((mean(bunrestrictedlrir1018 - ahead18test18$ahead18))^2) / ((mean(brestricted18-ahead18test18$ahead18))^2)))
as.numeric(bMSPElrir1024ratio <- (((mean(bunrestrictedlrir1024 - ahead24test24$ahead24))^2) / ((mean(brestricted24-ahead24test24$ahead24))^2)))

blrir10MSPE <- c(bMSPElrir101ratio,bMSPElrir102ratio,bMSPElrir103ratio,bMSPElrir106ratio,
                 bMSPElrir1012ratio,bMSPElrir1018ratio,bMSPElrir1024ratio)
#realbond
as.numeric(bMSPErealbond1ratio <- (((mean(bunrestrictedrealbond1 - ahead1test1$ahead1))^2) / ((mean(brestricted1-ahead1test1$ahead1))^2)))
as.numeric(bMSPErealbond2ratio <- (((mean(bunrestrictedrealbond2 - ahead2test2$ahead2))^2) / ((mean(brestricted2-ahead2test2$ahead2))^2)))
as.numeric(bMSPErealbond3ratio <- (((mean(bunrestrictedrealbond3 - ahead3test3$ahead3))^2) / ((mean(brestricted3-ahead3test3$ahead3))^2)))
as.numeric(bMSPErealbond6ratio <- (((mean(bunrestrictedrealbond6 - ahead6test6$ahead6))^2) / ((mean(brestricted6-ahead6test6$ahead6))^2)))
as.numeric(bMSPErealbond12ratio <- (((mean(bunrestrictedrealbond12 - ahead12test12$ahead12))^2) / ((mean(brestricted12-ahead12test12$ahead12))^2)))
as.numeric(bMSPErealbond18ratio <- (((mean(bunrestrictedrealbond18 - ahead18test18$ahead18))^2) / ((mean(brestricted18-ahead18test18$ahead18))^2)))
as.numeric(bMSPErealbond24ratio <- (((mean(bunrestrictedrealbond24 - ahead24test24$ahead24))^2) / ((mean(brestricted24-ahead24test24$ahead24))^2)))

brealbondMSPE <- c(bMSPErealbond1ratio,bMSPErealbond2ratio,bMSPErealbond3ratio,bMSPErealbond6ratio,
                   bMSPErealbond12ratio,bMSPErealbond18ratio,bMSPErealbond24ratio)
#realtotalreturn
as.numeric(bMSPErealtotalreturn1ratio <- (((mean(bunrestrictedrealtotalreturn1 - ahead1test1$ahead1))^2) / ((mean(brestricted1-ahead1test1$ahead1))^2)))
as.numeric(bMSPErealtotalreturn2ratio <- (((mean(bunrestrictedrealtotalreturn2 - ahead2test2$ahead2))^2) / ((mean(brestricted2-ahead2test2$ahead2))^2)))
as.numeric(bMSPErealtotalreturn3ratio <- (((mean(bunrestrictedrealtotalreturn3 - ahead3test3$ahead3))^2) / ((mean(brestricted3-ahead3test3$ahead3))^2)))
as.numeric(bMSPErealtotalreturn6ratio <- (((mean(bunrestrictedrealtotalreturn6 - ahead6test6$ahead6))^2) / ((mean(brestricted6-ahead6test6$ahead6))^2)))
as.numeric(bMSPErealtotalreturn12ratio <- (((mean(bunrestrictedrealtotalreturn12 - ahead12test12$ahead12))^2) / ((mean(brestricted12-ahead12test12$ahead12))^2)))
as.numeric(bMSPErealtotalreturn18ratio <- (((mean(bunrestrictedrealtotalreturn18 - ahead18test18$ahead18))^2) / ((mean(brestricted18-ahead18test18$ahead18))^2)))
as.numeric(bMSPErealtotalreturn24ratio <- (((mean(bunrestrictedrealtotalreturn24 - ahead24test24$ahead24))^2) / ((mean(brestricted24-ahead24test24$ahead24))^2)))

brealtotalreturnMSPE <- c(bMSPErealtotalreturn1ratio,bMSPErealtotalreturn2ratio,bMSPErealtotalreturn3ratio,bMSPErealtotalreturn6ratio,
                          bMSPErealtotalreturn12ratio,bMSPErealtotalreturn18ratio,bMSPErealtotalreturn24ratio)
#realtrscaledearnings
as.numeric(bMSPErealtrscaledearnings1ratio <- (((mean(bunrestrictedrealtrscaledearnings1 - ahead1test1$ahead1))^2) / ((mean(brestricted1-ahead1test1$ahead1))^2)))
as.numeric(bMSPErealtrscaledearnings2ratio <- (((mean(bunrestrictedrealtrscaledearnings2 - ahead2test2$ahead2))^2) / ((mean(brestricted2-ahead2test2$ahead2))^2)))
as.numeric(bMSPErealtrscaledearnings3ratio <- (((mean(bunrestrictedrealtrscaledearnings3 - ahead3test3$ahead3))^2) / ((mean(brestricted3-ahead3test3$ahead3))^2)))
as.numeric(bMSPErealtrscaledearnings6ratio <- (((mean(bunrestrictedrealtrscaledearnings6 - ahead6test6$ahead6))^2) / ((mean(brestricted6-ahead6test6$ahead6))^2)))
as.numeric(bMSPErealtrscaledearnings12ratio <- (((mean(bunrestrictedrealtrscaledearnings12 - ahead12test12$ahead12))^2) / ((mean(brestricted12-ahead12test12$ahead12))^2)))
as.numeric(bMSPErealtrscaledearnings18ratio <- (((mean(bunrestrictedrealtrscaledearnings18 - ahead18test18$ahead18))^2) / ((mean(brestricted18-ahead18test18$ahead18))^2)))
as.numeric(bMSPErealtrscaledearnings24ratio <- (((mean(bunrestrictedrealtrscaledearnings24 - ahead24test24$ahead24))^2) / ((mean(brestricted24-ahead24test24$ahead24))^2)))

brealtrscaledearningsMSPE <- c(bMSPErealtrscaledearnings1ratio,bMSPErealtrscaledearnings2ratio,bMSPErealtrscaledearnings3ratio,bMSPErealtrscaledearnings6ratio,
                               bMSPErealtrscaledearnings12ratio,bMSPErealtrscaledearnings18ratio,bMSPErealtrscaledearnings24ratio)
#TRCAPE
as.numeric(bMSPETRCAPE1ratio <- (((mean(bunrestrictedTRCAPE1 - ahead1test1$ahead1))^2) / ((mean(brestricted1-ahead1test1$ahead1))^2)))
as.numeric(bMSPETRCAPE2ratio <- (((mean(bunrestrictedTRCAPE2 - ahead2test2$ahead2))^2) / ((mean(brestricted2-ahead2test2$ahead2))^2)))
as.numeric(bMSPETRCAPE3ratio <- (((mean(bunrestrictedTRCAPE3 - ahead3test3$ahead3))^2) / ((mean(brestricted3-ahead3test3$ahead3))^2)))
as.numeric(bMSPETRCAPE6ratio <- (((mean(bunrestrictedTRCAPE6 - ahead6test6$ahead6))^2) / ((mean(brestricted6-ahead6test6$ahead6))^2)))
as.numeric(bMSPETRCAPE12ratio <- (((mean(bunrestrictedTRCAPE12 - ahead12test12$ahead12))^2) / ((mean(brestricted12-ahead12test12$ahead12))^2)))
as.numeric(bMSPETRCAPE18ratio <- (((mean(bunrestrictedTRCAPE18 - ahead18test18$ahead18))^2) / ((mean(brestricted18-ahead18test18$ahead18))^2)))
as.numeric(bMSPETRCAPE24ratio <- (((mean(bunrestrictedTRCAPE24 - ahead24test24$ahead24))^2) / ((mean(brestricted24-ahead24test24$ahead24))^2)))

bTRCAPEMSPE <- c(bMSPETRCAPE1ratio,bMSPETRCAPE2ratio,bMSPETRCAPE3ratio,bMSPETRCAPE6ratio,
                 bMSPETRCAPE12ratio,bMSPETRCAPE18ratio,bMSPETRCAPE24ratio)

binflMSPEbc <- round(binflMSPE, digits = 3)
brealdividendMSPEbc <- round(brealdividendMSPE, digits=3)
blrir10MSPEbc <- round(blrir10MSPE, digits=3)
brealbondMSPEbc <- round(brealbondMSPE, digits=3)
brealtotalreturnMSPEbc <- round(brealtotalreturnMSPE, digits=3)
brealtrscaledearningsMSPEbc <- round(brealtrscaledearningsMSPE, digits=3)
bTRCAPEMSPEbc <- round(bTRCAPEMSPE, digits=3)

bMSPEbc <- rbind(binflMSPEbc, brealdividendMSPEbc, blrir10MSPEbc,brealbondMSPEbc,
               brealtotalreturnMSPEbc,brealtrscaledearningsMSPEbc, bTRCAPEMSPEbc)
meanbMSPEbc <- mean(c(binflMSPEbc, brealdividendMSPEbc, blrir10MSPEbc,brealbondMSPEbc,
                      brealtotalreturnMSPEbc,brealtrscaledearningsMSPEbc, bTRCAPEMSPEbc))
print(bMSPEbc)
Horizons <- c("k=1","k=2","k=3","k=6","k=12","k=18","k=24")
# Set the column names of the MSPE matrix

bMSPEbc <- rbind(Horizons, binflMSPEbc, brealdividendMSPEbc, blrir10MSPEbc,brealbondMSPEbc,
               brealtotalreturnMSPEbc,brealtrscaledearningsMSPEbc, bTRCAPEMSPEbc)
rownames(bMSPEbc) <- c("Horizon","CPI","Real Dividend","Long Range Interest","Real Bond"
                     ,"Real Total Return","TR Scaled Earnings","TR CAPE")
bMSPEbc
print(meanbMSPEbc)
stargazer(bMSPEbc, type="text", out = "MSPEBETA101bc.html")

MSPEbc
print(meanMSPEbc)
stargazer(MSPEbc, type="text", out="MSPEOLS101bc.html")

bMSPE
print(meanbMSPE)
stargazer(bMSPE, type= "text")
stargazer(bMSPE, type="text", out="MSPEBETA.html")
MSPE
print(meanMSPE)
stargazer(MSPE, type="text", out="MSPEOLS.html")

stargazer(MSPE, type="text", out="MSPEfc.html")
stargazer(bMSPE, type="text", out="bMSPEfc.html")
stargazer(MSPEbc, type="text", out="MSPEbc.html")
stargazer(bMSPEbc, type="text", out="bMSPEbc.html")





combined_df <- ts(combined_df, start = c(1960, 01), end= c(2023, 12), frequency = 12)
plot(combined_df$infl, combined_df$lrir10, combined_df$realdividend, combined_df$realtrscaledearnings
, combined_df$TRCAPE, combined_df$realbond, combined_df$filterprobms2_regime1)
ts.plot(combined_dfts$infl)
ts.plot(combined_dfts$lrir10)
ts.plot(combined_dfts$realdividend)
ts.plot(combined_dfts$realtrscaledearnings)
ts.plot(combined_dfts$TRCAPE)
ts.plot(combined_dfts$realbond)
ts.plot(combined_dfts$filterprobms2_regime1)