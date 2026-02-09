"""SolarSpec CLI — Command line interface."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="solarspec",
    help="☀️ Generatore intelligente di capitolati tecnici per impianti fotovoltaici in Italia",
)
console = Console()


@app.command()
def analyze(
    address: str = typer.Argument(help="Indirizzo italiano completo"),
) -> None:
    """Analizza un sito per un impianto fotovoltaico."""
    from solarspec import SolarSpec

    with console.status("Analisi in corso..."):
        spec = SolarSpec()
        result = spec.analyze(address)

    table = Table(title=f"☀️ Analisi solare — {result.site.municipality}")
    table.add_column("Parametro", style="cyan")
    table.add_column("Valore", style="green")

    table.add_row("Indirizzo", result.site.address)
    table.add_row("Coordinate", f"{result.site.latitude:.5f}°N, {result.site.longitude:.5f}°E")
    table.add_row("Comune", f"{result.site.municipality} ({result.site.province})")
    table.add_row("Regione", result.site.region)
    table.add_row("Zona climatica", result.site.climate_zone or "N/D")
    table.add_row("Zona sismica", str(result.site.seismic_zone) if result.site.seismic_zone else "N/D")
    table.add_row("Irraggiamento annuo", f"{result.solar_data.annual_irradiation} kWh/m²/anno")
    table.add_row("Inclinazione ottimale", f"{result.solar_data.optimal_tilt}°")
    table.add_row("Azimut ottimale", f"{result.solar_data.optimal_azimuth}°")
    table.add_row("Produzione per kWp", f"{result.solar_data.annual_production_per_kwp} kWh/kWp/anno")

    console.print(table)

    if result.warnings:
        for w in result.warnings:
            console.print(f"⚠️  {w}", style="yellow")


@app.command()
def generate(
    address: str = typer.Option(..., "--address", "-a", help="Indirizzo italiano"),
    consumption: float = typer.Option(..., "--consumption", "-c", help="Consumo annuo kWh"),
    roof_area: float = typer.Option(..., "--roof-area", "-r", help="Area tetto disponibile m²"),
    output: str = typer.Option("capitolato.docx", "--output", "-o", help="File di output"),
) -> None:
    """Genera un capitolato tecnico completo."""
    from solarspec import SolarSpec

    spec = SolarSpec()

    with console.status("Analisi del sito..."):
        design = spec.design(
            address=address,
            annual_consumption_kwh=consumption,
            roof_area_m2=roof_area,
        )

    # Summary
    console.print(f"\n⚡ Impianto dimensionato: [bold green]{design.system_size_kwp} kWp[/]")
    console.print(f"   Moduli: {design.num_panels}")
    console.print(f"   Produzione stimata: {design.estimated_production_kwh:.0f} kWh/anno")
    if design.economics:
        console.print(f"   Costo stimato: €{design.economics.total_cost_eur:,.0f}")
        console.print(f"   Rientro: {design.economics.payback_years} anni")

    with console.status("Generazione documento..."):
        path = spec.generate_document(design=design, output_path=output)

    console.print(f"\n✅ Capitolato generato: [bold]{path}[/]")


@app.command()
def version() -> None:
    """Mostra la versione di SolarSpec."""
    from solarspec import __version__

    console.print(f"SolarSpec v{__version__}")


if __name__ == "__main__":
    app()
