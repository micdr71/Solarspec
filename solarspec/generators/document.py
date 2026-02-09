"""Technical specification document generator."""

from __future__ import annotations

from solarspec.models import SystemDesign


def generate(
    design: SystemDesign,
    output_path: str,
    format: str = "docx",
) -> str:
    """Generate a technical specification document.

    Args:
        design: Complete system design.
        output_path: Output file path.
        format: Output format ('docx' or 'pdf').

    Returns:
        Path to the generated document.

    Raises:
        NotImplementedError: Document generation is under development.
    """
    if format == "docx":
        return _generate_docx(design, output_path)
    elif format == "pdf":
        return _generate_pdf(design, output_path)
    else:
        raise ValueError(f"Formato non supportato: {format}. Usa 'docx' o 'pdf'.")


def _generate_docx(design: SystemDesign, output_path: str) -> str:
    """Generate a DOCX technical specification."""
    try:
        from docx import Document
        from docx.shared import Inches, Pt
    except ImportError:
        raise ImportError("Installa python-docx: pip install python-docx")

    doc = Document()

    # Title
    doc.add_heading("Capitolato Tecnico — Impianto Fotovoltaico", level=0)

    # Site info
    doc.add_heading("1. Dati del sito", level=1)
    doc.add_paragraph(f"Indirizzo: {design.site.address}")
    doc.add_paragraph(
        f"Coordinate: {design.site.latitude:.5f}°N, {design.site.longitude:.5f}°E"
    )
    doc.add_paragraph(f"Comune: {design.site.municipality} ({design.site.province})")
    doc.add_paragraph(f"Zona climatica: {design.site.climate_zone}")
    doc.add_paragraph(f"Zona sismica: {design.site.seismic_zone}")

    # Solar data
    doc.add_heading("2. Analisi solare", level=1)
    doc.add_paragraph(
        f"Irraggiamento annuo (piano ottimale): {design.solar_data.annual_irradiation} kWh/m²/anno"
    )
    doc.add_paragraph(f"Inclinazione ottimale: {design.solar_data.optimal_tilt}°")
    doc.add_paragraph(f"Azimut ottimale: {design.solar_data.optimal_azimuth}°")
    doc.add_paragraph(
        f"Producibilità specifica: {design.solar_data.annual_production_per_kwp} kWh/kWp/anno"
    )

    # System design
    doc.add_heading("3. Dimensionamento impianto", level=1)
    doc.add_paragraph(f"Potenza nominale: {design.system_size_kwp} kWp")
    doc.add_paragraph(f"Numero moduli: {design.num_panels}")
    if design.module:
        doc.add_paragraph(
            f"Modulo: {design.module.manufacturer} {design.module.model} "
            f"({design.module.power_wp} Wp, η={design.module.efficiency}%)"
        )
    doc.add_paragraph(f"Produzione annua stimata: {design.estimated_production_kwh:.0f} kWh")
    doc.add_paragraph(f"Autoconsumo stimato: {design.self_consumption_rate}%")
    doc.add_paragraph(f"Performance Ratio: {design.performance_ratio}")

    # Economics
    if design.economics:
        doc.add_heading("4. Analisi economica", level=1)
        doc.add_paragraph(f"Costo totale stimato: €{design.economics.total_cost_eur:,.2f}")
        doc.add_paragraph(f"Costo per kWp: €{design.economics.cost_per_kwp:,.2f}/kWp")
        doc.add_paragraph(f"Risparmio annuo stimato: €{design.economics.annual_savings_eur:,.2f}")
        doc.add_paragraph(f"Tempo di rientro: {design.economics.payback_years} anni")
        doc.add_paragraph(f"ROI a 25 anni: {design.economics.roi_25y_percent}%")
        doc.add_paragraph(f"LCOE: €{design.economics.lcoe}/kWh")
        doc.add_paragraph(f"Incentivo: {design.economics.incentive_type}")

    # Notes
    if design.notes:
        doc.add_heading("5. Note", level=1)
        for note in design.notes:
            doc.add_paragraph(f"• {note}")

    # Normativa
    doc.add_heading("6. Riferimenti normativi", level=1)
    norms = [
        "CEI 0-21 — Regola tecnica di connessione utenti attivi BT",
        "CEI 0-16 — Regola tecnica di connessione utenti attivi MT",
        "D.Lgs. 199/2021 — Attuazione direttiva RED II",
        "DM 14/01/2008 — Norme tecniche costruzioni (NTC)",
    ]
    for norm in norms:
        doc.add_paragraph(f"• {norm}")

    # Footer
    doc.add_paragraph("")
    doc.add_paragraph("Documento generato con SolarSpec — https://github.com/YOUR_USERNAME/solarspec")

    doc.save(output_path)
    return output_path


def _generate_pdf(design: SystemDesign, output_path: str) -> str:
    """Generate a PDF technical specification."""
    # TODO: Implement PDF generation via WeasyPrint
    raise NotImplementedError(
        "Generazione PDF in fase di sviluppo. Usa format='docx' per ora."
    )
