"""Tests for PV system designer module."""

from __future__ import annotations

from solarspec.generators.designer import _default_module, _select_inverter


class TestProductCatalog:
    def test_default_module_from_catalog(self) -> None:
        module = _default_module()
        assert module.power_wp > 0
        assert module.efficiency > 0
        assert module.area_m2 > 0

    def test_select_inverter_small_system(self) -> None:
        inverter = _select_inverter(3.0)
        assert inverter is not None
        assert inverter.power_kw >= 2.5

    def test_select_inverter_medium_system(self) -> None:
        inverter = _select_inverter(6.0)
        assert inverter is not None
        assert inverter.power_kw >= 5.0

    def test_select_inverter_large_system(self) -> None:
        inverter = _select_inverter(10.0)
        assert inverter is not None
        assert inverter.power_kw >= 8.0
