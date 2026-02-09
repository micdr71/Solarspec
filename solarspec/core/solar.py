"""Solar irradiation analysis via EU JRC PVGIS API."""

from __future__ import annotations

import httpx

from solarspec.config import Settings
from solarspec.models import SolarData


def get_solar_data(
    latitude: float,
    longitude: float,
    settings: Settings | None = None,
) -> SolarData:
    """Fetch solar irradiation data from PVGIS API.

    Uses the EU Joint Research Centre's PVGIS tool to obtain:
    - Annual and monthly irradiation on horizontal and optimal planes
    - Optimal tilt and azimuth angles
    - Estimated annual production per kWp

    Args:
        latitude: Site latitude.
        longitude: Site longitude.
        settings: Optional settings override.

    Returns:
        SolarData with irradiation and optimization data.

    Raises:
        httpx.HTTPError: If the PVGIS API request fails.
    """
    settings = settings or Settings()

    # Call PVGIS PVcalc endpoint for optimal angle calculation
    params = {
        "lat": latitude,
        "lon": longitude,
        "peakpower": 1,  # 1 kWp reference system
        "loss": 14,  # Standard system losses (%)
        "outputformat": "json",
        "optimalangles": 1,  # Let PVGIS calculate optimal tilt/azimuth
    }

    with httpx.Client(timeout=settings.pvgis_timeout) as client:
        response = client.get(
            f"{settings.pvgis_base_url}/PVcalc",
            params=params,
        )
        response.raise_for_status()
        data = response.json()

    inputs = data.get("inputs", {})
    outputs = data.get("outputs", {})
    monthly = outputs.get("monthly", {}).get("fixed", [])

    # Extract optimal angles from inputs (PVGIS returns them there)
    mounting = inputs.get("mounting_system", {}).get("fixed", {})
    optimal_tilt = mounting.get("slope", {}).get("value", 30.0)
    optimal_azimuth = mounting.get("azimuth", {}).get("value", 0.0)

    # Monthly irradiation values (on optimal plane)
    monthly_irradiation = [m.get("H(i)_m", 0.0) for m in monthly]

    # Annual totals
    totals = outputs.get("totals", {}).get("fixed", {})
    annual_irradiation = totals.get("H(i)_y", 0.0)  # kWh/m²/year on optimal plane
    annual_production = totals.get("E_y", 0.0)  # kWh/year per kWp

    return SolarData(
        annual_irradiation=round(annual_irradiation, 1),
        optimal_tilt=round(optimal_tilt, 1),
        optimal_azimuth=round(optimal_azimuth, 1),
        monthly_irradiation=[round(v, 1) for v in monthly_irradiation],
        annual_production_per_kwp=round(annual_production, 1),
    )
