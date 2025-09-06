# models.py
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

def simple_forecast(series: pd.Series, periods=7):
    if len(series) < 5:
        return pd.Series([series.mean()]*periods)
    try:
        model = ExponentialSmoothing(series, trend="add", seasonal=None)
        fit = model.fit()
        return pd.Series(fit.forecast(periods))
    except Exception:
        return pd.Series([series.mean()]*periods)

def zscore_anomaly(value, history_vals, z_thresh=2.5):
    mu = np.mean(history_vals) if len(history_vals)>0 else 0
    sigma = np.std(history_vals) if len(history_vals)>0 else 0.0001
    z = (value - mu) / sigma
    return abs(z) >= z_thresh, z
