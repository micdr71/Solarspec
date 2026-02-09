# ☀️ SolarSpec

**Generatore intelligente di capitolati tecnici per impianti fotovoltaici in Italia**

*Automated technical specification generator for photovoltaic installations in Italy*

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

---

## 🎯 Cosa fa SolarSpec?

SolarSpec trasforma un indirizzo italiano in un **capitolato tecnico completo** per l'installazione di un impianto fotovoltaico. Automatizza il lavoro che oggi richiede ore di analisi manuale, integrando dati geografici, normativi ed economici in un unico flusso.

### Il problema
Gli installatori fotovoltaici in Italia dedicano **2-4 ore per ogni preventivo tecnico**, raccogliendo manualmente dati da fonti diverse (catasto, PVGIS, normative locali, listini). SolarSpec riduce questo processo a **pochi minuti**.

### La soluzione

```
📍 Indirizzo → 🔍 Analisi automatica → 📄 Capitolato tecnico completo
```

1. **Input**: indirizzo o coordinate GPS
2. **Analisi**: irraggiamento solare, vincoli urbanistici, zona climatica e sismica
3. **Dimensionamento**: calcolo ottimale dell'impianto con selezione componenti
4. **Output**: documento tecnico conforme alla normativa italiana

---

## ✨ Funzionalità

| Modulo | Descrizione | Stato |
|--------|-------------|-------|
| 🌍 **Geo Analysis** | Geocoding, zona climatica, zona sismica, vincoli paesaggistici | 🔨 In sviluppo |
| ☀️ **Solar Analysis** | Irraggiamento via PVGIS API, analisi ombreggiamenti, orientamento ottimale | 🔨 In sviluppo |
| ⚡ **System Design** | Dimensionamento impianto, selezione inverter/moduli, schema elettrico | 📋 Pianificato |
| 📋 **Compliance** | Normativa CEI 0-21, pratiche GSE, regolamenti comunali | 📋 Pianificato |
| 💰 **Economics** | Stima costi, analisi ROI, simulazione incentivi (SSP, RID, detrazioni) | 📋 Pianificato |
| 📄 **Doc Generator** | Generazione capitolato in DOCX/PDF conforme | 📋 Pianificato |
| 🤖 **AI Layer** | Narrativa tecnica via LLM, Q&A sul progetto | 📋 Pianificato |

---

## 🚀 Quick Start

### Installazione

```bash
# Clone del repository
git clone https://github.com/YOUR_USERNAME/solarspec.git
cd solarspec

# Crea ambiente virtuale
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Installa dipendenze
pip install -e ".[dev]"
```

### Uso base

```python
from solarspec import SolarSpec

# Inizializza il generatore
spec = SolarSpec()

# Analisi da indirizzo
result = spec.analyze("Via Roma 1, 20121 Milano MI")

# Mostra risultati analisi solare
print(result.solar_data.annual_irradiation)  # kWh/m²/anno
print(result.solar_data.optimal_tilt)        # gradi
print(result.solar_data.optimal_azimuth)     # gradi

# Dimensiona l'impianto
design = spec.design(
    address="Via Roma 1, 20121 Milano MI",
    annual_consumption_kwh=4500,  # consumo annuo famiglia
    roof_area_m2=40,
)

print(design.system_size_kwp)      # Potenza nominale
print(design.num_panels)           # Numero moduli
print(design.estimated_production) # Produzione stimata kWh/anno
print(design.self_consumption_rate) # % autoconsumo

# Genera il capitolato tecnico
spec.generate_document(
    design=design,
    output_path="capitolato_via_roma_1.docx",
    format="docx"
)
```

### Uso via CLI

```bash
# Analisi rapida
solarspec analyze "Via Dante 10, 00100 Roma"

# Genera capitolato completo
solarspec generate \
    --address "Via Dante 10, 00100 Roma" \
    --consumption 5000 \
    --roof-area 50 \
    --output capitolato.docx
```

### Uso via API (FastAPI)

```bash
# Avvia il server
solarspec serve --port 8000

# Endpoint disponibili:
# POST /api/v1/analyze      - Analisi sito
# POST /api/v1/design       - Dimensionamento
# POST /api/v1/generate     - Genera documento
# GET  /api/v1/products     - Database prodotti
```

