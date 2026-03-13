const form = document.getElementById('search-form');
const modeSelect = document.getElementById('design_mode');
const summary = document.getElementById('summary');
const warningsList = document.getElementById('warnings');
const thermalSummary = document.getElementById('thermal-summary');
const candidatesBody = document.getElementById('candidates-body');
const makeVisualsBtn = document.getElementById('make-visuals');
const visualStatus = document.getElementById('visual-status');
const visual2d = document.getElementById('visual-2d');
const vizCore = document.getElementById('viz-core');
const vizWire = document.getElementById('viz-wire');
const vizTurns = document.getElementById('viz-turns');
const useBestVisualBtn = document.getElementById('use-best-visual');
const open3d = document.getElementById('open-3d');
const coreExcludeList = document.getElementById('core-exclude-list');
const permExcludeList = document.getElementById('perm-exclude-list');
const wireExcludeList = document.getElementById('wire-exclude-list');
const progressText = document.getElementById('progress-text');
const progressPercent = document.getElementById('progress-percent');
const progressFill = document.getElementById('progress-fill');
const prevPageBtn = document.getElementById('prev-page');
const nextPageBtn = document.getElementById('next-page');
const pageInfo = document.getElementById('page-info');
const derivedImin = document.getElementById('derived-imin');
const derivedIpk = document.getElementById('derived-ipk');
const derivedIrms = document.getElementById('derived-irms');

const state = {
  catalog: null,
  bestCandidate: null,
  activeJobId: null,
  pollTimer: null,
  rows: [],
  page: 1,
  pageSize: 20,
};

function setMode(mode) {
  document.querySelectorAll('.mode-panel').forEach((panel) => {
    panel.classList.toggle('hidden', panel.dataset.mode !== mode);
  });
}

function fmt(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '-';
  return Number(value).toFixed(digits);
}

function setProgress(text, pct) {
  progressText.textContent = text;
  progressPercent.textContent = `${Math.round(pct)}%`;
  progressFill.style.width = `${Math.max(0, Math.min(100, pct))}%`;
}

function checkedValues(root) {
  return [...root.querySelectorAll('input[type="checkbox"]:checked')].map((node) => node.value);
}

function renderChecklist(root, items, prefix, labelBuilder) {
  root.innerHTML = items.map((item) => `
    <label class="tick-item">
      <input type="checkbox" value="${item.value}" id="${prefix}-${item.value}">
      <span>${labelBuilder(item)}</span>
    </label>
  `).join('');
}

function populateCatalog(catalog) {
  state.catalog = catalog;
  vizCore.innerHTML = catalog.cores.map((core) => `<option value="${core.id}">${core.part_number} | ${core.permeability}</option>`).join('');
  vizWire.innerHTML = catalog.wires.map((wire) => `<option value="${wire.id}">AWG ${wire.awg}</option>`).join('');
  vizCore.value = catalog.defaults.core_id;
  vizWire.value = catalog.defaults.wire_id;

  const uniqueCoreIds = [...new Map(catalog.cores.map((core) => [core.part_number, core])).values()]
    .map((core) => ({ value: core.part_number, core }));
  renderChecklist(coreExcludeList, uniqueCoreIds, 'core', (item) => `${item.core.part_number} | Ve=${fmt(item.core.ve_mm3, 0)} mm^3`);

  const uniquePerms = [...new Set(catalog.cores.map((core) => core.permeability))].map((value) => ({ value }));
  renderChecklist(permExcludeList, uniquePerms, 'perm', (item) => item.value);

  const wires = catalog.wires.map((wire) => ({ value: wire.awg, wire }));
  renderChecklist(wireExcludeList, wires, 'wire', (item) => `AWG ${item.wire.awg} | ${fmt(item.wire.area_mm2, 3)} mm^2`);
}

function collectPayload() {
  const fd = new FormData(form);
  const payload = Object.fromEntries(fd.entries());
  payload.exclude_core_ids = checkedValues(coreExcludeList);
  payload.exclude_permeabilities = checkedValues(permExcludeList);
  payload.exclude_wire_awgs = checkedValues(wireExcludeList);
  return payload;
}

function renderWarnings(items = []) {
  warningsList.innerHTML = '';
  items.forEach((item) => {
    const li = document.createElement('li');
    li.textContent = item;
    warningsList.appendChild(li);
  });
}

