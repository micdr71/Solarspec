"""AI-powered technical narrative generation using Claude API."""

from __future__ import annotations

import logging

from solarspec.config import Settings
from solarspec.models import SystemDesign

logger = logging.getLogger(__name__)

# System prompt in Italian for the technical writer persona
_SYSTEM_PROMPT = """\
Sei un ingegnere fotovoltaico italiano esperto nella redazione di capitolati tecnici.
Scrivi in italiano tecnico-professionale, preciso e formale ma chiaro.
Non inventare dati: usa esclusivamente i dati forniti nel contesto.
Non usare markdown, emoji o formattazione speciale: scrivi solo testo piano.
Ogni sezione deve essere un paragrafo discorsivo di 3-6 frasi."""


def _build_narrative_prompt(design: SystemDesign) -> str:
    """Build the user prompt with all project data for the AI to narrate."""
    module_info = ""
    if design.module:
        module_info = (
            f"Modulo selezionato: {design.module.manufacturer} {design.module.model}, "
            f"potenza {design.module.power_wp} Wp, efficienza {design.module.efficiency}%, "
            f"area {design.module.area_m2} m2, garanzia {design.module.warranty_years} anni, "
            f"degradazione annua {design.module.degradation_rate}%."
        )

    inverter_info = ""
    if design.inverter:
        inverter_info = (
            f"Inverter selezionato: {design.inverter.manufacturer} {design.inverter.model}, "
            f"potenza AC {design.inverter.power_kw} kW, potenza DC max {design.inverter.max_dc_power_kw} kW, "
            f"efficienza europea {design.inverter.efficiency}%, "
            f"canali MPPT {design.inverter.mppt_channels}, garanzia {design.inverter.warranty_years} anni."
        )

    economics_info = ""
    if design.economics:
        e = design.economics
        economics_info = (
            f"Costo totale stimato: {e.total_cost_eur:.2f} EUR ({e.cost_per_kwp:.2f} EUR/kWp). "
            f"Risparmio annuo: {e.annual_savings_eur:.2f} EUR. "
            f"Tempo di rientro: {e.payback_years} anni. "
            f"ROI a 25 anni: {e.roi_25y_percent}%. "
            f"LCOE: {e.lcoe} EUR/kWh. "
            f"Incentivo: {e.incentive_type}, valore totale {e.incentive_value_eur:.2f} EUR."
        )

    monthly = ""
    if design.solar_data.monthly_irradiation:
        labels = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
        pairs = [f"{labels[i]}: {v}" for i, v in enumerate(design.solar_data.monthly_irradiation) if i < 12]
        monthly = f"Irraggiamento mensile (kWh/m2): {', '.join(pairs)}."

    notes_info = ""
    if design.notes:
        notes_info = "Note tecniche: " + "; ".join(design.notes)

    return f"""\
Genera la narrativa tecnica per il capitolato di un impianto fotovoltaico con i seguenti dati.

DATI DEL SITO:
Indirizzo: {design.site.address}
Coordinate: {design.site.latitude:.5f} N, {design.site.longitude:.5f} E
Comune: {design.site.municipality} ({design.site.province}), Regione: {design.site.region}
Zona climatica: {design.site.climate_zone}
Zona sismica: {design.site.seismic_zone}

DATI SOLARI:
Irraggiamento annuo: {design.solar_data.annual_irradiation} kWh/m2/anno
Inclinazione ottimale: {design.solar_data.optimal_tilt} gradi
Azimut ottimale: {design.solar_data.optimal_azimuth} gradi
Producibilita specifica: {design.solar_data.annual_production_per_kwp} kWh/kWp/anno
{monthly}

DIMENSIONAMENTO:
Potenza nominale: {design.system_size_kwp} kWp
Numero moduli: {design.num_panels}
{module_info}
{inverter_info}
Produzione annua stimata: {design.estimated_production_kwh:.0f} kWh
Autoconsumo stimato: {design.self_consumption_rate}%
Performance Ratio: {design.performance_ratio}

ANALISI ECONOMICA:
{economics_info}

{notes_info}

Scrivi le seguenti sezioni, ciascuna come paragrafo narrativo di 3-6 frasi:

1. PREMESSA: Descrivi brevemente lo scopo del capitolato e il contesto dell'installazione.

2. ANALISI DEL SITO: Descrivi la localizzazione, le caratteristiche climatiche e sismiche del sito e le implicazioni per la progettazione.

3. RISORSA SOLARE: Commenta l'irraggiamento del sito, la producibilita attesa e come si colloca rispetto alla media italiana.

4. DIMENSIONAMENTO DELL'IMPIANTO: Descrivi la scelta dei componenti (moduli e inverter), il numero di pannelli, la potenza totale e le motivazioni tecniche.

5. ANALISI ECONOMICA: Commenta la convenienza dell'investimento, il tempo di rientro, gli incentivi applicabili e il rendimento a lungo termine.

6. CONCLUSIONI: Sintesi finale con raccomandazioni tecniche.

Separa ogni sezione con una riga vuota e il titolo della sezione in maiuscolo seguito da due punti."""


