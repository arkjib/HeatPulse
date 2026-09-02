# Derived from WBGT Model (James C. Liljegren, Argonne National Laboratory)
# © 2008 UChicago Argonne, LLC. All Rights Reserved.
#
# Modifications:
# Python port of the globe temperature modeling component along with required
# helper functions from the original WBGT model by Nibir Kanti Roy, 2025.
# Key value modifications in the code are in D_GLOBE, CONVERGENCE, and MAX_ITER.
#
# See LICENSE for terms and required acknowledgment.

import math

# ------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------
# Mathematical constants
PI         = 3.1415926535897932
TWOPI      = 6.2831853071795864
DEG_RAD    = 0.017453292519943295
RAD_DEG    = 57.295779513082323

# Physical constants
SOLAR_CONST = 1367.0          # W/m2
STEFANB     = 5.6696e-8       # Stefan-Boltzmann constant, W/m2/K4
Cp          = 1003.5          # Specific heat capacity of air, J/kg/K
M_AIR       = 28.97
M_H2O       = 18.015
R_GAS       = 8314.34         # Gas constant
R_AIR       = R_GAS / M_AIR
Pr          = Cp / (Cp + 1.25 * R_AIR)    # Prandtl number

# Globe & surface constants
EMIS_GLOBE  = 0.95            # Globe emissivity
ALB_GLOBE   = 0.05            # globe albedo
D_GLOBE     = 0.0635          # Globe diameter, m

EMIS_SFC    = 0.999           # Surface emissivity
ALB_SFC     = 0.45            # Surface albedo

# Computational and physical limits
CZA_MIN         = 0.00873     # Minimum cosine of zenith angle
NORMSOLAR_MAX   = 0.85
MIN_SPEED       = 0.13        # Minimum wind speed
CONVERGENCE     = 0.01        # K
MAX_ITER        = 500         # Maximum no of iterations


# ------------------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------------------
def daynum(year: int, month: int, day: int) -> int:
    """Sequential day number during a Gregorian year (1–365/366)."""
    begmonth = (0, 0, 31, 59, 90, 120, 151,
                181, 212, 243, 273, 304, 334)

    if year < 1:
        raise ValueError("year must be ≥ 1")

    leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
    dnum = begmonth[month] + day
    if leap and month > 2:
        dnum += 1
    return dnum


