from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX, SARIMAXResults


@dataclass(frozen=True)
class SarimaxConfig:
    order: tuple[int, int, int] = (1, 0, 1)
    seasonal_order: tuple[int, int, int, int] = (1, 0, 1, 24)
    trend: str = "c"
    maxiter: int = 200


def build_time_features(index: pd.DatetimeIndex) -> pd.DataFrame:
    hours = index.hour.to_numpy()
    dow = index.dayofweek.to_numpy()
    month = index.month.to_numpy()

    hour_rad = 2 * np.pi * hours / 24.0
    dow_rad = 2 * np.pi * dow / 7.0
    month_rad = 2 * np.pi * (month - 1) / 12.0

    return pd.DataFrame(
        {
            "hour_sin": np.sin(hour_rad),
            "hour_cos": np.cos(hour_rad),
            "dow_sin": np.sin(dow_rad),
            "dow_cos": np.cos(dow_rad),
            "month_sin": np.sin(month_rad),
            "month_cos": np.cos(month_rad),
        },
        index=index,
    )


def fit_sarimax(
    y: pd.Series,
    exog: pd.DataFrame,
    cfg: SarimaxConfig,
    start_params=None,
    maxiter_override: int | None = None,
) -> SARIMAXResults:
    model = SARIMAX(
        y,
        exog=exog,
        order=cfg.order,
        seasonal_order=cfg.seasonal_order,
        trend=cfg.trend,
        enforce_stationarity=False,
        enforce_invertibility=False,
    )
    maxiter = maxiter_override if maxiter_override is not None else cfg.maxiter
    res = model.fit(disp=False, maxiter=maxiter, start_params=start_params)
    if res is None:
        raise RuntimeError("SARIMAX.fit returned None (unexpected)")
    return res


def forecast_probs(res: SARIMAXResults, exog_future: pd.DataFrame) -> pd.DataFrame:
    horizon_hours = len(exog_future)
    idx = exog_future.index
    yhat = res.get_forecast(steps=horizon_hours, exog=exog_future).predicted_mean.to_numpy(dtype=float)
    p = np.clip(yhat, 0.0, 1.0)
    return pd.DataFrame({"ts": idx, "p_alarm": p})

