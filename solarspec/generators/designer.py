"""PV system sizing and design."""

from __future__ import annotations

import json
import math
from pathlib import Path

from solarspec.config import Settings
from solarspec.models import (
    AnalysisResult,
    EconomicAnalysis,
    Inverter,
    PVModule,
    SystemDesign,
)

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load_product_catalog() -> dict:
    path = _DATA_DIR / "products.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"modules": [], "inverters": []}


def _default_module() -> PVModule:
    """Return best available module from catalog, or a generic fallback."""
    catalog = _load_product_catalog()
    modules = catalog.get("modules", [])
    if modules:
        best = max(modules, key=lambda m: m.get("efficiency", 0))
        return PVModule(**best)
    return PVModule(
        manufacturer="Generic",
        model="Mono PERC 440W",
        power_wp=440,
        efficiency=22.5,
        area_m2=1.95,
        voc=41.5,
        isc=13.5,
        warranty_years=25,
        degradation_rate=0.4,
    )


def _select_inverter(system_kwp: float) -> Inverter | None:
    """Select the best-matching inverter from the catalog for a given system size."""
    catalog = _load_product_catalog()
    inverters = catalog.get("inverters", [])
    if not inverters:
        return None

    best: dict | None = None
    best_score = float("inf")
    for inv in inverters:
        power = inv.get("power_kw", 0)
        max_dc = inv.get("max_dc_power_kw", 0)
        # Inverter AC power should be >= system kWp (slightly oversized OK)
        # DC input should accommodate the array
        if max_dc < system_kwp * 0.8:
            continue
        # Prefer smallest inverter that can handle the system
        score = abs(power - system_kwp) + (0 if power >= system_kwp * 0.9 else 10)
        if score < best_score:
            best_score = score
            best = inv

    if best is None and inverters:
        # Pick the largest available
        best = max(inverters, key=lambda i: i.get("power_kw", 0))

    if best:
        return Inverter(**{k: v for k, v in best.items() if not k.startswith("_")})
    return None