# ------------------------------------------------------------------------
# Solar geometry (low-precision ephemeris by N. Larson)
# ------------------------------------------------------------------------
def solarposition(year, month, day, days_1900,
                  latitude, longitude):
    """
    Port of solarposition() from the original C code.

    Parameters
    -----------------------------------
    year, month : int
    day         : float   (calendar day.fraction)
    days_1900   : float   (alternative date spec, 0 if not used)
    latitude    : float   (deg, +N)
    longitude   : float   (deg, +E)

    Returns
    -----------------------------------
    ap_ra  : apparent right ascension (h)
    ap_dec : apparent declination (deg)
    alt    : altitude w/ refraction (deg)
    refr   : refraction correction (deg)
    az     : azimuth (deg, 0=N, 90=E)
    dist   : Earth-Sun distance (au)
    """
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("invalid lat/lon")

    # ------------------------------------------------------------------
    # Convert date to days, centuries since J2000
    # ------------------------------------------------------------------
    if year!=0:                                       # Date via Y-M-D
        if not (1950 <= year <= 2049):
            raise ValueError("year out of range for low-precision formula")

        if month:                                     # Month ≠ 0 to calendar date
            if not (1 <= month <= 12 and 0 <= day <= 33):
                raise ValueError("bad month/day")
            daynumber = daynum(year, month, int(day))
        else:                                         # Month == 0 to day-of-year
            if not (0 <= day <= 368):
                raise ValueError("bad day-of-year")
            daynumber = int(day)

        delta_years = year - 2000
        delta_days  = delta_years*365 + delta_years//4 + daynumber
        if year > 2000:
            delta_days += 1
        days_J2000  = delta_days - 1.5

        # Compute centuries at 0h UT, before adding UT fraction
        cent_J2000 = days_J2000 / 36525.0
 
        ut, integral = math.modf(day)                 # Fractional day to UT
        days_J2000 += ut
        ut *= 24.0
    else:                                             # Date via days_1900
        if not (18262.0 <= days_1900 <= 54788.0):
            raise ValueError("days_1900 out of range")
        days_J2000 = days_1900 - 36525.5              # Convert 1900-based days to J2000-based
        ut, integral = math.modf(days_1900)
        ut *= 24.0
        cent_J2000 = (integral - 36525.5) / 36525.0   # Centuries since J2000 at 0h UT

    # ------------------------------------------------------------------
    # Sun coordinates, following Astronomical Almanac 1990
    # ------------------------------------------------------------------
    mean_anomaly   = math.radians((357.528 + 0.9856003 * days_J2000) % 360.0)
    mean_longitude = math.radians((280.460 + 0.9856474 * days_J2000) % 360.0)
    mean_obliq     = math.radians(23.439 - 4.0e-7 * days_J2000)

    ecl_long = mean_longitude + math.radians(
        1.915 * math.sin(mean_anomaly) + 0.020 * math.sin(2*mean_anomaly)
    )                                                    # Ecliptic longitude (rad)

    dist = 1.00014 - 0.01671 * math.cos(mean_anomaly) \
           - 0.00014 * math.cos(2*mean_anomaly)          # Earth-Sun distance

    # Apparent right ascension (RA)/ declination (DEC)
    sin_ecl = math.sin(ecl_long)
    cos_ecl = math.cos(ecl_long)
    ap_ra = math.atan2(math.cos(mean_obliq)*sin_ecl, cos_ecl)
    if ap_ra < 0:
        ap_ra += TWOPI
    ap_ra = ap_ra * 24 / TWOPI                # Radian to hours
    ap_dec = math.asin(math.sin(mean_obliq)*sin_ecl)

    # Local mean sidereal time (LMST)
    gmst0h = 24110.54841 + cent_J2000 * (8640184.812866 +
             cent_J2000*(0.093104 - cent_J2000*6.2e-6))
    gmst0h = (gmst0h / 3600.0 / 24.0) % 1.0 * 24.0
    if gmst0h < 0:
        gmst0h += 24.0
    lmst = (gmst0h + ut*1.00273790934 + longitude/15.0) % 24.0
    if lmst < 0:
        lmst += 24.0

    hour_angle = lmst - ap_ra
    if hour_angle < -12.0:
        hour_angle += 24.0
    elif hour_angle > 12.0:
        hour_angle -= 24.0
    hour_angle_rad = hour_angle / 24.0 * TWOPI

    # Altitude & azimuth
    lat_rad = math.radians(latitude)
    cos_dec = math.cos(ap_dec)
    sin_dec = math.sin(ap_dec)
    cos_lat = math.cos(lat_rad)
    sin_lat = math.sin(lat_rad)
    cos_h   = math.cos(hour_angle_rad)

    alt = math.asin(sin_dec*sin_lat + cos_dec*cos_h*cos_lat)
    cos_alt = math.cos(alt)
    tan_alt = math.tan(alt) if abs(alt) < math.radians(89.99999) else 6.0e6

    cos_az = (sin_dec*cos_lat - cos_dec*cos_h*sin_lat) / cos_alt
    sin_az = -cos_dec*math.sin(hour_angle_rad) / cos_alt
    az = math.acos(cos_az)
    if math.atan2(sin_az, cos_az) < 0:
        az = TWOPI - az

    # Simple refraction correction
    pressure = 1013.25                     # Assumed sea-level pressure (mb)
    temp_C   = 15.0                        # Assumed temperature (C) for refraction
    if alt < math.radians(-1.0) or tan_alt == 6.0e6:
        refr = 0.0
    else:
        alt_deg = math.degrees(alt)
        if alt_deg < 19.225:
            refr = ((0.1594 + alt_deg*(0.0196 + 0.00002*alt_deg))
                    * pressure /
                    ((1 + alt_deg*(0.505 + 0.0845*alt_deg))*(273 + temp_C)))
        else:
            refr = 0.00452 * pressure / (273 + temp_C) / tan_alt
    alt_corr = math.degrees(alt) + refr

    # Return all angles in required units
    return (ap_ra,
            math.degrees(ap_dec),
            alt_corr,
            refr,
            math.degrees(az),
            dist)

