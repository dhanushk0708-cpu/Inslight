import math
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import duckdb
from app.utils.formatters import format_val
from app.core.logging import logger

try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import LinearRegression
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class ForecastingService:
    """
    Predictive Analytics & Time-Series Forecasting Service.
    Supports Moving Averages, Holt's Exponential Smoothing, Linear Regression,
    and Random Forest Regression with validation metrics (MAE, RMSE, MAPE)
    and prediction intervals.
    """

    @classmethod
    def generate_forecast(
        cls,
        conn: duckdb.DuckDBPyConnection,
        table_name: str,
        target_metric: Optional[str] = None,
        date_col: Optional[str] = None,
        horizon: int = 30,
        method: str = "auto"
    ) -> Dict[str, Any]:
        """
        Generate time-series forecast with historical backtesting and prediction intervals.
        """
        df_cols = conn.execute(f"DESCRIBE {table_name}").df()
        col_names = list(df_cols["column_name"])
        col_types = {r["column_name"]: str(r["column_type"]).lower() for _, r in df_cols.iterrows()}

        # 1. Identify target metric
        if not target_metric:
            for cand in ["revenue", "sales", "total_amount", "amount", "units", "quantity"]:
                match = next((c for c in col_names if c.lower() == cand), None)
                if match:
                    target_metric = match
                    break
        if not target_metric:
            target_metric = next((c for c in col_names if any(t in col_types[c] for t in ["int", "double", "float", "decimal", "numeric"])), None)

        if not target_metric:
            return {
                "status": "error",
                "message": "No numeric metric found for forecasting."
            }

        # 2. Identify date column
        if not date_col:
            for cand in ["date", "order_date", "timestamp", "created_at", "month"]:
                match = next((c for c in col_names if c.lower() == cand), None)
                if match:
                    date_col = match
                    break

        if not date_col:
            return {
                "status": "unsupported",
                "message": "Dataset lacks a recognized temporal date column required for time-series forecasting."
            }

        # 3. Aggregate historical time-series at appropriate frequency (daily or monthly)
        try:
            # First check span of dates
            span_df = conn.execute(f"""
                SELECT MIN(CAST({date_col} AS DATE)) AS min_d,
                       MAX(CAST({date_col} AS DATE)) AS max_d,
                       COUNT(DISTINCT CAST({date_col} AS DATE)) AS dist_days
                FROM {table_name}
                WHERE {date_col} IS NOT NULL
            """).df()
            dist_days = int(span_df["dist_days"].iloc[0] or 0)

            # Determine grouping granularity
            if dist_days > 45:
                freq = "M"
                date_sql = f"strftime(CAST({date_col} AS DATE), '%Y-%m-01')"
                date_format = "%Y-%m"
                horizon_steps = min(horizon // 30 or 3, 12)  # months
                horizon_label = f"Next {horizon_steps} Months"
            else:
                freq = "D"
                date_sql = f"CAST({date_col} AS DATE)"
                date_format = "%Y-%m-%d"
                horizon_steps = min(horizon, 30)  # days
                horizon_label = f"Next {horizon_steps} Days"

            ts_query = f"""
                SELECT {date_sql} AS period_date,
                       SUM(CAST({target_metric} AS DOUBLE)) AS actual_val
                FROM {table_name}
                WHERE {date_col} IS NOT NULL
                GROUP BY period_date
                ORDER BY period_date ASC
            """
            df_ts = conn.execute(ts_query).df()
            df_ts["period_date"] = pd.to_datetime(df_ts["period_date"])
            df_ts = df_ts.dropna().sort_values("period_date").reset_index(drop=True)
        except Exception as e:
            logger.error(f"Failed to prepare time series data: {e}")
            return {
                "status": "error",
                "message": f"Time series extraction failed: {str(e)}"
            }

        n_points = len(df_ts)
        if n_points < 5:
            return {
                "status": "insufficient_data",
                "message": f"Historical series contains only {n_points} distinct periods. A minimum of 5 data points is required to train reliable predictive models without deceptive extrapolation.",
                "data_points_count": n_points
            }

        values = df_ts["actual_val"].values.astype(float)
        dates = df_ts["period_date"].values

        # 4. Model Selection & Historical Backtesting
        # Split train / test (last 20% or at least 2 points for testing)
        test_size = max(2, int(n_points * 0.2))
        train_vals = values[:-test_size]
        test_vals = values[-test_size:]

        # Train candidate models
        selected_method = method if method != "auto" else (
            "random_forest" if (SKLEARN_AVAILABLE and n_points >= 15) else (
                "linear_regression" if (SKLEARN_AVAILABLE and n_points >= 8) else "exponential_smoothing"
            )
        )

        # Generate Predictions & Interval Bounds
        history_series: List[Dict[str, Any]] = []
        for d, v in zip(dates, values):
            history_series.append({
                "date": pd.to_datetime(d).strftime(date_format),
                "actual": round(float(v), 2),
                "predicted": None,
                "lower_bound": None,
                "upper_bound": None
            })

        # Train and forecast based on selected method
        forecast_vals, lower_bounds, upper_bounds, eval_metrics = cls._train_and_predict(
            values=values,
            train_vals=train_vals,
            test_vals=test_vals,
            horizon_steps=horizon_steps,
            method=selected_method
        )

        # Future Date Generation
        last_date = pd.to_datetime(dates[-1])
        future_series: List[Dict[str, Any]] = []
        for i in range(1, horizon_steps + 1):
            if freq == "M":
                next_d = last_date + pd.DateOffset(months=i)
            else:
                next_d = last_date + pd.Timedelta(days=i)

            pred = max(0.0, float(forecast_vals[i - 1]))
            lb = max(0.0, float(lower_bounds[i - 1]))
            ub = max(pred, float(upper_bounds[i - 1]))

            future_series.append({
                "date": next_d.strftime(date_format),
                "actual": None,
                "predicted": round(pred, 2),
                "lower_bound": round(lb, 2),
                "upper_bound": round(ub, 2)
            })

        # Summary Metrics
        historical_sum = float(np.sum(values))
        forecast_sum = float(np.sum(forecast_vals))
        mean_forecast = float(np.mean(forecast_vals))

        trend_direction = "Growth" if forecast_vals[-1] > values[-1] else "Decline"
        growth_rate = round(((forecast_vals[-1] - values[-1]) / (values[-1] + 1e-6)) * 100.0, 1)

        return {
            "status": "success",
            "metric": target_metric,
            "method_used": selected_method,
            "horizon_label": horizon_label,
            "horizon_steps": horizon_steps,
            "granularity": "Monthly" if freq == "M" else "Daily",
            "evaluation_metrics": eval_metrics,
            "historical_total": round(historical_sum, 2),
            "forecasted_total": round(forecast_sum, 2),
            "mean_period_forecast": round(mean_forecast, 2),
            "trend_direction": trend_direction,
            "projected_growth_pct": growth_rate,
            "formatted_forecast_total": format_val(forecast_sum, "currency"),
            "history_data": history_series,
            "forecast_data": future_series,
            "limitations": "Forecast assumes stability in external market conditions and historical operational parameters. Sudden exogenous shifts or promotions will deviate from projected intervals."
        }

    @classmethod
    def _train_and_predict(
        cls,
        values: np.ndarray,
        train_vals: np.ndarray,
        test_vals: np.ndarray,
        horizon_steps: int,
        method: str
    ):
        """Internal router to train selected ML or statistical model and compute backtest metrics."""
        n = len(values)
        std_residual = float(np.std(values)) if np.std(values) > 0 else 1.0

        if method == "linear_regression" and SKLEARN_AVAILABLE:
            X_train = np.arange(len(train_vals)).reshape(-1, 1)
            reg = LinearRegression().fit(X_train, train_vals)
            test_preds = reg.predict(np.arange(len(train_vals), n).reshape(-1, 1))

            # Fit on full data
            reg_full = LinearRegression().fit(np.arange(n).reshape(-1, 1), values)
            future_X = np.arange(n, n + horizon_steps).reshape(-1, 1)
            forecast_vals = reg_full.predict(future_X)

            residuals = values - reg_full.predict(np.arange(n).reshape(-1, 1))
            std_residual = float(np.std(residuals)) or 1.0

        elif method == "random_forest" and SKLEARN_AVAILABLE and n >= 10:
            # Create autoregressive lag features
            lags = 2
            X, y = [], []
            for i in range(lags, n):
                X.append([values[i - 1], values[i - 2], np.mean(values[max(0, i - 3):i])])
                y.append(values[i])
            X, y = np.array(X), np.array(y)

            split = max(1, len(X) - len(test_vals))
            rf = RandomForestRegressor(n_estimators=50, random_state=42).fit(X[:split], y[:split])
            test_preds = rf.predict(X[split:]) if split < len(X) else rf.predict(X)

            # Fit full
            rf_full = RandomForestRegressor(n_estimators=50, random_state=42).fit(X, y)
            last_seq = list(values[-lags:])
            forecast_vals = []
            for _ in range(horizon_steps):
                feat = np.array([[last_seq[-1], last_seq[-2], np.mean(last_seq[-3:])]])
                p = rf_full.predict(feat)[0]
                forecast_vals.append(p)
                last_seq.append(p)
            forecast_vals = np.array(forecast_vals)
            std_residual = float(np.std(y - rf_full.predict(X))) or 1.0

        elif method == "moving_average":
            k = min(3, len(train_vals))
            test_preds = np.full(len(test_vals), np.mean(train_vals[-k:]))
            avg_last = np.mean(values[-k:])
            forecast_vals = np.full(horizon_steps, avg_last)

        else:
            # Holt's Double Exponential Smoothing (Level + Trend)
            alpha, beta = 0.5, 0.3
            level = train_vals[0]
            trend = train_vals[1] - train_vals[0] if len(train_vals) > 1 else 0
            for v in train_vals[1:]:
                last_l = level
                level = alpha * v + (1 - alpha) * (level + trend)
                trend = beta * (level - last_l) + (1 - beta) * trend

            test_preds = [level + (i + 1) * trend for i in range(len(test_vals))]

            # Full fit
            level = values[0]
            trend = values[1] - values[0] if n > 1 else 0
            for v in values[1:]:
                last_l = level
                level = alpha * v + (1 - alpha) * (level + trend)
                trend = beta * (level - last_l) + (1 - beta) * trend

            forecast_vals = np.array([level + (i + 1) * trend for i in range(horizon_steps)])

        # Compute backtest evaluation metrics on test split
        mae = float(np.mean(np.abs(test_vals - test_preds)))
        rmse = float(np.sqrt(np.mean((test_vals - test_preds) ** 2)))
        # Safe MAPE calculation with epsilon
        mape = float(np.mean(np.abs((test_vals - test_preds) / (test_vals + 1e-6)))) * 100.0

        eval_metrics = {
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "mape_pct": round(min(mape, 99.9), 1)
        }

        # Prediction intervals (95% CI ~ 1.96 * std_residual * sqrt(t))
        lower_bounds = []
        upper_bounds = []
        for step, val in enumerate(forecast_vals, start=1):
            margin = 1.96 * std_residual * math.sqrt(step * 0.5 + 1)
            lower_bounds.append(val - margin)
            upper_bounds.append(val + margin)

        return forecast_vals, lower_bounds, upper_bounds, eval_metrics