function renderSummary(result) {
  const best = result.best;
  if (!best) {
    summary.className = 'summary empty';
    summary.textContent = 'No valid candidate found.';
    thermalSummary.classList.add('hidden');
    return;
  }
  const core = best.core;
  const wire = best.wire;
  const op = result.operating_point;
  summary.className = 'summary';
  thermalSummary.classList.remove('hidden');
  thermalSummary.innerHTML = `<div>Thermal model: ventilation=${best.thermal_details?.Ventilation ?? '-'}, k=${fmt(best.thermal_details?.k_used, 4)}, Rth=${fmt(best.rth_c_per_w, 3)} C/W</div>`;
  summary.innerHTML = `
    <div class="summary-grid">
      <div class="metric"><span class="label">Core</span><span class="value">${core.part_number} / ${core.permeability}</span></div>
      <div class="metric"><span class="label">Wire</span><span class="value">AWG ${wire.awg}</span></div>
      <div class="metric"><span class="label">Parallel wires</span><span class="value">${best.parallel_count}</span></div>
      <div class="metric"><span class="label">Turns</span><span class="value">${best.turns}</span></div>
      <div class="metric"><span class="label">Layers</span><span class="value">${best.layers}</span></div>
      <div class="metric"><span class="label">Target L</span><span class="value">${fmt(op.target_inductance_uH, 1)} uH</span></div>
      <div class="metric"><span class="label">Loaded L</span><span class="value">${fmt(best.l_uH, 1)} uH</span></div>
      <div class="metric"><span class="label">Iavg / DeltaI</span><span class="value">${fmt(op.i_avg_a, 2)} A / ${fmt(op.delta_i_pp_a, 2)} A</span></div>
      <div class="metric"><span class="label">Imin / Ipk</span><span class="value">${fmt(op.i_min_a, 2)} A / ${fmt(op.i_pk_a, 2)} A</span></div>
      <div class="metric"><span class="label">Irms</span><span class="value">${fmt(op.i_rms_a, 2)} A</span></div>
      <div class="metric"><span class="label">Total loss</span><span class="value">${fmt(best.p_tot_w, 2)} W</span></div>
      <div class="metric"><span class="label">Core temp</span><span class="value">${fmt(best.t_core_c, 1)} C</span></div>
      <div class="metric"><span class="label">Current density</span><span class="value">${fmt(best.wire_current_density_a_per_mm2, 2)} A/mm^2</span></div>
      <div class="metric"><span class="label">Ku (inner)</span><span class="value">${fmt(best.ku_inner, 3)}</span></div>
      <div class="metric"><span class="label">Rank score</span><span class="value">${fmt(best.rank_score, 3)}</span></div>
    </div>
    <div class="inline-note">
      ${op.notes.map((note) => `<div>${note}</div>`).join('')}
      <div>Bundle suggestion: ${best.bundle_name}</div>
      <div>Loaded inductance is evaluated under DC bias and temperature-adjusted effective permeability.</div>
    </div>
  `;
}

