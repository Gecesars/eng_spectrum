
const API_BASE = '/api/v4';

// --- PORTAL ---

async function fetchNetworks() {
    try {
        const res = await fetch(`${API_BASE}/networks`);
        const data = await res.json();
        renderNetworks(data);
    } catch (e) {
        console.error(e);
        document.getElementById('networkGrid').innerHTML = '<div class="error">Failed to load networks</div>';
    }
}

function renderNetworks(networks) {
    const grid = document.getElementById('networkGrid');
    if (!grid) return;

    grid.innerHTML = networks.map(n => `
        <div class="card" onclick="openNetwork('${n.id}')">
            <h3>${n.name}</h3>
            <p>${n.description || 'No description'}</p>
            <p><small>${new Date(n.created_at).toLocaleDateString()}</small></p>
        </div>
    `).join('');
}

async function createNetwork() {
    const name = prompt("Network Name:");
    if (!name) return;

    await fetch(`${API_BASE}/networks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
    });
    fetchNetworks();
}

function openNetwork(id) {
    window.location.href = `map.html?network_id=${id}`;
}

// --- MAP ---

let map;
let stationsLayer;
let currentNetworkId;

async function initMap(networkId) {
    currentNetworkId = networkId;
    map = L.map('map').setView([-15.79, -47.88], 5); // Brazil center

    // Dark Matter tiles
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);

    await loadStations(networkId);
}

async function loadStations(networkId) {
    const res = await fetch(`${API_BASE}/networks/${networkId}/stations`);
    const geojson = await res.json();

    const sidebarList = document.getElementById('stationList');
    const txSelect = document.getElementById('txSelect');
    const rxSelect = document.getElementById('rxSelect');

    sidebarList.innerHTML = '';
    txSelect.innerHTML = '<option value="">Select TX</option>';
    rxSelect.innerHTML = '<option value="">Select RX</option>';

    stationsLayer = L.geoJSON(geojson, {
        pointToLayer: (feature, latlng) => {
            return L.circleMarker(latlng, {
                radius: 6,
                fillColor: "#238636",
                color: "#fff",
                weight: 1,
                opacity: 1,
                fillOpacity: 0.8
            });
        },
        onEachFeature: (feature, layer) => {
            const p = feature.properties;
            layer.bindPopup(`<b>${p.name}</b><br>Freq: ${p.freq} MHz<br>ERP: ${p.erp} dBm`);

            // Populate Sidebar
            const item = document.createElement('div');
            item.className = 'station-item';
            item.innerText = p.name;
            item.onclick = () => {
                map.flyTo(layer.getLatLng(), 12);
                layer.openPopup();
            };
            sidebarList.appendChild(item);

            // Populate Selects
            const opt = `<option value="${p.id}">${p.name}</option>`;
            txSelect.innerHTML += opt;
            rxSelect.innerHTML += opt;
        }
    }).addTo(map);

    if (geojson.features.length > 0) {
        map.fitBounds(stationsLayer.getBounds());
    }
}

async function runCalculation() {
    const txId = document.getElementById('txSelect').value;
    const rxId = document.getElementById('rxSelect').value;

    if (!txId || !rxId) {
        alert("Please select both TX and RX stations");
        return;
    }

    const res = await fetch(`${API_BASE}/jobs/link`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            network_id: currentNetworkId,
            tx_id: txId,
            rx_id: rxId
        })
    });

    const data = await res.json();
    const jobId = data.job_id;

    document.getElementById('results').innerHTML = `<div class="loading">Calculating... Job ${jobId}</div>`;

    pollJob(jobId);
}

async function pollJob(jobId) {
    const interval = setInterval(async () => {
        const res = await fetch(`${API_BASE}/jobs/${jobId}`);
        const job = await res.json();

        if (job.status === 'done') {
            clearInterval(interval);
            const r = job.result;
            document.getElementById('results').innerHTML = `
                <div class="card" style="margin-top:1rem; border-color: #238636;">
                    <h4>Result</h4>
                    <p>Loss: <b>${r.loss_db.toFixed(2)} dB</b></p>
                    <p>Dist: ${r.distance_km.toFixed(2)} km</p>
                </div>
            `;
        } else if (job.status === 'error') {
            clearInterval(interval);
            document.getElementById('results').innerHTML = `<div class="error">Error: ${job.error}</div>`;
        }
    }, 1000);
}

// Auto-run based on page
if (document.getElementById('networkGrid')) {
    fetchNetworks();
}
