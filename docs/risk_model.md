# STEP 5: Human Vulnerability and Health Risk Model

## 1. Hazard Definition
Thermal Hazard represents the physical/meteorological severity of the environment. In this engine, we utilize established indices from STEP 3 and 4:
- Wet-Bulb Globe Temperature (WBGT)
- Universal Thermal Climate Index (UTCI)
- Heat Index (HI)

The primary anchor for the hazard score normalization is WBGT. 

## 2. Exposure Definition
Exposure quantifies the number of people subjected to the hazard. Variables include:
- Total Population
- Population Density

## 3. Vulnerability Definition
Vulnerability represents underlying susceptibility factors:
- Elderly Percentage (e.g. >= 65 years)
- Outdoor Worker Percentage
- Local Vulnerability Index (socioeconomic access to cooling/healthcare)

## 4. Risk Equation
`Overall_Risk = (W_haz * Hazard_Score) + (W_exp * Exposure_Score) + (W_vul * Vulnerability_Score)`

## 5. Normalization
Each raw component is normalized to a `0–100` scale.
For example, WBGT is normalized such that `<25°C` approaches 0 and `>35°C` approaches 100.
Missing values are preserved strictly as `None` alongside an explicit status (e.g., `MISSING`).

## 6. Weighting
Weights are strictly specified as `EXPERT_HEURISTIC`:
- Hazard = 50%
- Vulnerability = 30%
- Exposure = 20%

These are configurable in `backend/app/core/config.py`.

## 7. Risk Categories
- **LOW**: 0-19
- **MODERATE**: 20-39
- **HIGH**: 40-59
- **VERY_HIGH**: 60-79
- **EXTREME**: 80-100

## 8. Data Sources
Currently, dynamic data extraction for demographic profiles is implemented as an interface. In production mode, demographic data defaults to `MISSING`. Synthetic profiles can be enabled via `DEMO_DATA_ENABLED` but are explicitly labeled as `ESTIMATED`.

## 9. Geographic Resolution
Supported scales include `CITY`, `ZONE`, `WARD`. The engine explicitly rejects calculations blending variables of mismatched geographic resolutions.

## 10. Missing-Data Handling
Missing components **DO NOT** default to 0. If exposure or vulnerability data are entirely missing, the composite risk score returns `None`, the category evaluates to `HAZARD_ONLY`, and `risk_status` becomes `PARTIAL_DATA`.

## 11. Health-Data Methodology
The system interfaces with `HealthDataService` capable of intaking mortality and hospitalization rates. However, no statistically trained health outcome model is present yet.

## 12. Validation Status
**STATUS: NOT_HEALTH_VALIDATED**
This engine operates as a vulnerability-weighted decision support tool. It does NOT predict mortality probability. The system explicitly identifies its methodology as heuristic until real-world outcome models can be trained.

## 13. Limitations
- Weights are uncalibrated and heuristics-based.
- Demographic profiles require live dataset ingestion before production deployment.
- No direct mortality/morbidity probability function is currently validated.
