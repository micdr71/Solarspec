"""Geographic analysis: geocoding, climate zones, seismic classification."""

from __future__ import annotations

import httpx

from solarspec.config import Settings
from solarspec.models import Location


def geocode_address(address: str, settings: Settings | None = None) -> Location:
    """Geocode an Italian address using Nominatim (OpenStreetMap).

    Args:
        address: Full Italian address string.
        settings: Optional settings override.

    Returns:
        Location with coordinates and administrative info.

    Raises:
        ValueError: If the address cannot be geocoded.
    """
    settings = settings or Settings()

    params = {
        "q": address,
        "format": "jsonv2",
        "addressdetails": 1,
        "countrycodes": "it",
        "limit": 1,
    }
    headers = {"User-Agent": settings.nominatim_user_agent}

    with httpx.Client(timeout=10) as client:
        response = client.get(
            f"{settings.nominatim_base_url}/search",
            params=params,
            headers=headers,
        )
        response.raise_for_status()
        results = response.json()

    if not results:
        raise ValueError(f"Impossibile geocodificare l'indirizzo: {address}")

    result = results[0]
    addr = result.get("address", {})

    return Location(
        latitude=float(result["lat"]),
        longitude=float(result["lon"]),
        municipality=addr.get("city", addr.get("town", addr.get("village", ""))),
        province=addr.get("county", ""),
        region=addr.get("state", ""),
        raw_address=result.get("display_name", address),
    )


# Italian climate zones by degree-day ranges (DPR 412/1993)
# In production this would be a full database lookup by municipality ISTAT code
_CLIMATE_ZONE_RANGES = {
    "A": (0, 600),
    "B": (601, 900),
    "C": (901, 1400),
    "D": (1401, 2100),
    "E": (2101, 3000),
    "F": (3001, 9999),
}

# Simplified region-based climate zone defaults
_REGION_CLIMATE_DEFAULTS: dict[str, str] = {
    "Sicilia": "B",
    "Sardegna": "C",
    "Calabria": "C",
    "Puglia": "C",
    "Campania": "C",
    "Basilicata": "D",
    "Molise": "D",
    "Abruzzo": "D",
    "Lazio": "D",
    "Marche": "D",
    "Umbria": "E",
    "Toscana": "D",
    "Emilia-Romagna": "E",
    "Liguria": "D",
    "Piemonte": "E",
    "Valle d'Aosta": "F",
    "Lombardia": "E",
    "Trentino-Alto Adige": "F",
    "Veneto": "E",
    "Friuli Venezia Giulia": "E",
}


def get_climate_zone(municipality: str, region: str = "") -> str:
    """Get Italian climate zone for a municipality.

    Args:
        municipality: Municipality name.
        region: Region name (used as fallback).

    Returns:
        Climate zone letter (A-F) or empty string if unknown.
    """
    # TODO: Implement full ISTAT-based lookup from data/climate_zones.json
    if region in _REGION_CLIMATE_DEFAULTS:
        return _REGION_CLIMATE_DEFAULTS[region]
    return ""


# Simplified seismic zone defaults by region
_REGION_SEISMIC_DEFAULTS: dict[str, int] = {
    "Calabria": 1,
    "Sicilia": 2,
    "Campania": 2,
    "Basilicata": 1,
    "Friuli Venezia Giulia": 2,
    "Abruzzo": 2,
    "Molise": 2,
    "Puglia": 3,
    "Umbria": 2,
    "Marche": 2,
    "Lazio": 2,
    "Toscana": 2,
    "Emilia-Romagna": 3,
    "Liguria": 3,
    "Piemonte": 3,
    "Valle d'Aosta": 3,
    "Lombardia": 3,
    "Trentino-Alto Adige": 4,
    "Veneto": 3,
    "Sardegna": 4,
}


def get_seismic_zone(municipality: str, region: str = "") -> int:
    """Get Italian seismic zone for a municipality.

    Args:
        municipality: Municipality name.
        region: Region name (used as fallback).

    Returns:
        Seismic zone (1-4) or 0 if unknown.
    """
    # TODO: Implement full municipality-based lookup from data/seismic_zones.json
    if region in _REGION_SEISMIC_DEFAULTS:
        return _REGION_SEISMIC_DEFAULTS[region]
    return 0
