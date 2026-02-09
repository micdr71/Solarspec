"""Data models for SolarSpec."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Location(BaseModel):
    """Geocoded location result."""

    latitude: float
    longitude: float
    municipality: str = ""
    province: str = ""
    region: str = ""
    raw_address: str = ""


class SiteData(BaseModel):
    """Complete site characterization."""

    address: str
    latitude: float
    longitude: float
    municipality: str = ""
    province: str = ""
    region: str = ""
    climate_zone: str = Field(default="", description="Zona climatica italiana (A-F)")
    seismic_zone: int = Field(default=0, ge=0, le=4, description="Zona sismica (1-4, 0=unknown)")


class SolarData(BaseModel):
    """Solar irradiation data from PVGIS."""

    annual_irradiation: float = Field(
        description="Annual global irradiation on horizontal plane (kWh/m²/year)"
    )
    optimal_tilt: float = Field(description="Optimal panel tilt angle (degrees)")
    optimal_azimuth: float = Field(description="Optimal azimuth angle (degrees, 0=South)")
    monthly_irradiation: list[float] = Field(
        default_factory=list, description="Monthly irradiation values (12 values, kWh/m²)"
    )
    annual_production_per_kwp: float = Field(
        default=0.0, description="Estimated annual production per kWp installed (kWh/kWp)"
    )


class PVModule(BaseModel):
    """Photovoltaic module specifications."""

    manufacturer: str
    model: str
    power_wp: float = Field(description="Nominal power (Wp)")
    efficiency: float = Field(description="Module efficiency (%)")
    area_m2: float = Field(description="Module area (m²)")
    voc: float = Field(default=0.0, description="Open circuit voltage (V)")
    isc: float = Field(default=0.0, description="Short circuit current (A)")
    warranty_years: int = 25
    degradation_rate: float = Field(default=0.5, description="Annual degradation (%)")


class Inverter(BaseModel):
    """Inverter specifications."""

    manufacturer: str
    model: str
    power_kw: float = Field(description="Nominal AC power (kW)")
    max_dc_power_kw: float = Field(description="Max DC input power (kW)")
    efficiency: float = Field(description="European efficiency (%)")
    mppt_channels: int = 1
    warranty_years: int = 10


class EconomicAnalysis(BaseModel):
    """Economic feasibility analysis."""

    total_cost_eur: float = Field(description="Total installation cost (EUR)")
    cost_per_kwp: float = Field(description="Cost per kWp installed (EUR/kWp)")
    annual_savings_eur: float = Field(description="Estimated annual savings (EUR)")
    payback_years: float = Field(description="Simple payback period (years)")
    roi_25y_percent: float = Field(description="ROI over 25 years (%)")
    incentive_type: str = Field(default="", description="Applicable incentive (SSP, RID, etc.)")
    incentive_value_eur: float = Field(default=0.0, description="Estimated incentive value (EUR)")
    lcoe: float = Field(default=0.0, description="Levelized Cost of Energy (EUR/kWh)")


class SystemDesign(BaseModel):
    """Complete PV system design."""

    site: SiteData
    solar_data: SolarData
    system_size_kwp: float = Field(description="Total system size (kWp)")
    num_panels: int = Field(description="Number of PV modules")
    module: PVModule | None = None
    inverter: Inverter | None = None
    estimated_production_kwh: float = Field(description="Annual production estimate (kWh)")
    self_consumption_rate: float = Field(
        default=0.0, description="Estimated self-consumption rate (%)"
    )
    performance_ratio: float = Field(default=0.8, description="System performance ratio")
    economics: EconomicAnalysis | None = None
    notes: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    """Result of a site analysis."""

    site: SiteData
    solar_data: SolarData
    warnings: list[str] = Field(default_factory=list)
