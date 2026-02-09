/* SolarSpec — Web Application */

const API_BASE = '';

// State
let currentDesign = null;
let map = null;
let marker = null;
let monthlyChart = null;

// --- Tab Management ---

function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));
    document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');
    document.getElementById(tabId).classList.add('active');
}

// --- Utilities ---

function showError(elementId, message) {
    const el = document.getElementById(elementId);
    if (el) {
        el.textContent = message;
        el.classList.add('visible');
    }
}

function hideError(elementId) {
    const el = document.getElementById(elementId);
    if (el) {
        el.classList.remove('visible');
    }
}

function showSpinner(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add('active');
}

function hideSpinner(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove('active');
}

function formatNumber(num, decimals = 0) {
    return new Intl.NumberFormat('it-IT', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(num);
}

function formatCurrency(num) {
    return new Intl.NumberFormat('it-IT', {
        style: 'currency',
        currency: 'EUR'
    }).format(num);
}

// --- API Calls ---

async function apiCall(endpoint, data) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });

    if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: 'Errore sconosciuto' }));
        throw new Error(err.detail || `Errore HTTP ${response.status}`);
    }

    return response;
}

// --- Analyze ---

async function analyzeAddress() {
    const address = document.getElementById('analyze-address').value.trim();
    if (!address) {
        showError('analyze-error', 'Inserisci un indirizzo valido.');
        return;
    }

    hideError('analyze-error');
    showSpinner('analyze-spinner');
    document.getElementById('analyze-results').style.display = 'none';
    document.getElementById('analyze-btn').disabled = true;

    try {
        const response = await apiCall('/api/analyze', { address });
        const data = await response.json();
        displayAnalysisResults(data);
    } catch (err) {
        showError('analyze-error', `Errore: ${err.message}`);
    } finally {
        hideSpinner('analyze-spinner');
        document.getElementById('analyze-btn').disabled = false;
    }
}

function displayAnalysisResults(data) {
    const resultsDiv = document.getElementById('analyze-results');
    resultsDiv.style.display = 'block';
    resultsDiv.classList.add('fade-in');

    // Site data
    document.getElementById('res-address').textContent = data.site.address;
    document.getElementById('res-coords').textContent =
        `${data.site.latitude.toFixed(5)}°N, ${data.site.longitude.toFixed(5)}°E`;
    document.getElementById('res-municipality').textContent =
        `${data.site.municipality} (${data.site.province})`;
    document.getElementById('res-region').textContent = data.site.region;
    document.getElementById('res-climate').textContent = data.site.climate_zone || 'N/D';
    document.getElementById('res-seismic').textContent = data.site.seismic_zone || 'N/D';

    // Solar data
    document.getElementById('res-irradiation').innerHTML =
        `${formatNumber(data.solar_data.annual_irradiation, 1)} <span class="unit">kWh/m²/anno</span>`;
    document.getElementById('res-tilt').innerHTML =
        `${data.solar_data.optimal_tilt}° <span class="unit">inclinazione</span>`;
    document.getElementById('res-azimuth').innerHTML =
        `${data.solar_data.optimal_azimuth}° <span class="unit">azimut</span>`;
    document.getElementById('res-production').innerHTML =
        `${formatNumber(data.solar_data.annual_production_per_kwp, 0)} <span class="unit">kWh/kWp/anno</span>`;

    // Map
    initMap(data.site.latitude, data.site.longitude, data.site.address);

    // Monthly chart
    if (data.solar_data.monthly_irradiation && data.solar_data.monthly_irradiation.length > 0) {
        initMonthlyChart(data.solar_data.monthly_irradiation);
    }

    // Copy address to design tab
    document.getElementById('design-address').value = data.site.address;
}

