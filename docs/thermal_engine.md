# Thermal Stress Engine Methodology

## Overview
This document outlines the algorithms, assumptions, and libraries used to calculate the core thermal indices for the SIH26083 backend: Heat Index (HI), Wet Bulb Globe Temperature (WBGT), Universal Thermal Climate Index (UTCI), and Mean Radiant Temperature (MRT).

The engine is encapsulated in the `backend/app/thermal` module. 

## Inputs & Units
The system relies on the following measured environmental inputs sourced from Open-Meteo:
- **Temperature ($T_a$)**: Celsius ($^\circ\text{C}$)
- **Relative Humidity ($RH$)**: Percentage (0-100%)
- **Wind Speed ($v$)**: meters per second (m/s) at 10m altitude
- **Shortwave Radiation (GHI)**: Watts per square meter ($W/m^2$)
- **Direct Radiation**: $W/m^2$
- **Diffuse Radiation**: $W/m^2$
- **Direct Normal Irradiance (DNI)**: $W/m^2$
- **Pressure**: hPa

**Note on Radiation:** We do not derive radiation fields ourselves; we accept the direct provided observations. At night, values of $0.0 W/m^2$ are strictly preserved as valid observations.

## 1. Heat Index (HI)
**Methodology:** US National Weather Service (NWS) / Rothfusz regression.
**Implementation:** Native Python implementation in `heat_index.py`.
**Validity Range:** Valid only for $T_a \ge 80^\circ\text{F}$ ($26.7^\circ\text{C}$). If temperature is lower, the index returns a `NOT_APPLICABLE` status rather than returning the air temperature.
**Adjustments:** Includes standard NWS low-RH and high-RH adjustments.

## 2. Mean Radiant Temperature (MRT)
**Methodology:** ASHRAE 55 / Jendritzky MENEX Outdoor Solar Geometry Model.
**Implementation:** Native Python in `radiant_temperature.py`.
**Details:** MRT is explicitly flagged as `DERIVED` because it is not directly measured by a globe thermometer. The formulation:
1. Calculates Solar Zenith Angle using the validated `pvlib` library based on precise latitude, longitude, and timestamp.
2. Derives the Projected Area Factor ($f_p$) for a standing human using the Jendritzky et al. approximation.
3. Computes absorbed shortwave radiation ($E_{solar}$) incorporating provided DNI, Diffuse Radiation, and GHI using standard assumptions (clothing shortwave absorptivity $\alpha=0.7$, emissivity $\epsilon=0.95$, effective radiation area $f_{eff}=0.725$, and ground albedo $=0.2$).
4. Solves the fourth-order thermal balance equation to yield MRT.

## 3. Wet Bulb Globe Temperature (WBGT)
**Methodology:** Liljegren et al. (2008) Non-Linear Heat Balance Solver.
**Implementation:** `lwbgt` Python-C extension in `wbgt.py`.
**Details:** Initially, a native Python numeric solver using `scipy.optimize.newton` was built, but independent validation against the official Liljegren test cases revealed unacceptably large divergences (up to 11°C) in Natural Wet Bulb Temperature ($T_{nwb}$) during hot, very dry conditions due to simplifications in the convective-evaporative mass transfer term.
To ensure strict scientific rigor without compromising dependencies, the backend directly integrates the `lwbgt` C-library. `lwbgt` is a dependency-free, ABI-stable port of the original Liljegren 2008 meteorological model.
1. **Globe Temperature ($T_g$)**: Calculated natively by `lwbgt` using its internal solar position algorithms and full fourth-order radiation exchange balances.
2. **Natural Wet Bulb ($T_{nwb}$)**: Solved flawlessly matching psychrometric constraints and explicitly accounting for radiative sky cooling at night.
3. **WBGT**: Integrates the solved $T_g$ and $T_{nwb}$ into the standard outdoor weighted formulation: $WBGT = 0.7 T_{nwb} + 0.2 T_g + 0.1 T_a$.
*Note: Secondary validation of the final weighted combination is continuously run against the ISO 7243 reference in `pythermalcomfort` using our `pytest` suite.*

## 4. Universal Thermal Climate Index (UTCI)
**Methodology:** UTCI 6th-order Polynomial Operational Procedure.
**Implementation:** Wrapped via `pythermalcomfort.models.utci`.
**Validity Domain:** 
- Air temperature must be between $-50^\circ\text{C}$ and $50^\circ\text{C}$.
- Wind speed must be $\le 17\text{ m/s}$. 
**Details:** The engine strictly enforces domain validation. If conditions fall out of bounds, the system traps the error and issues a `NOT_APPLICABLE` status. Vapor pressure derivation is handled natively inside `pythermalcomfort`. Wind speed is assumed to be the 10m meteorological standard (as supplied by Open-Meteo).

## External Libraries
- **`pythermalcomfort` (v4.4.2)**: Used exclusively for the highly complex UTCI polynomial.
- **`pvlib`**: Used strictly for highly accurate astronomical solar zenith angle calculation.
- **`scipy`**: Supplies the Newton-Raphson non-linear root solver for the Liljegren WBGT physics equations.
