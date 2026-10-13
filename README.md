# Predictive Stochastic Modeling for Financial Markets

## Introduction
Welcome to the repository for my undergraduate thesis, *Predictive Stochastic Modeling for Financial Markets*, which was honored with the **Adam Smith Award** for outstanding economic research. This project investigates how advanced financial and macroeconomic indicators can enhance the prediction of bear markets in the S&P 500 using state-of-the-art **Markov-switching autoregressive models** and **regression-based predictive techniques**.

By integrating **Bayesian inference**, **time-series econometrics**, and **machine learning-inspired forecasting**, this work provides deep insights into market downturn dynamics and contributes both to academic literature and to the development of practical investment strategies.

📄 **Read the full thesis here:** [Predictive Stochastic Modeling for Financial Markets](https://github.com/jadenfix/Predictive-Stochastic-Modeling-for-Financial-Markets-/blob/main/Predictive_Stochastic_Modeling_for_Financial_Markets.pdf)

---

## Project Overview
This repository contains the complete implementation of the predictive modeling framework, including:

- ✅ **Bayesian Markov-Switching Autoregressive Models** to estimate bear market probabilities.
- ✅ **OLS & Beta Regression-Based Predictive Modeling** for both in-sample and out-of-sample testing.
- ✅ **Feature Selection & Data Engineering** utilizing key stock market and macroeconomic indicators.
- ✅ **Robust Statistical Evaluation** of predictive accuracy across various forecasting horizons.

In addition, the project integrates reproducible research practices, offering comprehensive code, data, and documentation that collectively enable full replication of the study’s results.

---

## How to Explore the Project

- **Code Implementation:**  
  [Code Implementation (R)](https://github.com/jadenfix/Predictive-Stochastic-Modeling-for-Financial-Markets-/blob/main/code.R)

- **Dataset:**  
  [one45.csv](https://github.com/jadenfix/Predictive-Stochastic-Modeling-for-Financial-Markets-/blob/main/one45.csv)

Feel free to clone the repository and run the provided R scripts to reproduce the analysis and explore the predictive modeling framework.

---

## Why This Matters for Data Science & Finance
This project demonstrates advanced skills in **financial time-series modeling**, **Bayesian statistical analysis**, and **machine learning for prediction**—areas that are crucial for quantitative finance, risk management, and data science. The methodology not only advances theoretical understanding but also has practical applications in asset pricing, volatility forecasting, and algorithmic trading strategies.

### Key Skills Demonstrated:
- **Time-Series Forecasting:** Implementation of Markov-switching models, OLS, and Beta Regression techniques.
- **Bayesian Statistical Modeling:** Utilizing Bayesian inference and filtering techniques for dynamic regime estimation.
- **Financial & Macroeconomic Data Analysis:** Rigorous preprocessing and feature engineering using key indicators.
- **Predictive Analytics & Machine Learning Concepts:** Integration of modern forecasting methods into econometric modeling.
- **R Programming for Quantitative Finance:** Development of reproducible code for robust empirical analysis.

If you have any questions or would like to discuss the research further, please feel free to reach out. Let's connect and explore the exciting intersection of finance and data science! 🚀

## Original research reproduction

```bash
# Run from the repository root with R installed.
Rscript install_dependencies.R
Rscript run_research.R
```

The runner executes `code.R` with committed original data; pass an archived R filename as the first argument to select another script. Exploratory intermediate sections remain research artifacts. R was unavailable here, so package installation, convergence and complete outputs remain unverified. No replacement observations or estimators are supplied.
