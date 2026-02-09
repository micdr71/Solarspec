# SolarSpec

**Generatore intelligente di capitolati tecnici per impianti fotovoltaici in Italia**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

---

## Cosa fa SolarSpec?

SolarSpec trasforma un indirizzo italiano in un **capitolato tecnico completo** per l'installazione di un impianto fotovoltaico. Automatizza il lavoro che oggi richiede ore di analisi manuale, integrando dati geografici, solari, normativi ed economici in un unico flusso.

**Il problema:** gli installatori fotovoltaici in Italia dedicano 2-4 ore per ogni preventivo tecnico, raccogliendo manualmente dati da fonti diverse (PVGIS, normative, listini). SolarSpec riduce questo processo a pochi minuti.

```
Indirizzo --> Geocoding --> Analisi solare PVGIS --> Zona climatica/sismica
                                                          |
                                                          v
   Capitolato PDF/DOCX <-- Analisi economica <-- Dimensionamento impianto
```

---

## Funzionalita'

| Modulo | Descrizione | Stato |
|--------|-------------|-------|
| **Geo Analysis** | Geocoding Nominatim, zona climatica (A-F), zona sismica (1-4) per 110+ comuni | Completo |
| **Solar Analysis** | Irraggiamento via PVGIS API, inclinazione/azimut ottimali, producibilita' per kWp | Completo |
| **System Design** | Dimensionamento impianto, selezione automatica modulo e inverter da catalogo | Completo |
| **Economics** | Costi, ROI 25 anni, LCOE, detrazioni fiscali 50%, SSP/RID, payback | Completo |
| **Doc Generator** | Generazione capitolato tecnico in DOCX e PDF (via WeasyPrint) | Completo |
| **Web Interface** | Interfaccia grafica web con FastAPI, 3 step interattivi, mappa, grafici | Completo |
| **PV Catalog** | Database prodotti: 6 moduli (LONGi, Trina, JA Solar, SunPower, Canadian Solar, REC) + 10 inverter (Huawei, SMA, Fronius, SolarEdge) | Completo |
| **AI Layer** | Narrativa tecnica via Claude API (Anthropic), 6 sezioni generate automaticamente | Completo |

---

## Quick Start

### Installazione

```bash
git clone https://github.com/micdr71/Solarspec.git
cd Solarspec

# Crea ambiente virtuale
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Installa con tutte le dipendenze
pip install -e ".[all]"
```

### Interfaccia web (consigliato)

```bash
solarspec serve
# Apri nel browser: http://localhost:8000
```

L'interfaccia web guida l'utente in 3 step:
1. **Analisi Sito** -- inserisci un indirizzo, ottieni dati solari, mappa interattiva, grafico irraggiamento mensile
2. **Dimensionamento** -- inserisci consumo annuo e area tetto, ottieni progetto completo con componenti, economia, incentivi
3. **Genera Documento** -- scarica il capitolato tecnico in PDF o DOCX, oppure visualizza l'anteprima

### Uso via Python

```python
from solarspec import SolarSpec

spec = SolarSpec()

# Analisi sito
result = spec.analyze("Via Roma 1, 20121 Milano MI")
print(result.solar_data.annual_irradiation)       # kWh/m2/anno
print(result.solar_data.optimal_tilt)              # gradi
print(result.solar_data.annual_production_per_kwp) # kWh/kWp/anno

# Dimensionamento impianto
design = spec.design(
    address="Via Roma 1, 20121 Milano MI",
    annual_consumption_kwh=4500,
    roof_area_m2=40,
)

print(design.system_size_kwp)        # Potenza nominale (kWp)
print(design.num_panels)             # Numero moduli
print(design.estimated_production_kwh)  # Produzione stimata (kWh/anno)
print(design.economics.payback_years)   # Tempo di rientro (anni)
print(design.inverter.manufacturer)     # Inverter selezionato

# Genera capitolato PDF
spec.generate_document(design=design, output_path="capitolato.pdf", format="pdf")

# Oppure DOCX
spec.generate_document(design=design, output_path="capitolato.docx", format="docx")
```

### Uso via CLI

```bash
# Analisi rapida di un sito
solarspec analyze "Via Dante 10, 00100 Roma"

# Genera capitolato completo
solarspec generate \
    --address "Via Dante 10, 00100 Roma" \
    --consumption 5000 \
    --roof-area 50 \
    --output capitolato.docx

# Avvia server web
solarspec serve --port 8000

# Versione
solarspec version
```