def generate_narrative(
    design: SystemDesign,
    settings: Settings | None = None,
) -> dict[str, str]:
    """Generate AI-powered technical narrative sections for a system design.

    Uses the Anthropic Claude API to produce professional Italian technical text.
    Falls back to empty dict if the API key is not configured or the call fails.

    Args:
        design: Complete system design with all data.
        settings: Optional settings (for API key and model).

    Returns:
        Dict mapping section names to narrative text paragraphs.
        Keys: "premessa", "analisi_sito", "risorsa_solare",
              "dimensionamento", "analisi_economica", "conclusioni".
        Empty dict if AI is unavailable.
    """
    settings = settings or Settings()

    if not settings.anthropic_api_key:
        logger.info("Chiave API Anthropic non configurata, narrativa AI non disponibile.")
        return {}

    try:
        import anthropic
    except ImportError:
        logger.warning("Pacchetto 'anthropic' non installato. Installa con: pip install solarspec[ai]")
        return {}

    prompt = _build_narrative_prompt(design)

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        message = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=2000,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract text from response
        raw_text = ""
        for block in message.content:
            if block.type == "text":
                raw_text += block.text

        return _parse_sections(raw_text)

    except Exception as e:
        logger.error("Errore nella generazione della narrativa AI: %s", e)
        return {}


def _parse_sections(text: str) -> dict[str, str]:
    """Parse the AI response into named sections."""
    sections: dict[str, str] = {}
    section_map = {
        "PREMESSA": "premessa",
        "ANALISI DEL SITO": "analisi_sito",
        "RISORSA SOLARE": "risorsa_solare",
        "DIMENSIONAMENTO": "dimensionamento",
        "DIMENSIONAMENTO DELL'IMPIANTO": "dimensionamento",
        "ANALISI ECONOMICA": "analisi_economica",
        "CONCLUSIONI": "conclusioni",
    }

    current_key: str | None = None
    current_lines: list[str] = []

    for line in text.split("\n"):
        stripped = line.strip()
        # Check if this line is a section header
        matched = False
        for header, key in section_map.items():
            if stripped.upper().startswith(header):
                # Save previous section
                if current_key and current_lines:
                    sections[current_key] = "\n".join(current_lines).strip()
                current_key = key
                current_lines = []
                # Check if there's text after the header on the same line
                rest = stripped[len(header):].lstrip(":").lstrip()
                if rest:
                    current_lines.append(rest)
                matched = True
                break
        if not matched and current_key is not None:
            current_lines.append(line.rstrip())

    # Save last section
    if current_key and current_lines:
        sections[current_key] = "\n".join(current_lines).strip()

    return sections
