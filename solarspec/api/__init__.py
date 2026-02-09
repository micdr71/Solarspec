"""FastAPI application for SolarSpec web interface."""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from solarspec import SolarSpec
from solarspec.generators.document import _build_html

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

# Serve static files
_STATIC_DIR = Path(__file__).resolve().parent.parent / "web" / "static"
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "web" / "templates"

if _STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


# --- Request/Response models ---


class AnalyzeRequest(BaseModel):
    address: str = Field(description="Indirizzo italiano completo")


class DesignRequest(BaseModel):
    address: str = Field(description="Indirizzo italiano completo")
    annual_consumption_kwh: float = Field(description="Consumo annuo in kWh")
    roof_area_m2: float = Field(description="Area tetto disponibile in m2")
    roof_tilt: float | None = Field(default=None, description="Inclinazione tetto (gradi)")
    roof_azimuth: float | None = Field(default=None, description="Azimut tetto (gradi, 0=Sud)")


class GenerateRequest(BaseModel):
    address: str
    annual_consumption_kwh: float
    roof_area_m2: float
    roof_tilt: float | None = None
    roof_azimuth: float | None = None
    format: str = Field(default="pdf", description="Formato output: 'docx' o 'pdf'")


# --- Routes ---


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main web page."""
    index_path = _TEMPLATES_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>SolarSpec</h1><p>Frontend non trovato.</p>")


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
        spec = SolarSpec()
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


@app.post("/api/preview")
async def preview_document(req: DesignRequest):
    """Generate an HTML preview of the technical specification."""
    try:
        spec = SolarSpec()
        result = spec.design(
            address=req.address,
            annual_consumption_kwh=req.annual_consumption_kwh,
            roof_area_m2=req.roof_area_m2,
            roof_tilt=req.roof_tilt,
            roof_azimuth=req.roof_azimuth,
        )
        html = _build_html(result)
        return {"html": html}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore nella preview: {e}")
