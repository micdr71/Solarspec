"""SolarSpec — Generatore intelligente di capitolati tecnici per impianti fotovoltaici in Italia."""

from __future__ import annotations

__version__ = "0.1.0"

from solarspec.config import Settings
from solarspec.models import AnalysisResult, SystemDesign, SiteData, SolarData

__all__ = [
    "SolarSpec",
    "Settings",
    "AnalysisResult",
    "SystemDesign",
    "SiteData",
    "SolarData",
]


class SolarSpec:
    """Main entry point for SolarSpec analysis and document generation.

    Example:
        >>> spec = SolarSpec()
        >>> result = spec.analyze("Via Roma 1, 20121 Milano MI")
        >>> print(result.solar_data.annual_irradiation)
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()

    def analyze(self, address: str) -> AnalysisResult:
        """Analyze a site given an Italian address.

        Args:
            address: Full Italian address string.

        Returns:
            AnalysisResult with geographic, solar, and regulatory data.
        """
        from solarspec.core.geo import geocode_address, get_climate_zone, get_seismic_zone
        from solarspec.core.solar import get_solar_data

        # Step 1: Geocoding
        location = geocode_address(address)

        # Step 2: Solar analysis via PVGIS
        solar_data = get_solar_data(location.latitude, location.longitude)

        # Step 3: Climate and seismic classification
        climate_zone = get_climate_zone(location.municipality)
        seismic_zone = get_seismic_zone(location.municipality)

        site = SiteData(
            address=address,
            latitude=location.latitude,
            longitude=location.longitude,
            municipality=location.municipality,
            province=location.province,
            region=location.region,
            climate_zone=climate_zone,
            seismic_zone=seismic_zone,
        )

        return AnalysisResult(site=site, solar_data=solar_data)

    def design(
        self,
        address: str,
        annual_consumption_kwh: float,
        roof_area_m2: float,
        roof_tilt: float | None = None,
        roof_azimuth: float | None = None,
    ) -> SystemDesign:
        """Design an optimal PV system for the given site.

        Args:
            address: Full Italian address.
            annual_consumption_kwh: Annual electricity consumption in kWh.
            roof_area_m2: Available roof area in square meters.
            roof_tilt: Roof tilt in degrees (None = use optimal).
            roof_azimuth: Roof azimuth in degrees (None = use optimal, 0=South).

        Returns:
            SystemDesign with sizing, components, and economics.
        """
        from solarspec.generators.designer import design_system

        analysis = self.analyze(address)
        return design_system(
            analysis=analysis,
            annual_consumption_kwh=annual_consumption_kwh,
            roof_area_m2=roof_area_m2,
            roof_tilt=roof_tilt,
            roof_azimuth=roof_azimuth,
        )

    def generate_document(
        self,
        design: SystemDesign,
        output_path: str,
        format: str = "docx",
    ) -> str:
        """Generate the technical specification document.

        Args:
            design: A SystemDesign from the design() method.
            output_path: Where to save the document.
            format: Output format ('docx' or 'pdf').

        Returns:
            Path to the generated document.
        """
        from solarspec.generators.document import generate

        return generate(design=design, output_path=output_path, format=format)