function renderPage() {
  const totalPages = Math.max(1, Math.ceil(state.rows.length / state.pageSize));
  state.page = Math.min(Math.max(1, state.page), totalPages);
  pageInfo.textContent = `Page ${state.page} / ${totalPages}`;
  prevPageBtn.disabled = state.page <= 1;
  nextPageBtn.disabled = state.page >= totalPages;

  const start = (state.page - 1) * state.pageSize;
  const pageRows = state.rows.slice(start, start + state.pageSize);
  candidatesBody.innerHTML = '';
  pageRows.forEach((item) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${item.core.part_number}/${item.core.permeability}</td>
      <td>AWG ${item.wire.awg}</td>
      <td>${item.parallel_count}</td>
      <td>${item.turns}</td>
      <td>${item.layers}</td>
      <td>${fmt(item.l_uH, 1)}</td>
      <td>${fmt(item.p_tot_w, 2)}</td>
      <td>${fmt(item.t_core_c, 1)}</td>
      <td>${fmt(item.ku_inner, 3)}</td>
      <td>${fmt(item.wire_current_density_a_per_mm2, 2)}</td>
      <td>${fmt(item.b_total_pk_t, 3)}</td>
      <td>${fmt(item.rank_score, 3)}</td>
    `;
    candidatesBody.appendChild(tr);
  });
}

async function loadCatalog() {
  const response = await fetch('/api/catalog');
  const catalog = await response.json();
  populateCatalog(catalog);
  setMode(modeSelect.value);
  updateDerivedCurrents();
  summary.textContent = 'Ready.';
  setProgress('Idle.', 0);
}

async function submitBruteforce(event) {
  event.preventDefault();
  summary.className = 'summary empty';
  summary.textContent = 'Starting brute-force scan...';
  renderWarnings([]);
  state.rows = [];
  renderPage();
  setProgress('Queueing brute-force scan...', 0);
  const response = await fetch('/api/search/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(collectPayload()),
  });
  const result = await response.json();
  if (!response.ok) {
    summary.textContent = result.error || 'Failed to start search';
    return;
  }
  state.activeJobId = result.job_id;
  if (state.pollTimer) clearInterval(state.pollTimer);
  state.pollTimer = setInterval(pollJobStatus, 1000);
}

async function pollJobStatus() {
  if (!state.activeJobId) return;
  const response = await fetch(`/api/search/status?id=${state.activeJobId}`);
  const result = await response.json();
  if (!response.ok) {
    setProgress(result.error || 'Job status failed', 0);
    clearInterval(state.pollTimer);
    return;
  }
  const coreText = result.current_core ? `Scanning core ${result.current_core} (${result.processed_cores}/${result.total_cores})` : 'Preparing scan...';
  setProgress(coreText, result.progress_pct || 0);
  if (result.status === 'completed') {
    clearInterval(state.pollTimer);
    state.pollTimer = null;
    const finalResult = result.result;
    state.bestCandidate = finalResult.best;
    state.rows = finalResult.results || [];
    state.page = 1;
    renderSummary(finalResult);
    renderWarnings(finalResult.warnings || []);
    renderPage();
    setProgress(`Completed. Valid candidates: ${finalResult.count}`, 100);
  } else if (result.status === 'failed') {
    clearInterval(state.pollTimer);
    state.pollTimer = null;
    summary.textContent = result.error || 'Brute-force search failed';
    setProgress('Failed.', 0);
  }
}

async function generateVisuals() {
  visualStatus.textContent = 'Generating visuals...';
  const query = new URLSearchParams({
    core_id: vizCore.value,
    wire_id: vizWire.value,
    turns: String(vizTurns.value || 1),
  });
  const response = await fetch(`/api/visualize?${query.toString()}`);
  const result = await response.json();
  if (!response.ok) {
    visualStatus.textContent = result.error || 'Visualization failed';
    return;
  }
  visualStatus.textContent = `${vizCore.options[vizCore.selectedIndex].text} | AWG ${vizWire.value} | N=${vizTurns.value}`;
  visual2d.src = `${result.image_2d}?t=${Date.now()}`;
  visual2d.classList.remove('hidden');
  open3d.href = result.html_3d;
  open3d.classList.remove('disabled');
}

prevPageBtn.addEventListener('click', () => { state.page -= 1; renderPage(); });
nextPageBtn.addEventListener('click', () => { state.page += 1; renderPage(); });
modeSelect.addEventListener('change', () => { setMode(modeSelect.value); updateDerivedCurrents(); });
form.addEventListener('submit', submitBruteforce);
makeVisualsBtn.addEventListener('click', generateVisuals);
useBestVisualBtn.addEventListener('click', useBestVisualSelection);
loadCatalog().catch((error) => {
  summary.textContent = `Catalog load failed: ${error}`;
});

function useBestVisualSelection() {
  const best = state.bestCandidate;
  if (!best) return;
  vizCore.value = best.core_id;
  vizWire.value = best.wire_id;
  vizTurns.value = best.turns;
}


function updateDerivedCurrents() {
  const iAvg = Number(form.elements['i_avg_a']?.value || 0);
  const deltaI = Number(form.elements['delta_i_pp_a']?.value || 0);
  const iMin = iAvg - deltaI / 2;
  const iPk = iAvg + deltaI / 2;
  const iRms = Math.sqrt((iAvg ** 2) + (deltaI ** 2) / 12);
  if (derivedImin) derivedImin.textContent = fmt(iMin, 2);
  if (derivedIpk) derivedIpk.textContent = fmt(iPk, 2);
  if (derivedIrms) derivedIrms.textContent = fmt(iRms, 2);
}

form.elements['i_avg_a']?.addEventListener('input', updateDerivedCurrents);
form.elements['delta_i_pp_a']?.addEventListener('input', updateDerivedCurrents);