function initMap(lat, lng, label) {
    const mapDiv = document.getElementById('map');
    if (!mapDiv) return;

    // Leaflet might not be loaded yet (CDN async), retry
    if (typeof L === 'undefined') {
        mapDiv.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#7f8c8d;font-size:0.9em;">
            <p>Coordinate: ${lat.toFixed(5)}°N, ${lng.toFixed(5)}°E</p></div>`;
        setTimeout(() => initMap(lat, lng, label), 1500);
        return;
    }

    if (map) {
        map.remove();
    }

    map = L.map('map').setView([lat, lng], 15);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    marker = L.marker([lat, lng]).addTo(map);
    marker.bindPopup(`<b>${label}</b>`).openPopup();
}

function initMonthlyChart(monthlyData) {
    const ctx = document.getElementById('monthly-chart');
    if (!ctx) return;

    // Chart.js might not be loaded yet (CDN async), retry
    if (typeof Chart === 'undefined') {
        const parent = ctx.parentElement;
        if (parent) {
            const labels = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic'];
            parent.innerHTML = '<table class="data-table" style="font-size:0.85em">' +
                monthlyData.map((v, i) => `<tr><td>${labels[i] || ''}</td><td>${v} kWh/m²</td></tr>`).join('') +
                '</table>';
        }
        setTimeout(() => {
            if (typeof Chart !== 'undefined') {
                // Re-create canvas and render chart
                const container = document.querySelector('.chart-container');
                if (container) {
                    container.innerHTML = '<canvas id="monthly-chart"></canvas>';
                    initMonthlyChart(monthlyData);
                }
            }
        }, 2000);
        return;
    }

    const labels = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic'];

    if (monthlyChart) {
        monthlyChart.destroy();
    }

    monthlyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels.slice(0, monthlyData.length),
            datasets: [{
                label: 'Irraggiamento (kWh/m²)',
                data: monthlyData,
                backgroundColor: 'rgba(243, 156, 18, 0.7)',
                borderColor: 'rgba(243, 156, 18, 1)',
                borderWidth: 1,
                borderRadius: 4,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'kWh/m²' }
                }
            }
        }
    });
}

// --- Design ---

async function designSystem() {
    const address = document.getElementById('design-address').value.trim();
    const consumption = parseFloat(document.getElementById('design-consumption').value);
    const roofArea = parseFloat(document.getElementById('design-roof-area').value);
    const roofTilt = document.getElementById('design-tilt').value;
    const roofAzimuth = document.getElementById('design-azimuth').value;

    if (!address) {
        showError('design-error', 'Inserisci un indirizzo.');
        return;
    }
    if (isNaN(consumption) || consumption <= 0) {
        showError('design-error', 'Inserisci un consumo annuo valido.');
        return;
    }
    if (isNaN(roofArea) || roofArea <= 0) {
        showError('design-error', 'Inserisci un\'area tetto valida.');
        return;
    }

    hideError('design-error');
    showSpinner('design-spinner');
    document.getElementById('design-results').style.display = 'none';
    document.getElementById('design-btn').disabled = true;

    try {
        const payload = {
            address,
            annual_consumption_kwh: consumption,
            roof_area_m2: roofArea,
        };
        if (roofTilt) payload.roof_tilt = parseFloat(roofTilt);
        if (roofAzimuth) payload.roof_azimuth = parseFloat(roofAzimuth);

        const response = await apiCall('/api/design', payload);
        const data = await response.json();
        currentDesign = data;
        displayDesignResults(data);
    } catch (err) {
        showError('design-error', `Errore: ${err.message}`);
    } finally {
        hideSpinner('design-spinner');
        document.getElementById('design-btn').disabled = false;
    }
}

function displayDesignResults(data) {
    const resultsDiv = document.getElementById('design-results');
    resultsDiv.style.display = 'block';
    resultsDiv.classList.add('fade-in');

    // System sizing
    document.getElementById('des-kwp').innerHTML =
        `${data.system_size_kwp} <span class="unit">kWp</span>`;
    document.getElementById('des-panels').innerHTML =
        `${data.num_panels} <span class="unit">moduli</span>`;
    document.getElementById('des-production').innerHTML =
        `${formatNumber(data.estimated_production_kwh)} <span class="unit">kWh/anno</span>`;
    document.getElementById('des-selfcons').innerHTML =
        `${data.self_consumption_rate} <span class="unit">%</span>`;

    // Module info
    if (data.module) {
        document.getElementById('des-module').textContent =
            `${data.module.manufacturer} ${data.module.model} (${data.module.power_wp} Wp)`;
    }

    // Inverter info
    if (data.inverter) {
        document.getElementById('des-inverter').textContent =
            `${data.inverter.manufacturer} ${data.inverter.model} (${data.inverter.power_kw} kW)`;
        document.getElementById('des-inverter-row').style.display = '';
    } else {
        document.getElementById('des-inverter-row').style.display = 'none';
    }

    // Economics
    if (data.economics) {
        document.getElementById('des-cost').innerHTML =
            `${formatCurrency(data.economics.total_cost_eur)} <span class="unit">totale</span>`;
        document.getElementById('des-savings').innerHTML =
            `${formatCurrency(data.economics.annual_savings_eur)} <span class="unit">/anno</span>`;
        document.getElementById('des-payback').innerHTML =
            `${data.economics.payback_years} <span class="unit">anni</span>`;
        document.getElementById('des-roi').innerHTML =
            `${data.economics.roi_25y_percent} <span class="unit">%</span>`;
        document.getElementById('des-lcoe').textContent = `€${data.economics.lcoe}/kWh`;
        document.getElementById('des-incentive').textContent = data.economics.incentive_type;
        document.getElementById('des-incentive-val').textContent =
            formatCurrency(data.economics.incentive_value_eur);
    }

    // Notes
    const notesList = document.getElementById('des-notes');
    notesList.innerHTML = '';
    if (data.notes && data.notes.length > 0) {
        data.notes.forEach(note => {
            const li = document.createElement('li');
            li.textContent = note;
            notesList.appendChild(li);
        });
        document.getElementById('des-notes-section').style.display = 'block';
    } else {
        document.getElementById('des-notes-section').style.display = 'none';
    }

    // Enable document generation tab
    document.querySelector('[data-tab="tab-generate"]').style.opacity = '1';
    document.querySelector('[data-tab="tab-generate"]').style.pointerEvents = 'auto';
}

// --- Generate Document ---

async function generateDocument(format) {
    if (!currentDesign) {
        showError('generate-error', 'Devi prima dimensionare un impianto.');
        return;
    }

    hideError('generate-error');
    showSpinner('generate-spinner');

    const address = document.getElementById('design-address').value.trim();
    const consumption = parseFloat(document.getElementById('design-consumption').value);
    const roofArea = parseFloat(document.getElementById('design-roof-area').value);

    try {
        const response = await fetch(`${API_BASE}/api/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                address,
                annual_consumption_kwh: consumption,
                roof_area_m2: roofArea,
                format: format,
            }),
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: 'Errore sconosciuto' }));
            throw new Error(err.detail || `Errore HTTP ${response.status}`);
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `capitolato_tecnico.${format}`;
        a.click();
        window.URL.revokeObjectURL(url);
    } catch (err) {
        showError('generate-error', `Errore: ${err.message}`);
    } finally {
        hideSpinner('generate-spinner');
    }
}

