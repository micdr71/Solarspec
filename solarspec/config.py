"""Configuration and settings for SolarSpec."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings, configurable via environment variables."""

    model_config = {"env_prefix": "SOLARSPEC_"}

    # PVGIS API
    pvgis_base_url: str = "https://re.jrc.ec.europa.eu/api/v5_3"
    pvgis_timeout: int = 30

    # Geocoding
    nominatim_base_url: str = "https://nominatim.openstreetmap.org"
    nominatim_user_agent: str = "solarspec/0.1.0"

    # System defaults
    default_electricity_price: float = Field(
        default=0.25, description="Default electricity price EUR/kWh"
    )
    default_panel_wp: float = Field(default=440, description="Default panel wattage (Wp)")
    default_panel_area: float = Field(default=1.95, description="Default panel area (m²)")
    default_cost_per_kwp: float = Field(
        default=1500, description="Default installation cost EUR/kWp"
    )
    default_performance_ratio: float = Field(default=0.80, description="Default PR")

    # AI (optional — set SOLARSPEC_ANTHROPIC_API_KEY to enable)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5-20250929"