def design_system(
    analysis: AnalysisResult,
    annual_consumption_kwh: float,
    roof_area_m2: float,
    roof_tilt: float | None = None,
    roof_azimuth: float | None = None,
    settings: Settings | None = None,
) -> SystemDesign:
    """Design an optimal PV system based on site analysis and consumption.

    The algorithm:
    1. Calculate target system size from consumption and local production factor
    2. Constrain by available roof area
    3. Select number of panels
    4. Estimate production and self-consumption
    5. Run economic analysis

    Args:
        analysis: Result from SolarSpec.analyze().
        annual_consumption_kwh: Annual household/business consumption (kWh).
        roof_area_m2: Available roof area (m²).
        roof_tilt: Actual roof tilt (None = use optimal from analysis).
        roof_azimuth: Actual roof azimuth (None = use optimal from analysis).
        settings: Optional settings override.

    Returns:
        Complete SystemDesign with sizing and economics.
    """
    settings = settings or Settings()
    module = _default_module()
    notes: list[str] = []

    # Production per kWp at this location
    prod_per_kwp = analysis.solar_data.annual_production_per_kwp
    if prod_per_kwp <= 0:
        prod_per_kwp = analysis.solar_data.annual_irradiation * settings.default_performance_ratio
        notes.append("Produzione stimata da irraggiamento (dati PVGIS parziali)")

    # Apply tilt/azimuth correction if roof differs from optimal
    correction_factor = 1.0
    if roof_tilt is not None or roof_azimuth is not None:
        # Simplified correction — in production use pvlib transposition models
        tilt_diff = abs((roof_tilt or analysis.solar_data.optimal_tilt) - analysis.solar_data.optimal_tilt)
        azimuth_diff = abs((roof_azimuth or analysis.solar_data.optimal_azimuth) - analysis.solar_data.optimal_azimuth)
        correction_factor = max(0.7, 1.0 - tilt_diff * 0.003 - azimuth_diff * 0.002)
        if correction_factor < 0.85:
            notes.append(
                f"Orientamento non ottimale: perdita stimata {(1 - correction_factor) * 100:.0f}%"
            )

    effective_prod_per_kwp = prod_per_kwp * correction_factor

    # Target size: cover ~90% of consumption (grid-tied, no storage)
    target_kwp = (annual_consumption_kwh * 0.9) / effective_prod_per_kwp

    # Constrain by roof area
    max_panels_by_area = math.floor(roof_area_m2 / module.area_m2)
    max_kwp_by_area = max_panels_by_area * module.power_wp / 1000

    if target_kwp > max_kwp_by_area:
        notes.append(
            f"Area tetto insufficiente per coprire il 90% dei consumi. "
            f"Ridimensionato da {target_kwp:.1f} kWp a {max_kwp_by_area:.1f} kWp."
        )
        target_kwp = max_kwp_by_area

    # Calculate actual number of panels
    num_panels = max(1, math.ceil(target_kwp * 1000 / module.power_wp))
    actual_kwp = num_panels * module.power_wp / 1000

    # Estimated annual production
    estimated_production = actual_kwp * effective_prod_per_kwp

    # Self-consumption estimate (simplified model)
    # Higher ratios for smaller systems relative to consumption
    coverage_ratio = estimated_production / annual_consumption_kwh if annual_consumption_kwh > 0 else 1.0
    if coverage_ratio <= 0.5:
        self_consumption_rate = 0.70
    elif coverage_ratio <= 0.8:
        self_consumption_rate = 0.55
    elif coverage_ratio <= 1.0:
        self_consumption_rate = 0.40
    else:
        self_consumption_rate = 0.30

    # Inverter selection
    inverter = _select_inverter(actual_kwp)
    if inverter:
        notes.append(f"Inverter selezionato: {inverter.manufacturer} {inverter.model}")

    # Economic analysis
    total_cost = actual_kwp * settings.default_cost_per_kwp
    annual_self_consumed = estimated_production * self_consumption_rate
    annual_exported = estimated_production * (1 - self_consumption_rate)

    # Detrazione fiscale 50% (ristrutturazione edilizia) — max €96.000, in 10 anni
    tax_deduction_rate = 0.50
    max_deduction = 96000.0
    deduction_total = min(total_cost * tax_deduction_rate, max_deduction)
    annual_deduction = deduction_total / 10  # 10 rate annuali

    # SSP (Scambio Sul Posto) for systems <= 500 kWp
    # RID (Ritiro Dedicato) as alternative
    if actual_kwp <= 20:
        incentive_type = "SSP (Scambio Sul Posto) + Detrazione 50%"
        feed_in_tariff = 0.06  # SSP more favorable for small systems
    elif actual_kwp <= 500:
        incentive_type = "SSP (Scambio Sul Posto) + Detrazione 50%"
        feed_in_tariff = 0.04
    else:
        incentive_type = "RID (Ritiro Dedicato)"
        feed_in_tariff = 0.04
        deduction_total = 0.0
        annual_deduction = 0.0

    annual_savings = (
        annual_self_consumed * settings.default_electricity_price
        + annual_exported * feed_in_tariff
        + annual_deduction
    )

    # Effective cost after incentives
    effective_cost = total_cost - deduction_total
    payback = effective_cost / (annual_savings - annual_deduction) if (annual_savings - annual_deduction) > 0 else 99
    roi_25y = ((annual_savings * 25 - total_cost) / total_cost) * 100
    lcoe = effective_cost / (estimated_production * 25) if estimated_production > 0 else 0

    economics = EconomicAnalysis(
        total_cost_eur=round(total_cost, 2),
        cost_per_kwp=round(settings.default_cost_per_kwp, 2),
        annual_savings_eur=round(annual_savings, 2),
        payback_years=round(payback, 1),
        roi_25y_percent=round(roi_25y, 1),
        incentive_type=incentive_type,
        incentive_value_eur=round(deduction_total + annual_exported * feed_in_tariff * 25, 2),
        lcoe=round(lcoe, 4),
    )

    return SystemDesign(
        site=analysis.site,
        solar_data=analysis.solar_data,
        system_size_kwp=round(actual_kwp, 2),
        num_panels=num_panels,
        module=module,
        inverter=inverter,
        estimated_production_kwh=round(estimated_production, 0),
        self_consumption_rate=round(self_consumption_rate * 100, 1),
        performance_ratio=settings.default_performance_ratio,
        economics=economics,
        notes=notes,
    )
