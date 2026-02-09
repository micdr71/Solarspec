"""Tests for the AI narrative module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from solarspec.config import Settings
from solarspec.core.narrative import (
    _build_narrative_prompt,
    _parse_sections,
    generate_narrative,
)
from solarspec.models import (
    EconomicAnalysis,
    Inverter,
    PVModule,
    SiteData,
    SolarData,
    SystemDesign,
)


def _make_design() -> SystemDesign:
    """Create a sample SystemDesign for testing."""
    return SystemDesign(
        site=SiteData(
            address="Via Roma 1, 20121 Milano MI",
            latitude=45.46427,
            longitude=9.18951,
            municipality="Milano",
            province="MI",
            region="Lombardia",
            climate_zone="E",
            seismic_zone=3,
        ),
        solar_data=SolarData(
            annual_irradiation=1250.5,
            optimal_tilt=35,
            optimal_azimuth=0,
            monthly_irradiation=[65, 80, 110, 140, 160, 170, 180, 165, 130, 100, 70, 55],
            annual_production_per_kwp=1180,
        ),
        system_size_kwp=4.4,
        num_panels=10,
        module=PVModule(
            manufacturer="LONGi",
            model="Hi-MO 6",
            power_wp=440,
            efficiency=22.3,
            area_m2=1.95,
        ),
        inverter=Inverter(
            manufacturer="Huawei",
            model="SUN2000-5KTL-M1",
            power_kw=5.0,
            max_dc_power_kw=7.5,
            efficiency=98.6,
            mppt_channels=2,
        ),
        estimated_production_kwh=5192,
        self_consumption_rate=55.0,
        performance_ratio=0.80,
        economics=EconomicAnalysis(
            total_cost_eur=6600.0,
            cost_per_kwp=1500.0,
            annual_savings_eur=1150.0,
            payback_years=5.7,
            roi_25y_percent=335.6,
            incentive_type="SSP (Scambio Sul Posto) + Detrazione 50%",
            incentive_value_eur=3500.0,
            lcoe=0.051,
        ),
        notes=["Inverter selezionato: Huawei SUN2000-5KTL-M1"],
    )


def test_build_narrative_prompt():
    """Test that the prompt builder includes all key data."""
    design = _make_design()
    prompt = _build_narrative_prompt(design)
    assert "Milano" in prompt
    assert "4.4" in prompt
    assert "LONGi" in prompt
    assert "Huawei" in prompt
    assert "1250.5" in prompt
    assert "PREMESSA" in prompt
    assert "CONCLUSIONI" in prompt


def test_parse_sections_basic():
    """Test parsing AI response into sections."""
    text = """PREMESSA:
Questo capitolato descrive l'impianto fotovoltaico.

ANALISI DEL SITO:
Il sito si trova a Milano, in zona climatica E.

RISORSA SOLARE:
L'irraggiamento annuo e' di 1250 kWh/m2.

DIMENSIONAMENTO DELL'IMPIANTO:
L'impianto prevede 10 moduli LONGi.

ANALISI ECONOMICA:
L'investimento ha un payback di 5.7 anni.

CONCLUSIONI:
Si raccomanda l'installazione."""

    sections = _parse_sections(text)
    assert "premessa" in sections
    assert "analisi_sito" in sections
    assert "risorsa_solare" in sections
    assert "dimensionamento" in sections
    assert "analisi_economica" in sections
    assert "conclusioni" in sections
    assert "Milano" in sections["analisi_sito"]
    assert "LONGi" in sections["dimensionamento"]


def test_parse_sections_empty():
    """Test parsing empty text."""
    assert _parse_sections("") == {}


def test_generate_narrative_no_api_key():
    """Test that narrative returns empty dict when no API key."""
    design = _make_design()
    settings = Settings(anthropic_api_key="")
    result = generate_narrative(design, settings=settings)
    assert result == {}


def test_generate_narrative_no_anthropic_package():
    """Test graceful fallback when anthropic package is not installed."""
    design = _make_design()
    settings = Settings(anthropic_api_key="sk-test-key")

    with patch.dict("sys.modules", {"anthropic": None}):
        result = generate_narrative(design, settings=settings)
        assert result == {}


def test_generate_narrative_api_error():
    """Test graceful fallback on API error."""
    design = _make_design()
    settings = Settings(anthropic_api_key="sk-test-key")

    mock_anthropic = MagicMock()
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception("API error")
    mock_anthropic.Anthropic.return_value = mock_client

    with patch.dict("sys.modules", {"anthropic": mock_anthropic}):
        result = generate_narrative(design, settings=settings)
        assert result == {}


def test_generate_narrative_success():
    """Test successful narrative generation with mocked API."""
    design = _make_design()
    settings = Settings(anthropic_api_key="sk-test-key")

    # Mock the anthropic module and response
    mock_block = MagicMock()
    mock_block.type = "text"
    mock_block.text = """PREMESSA:
Il presente capitolato tecnico descrive un impianto fotovoltaico a Milano.

ANALISI DEL SITO:
Il sito si trova in zona climatica E con rischio sismico 3.

RISORSA SOLARE:
L'irraggiamento annuo di 1250 kWh/m2 e' nella media del Nord Italia.

DIMENSIONAMENTO DELL'IMPIANTO:
L'impianto da 4.4 kWp utilizza 10 moduli LONGi Hi-MO 6.

ANALISI ECONOMICA:
Con un payback di 5.7 anni l'investimento e' molto conveniente.

CONCLUSIONI:
Si raccomanda di procedere con l'installazione."""

    mock_message = MagicMock()
    mock_message.content = [mock_block]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    mock_anthropic = MagicMock()
    mock_anthropic.Anthropic.return_value = mock_client

    with patch.dict("sys.modules", {"anthropic": mock_anthropic}):
        result = generate_narrative(design, settings=settings)

    assert len(result) == 6
    assert "premessa" in result
    assert "conclusioni" in result
    assert "Milano" in result["premessa"]
    assert "LONGi" in result["dimensionamento"]

    # Verify API was called correctly
    mock_client.messages.create.assert_called_once()
    call_kwargs = mock_client.messages.create.call_args
    assert call_kwargs.kwargs["model"] == "claude-sonnet-4-5-20250929"
    assert call_kwargs.kwargs["max_tokens"] == 2000
