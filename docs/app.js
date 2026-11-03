const state = { data: null, sector: "power", caseId: "sammis" };

async function loadProjectData(url = "data/project.json") {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Could not load GreenSeer data (${response.status})`);
  return response.json();
}

function formatNumber(value) {
  return new Intl.NumberFormat("en-US").format(value);
}

function selectSector(sectorId) {
  state.sector = sectorId;
  const match = state.data.cases.find(item => item.sector === sectorId);
  if (match) selectCase(match.id);
}

function selectCase(caseId) {
  state.caseId = caseId;
  document.querySelectorAll(".sector-card").forEach(button => {
    button.setAttribute("aria-pressed", String(button.dataset.caseId === caseId));
  });
  const item = state.data.cases.find(entry => entry.id === caseId);
  if (!item) return;
  const panel = document.querySelector("#case-panel");
  panel.innerHTML = `
    <div>
      <p class="case-kicker">${item.sector} · ${item.evidence_type.replaceAll("_", " ")}</p>
      <h3>${item.title}</h3>
      <p class="case-finding">${item.finding}</p>
      <p>${item.interpretation}</p>
    </div>
    <div class="case-meta">
      <div><small>Place</small><strong>${item.place}</strong></div>
      <div><small>Period</small><strong>${item.period}</strong></div>
      <div><small>Outcome</small><strong>${item.outcome}</strong></div>
      <div><small>Unit</small><strong>${item.unit}</strong></div>
      <p class="claim-boundary"><strong>What this result supports:</strong><br>${item.claim_boundary}</p>
      <a class="source-link" href="${item.source}" target="_blank" rel="noreferrer">Open the authoritative source ↗</a>
    </div>`;
}

function renderMetrics(data) {
  document.querySelector("#metrics").innerHTML = data.metrics.map(item => `
    <div class="metric"><strong>${formatNumber(item.value)}</strong><span>${item.meaning}</span></div>`).join("");
}

function renderWorkflow(data) {
  document.querySelector("#workflow-grid").innerHTML = data.workflow.map(item => `
    <article class="workflow-step"><div class="step-number">${String(item.step).padStart(2, "0")}</div><h3>${item.name}</h3><p>${item.description}</p></article>`).join("");
}

function renderSectors(data) {
  const assets = {
    power: ["assets/sector-power.webp", "Power plant emissions-control equipment"],
    residential: ["assets/sector-residential.webp", "Residential heating and wood-burning intervention"],
    transport: ["assets/sector-transport.webp", "Electric school buses in a transportation fleet"],
    industrial: ["assets/sector-industrial.webp", "Industrial emissions-control facility"],
  };
  document.querySelector("#sector-grid").innerHTML = data.cases.map(item => {
    const [src, alt] = assets[item.sector];
    return `<button class="sector-card" type="button" data-case-id="${item.id}" data-sector="${item.sector}" aria-pressed="false"><img src="${src}" alt="${alt}"><span>${item.sector[0].toUpperCase() + item.sector.slice(1)} <b aria-hidden="true">→</b></span></button>`;
  }).join("");
  document.querySelectorAll(".sector-card").forEach(button => button.addEventListener("click", () => selectSector(button.dataset.sector)));
  selectCase(state.caseId);
}

function renderModelChart(data) {
  const rows = data.model_comparison;
  const maximum = Math.max(...rows.map(row => row.rmse));
  const minimum = Math.min(...rows.map(row => row.rmse));
  document.querySelector("#model-chart").innerHTML = rows.map(row => `
    <div class="bar-row ${row.rmse === minimum ? "best" : ""}">
      <span class="bar-label">${row.model}</span>
      <div class="bar-track" aria-label="${row.model} RMSE ${row.rmse.toFixed(3)}"><div class="bar-fill" style="width:${(row.rmse / maximum) * 100}%"></div></div>
      <strong>${row.rmse.toFixed(2)}</strong>
    </div>`).join("");
}

function renderContributions(data) {
  const rows = data.prediction_contributions;
  const maximum = Math.max(...rows.map(row => Math.abs(row.mean_signed_contribution)), .001);
  document.querySelector("#contribution-chart").innerHTML = rows.map(row => {
    const value = row.mean_signed_contribution;
    const side = value < 0 ? "negative" : "positive";
    return `<div class="diverging-row"><span>${row.feature}</span><div class="diverging-track" aria-label="${row.feature}: ${value.toFixed(3)}"><div class="diverging-fill ${side}" style="width:${(Math.abs(value) / maximum) * 48}%"></div></div><strong>${value.toFixed(3)}</strong></div>`;
  }).join("");
}

async function renderSources(data) {
  const response = await fetch("data/source-manifest.json");
  const manifest = await response.json();
  document.querySelector("#source-grid").innerHTML = manifest.sources.map(item => `<article class="source-card"><a href="${item.public_url}" target="_blank" rel="noreferrer">${item.name} ↗</a><p>${item.project_use}</p></article>`).join("");
  document.querySelector("#disclosures").innerHTML = data.disclosures.map(item => `<li>${item}</li>`).join("");
}

async function initialise() {
  try {
    state.data = await loadProjectData();
    renderMetrics(state.data);
    renderWorkflow(state.data);
    renderSectors(state.data);
    renderModelChart(state.data);
    renderContributions(state.data);
    await renderSources(state.data);
  } catch (error) {
    document.querySelector("#main-content").insertAdjacentHTML("afterbegin", `<p role="alert" class="model-note">${error.message}. Run this site through a local web server rather than opening the HTML file directly.</p>`);
  }
}

document.addEventListener("DOMContentLoaded", initialise);