### API REST

Con il server avviato (`solarspec serve`), sono disponibili i seguenti endpoint:

| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| GET | `/` | Interfaccia web |
| GET | `/api/health` | Health check |
| POST | `/api/analyze` | Analisi sito (geocoding + PVGIS) |
| POST | `/api/design` | Dimensionamento impianto completo |
| POST | `/api/generate` | Genera e scarica capitolato PDF/DOCX |
| POST | `/api/narrative` | Genera narrativa tecnica AI (richiede API key) |
| POST | `/api/preview` | Anteprima HTML del capitolato |
| GET | `/docs` | Documentazione interattiva Swagger |

Esempio con curl:

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"address": "Via Roma 1, Milano"}'
```

---

## Architettura

```
solarspec/
├── solarspec/
│   ├── __init__.py          # Classe SolarSpec (entry point principale)
│   ├── config.py            # Settings (Pydantic BaseSettings, env vars)
│   ├── models.py            # Modelli dati: Location, SiteData, SolarData,
│   │                        #   PVModule, Inverter, EconomicAnalysis, SystemDesign
│   ├── cli.py               # CLI Typer: analyze, generate, serve, version
│   ├── core/
│   │   ├── geo.py           # Geocoding Nominatim + DB zone climatiche/sismiche
│   │   ├── solar.py         # Integrazione PVGIS (irraggiamento, angoli ottimali)
│   │   └── narrative.py     # Narrativa tecnica AI via Claude API (Anthropic)
│   ├── generators/
│   │   ├── designer.py      # Dimensionamento, selezione inverter, analisi economica
│   │   └── document.py      # Generazione DOCX (python-docx) e PDF (WeasyPrint)
│   ├── api/
│   │   └── __init__.py      # FastAPI app + tutti gli endpoint + HTML inline
│   ├── data/
│   │   ├── climate_zones.json   # Zone climatiche per 110+ capoluoghi
│   │   ├── seismic_zones.json   # Zone sismiche per 110+ capoluoghi
│   │   └── products.json        # Catalogo moduli FV e inverter
│   └── web/
│       ├── static/
│       │   ├── style.css    # CSS interfaccia web
│       │   └── app.js       # JavaScript frontend
│       └── templates/
│           └── index.html   # Template HTML
├── tests/
│   ├── test_core.py         # Test modelli e designer
│   ├── test_geo.py          # Test zone climatiche e sismiche
│   ├── test_designer.py     # Test catalogo prodotti e selezione inverter
│   ├── test_api.py          # Test endpoint API
│   └── test_narrative.py    # Test narrativa AI (mock API)
├── examples/
│   └── quick_analysis.py    # Script esempio
├── docs/
│   └── CONTRIBUTING.md
├── pyproject.toml
└── README.md
```

### Stack tecnologico

| Componente | Tecnologia |
|-----------|-----------|
| Linguaggio | Python 3.11+ |
| Validazione dati | Pydantic v2 + pydantic-settings |
| HTTP client | HTTPX (per Nominatim e PVGIS) |
| Calcoli PV | pvlib |
| Generazione DOCX | python-docx |
| Generazione PDF | WeasyPrint |
| CLI | Typer + Rich |
| API web | FastAPI + Uvicorn |
| Frontend | HTML/CSS/JS (Leaflet per mappe, Chart.js per grafici) |
| AI narrativa | Anthropic Claude API (opzionale) |
| Test | Pytest |
| Linting | Ruff |

### API esterne utilizzate

| API | Uso | Costo |
|-----|-----|-------|
| [PVGIS (EU JRC)](https://re.jrc.ec.europa.eu/pvg_tools/en/) | Dati irraggiamento solare, angoli ottimali, producibilita' | Gratuita |
| [Nominatim (OpenStreetMap)](https://nominatim.org/) | Geocoding indirizzi italiani | Gratuita |
| [Anthropic Claude API](https://docs.anthropic.com/) | Narrativa tecnica AI per capitolati | A consumo (opzionale) |

---

## Database inclusi

### Catalogo prodotti PV

**Moduli fotovoltaici:**
- LONGi Hi-MO 6 (440 Wp, 22.3%)
- JA Solar JAM54S31 (410 Wp, 21.5%)
- Trina Solar Vertex S+ (445 Wp, 22.5%)
- SunPower Maxeon 6 (440 Wp, 22.8%)
- Canadian Solar HiHero (420 Wp, 21.8%)
- REC Alpha Pure-R (430 Wp, 22.2%)

**Inverter:**
- Huawei SUN2000 (3/5/6/10 kW)
- SMA Sunny Tripower (5/8 kW)
- Fronius Primo GEN24 (3/6 kW)
- SolarEdge SE-H-IT (5/10 kW)

### Zone climatiche e sismiche

Database JSON per 110+ capoluoghi di provincia italiani, con fallback automatico a livello regionale per i comuni non presenti.

---

## Analisi economica

Il dimensionamento include un'analisi economica completa:

- **Costo totale** e costo per kWp
- **Risparmio annuo** (autoconsumo + vendita energia)
- **Tempo di rientro** (payback) considerando incentivi
- **ROI a 25 anni**
- **LCOE** (Levelized Cost of Energy)
- **Detrazione fiscale 50%** -- max 96.000 EUR in 10 rate annuali
- **SSP** (Scambio Sul Posto) per impianti fino a 500 kWp
- **RID** (Ritiro Dedicato) per impianti piu' grandi

---

## AI Layer (Narrativa Tecnica)

SolarSpec integra l'API Claude di Anthropic per generare **narrativa tecnica professionale** in italiano, inserita automaticamente nel capitolato. L'AI produce 6 sezioni discorsive:

1. **Premessa** -- scopo del capitolato e contesto dell'installazione
2. **Analisi del sito** -- caratteristiche climatiche, sismiche e implicazioni progettuali
3. **Risorsa solare** -- commento sull'irraggiamento e confronto con la media italiana
4. **Dimensionamento** -- motivazioni tecniche per la scelta dei componenti
5. **Analisi economica** -- commento sulla convenienza e gli incentivi
6. **Conclusioni** -- sintesi e raccomandazioni tecniche

### Configurazione

```bash
# Imposta la chiave API Anthropic
export SOLARSPEC_ANTHROPIC_API_KEY="sk-ant-..."