async function previewDocument() {
    if (!currentDesign) {
        showError('generate-error', 'Devi prima dimensionare un impianto.');
        return;
    }

    hideError('generate-error');
    showSpinner('generate-spinner');

    const address = document.getElementById('design-address').value.trim();
    const consumption = parseFloat(document.getElementById('design-consumption').value);
    const roofArea = parseFloat(document.getElementById('design-roof-area').value);

    try {
        const response = await apiCall('/api/preview', {
            address,
            annual_consumption_kwh: consumption,
            roof_area_m2: roofArea,
        });
        const data = await response.json();

        // Show modal
        const modal = document.getElementById('preview-modal');
        modal.classList.add('active');

        const iframe = document.getElementById('preview-iframe');
        iframe.srcdoc = data.html;
    } catch (err) {
        showError('generate-error', `Errore: ${err.message}`);
    } finally {
        hideSpinner('generate-spinner');
    }
}

function closePreview() {
    document.getElementById('preview-modal').classList.remove('active');
}

// --- Event Listeners ---

document.addEventListener('DOMContentLoaded', () => {
    // Tab clicks
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    // Enter key on address field
    document.getElementById('analyze-address').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') analyzeAddress();
    });

    // Close modal on overlay click
    document.getElementById('preview-modal').addEventListener('click', (e) => {
        if (e.target === e.currentTarget) closePreview();
    });

    // Close modal on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closePreview();
    });
});
