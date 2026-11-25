# Predictive Analytics & Time Series Forecasting
## Machine Learning Architectures & Statistical Models

---

### 1. Purpose & Overview
Inslight's Forecasting Engine enables organizations to anticipate demand, revenue, and transaction volume over 7, 30, or 90 future time periods. It evaluates multiple machine learning and statistical models, selects the best-performing model based on cross-validation backtesting, and generates confidence intervals.

---

### 2. Supported Algorithms & Techniques

1. **Holt's Linear Exponential Smoothing:**
   - Level equation: $L_t = \alpha Y_t + (1 - \alpha)(L_{t-1} + b_{t-1})$
   - Trend equation: $b_t = \beta (L_t - L_{t-1}) + (1 - \beta) b_{t-1}$
   - Forecast equation: $\hat{Y}_{t+h} = L_t + h b_t$
   - Ideal for trended time-series with low volatility.

2. **Random Forest Regression (`scikit-learn`):**
   - Ensemble of decision trees trained on lag features ($Y_{t-1}, Y_{t-2}, Y_{t-3}$) and temporal features (day of week, day of month, month).
   - Robust against non-linear patterns and outliers.

3. **Linear Regression with Ridge Regularization:**
   - Evaluates trend slope with deterministic feature extrapolation.

4. **Moving Average (Baseline):**
   - Window-based rolling average used as a fallback and baseline comparator.

---

### 3. Evaluation Metrics & Model Selection
Models are evaluated on hold-out validation sets using:
- **MAE (Mean Absolute Error):** $\frac{1}{n} \sum |y_i - \hat{y}_i|$
- **RMSE (Root Mean Squared Error):** $\sqrt{\frac{1}{n} \sum (y_i - \hat{y}_i)^2}$
- **MAPE (Mean Absolute Percentage Error):** $\frac{100\%}{n} \sum |\frac{y_i - \hat{y}_i}{y_i}|$

The engine automatically selects the model minimizing MAPE on validation data.

---

### 4. 95% Confidence Intervals
Prediction intervals are calculated using residual standard deviation ($\sigma_e$):
$$\hat{Y}_{t+h} \pm 1.96 \times \sigma_e \times \sqrt{1 + \frac{h}{N}}$$
This provides upper and lower uncertainty bounds that widen as the horizon increases.

---

### 5. Guards & Data Requirements
- Minimum data threshold: At least 5 historical data points are required.
- Insufficient data triggers a clear diagnostic error without server crashing.