---

## 🏗️ Architettura

```
solarspec/
├── solarspec/
│   ├── __init__.py          # Package principale + classe SolarSpec
│   ├── config.py            # Configurazione e settings
│   ├── models.py            # Modelli dati (Pydantic)
│   ├── core/
│   │   ├── geo.py           # Geocoding e analisi geografica
│   │   ├── solar.py         # Analisi solare (PVGIS integration)
│   │   ├── climate.py       # Zone climatiche italiane
│   │   ├── seismic.py       # Classificazione sismica
│   │   └── compliance.py    # Verifica normativa
│   ├── generators/
│   │   ├── designer.py      # Dimensionamento impianto
│   │   ├── economics.py     # Analisi economica
│   │   └── document.py      # Generazione documenti
│   ├── api/
│   │   ├── app.py           # FastAPI application
│   │   └── routes.py        # API endpoints
│   ├── data/
│   │   ├── climate_zones.json    # Zone climatiche per comune
│   │   ├── seismic_zones.json    # Zone sismiche per comune
│   │   └── products/             # Database prodotti (moduli, inverter)
│   └── utils/
│       ├── geocoding.py     # Utility geocoding
│       └── units.py         # Conversioni unità di misura
├── tests/
├── docs/
├── examples/
├── pyproject.toml
└── README.md
```

### Stack tecnologico

- **Python 3.11+** — Linguaggio principale
- **Pydantic v2** — Validazione dati e modelli
- **HTTPX** — Client HTTP async per API esterne
- **pvlib** — Calcoli fotovoltaici (irraggiamento, produzione)
- **FastAPI** — API REST opzionale
- **python-docx** — Generazione documenti Word
- **WeasyPrint** — Generazione PDF
- **Ruff** — Linting e formatting

### API esterne utilizzate

| API | Uso | Costo |
|-----|-----|-------|
| [PVGIS (EU JRC)](https://re.jrc.ec.europa.eu/pvg_tools/en/) | Dati irraggiamento solare | Gratuita |
| [Nominatim (OpenStreetMap)](https://nominatim.org/) | Geocoding | Gratuita |
| [OpenMeteo](https://open-meteo.com/) | Dati meteo storici | Gratuita |

---

## 🇮🇹 Normativa di riferimento

SolarSpec genera documentazione conforme a:

- **CEI 0-21** — Regola tecnica di connessione utenti attivi BT
- **CEI 0-16** — Regola tecnica di connessione utenti attivi MT
- **D.Lgs. 199/2021** — Attuazione direttiva RED II
- **DM 14/01/2008** — Norme tecniche costruzioni (NTC)
- **GSE** — Procedure per Scambio Sul Posto e Ritiro Dedicato
- **Regolamenti edilizi comunali** — Vincoli locali

---

## 🤝 Contributing

I contributi sono benvenuti! Consulta [CONTRIBUTING.md](docs/CONTRIBUTING.md) per le linee guida.

### Come contribuire

1. Fork del repository
2. Crea un branch (`git checkout -b feature/nuova-funzionalita`)
3. Commit delle modifiche (`git commit -m 'Aggiunge nuova funzionalità'`)
4. Push sul branch (`git push origin feature/nuova-funzionalita`)
5. Apri una Pull Request

### Aree dove servono contributi

- 🗺️ Database vincoli paesaggistici per provincia
- ⚡ Database prodotti fotovoltaici aggiornato
- 📐 Template capitolati per diverse tipologie di impianto
- 🧪 Test e validazione calcoli

---

## 📜 Licenza

Distribuito sotto licenza MIT. Vedi [LICENSE](LICENSE) per dettagli.

---

## 📬 Contatti

Creato con ☀️ da **Michele** — Ingegnere edile, imprenditore nel settore delle energie rinnovabili.

- 🌐 [LuceViva](https://luceviva.it) — Marketplace B2B per il fotovoltaico in Italia

---

> *"Portare i metodi della progettazione parametrica nel mondo del fotovoltaico residenziale."*
