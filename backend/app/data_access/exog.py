from __future__ import annotations

import pandas as pd

from app.data_access.bins import load_bins_series
from app.ua_neighbors import neighbors_for


def build_exog_for_uid(uid: int, index: pd.DatetimeIndex) -> pd.DataFrame:
    from app.ml.sarimax_core import build_time_features

    exog = build_time_features(index)

    nbrs = neighbors_for(uid)
    if not nbrs:
        exog["nbr_frac_lag1"] = 0.0
        exog["nbr_frac_lag2"] = 0.0
        exog["nbr_any_lag1"] = 0.0
        return exog

    nbr_series = []
    for nuid in nbrs:
        s = load_bins_series(nuid).reindex(index).fillna(0).astype(int)
        nbr_series.append(s)

    mat = pd.concat(nbr_series, axis=1).to_numpy(dtype=float)

    frac = mat.mean(axis=1)
    any1 = (mat.max(axis=1) > 0).astype(float)

    exog["nbr_frac_lag1"] = pd.Series(frac, index=index).shift(1).fillna(0.0)
    exog["nbr_frac_lag2"] = pd.Series(frac, index=index).shift(2).fillna(0.0)
    exog["nbr_any_lag1"] = pd.Series(any1, index=index).shift(1).fillna(0.0)

    return exog