# Opzionale: cambia modello (default: claude-sonnet-4-5-20250929)
export SOLARSPEC_ANTHROPIC_MODEL="claude-sonnet-4-5-20250929"
```

La narrativa AI e' **opzionale**: senza chiave API, SolarSpec genera documenti con solo i dati tecnici tabulari.

```python
# Uso via Python
spec = SolarSpec()
design = spec.design(address="Via Roma 1, Milano", annual_consumption_kwh=4500, roof_area_m2=40)

# Genera narrativa separatamente
narrative = spec.generate_narrative(design)
print(narrative["premessa"])

# Oppure includi automaticamente nel documento
spec.generate_document(design=design, output_path="capitolato.pdf", format="pdf")
```

---

## Normativa di riferimento

SolarSpec genera documentazione con riferimenti a:

- **CEI 0-21** -- Regola tecnica di connessione utenti attivi BT
- **CEI 0-16** -- Regola tecnica di connessione utenti attivi MT
- **D.Lgs. 199/2021** -- Attuazione direttiva RED II
- **DM 14/01/2008** -- Norme tecniche costruzioni (NTC)
- **D.L. 63/2013** -- Detrazioni fiscali ristrutturazione edilizia
- **Delibera ARERA 03/2020** -- Regolazione SSP

---

## Test

```bash
# Esegui tutti i test (31 test)
pytest

# Con coverage
pytest --cov=solarspec

# Solo test specifici
pytest tests/test_api.py -v
pytest tests/test_geo.py -v
```

---

## Contributing

I contributi sono benvenuti! Consulta [CONTRIBUTING.md](docs/CONTRIBUTING.md) per le linee guida.

### Aree dove servono contributi

- Ampliare il database zone climatiche/sismiche a tutti i comuni italiani
- Aggiungere altri prodotti al catalogo PV
- Analisi ombreggiamenti
- Integrazione catasto per dati edificio
- Deploy cloud (Railway, Render, Fly.io)

---

## Licenza

Distribuito sotto licenza MIT. Vedi [LICENSE](LICENSE) per dettagli.

---

## Contatti

Creato da **Michele** -- Ingegnere edile, imprenditore nel settore delle energie rinnovabili.

- [LuceViva](https://luceviva.org) -- Marketplace B2B per il fotovoltaico in Italia
