"""Esempio: analisi rapida di un sito a Roma."""

from solarspec import SolarSpec


def main() -> None:
    spec = SolarSpec()

    # Analisi del sito
    result = spec.analyze("Piazza del Colosseo, 00184 Roma RM")

    print(f"📍 {result.site.municipality} ({result.site.province})")
    print(f"☀️ Irraggiamento: {result.solar_data.annual_irradiation} kWh/m²/anno")
    print(f"📐 Inclinazione ottimale: {result.solar_data.optimal_tilt}°")
    print(f"⚡ Produzione per kWp: {result.solar_data.annual_production_per_kwp} kWh/kWp/anno")

    # Dimensionamento
    design = spec.design(
        address="Piazza del Colosseo, 00184 Roma RM",
        annual_consumption_kwh=4500,
        roof_area_m2=35,
    )

    print(f"\n🔧 Impianto: {design.system_size_kwp} kWp ({design.num_panels} moduli)")
    print(f"📊 Produzione annua: {design.estimated_production_kwh:.0f} kWh")
    print(f"💰 Costo: €{design.economics.total_cost_eur:,.0f}")
    print(f"⏱️  Rientro: {design.economics.payback_years} anni")


if __name__ == "__main__":
    main()
