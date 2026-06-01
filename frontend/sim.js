"use strict";

const API = "http://localhost:8765";

// --- Slider-Binding ---
function bindSlider(id, displayId, fmt) {
  const slider = document.getElementById(id);
  const display = document.getElementById(displayId);
  slider.addEventListener("input", () => {
    display.textContent = fmt(slider.value);
    debouncedSimulate();
  });
}

bindSlider("temp",  "temp-val",  v => `${v} °C`);
bindSlider("ph",    "ph-val",    v => parseFloat(v).toFixed(1));
bindSlider("pet0",  "pet0-val",  v => `${parseFloat(v).toFixed(1)} mM`);
document.getElementById("runs").addEventListener("change", debouncedSimulate);
document.getElementById("run-btn").addEventListener("click", runSimulation);

// --- Chart-Instanzen ---
let odeChart = null;
let heatmapChart = null;

function initOdeChart() {
  const ctx = document.getElementById("ode-chart").getContext("2d");
  odeChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        { label: "[PET] mM",  data: [], borderColor: "#ff6b6b", backgroundColor: "rgba(255,107,107,0.08)", tension: 0.3, pointRadius: 0 },
        { label: "[MHET] mM", data: [], borderColor: "#ffd93d", backgroundColor: "rgba(255,217,61,0.08)",  tension: 0.3, pointRadius: 0 },
        { label: "[TPA] mM",  data: [], borderColor: "#4fffb0", backgroundColor: "rgba(79,255,176,0.08)", tension: 0.3, pointRadius: 0 },
      ],
    },
    options: {
      responsive: true,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { labels: { color: "#e2e8f0", boxWidth: 12 } },
        tooltip: {
          callbacks: {
            label: ctx => `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(4)}`,
          },
        },
      },
      scales: {
        x: {
          ticks: { color: "#8892a4", maxTicksLimit: 10, callback: v => `${v} min` },
          grid: { color: "rgba(255,255,255,0.05)" },
        },
        y: {
          ticks: { color: "#8892a4" },
          grid: { color: "rgba(255,255,255,0.05)" },
          title: { display: true, text: "Konzentration (mM)", color: "#8892a4" },
        },
      },
    },
  });
}

function updateOdeChart(ode) {
  // Downsampling auf max 150 Punkte für flüssige Darstellung
  const step = Math.max(1, Math.floor(ode.t.length / 150));
  const labels = [];
  const pet = [], mhet = [], tpa = [];
  for (let i = 0; i < ode.t.length; i += step) {
    labels.push(ode.t[i].toFixed(1));
    pet.push(ode.PET[i]);
    mhet.push(ode.MHET[i]);
    tpa.push(ode.TPA[i]);
  }
  odeChart.data.labels = labels;
  odeChart.data.datasets[0].data = pet;
  odeChart.data.datasets[1].data = mhet;
  odeChart.data.datasets[2].data = tpa;
  odeChart.update("none");
}

// --- Heatmap als Bubble-Chart (Temp × pH, Größe = Rate) ---
function initHeatmapChart() {
  const ctx = document.getElementById("heatmap-chart").getContext("2d");
  heatmapChart = new Chart(ctx, {
    type: "bubble",
    data: { datasets: [] },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => {
              const d = ctx.raw;
              return `T=${d.x}°C  pH=${d.y}  Rate=${d.rate !== undefined ? d.rate.toExponential(3) : "?"} µmol/min/mg`;
            },
          },
        },
      },
      scales: {
        x: {
          title: { display: true, text: "Temperatur (°C)", color: "#8892a4" },
          ticks: { color: "#8892a4" },
          grid: { color: "rgba(255,255,255,0.05)" },
        },
        y: {
          title: { display: true, text: "pH", color: "#8892a4" },
          ticks: { color: "#8892a4" },
          grid: { color: "rgba(255,255,255,0.05)" },
          min: 4, max: 10,
        },
      },
    },
  });
}

function updateHeatmapChart(heatmap) {
  const rates = heatmap.map(d => d.rate).filter(r => r > 0);
  const maxRate = rates.length > 0 ? Math.max(...rates) : 1;

  // Farb- und Größen-Mapping über Rate
  const data = heatmap.map(d => ({
    x: d.temp,
    y: d.ph,
    r: 6 + 20 * (d.rate / maxRate),
    rate: d.rate,
  }));

  const colors = data.map(d => {
    const t = d.rate / maxRate;
    const r = Math.round(255 * (1 - t) * 0.4 + 79 * t);
    const g = Math.round(107 * (1 - t) + 255 * t);
    const b = Math.round(107 * (1 - t) * 0.4 + 176 * t);
    return `rgba(${r},${g},${b},0.75)`;
  });

  heatmapChart.data.datasets = [{
    data,
    backgroundColor: colors,
    borderColor: "rgba(255,255,255,0.15)",
    borderWidth: 1,
  }];
  heatmapChart.update("none");
}

// --- Stats-Panel ---
function updateStats(mc) {
  const fmt = v => (typeof v === "number" && !isNaN(v)) ? v.toExponential(3) : "n/a";
  document.getElementById("stat-tpa").textContent   = fmt(mc.mean_final_tpa) + " mM";
  document.getElementById("stat-rate").textContent  = fmt(mc.mean_max_rate) + " µmol/min/mg";
  document.getElementById("stat-thalf").textContent = mc.mean_t_half ? mc.mean_t_half.toFixed(1) + " min" : "n/a";
  document.getElementById("stat-valid").textContent = mc.n_valid;
  document.getElementById("ci-bar").textContent =
    `95%-KI finale TPA: [${fmt(mc.ci_95_lower)}, ${fmt(mc.ci_95_upper)}] mM`;
}

// --- API-Calls ---
async function runSimulation() {
  const temp  = document.getElementById("temp").value;
  const ph    = document.getElementById("ph").value;
  const pet0  = document.getElementById("pet0").value;
  const runs  = document.getElementById("runs").value;

  const odePanel     = document.getElementById("ode-panel");
  const heatmapPanel = document.getElementById("heatmap-panel");
  const btn          = document.getElementById("run-btn");

  odePanel.classList.add("loading");
  btn.disabled = true;
  btn.textContent = "Läuft…";

  try {
    const simResp = await fetch(`${API}/api/simulate?temp=${temp}&ph=${ph}&pet0=${pet0}&runs=${runs}`);
    if (!simResp.ok) throw new Error(await simResp.text());
    const simData = await simResp.json();
    updateOdeChart(simData.ode);
    updateStats(simData.monte_carlo);
  } catch (e) {
    console.error("Simulate error:", e);
  } finally {
    odePanel.classList.remove("loading");
  }

  heatmapPanel.classList.add("loading");
  try {
    const hmResp = await fetch(`${API}/api/heatmap?runs=50`);
    if (!hmResp.ok) throw new Error(await hmResp.text());
    const hmData = await hmResp.json();
    updateHeatmapChart(hmData.heatmap);
  } catch (e) {
    console.error("Heatmap error:", e);
  } finally {
    heatmapPanel.classList.remove("loading");
    btn.disabled = false;
    btn.textContent = "Simulation starten";
  }
}

// --- Debounce ---
let debounceTimer = null;
function debouncedSimulate() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(runSimulation, 300);
}

// --- Init ---
initOdeChart();
initHeatmapChart();
runSimulation();
