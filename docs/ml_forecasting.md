# ML Thermal-Stress Forecasting — SIH26083

## 1. Forecast Objective

Predict future **thermal stress** (WBGT, UTCI, Heat Index) for the next 3–5 days at a specific location, given:
- A historical thermal record (ERA5 reanalysis, via Open-Meteo Archive API)
- Forecast meteorological data (Open-Meteo, same variables as STEP 2)

> [!IMPORTANT]
> **Thermal-stress forecasting ≠ health/mortality-risk prediction.**
> This pipeline predicts *environmental* thermal exposure indices, not health outcomes.
> Vulnerability scoring and health-risk modeling belong to STEPs 6–7.

---

## 2. Data Sources

| Source | Purpose | URL |
|---|---|---|
| Open-Meteo Archive API (ERA5) | Historical hourly meteorological data | `archive-api.open-meteo.com/v1/archive` |
| Open-Meteo Forecast API | 3–5 day forecast weather | `api.open-meteo.com/v1/forecast` |

**Historical variables** retrieved (hourly):
- `temperature_2m` (°C)
- `relative_humidity_2m` (%)
- `wind_speed_10m` (m/s)
- `shortwave_radiation` GHI (W/m²)
- `direct_radiation` (W/m²)
- `diffuse_radiation` (W/m²)
- `direct_normal_irradiance` DNI (W/m²)
- `surface_pressure` (hPa)

---

## 3. Feature Engineering

All features are **strictly backward-looking**. No future information enters any feature used to predict a target at horizon `h`. This is enforced by `pd.shift()` semantics.

### Feature Groups

| Group | Features |
|---|---|
| **Meteorological** | temp_c, rh_pct, wind_ms, pressure_hpa, ghi_wm2, direct_rad, diffuse_rad, dni |
| **Thermal** (STEP 3 derived) | heat_index_c, wbgt_c, utci_c, mrt_c |
| **Temporal** | hour, day_of_year, month, is_daytime, hour_sin, hour_cos, doy_sin, doy_cos |
| **Lag (1/3/6/12/24 h)** | `{col}_lag{n}h` for all base features |
| **Rolling mean (6/12/24 h)** | `{col}_roll_mean_{n}h` for wbgt, utci, hi, temp |
| **Rolling max (6/12/24 h)** | `{col}_roll_max_{n}h` for wbgt, utci, hi, temp |
| **Stress persistence** | hours_wbgt_above_28, hours_utci_above_32 |

Cyclical encoding of `hour` and `day_of_year` (sin/cos) preserves their circular periodicity without forcing a linear relationship.

---

## 4. Prediction Targets

Three **separate** target variables, each treated independently:

| Target | Column | Description |
|---|---|---|
| `wbgt` | `wbgt_c` | Outdoor WBGT (°C), Liljegren 2008 |
| `utci` | `utci_c` | UTCI (°C), 6th-order polynomial |
| `hi` | `heat_index_c` | NWS Rothfusz Heat Index (°C), `None` when Ta < 26.7°C |

**Forecast horizons:** 24 h, 48 h, 72 h, 96 h, 120 h — giving **15 models total** (3 targets × 5 horizons).

Target definition (leakage-safe):
```
target_wbgt_h24 at row i = wbgt_c at row i+24
```
The model never receives `wbgt_c` at row `i+24` as a feature.

---

## 5. Baseline

**Persistence baseline:** `ŷ_h = y_current`  
Predicts future thermal stress equals the most recently observed value.

This is the simplest non-trivial baseline. The ML model must outperform it to justify added complexity.

---

## 6. Candidate Models

Three candidates evaluated per (target, horizon):

| Candidate | Implementation | Key Hyperparameters |
|---|---|---|
| `ridge` | `sklearn.linear_model.Ridge` wrapped in `StandardScaler` Pipeline | α=1.0 |
| `rf` | `sklearn.ensemble.RandomForestRegressor` | 100 trees, max_depth=12, min_samples_leaf=5 |
| `gbm` | `sklearn.ensemble.GradientBoostingRegressor` | 200 estimators, lr=0.05, max_depth=5, subsample=0.8 |

