"""Tests for geographic analysis module."""

from __future__ import annotations

from solarspec.core.geo import get_climate_zone, get_seismic_zone


class TestClimateZones:
    def test_known_municipality(self) -> None:
        assert get_climate_zone("Milano") == "E"
        assert get_climate_zone("Roma") == "D"
        assert get_climate_zone("Palermo") == "B"
        assert get_climate_zone("Aosta") == "F"

    def test_case_insensitive(self) -> None:
        assert get_climate_zone("milano") == "E"
        assert get_climate_zone("ROMA") == "D"

    def test_fallback_to_region(self) -> None:
        # Unknown municipality, known region
        assert get_climate_zone("Paesino Sconosciuto", "Lombardia") == "E"

    def test_unknown_municipality(self) -> None:
        assert get_climate_zone("NonExistent") == ""


class TestSeismicZones:
    def test_known_municipality(self) -> None:
        assert get_seismic_zone("L'Aquila") == 1
        assert get_seismic_zone("Milano") == 3
        assert get_seismic_zone("Catanzaro") == 1
        assert get_seismic_zone("Cagliari") == 4

    def test_case_insensitive(self) -> None:
        assert get_seismic_zone("milano") == 3

    def test_fallback_to_region(self) -> None:
        assert get_seismic_zone("Paesino Sconosciuto", "Calabria") == 1

    def test_unknown_municipality(self) -> None:
        assert get_seismic_zone("NonExistent") == 0