# ------------------------------------------------------------------------
# Solar wrapper used by the globe solver
# ------------------------------------------------------------------------
def calc_solar_parameters(year, month, day_frac, lat, lon, solar_ghi):
    """
    Adjust GHI, compute cosine solar zenith (cza) and beam-fraction (fdir).

    Parameters
    -----------------------------------
    day_frac : float   (day + UT/24.)
    solar_ghi: float   (W m-2) – measured global horizontal irradiance

    Returns
    -----------------------------------
    solar : float  (adjusted GHI, W m-2)
    cza   : float  (cosine zenith angle)
    fdir  : float  (direct-beam fraction)
    """
    ap_ra, ap_dec, alt_deg, _, _, dist = solarposition(
        year, month, day_frac, 0.0, lat, lon
    )
    cza = math.cos(math.radians(90.0 - alt_deg))
    toasolar = SOLAR_CONST * max(0.0, cza) / (dist*dist)  # Top of atmosphere solar radiation

    if cza < CZA_MIN:
        toasolar = 0.0

    if toasolar > 0.0:
        normsolar = min(solar_ghi / toasolar, NORMSOLAR_MAX)
        solar = normsolar * toasolar
        if normsolar > 0.0:
            fdir = math.exp(3.0 - 1.34*normsolar - 1.65/normsolar)
            fdir = max(min(fdir, 0.9), 0.0)
        else:
            fdir = 0.0
    else:
        solar = solar_ghi
        fdir  = 0.0                 # No beam component at night

    return solar, cza, fdir


# ------------------------------------------------------------------------
# Thermophysical properties
# ------------------------------------------------------------------------
def esat(tk, phase):
    """Buck (1981) saturation vapour pressure (mb)"""
    if phase == 0:
        y = (tk - 273.15)/(tk - 32.18)
        es = 6.1121 * math.exp(17.502 * y)
    else:
        y = (tk - 273.15)/(tk - 0.6)
        es = 6.1115 * math.exp(22.452 * y)
    return 1.004 * es


def viscosity(Tair):
    sigma      = 3.617
    eps_kappa  = 97.0
    Tr         = Tair / eps_kappa
    omega      = ((Tr - 2.9) / 0.4) * (-0.034) + 1.048
    return 2.6693e-6 * math.sqrt(M_AIR*Tair) / (sigma*sigma*omega)


def thermal_cond(Tair):
    return (Cp + 1.25*R_AIR) * viscosity(Tair)


def emis_atm(Tair, rh):
    e = rh * esat(Tair, 0)
    return 0.575 * e**0.143


def h_sphere_in_air(D, Tair, Pair, speed):
    density = Pair*100.0 / (R_AIR * Tair)
    Re      = max(speed, MIN_SPEED) * density * D / viscosity(Tair)
    Nu      = 2.0 + 0.6*math.sqrt(Re) * Pr**(1/3)
    return Nu * thermal_cond(Tair) / D


# ------------------------------------------------------------------------
# Globe temperature solver
# ------------------------------------------------------------------------
def Tglobe(Tair_K, rh_frac, Pair_mb, speed, solar, fdir, cza):
    """
    Globe temperature solver using the energy-balance from Liljegren's 
    WBGT model.

    Parameters
    -----------------------------------
    Tair_K   : float   – air temperature (K)
    rh_frac  : float   – relative humidity (0-1)
    Pair_mb  : float   – pressure (mb)
    speed    : float   – wind speed (m/s)
    solar    : float   – global solar (W/m2)
    fdir     : float   – direct-beam fraction
    cza      : float   – cosine of zenith angle

    Returns
    -----------------------------------
    Tg_C     : float   – globe temperature (C)
    """
    Tsfc   = Tair_K         # Approximate ground temperature == air temp (K)
    T_prev = Tair_K         # Initial globe temperature guess == air temp (K)

    for _ in range(MAX_ITER):
        T_ref = 0.5 * (T_prev + Tair_K)
        h     = h_sphere_in_air(D_GLOBE, T_ref, Pair_mb, speed)

        rhs = (0.5 * (emis_atm(Tair_K, rh_frac) * Tair_K**4 + EMIS_SFC * Tsfc**4)
               - h / (STEFANB * EMIS_GLOBE) * (T_prev - Tair_K)
               + solar / (2 * STEFANB * EMIS_GLOBE) * (1 - ALB_GLOBE)
                 * (fdir * (1 / (2 * cza) - 1) + 1 + ALB_SFC))

        T_new = rhs ** 0.25

        if abs(T_new - T_prev) < CONVERGENCE:
            return T_new - 273.15       # Return the new value in C

        # Under-relaxation
        T_prev = 0.9 * T_prev + 0.1 * T_new

    return -9999.0