**Random seed**: 42 (all candidates). Documented for reproducibility.

**Not used**: LightGBM, XGBoost, PyTorch. These may be evaluated if scikit-learn models are found insufficient after measuring on real data.

---

## 7. Final Model Selection

Best candidate selected **per (target, horizon)** by **validation-set RMSE**.

The model must:
1. Outperform the persistence baseline (lower RMSE)
2. Outperform or match the physical STEP 3 deterministic baseline (when applied to forecast weather)

If a candidate underperforms the persistence baseline, this is reported explicitly. The physical forecast is retained as the primary output in that case.

---

## 8. Time-Series Validation

> [!CAUTION]
> **Never shuffle time-series data for train/test splitting.** Shuffling would allow the model to "see" future observations during training.

**Chronological split:**
- **Train**: first 70% of records (by time)
- **Validation**: next 15% (model selection)
- **Test**: final 15% (final metric evaluation)

Three sets are non-overlapping and ordered by time.

---

## 9. Leakage Prevention

| Leakage type | How prevented |
|---|---|
| Future target in features | Lag features use `pd.shift(k)` — row `i` gets value from row `i-k` |
| Rolling window sees present row | Rolling features apply `.shift(1)` first |
| Future target in target column | Target `h` created with `pd.shift(-h)` — strictly future |
| Train/test overlap | Chronological split — test starts after validation ends |
| Feature built on test rows during training | `sklearn.Pipeline` fit only on train set |

---

## 10. Evaluation Metrics

Per target, per horizon:

| Metric | Formula | Interpretation |
|---|---|---|
| MAE | mean|y - ŷ| | Average absolute error in °C |
| RMSE | √mean(y-ŷ)² | Penalizes large errors more |
| R² | 1 - SS_res/SS_tot | Explained variance (1 = perfect) |

Compared against:
- **A. Persistence baseline** — `ŷ = y_current`
- **B. Physical STEP 3 deterministic** — STEP 3 applied to observed weather at target hour (ceiling for physical path)
- **C. ML model** — selected candidate

All evaluated exclusively on the **held-out test set** (no data seen during training).

---

## 11. Uncertainty

Prediction uncertainty is **not estimated in v1**.

All API responses return:
```json
"uncertainty": null,
"confidence_status": "NOT_ESTIMATED"
```

Future: conformal prediction intervals using validation residuals.

---

## 12. Model Versioning

Model artifacts stored in `backend/training/artifacts/`:

| File | Content |
|---|---|
| `wbgt_h24_v1.pkl` | joblib-serialized sklearn model for (WBGT, 24h) |
| `utci_h48_v1.pkl` | joblib-serialized sklearn model for (UTCI, 48h) |
| ... | (15 files total) |
| `model_metadata.json` | feature list, metrics, training dates, data period, status |

**Status values:**
- `MODEL_READY` — at least one model trained and saved
- `MODEL_NOT_TRAINED` — no artifacts exist
- `MODEL_ERROR` — loading failed

API reports status honestly; it never silently invents predictions.

---

## 13. Known Limitations

1. **UTCI missing at low wind**: ERA5 wind speeds below 0.5 m/s cause `pythermalcomfort.utci` to return `NaN`. This is physically correct (UTCI validity domain). These rows become missing targets for the UTCI model.

2. **Heat Index missing at low temperature**: NWS Rothfusz only applies above 26.7°C. ~50% of Delhi winter hours will have `heat_index_c = None`. The HI model trains only on valid rows.

3. **Physical vs. ML comparison boundary**: The physical STEP 3 "forecast" in `evaluate.py` uses *observed* weather at the target hour (best case). In production, STEP 3 uses *forecast* weather, which adds NWP model error. The true advantage of ML over physical may be greater than evaluation shows.

4. **Single location training**: The initial dataset covers New Delhi (lat 28.61, lon 77.23). Models trained here are location-specific and should not be applied to climatically different regions without retraining.

5. **No external health data**: This pipeline is deliberately separated from health/mortality data. It predicts thermal stress, not health outcomes.
