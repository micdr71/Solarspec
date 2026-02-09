"""FastAPI application for SolarSpec web interface."""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

from solarspec import SolarSpec
from solarspec.generators.document import _build_html


def _make_spec(api_key: str | None = None) -> SolarSpec:
    """Create a SolarSpec instance, optionally with a runtime API key."""
    spec = SolarSpec()
    if api_key:
        spec.settings = spec.settings.model_copy(update={"anthropic_api_key": api_key})
    return spec

app = FastAPI(
    title="SolarSpec API",
    description="API per la generazione di capitolati tecnici per impianti fotovoltaici in Italia",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request/Response models ---


class AnalyzeRequest(BaseModel):
    address: str = Field(description="Indirizzo italiano completo")


class DesignRequest(BaseModel):
    address: str = Field(description="Indirizzo italiano completo")
    annual_consumption_kwh: float = Field(description="Consumo annuo in kWh")
    roof_area_m2: float = Field(description="Area tetto disponibile in m2")
    roof_tilt: float | None = Field(default=None, description="Inclinazione tetto (gradi)")
    roof_azimuth: float | None = Field(default=None, description="Azimut tetto (gradi, 0=Sud)")
    api_key: str | None = Field(default=None, description="Chiave API Anthropic (opzionale)")


class GenerateRequest(BaseModel):
    address: str
    annual_consumption_kwh: float
    roof_area_m2: float
    roof_tilt: float | None = None
    roof_azimuth: float | None = None
    format: str = Field(default="pdf", description="Formato output: 'docx' o 'pdf'")
    api_key: str | None = Field(default=None, description="Chiave API Anthropic (opzionale)")


# --- Inline HTML page (no static files needed) ---

_CSS_PATH = Path(__file__).resolve().parent.parent / "web" / "static" / "style.css"
_JS_PATH = Path(__file__).resolve().parent.parent / "web" / "static" / "app.js"
_HTML_PATH = Path(__file__).resolve().parent.parent / "web" / "templates" / "index.html"

# Cache inline page at startup
_INLINE_PAGE: str | None = None


def _build_inline_page() -> str:
    """Build a fully self-contained HTML page with inline CSS and JS."""
    global _INLINE_PAGE
    if _INLINE_PAGE is not None:
        return _INLINE_PAGE

    css = _CSS_PATH.read_text(encoding="utf-8") if _CSS_PATH.exists() else ""
    js = _JS_PATH.read_text(encoding="utf-8") if _JS_PATH.exists() else ""

    _INLINE_PAGE = _render_inline_html(css, js)
    return _INLINE_PAGE


def _render_inline_html(css: str, js: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SolarSpec — Generatore Capitolati Tecnici FV</title>
<style>{css}</style>
</head>
<body>

<header class="header">
    <div class="header-content">
        <div class="logo">
            <span class="logo-icon">&#9728;</span>
            <div>
                <h1>SolarSpec</h1>
                <p>Generatore capitolati tecnici per impianti fotovoltaici</p>
            </div>
        </div>
        <span class="header-badge">v0.1.0 Alpha</span>
    </div>
</header>

<div class="container">
    <div class="tabs">
        <button class="tab-btn active" data-tab="tab-analyze">
            <span class="step-num">1</span> Analisi Sito
        </button>
        <button class="tab-btn" data-tab="tab-design">
            <span class="step-num">2</span> Dimensionamento
        </button>
        <button class="tab-btn" data-tab="tab-generate" style="opacity:0.5;pointer-events:none;">
            <span class="step-num">3</span> Genera Documento
        </button>
    </div>

    <!-- TAB 1: ANALISI -->
    <div id="tab-analyze" class="tab-panel active">
        <div class="card">
            <div class="card-title"><span class="icon">&#128205;</span> Analisi del sito</div>
            <p style="color:var(--text-light);margin-bottom:20px;">
                Inserisci un indirizzo italiano per ottenere l'analisi solare completa del sito.
            </p>
            <div class="form-group">
                <label class="form-label" for="analyze-address">Indirizzo</label>
                <input type="text" id="analyze-address" class="form-input"
                       placeholder="Es. Via Roma 1, 20121 Milano MI" autocomplete="off">
                <p class="form-hint">Indirizzo completo con numero civico, CAP, comune e provincia</p>
            </div>
            <div id="analyze-error" class="error-msg"></div>
            <button id="analyze-btn" class="btn btn-primary" onclick="analyzeAddress()">
                &#128269; Analizza sito
            </button>
        </div>
        <div id="analyze-spinner" class="spinner">
            <div class="spinner-circle"></div>
            <p class="spinner-text">Analisi in corso... (geocoding + dati solari PVGIS)</p>
        </div>
        <div id="analyze-results" style="display:none;">
            <div class="results-grid" style="margin-bottom:20px;">
                <div class="result-card"><h3>Irraggiamento annuo</h3><div class="result-value" id="res-irradiation">-</div></div>
                <div class="result-card"><h3>Inclinazione ottimale</h3><div class="result-value" id="res-tilt">-</div></div>
                <div class="result-card"><h3>Azimut ottimale</h3><div class="result-value" id="res-azimuth">-</div></div>
                <div class="result-card highlight"><h3>Producibilita' per kWp</h3><div class="result-value" id="res-production">-</div></div>
            </div>
            <div class="form-row">
                <div class="card">
                    <div class="card-title"><span class="icon">&#127968;</span> Dati del sito</div>
                    <table class="data-table">
                        <tr><td>Indirizzo</td><td id="res-address">-</td></tr>
                        <tr><td>Coordinate</td><td id="res-coords">-</td></tr>
                        <tr><td>Comune</td><td id="res-municipality">-</td></tr>
                        <tr><td>Regione</td><td id="res-region">-</td></tr>
                        <tr><td>Zona climatica</td><td id="res-climate">-</td></tr>
                        <tr><td>Zona sismica</td><td id="res-seismic">-</td></tr>
                    </table>
                </div>
                <div class="card">
                    <div class="card-title"><span class="icon">&#127758;</span> Mappa</div>
                    <div id="map"></div>
                </div>
            </div>
            <div class="card">
                <div class="card-title"><span class="icon">&#128200;</span> Irraggiamento mensile</div>
                <div class="chart-container"><canvas id="monthly-chart"></canvas></div>
            </div>
            <div style="text-align:center;margin-top:20px;">
                <button class="btn btn-secondary" onclick="switchTab('tab-design')">Procedi al dimensionamento &#8594;</button>
            </div>
        </div>
    </div>

    <!-- TAB 2: DIMENSIONAMENTO -->
    <div id="tab-design" class="tab-panel">
        <div class="card">
            <div class="card-title"><span class="icon">&#9889;</span> Dimensionamento impianto</div>
            <p style="color:var(--text-light);margin-bottom:20px;">
                Inserisci i dati di consumo e tetto per dimensionare l'impianto ottimale.
            </p>
            <div class="form-group">
                <label class="form-label" for="design-address">Indirizzo</label>
                <input type="text" id="design-address" class="form-input" placeholder="Es. Via Roma 1, 20121 Milano MI">
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label class="form-label" for="design-consumption">Consumo annuo (kWh)</label>
                    <input type="number" id="design-consumption" class="form-input" placeholder="Es. 4500" min="100" step="100">
                    <p class="form-hint">Dalla bolletta elettrica annuale</p>
                </div>
                <div class="form-group">
                    <label class="form-label" for="design-roof-area">Area tetto disponibile (m&sup2;)</label>
                    <input type="number" id="design-roof-area" class="form-input" placeholder="Es. 40" min="2" step="1">
                    <p class="form-hint">Superficie utilizzabile per i pannelli</p>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label class="form-label" for="design-tilt">Inclinazione tetto (opzionale)</label>
                    <input type="number" id="design-tilt" class="form-input" placeholder="Lascia vuoto per ottimale" min="0" max="90" step="1">
                </div>
                <div class="form-group">
                    <label class="form-label" for="design-azimuth">Azimut tetto (opzionale)</label>
                    <input type="number" id="design-azimuth" class="form-input" placeholder="Lascia vuoto per ottimale" min="-180" max="180" step="1">
                </div>
            </div>
            <div id="design-error" class="error-msg"></div>
            <button id="design-btn" class="btn btn-primary" onclick="designSystem()">&#9889; Dimensiona impianto</button>
        </div>
        <div id="design-spinner" class="spinner"><div class="spinner-circle"></div><p class="spinner-text">Dimensionamento in corso...</p></div>
        <div id="design-results" style="display:none;">
            <div class="results-grid" style="margin-bottom:20px;">
                <div class="result-card highlight"><h3>Potenza impianto</h3><div class="result-value" id="des-kwp">-</div></div>
                <div class="result-card"><h3>Numero moduli</h3><div class="result-value" id="des-panels">-</div></div>
                <div class="result-card"><h3>Produzione annua</h3><div class="result-value" id="des-production">-</div></div>
                <div class="result-card"><h3>Autoconsumo</h3><div class="result-value" id="des-selfcons">-</div></div>
            </div>
            <div class="form-row">
                <div class="card">
                    <div class="card-title"><span class="icon">&#128268;</span> Componenti</div>
                    <table class="data-table">
                        <tr><td>Modulo FV</td><td id="des-module">-</td></tr>
                        <tr id="des-inverter-row"><td>Inverter</td><td id="des-inverter">-</td></tr>
                        <tr><td>Performance Ratio</td><td>0.80</td></tr>
                    </table>
                </div>
                <div class="card">
                    <div class="card-title"><span class="icon">&#128176;</span> Analisi economica</div>
                    <table class="data-table">
                        <tr><td>LCOE</td><td id="des-lcoe">-</td></tr>
                        <tr><td>Incentivo</td><td id="des-incentive">-</td></tr>
                        <tr><td>Valore incentivi (25a)</td><td id="des-incentive-val">-</td></tr>
                    </table>
                </div>
            </div>
            <div class="results-grid" style="margin-bottom:20px;">
                <div class="result-card"><h3>Costo totale</h3><div class="result-value" id="des-cost">-</div></div>
                <div class="result-card highlight"><h3>Risparmio annuo</h3><div class="result-value" id="des-savings">-</div></div>
                <div class="result-card"><h3>Tempo di rientro</h3><div class="result-value" id="des-payback">-</div></div>
                <div class="result-card highlight"><h3>ROI 25 anni</h3><div class="result-value" id="des-roi">-</div></div>
            </div>
            <div id="des-notes-section" class="card" style="display:none;">
                <div class="card-title"><span class="icon">&#128221;</span> Note</div>
                <ul class="notes-list" id="des-notes"></ul>
            </div>
            <div style="text-align:center;margin-top:20px;">
                <button class="btn btn-secondary" onclick="switchTab('tab-generate')">Genera capitolato &#8594;</button>
            </div>
        </div>
    </div>

    <!-- TAB 3: GENERA DOCUMENTO -->
    <div id="tab-generate" class="tab-panel">
        <div class="card">
            <div class="card-title"><span class="icon">&#129302;</span> AI Narrativa (opzionale)</div>
            <p style="color:var(--text-light);margin-bottom:16px;">
                Inserisci la tua chiave API Anthropic per arricchire il capitolato con narrativa tecnica professionale generata dall'AI.
            </p>
            <div class="form-group" style="margin-bottom:12px;">
                <label class="form-label" for="api-key">Chiave API Anthropic</label>
                <div class="api-key-wrapper">
                    <input type="password" id="api-key" class="form-input" placeholder="sk-ant-..." autocomplete="off">
                    <button type="button" class="btn-toggle-key" onclick="toggleApiKey()">Mostra</button>
                </div>
                <p class="form-hint">La chiave viene usata solo per questa sessione e non viene salvata. <a href="https://console.anthropic.com/" target="_blank" rel="noopener">Ottieni una chiave</a></p>
            </div>
            <div id="ai-status" class="ai-badge inactive">Narrativa AI non attiva</div>
        </div>
        <div class="card">
            <div class="card-title"><span class="icon">&#128196;</span> Genera Capitolato Tecnico</div>
            <p style="color:var(--text-light);margin-bottom:24px;">
                Genera il capitolato tecnico completo in formato PDF o DOCX, oppure visualizza l'anteprima.
            </p>
            <div id="generate-error" class="error-msg"></div>
            <div class="btn-group">
                <button class="btn btn-primary" onclick="generateDocument('pdf')">&#128196; Scarica PDF</button>
                <button class="btn btn-outline" onclick="generateDocument('docx')">&#128196; Scarica DOCX</button>
                <button class="btn btn-secondary" onclick="previewDocument()">&#128065; Anteprima</button>
            </div>
        </div>
        <div id="generate-spinner" class="spinner"><div class="spinner-circle"></div><p class="spinner-text">Generazione documento...</p></div>
    </div>
</div>

<div id="preview-modal" class="modal-overlay">
    <div class="modal-content">
        <div class="modal-header">
            <h3>Anteprima Capitolato Tecnico</h3>
            <button class="modal-close" onclick="closePreview()">&times;</button>
        </div>
        <div class="modal-body"><iframe id="preview-iframe"></iframe></div>
    </div>
</div>

<footer class="footer">SolarSpec v0.1.0 &mdash; Generatore intelligente di capitolati tecnici per impianti fotovoltaici in Italia</footer>

<script>{js}</script>
<script>
(function(){{
    function loadScript(src){{
        var s=document.createElement('script');s.src=src;s.async=true;
        s.onerror=function(){{console.warn('CDN non raggiungibile: '+src);}};
        document.body.appendChild(s);
    }}
    loadScript('https://unpkg.com/leaflet@1.9.4/dist/leaflet.js');
    loadScript('https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js');
    var lnk=document.createElement('link');lnk.rel='stylesheet';
    lnk.href='https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
    document.head.appendChild(lnk);
}})();
</script>
</body>
</html>"""


# --- Routes ---


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main web page (fully inline, no static files needed)."""
    return HTMLResponse(content=_build_inline_page())


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest):
    """Analyze a site from an address."""
    try:
        spec = SolarSpec()
        result = spec.analyze(req.address)
        return result.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore durante l'analisi: {e}")


@app.post("/api/design")
async def design(req: DesignRequest):
    """Design a PV system."""
    try:
        spec = SolarSpec()
        result = spec.design(
            address=req.address,
            annual_consumption_kwh=req.annual_consumption_kwh,
            roof_area_m2=req.roof_area_m2,
            roof_tilt=req.roof_tilt,
            roof_azimuth=req.roof_azimuth,
        )
        return result.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore durante il dimensionamento: {e}")


@app.post("/api/generate")
async def generate_document(req: GenerateRequest):
    """Generate and download a technical specification document."""
    try:
        spec = _make_spec(req.api_key)
        result = spec.design(
            address=req.address,
            annual_consumption_kwh=req.annual_consumption_kwh,
            roof_area_m2=req.roof_area_m2,
            roof_tilt=req.roof_tilt,
            roof_azimuth=req.roof_azimuth,
        )

        ext = "pdf" if req.format == "pdf" else "docx"
        suffix = f".{ext}"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            output_path = f.name

        spec.generate_document(design=result, output_path=output_path, format=req.format)

        media_type = (
            "application/pdf"
            if ext == "pdf"
            else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        return FileResponse(
            path=output_path,
            media_type=media_type,
            filename=f"capitolato_tecnico.{ext}",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore nella generazione: {e}")


@app.post("/api/narrative")
async def narrative(req: DesignRequest):
    """Generate AI-powered technical narrative for a system design."""
    try:
        spec = _make_spec(req.api_key)
        result = spec.design(
            address=req.address,
            annual_consumption_kwh=req.annual_consumption_kwh,
            roof_area_m2=req.roof_area_m2,
            roof_tilt=req.roof_tilt,
            roof_azimuth=req.roof_azimuth,
        )
        narr = spec.generate_narrative(result)
        return {"narrative": narr, "available": bool(narr)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore nella generazione narrativa: {e}")


@app.post("/api/preview")
async def preview_document(req: DesignRequest):
    """Generate an HTML preview of the technical specification."""
    try:
        spec = _make_spec(req.api_key)
        result = spec.design(
            address=req.address,
            annual_consumption_kwh=req.annual_consumption_kwh,
            roof_area_m2=req.roof_area_m2,
            roof_tilt=req.roof_tilt,
            roof_azimuth=req.roof_azimuth,
        )
        narr = spec.generate_narrative(result)
        html = _build_html(result, narrative=narr or None)
        return {"html": html}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore nella preview: {e}")
