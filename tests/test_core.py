"""Tests for SolarSpec core functionality."""

from __future__ import annotations

import pytest

from solarspec.models import SiteData, SolarData, AnalysisResult, SystemDesign


class TestModels:
    """Test Pydantic models."""

    def test_site_data_creation(self) -> None:
        site = SiteData(
            address="Via Roma 1, Milano",
            latitude=45.4642,
            longitude=9.1900,
            municipality="Milano",
            province="MI",
            region="Lombardia",
            climate_zone="E",
            seismic_zone=3,
        )
        assert site.municipality == "Milano"
        assert site.climate_zone == "E"

    def test_solar_data_creation(self) -> None:
        solar = SolarData(
            annual_irradiation=1450.5,
            optimal_tilt=34.0,
            optimal_azimuth=0.0,
            annual_production_per_kwp=1200.0,
        )
        assert solar.annual_irradiation == 1450.5
        assert solar.optimal_tilt == 34.0

    def test_analysis_result(self) -> None:
        site = SiteData(address="Test", latitude=45.0, longitude=9.0)
        solar = SolarData(
            annual_irradiation=1400.0,
            optimal_tilt=35.0,
            optimal_azimuth=0.0,
        )
        result = AnalysisResult(site=site, solar_data=solar)
        assert result.site.address == "Test"
        assert len(result.warnings) == 0


class TestDesigner:
    """Test system design logic."""

    def test_design_basic(self) -> None:
        from solarspec.generators.designer import design_system

        site = SiteData(
            address="Via Roma 1, Milano",
            latitude=45.4642,
            longitude=9.1900,
            climate_zone="E",
        )
        solar = SolarData(
            annual_irradiation=1450.0,
            optimal_tilt=34.0,
            optimal_azimuth=0.0,
            annual_production_per_kwp=1200.0,
        )
        analysis = AnalysisResult(site=site, solar_data=solar)

        design = design_system(
            analysis=analysis,
            annual_consumption_kwh=4500,
            roof_area_m2=40,
        )

        assert design.system_size_kwp > 0
        assert design.num_panels > 0
        assert design.estimated_production_kwh > 0
        assert design.economics is not None
        assert design.economics.payback_years > 0

    def test_design_small_roof(self) -> None:
        """Test that small roof area constrains the system."""
        from solarspec.generators.designer import design_system

        site = SiteData(address="Test", latitude=45.0, longitude=9.0)
        solar = SolarData(
            annual_irradiation=1400.0,
            optimal_tilt=35.0,
            optimal_azimuth=0.0,
            annual_production_per_kwp=1100.0,
        )
        analysis = AnalysisResult(site=site, solar_data=solar)

        design = design_system(
            analysis=analysis,
            annual_consumption_kwh=10000,  # High consumption
            roof_area_m2=10,  # Very small roof
        )

        # Should be constrained by roof area
        assert design.num_panels <= 5
        assert any("insufficiente" in n.lower() for n in design.notes)
