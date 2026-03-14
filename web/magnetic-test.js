const testForm = document.getElementById('test-form');
const designMode = document.getElementById('test-design-mode');
const coreSelect = document.getElementById('test-core');
const wireSelect = document.getElementById('test-wire');
const turnsInput = document.getElementById('test-turns');
const summary = document.getElementById('test-summary');
const statusBox = document.getElementById('test-status');
const functionMap = document.getElementById('function-map');
const formulaSections = document.getElementById('formula-sections');
const derivedIavg = document.getElementById('test-derived-iavg');
const derivedImin = document.getElementById('test-derived-imin');
const derivedIpk = document.getElementById('test-derived-ipk');
const derivedIrms = document.getElementById('test-derived-irms');

const state = {
  catalog: null,
};

function fmt(value, digits = 3) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '-';
  return Number(value).toFixed(digits);
}

function modePanels(mode) {
  document.querySelectorAll('.mode-panel').forEach((panel) => {
    panel.classList.toggle('hidden', panel.dataset.mode !== mode);
  });
}

function loadDerivedCurrents() {
  const iPk = Number(testForm.elements.i_pk_a?.value || 0);
  const deltaI = Number(testForm.elements.delta_i_pp_a?.value || 0);
  const iAvg = iPk - deltaI / 2;
  const iMin = iPk - deltaI;
  const iRms = Math.sqrt((iAvg ** 2) + (deltaI ** 2) / 12);
  if (derivedIavg) derivedIavg.textContent = fmt(iAvg, 2);
  if (derivedImin) derivedImin.textContent = fmt(iMin, 2);
  if (derivedIpk) derivedIpk.textContent = fmt(iPk, 2);
  if (derivedIrms) derivedIrms.textContent = fmt(iRms, 2);
}

function payloadFromForm() {
  const fd = new FormData(testForm);
  return Object.fromEntries(fd.entries());
}

function renderFunctionMap() {
  const items = [
    ['_derive_operating_point', 'PFC veya manual moda gore hedef L, Iavg, Ipk, Imin, Irms ve ripple turetilir.'],
    ['_build_parallel_wire', 'Hedef akim yogunluguna gore paralel tel sayisi, etkili alan ve bundle capi hesaplanir.'],
    ['_winding_geometry', 'Katman, turns/layer, Ku ve toplam tel boyu hesaplanir.'],
    ['_magnetic_field_oe', 'Ampere-turn ile H alani Oersted cinsine cevrilir.'],
    ['permeability_dc_bias_ratio', 'DC bias altinda etkin gecirgenlik orani hesaplanir.'],
    ['permeability_temp_ratio', 'Sicakliga bagli gecirgenlik duzeltmesi uygulanir.'],
    ['dc_flux_density_koolmu', 'Malzeme BH egri uyumuna gore DC aki yogunlugu hesaplanir.'],
    ['steinmetz_loss', 'AC aki salinimindan cekirdek hacimsel kaybi bulunur.'],
    ['losses_copper_ac_dowell', 'Skin/proximity etkisi ile AC bakir kaybi hesaplanir.'],
    ['thermal_estimate_hurley', 'Toplam kayiptan Rth ve tahmini cekirdek sicakligi bulunur.'],
    ['_evaluate_turn', 'Tum alt fonksiyonlar birlestirilir ve aday gecerlilik kontrolu yapilir.'],
  ];
  functionMap.innerHTML = items.map(([name, text]) => `
    <article class="formula-card">
      <div class="formula-name">${name}</div>
      <p>${text}</p>
    </article>
  `).join('');
}

function kv(label, value, digits = 3) {
  return `<div class="kv"><span>${label}</span><strong>${fmt(value, digits)}</strong></div>`;
}

function eq(lines) {
  return `<div class="math-lines">${lines.map((line) => `<div>${line}</div>`).join('')}</div>`;
}

function formulaCard(title, subtitle, equation, details, metrics) {
  return `
    <article class="formula-card">
      <div class="formula-head">
        <div>
          <h3>${title}</h3>
          <p>${subtitle}</p>
        </div>
      </div>
      <div class="equation">${equation}</div>
      ${details ? `<div class="formula-detail">${details}</div>` : ''}
      <div class="kv-grid">${metrics.join('')}</div>
    </article>
  `;
}

function renderSummary(data) {
  const { core, wire, bundle, result, operating_point: op, geometry } = data;
  const feasibility = result.feasible ? 'Gecerli aday' : `Sinir disi: ${result.reason || 'kontrol gerekli'}`;
  summary.className = 'summary';
  summary.innerHTML = `
    <div class="summary-grid">
      <div class="metric"><span class="label">Core</span><span class="value">${core.part_number} / ${core.permeability}</span></div>
      <div class="metric"><span class="label">Wire</span><span class="value">AWG ${wire.awg}</span></div>
      <div class="metric"><span class="label">Turns</span><span class="value">${data.turns}</span></div>
      <div class="metric"><span class="label">Parallel</span><span class="value">${bundle.parallel_count}</span></div>
      <div class="metric"><span class="label">Loaded L</span><span class="value">${fmt(result.l_uH, 1)} uH</span></div>
      <div class="metric"><span class="label">Total Loss</span><span class="value">${fmt(result.p_tot_w, 2)} W</span></div>
      <div class="metric"><span class="label">Tcore</span><span class="value">${fmt(result.t_core_c, 1)} C</span></div>
      <div class="metric"><span class="label">Ku</span><span class="value">${fmt(result.ku_inner ?? geometry.ku_inner, 3)}</span></div>
    </div>
    <div class="inline-note">
      <div>${feasibility}</div>
      <div>Target L = ${fmt(op.target_inductance_uH, 1)} uH, DC bias kontrolu Ipk = ${fmt(op.i_pk_a, 2)} A noktasinda yapiliyor.</div>
      <div>Irms = ${fmt(op.i_rms_a, 2)} A, Iavg = ${fmt(op.i_avg_a, 2)} A</div>
    </div>
  `;
}

function renderSections(data) {
  const op = data.operating_point;
  const core = data.core;
  const wire = data.wire;
  const bundle = data.bundle;
  const geom = data.geometry;
  const result = data.result;
  const coeffs = data.material_coefficients || {};
  const dcBias = coeffs.dc_bias || {};
  const temp = coeffs.temperature || {};
  const magnet = coeffs.dc_magnetization || {};
  const loss = coeffs.core_loss || {};
  const equations = [];

  if (op.mode === 'pfc') {
    equations.push(formulaCard(
      '1. PFC calisma noktasi',
      'Dusuk hat kosulunda hedef akim ripple ve hedef enduktans buradan turetilir.',
      eq([
        'V<sub>in,pk</sub> = &radic;2 &middot; V<sub>in,rms</sub>',
        'P<sub>in</sub> = P<sub>out</sub> / &eta;',
        'I<sub>line,pk</sub> = &radic;2 &middot; P<sub>in</sub> / V<sub>in,rms</sub>',
        '&Delta;I<sub>pp</sub> = ripple &middot; I<sub>line,pk</sub>',
        'L<sub>target</sub> = V<sub>in,pk</sub> &middot; D / (f<sub>sw</sub> &middot; &Delta;I<sub>pp</sub>)',
      ]),
      'D = 1 - V_in,pk / V_out',
      [
        kv('Vin,pk (V)', op.vin_pk_v, 2),
        kv('Duty', op.duty_at_low_line, 4),
        kv('Iavg (A)', op.i_avg_a, 2),
        kv('Ipk (A)', op.i_pk_a, 2),
        kv('Irms (A)', op.i_rms_a, 2),
        kv('Target L (uH)', op.target_inductance_uH, 1),
      ],
    ));
  } else {
    equations.push(formulaCard(
      '1. Manual calisma noktasi',
      'Girilen L, Imax/Ipk ve DeltaIpp uzerinden tum akim turevleri hesaplanir.',
      eq([
        'I<sub>avg</sub> = I<sub>pk</sub> - &Delta;I<sub>pp</sub> / 2',
        'I<sub>min</sub> = I<sub>pk</sub> - &Delta;I<sub>pp</sub>',
        'I<sub>rms</sub> = &radic;(I<sub>avg</sub><sup>2</sup> + &Delta;I<sub>pp</sub><sup>2</sup> / 12)',
      ]),
      'Manual modda hedef enduktans Ipk noktasindaki DC bias altinda kontrol edilir.',
      [
        kv('Ipk (A)', op.i_pk_a, 2),
        kv('DeltaIpp (A)', op.delta_i_pp_a, 2),
        kv('Iavg (A)', op.i_avg_a, 2),
        kv('Imin (A)', op.i_min_a, 2),
        kv('Irms (A)', op.i_rms_a, 2),
        kv('Target L (uH)', op.target_inductance_uH, 1),
      ],
    ));
  }

  equations.push(formulaCard(
    '2. Paralel tel secimi',
    'Irms ve hedef akim yogunlugundan gereken bakir alan bulunur.',
    eq([
      'A<sub>req</sub> = I<sub>rms</sub> / J<sub>target</sub>',
      'n<sub>parallel</sub> = ceil(A<sub>req</sub> / A<sub>wire</sub>)',
      'A<sub>bundle</sub> = n<sub>parallel</sub> &middot; A<sub>wire</sub>',
      'd<sub>bundle</sub> &asymp; d<sub>wire</sub> &middot; &radic;n<sub>parallel</sub> &middot; 1.12',
    ]),
    'Sabit parallel count verilirse otomatik alan hesabinin yerine o deger kullanilir.',
    [
      kv('Wire dia (mm)', wire.diameter_mm, 4),
      kv('Awire (mm2)', wire.area_mm2, 4),
      kv('Parallel', bundle.parallel_count, 0),
      kv('Abundle (mm2)', bundle.effective_area_mm2, 4),
      kv('dbundle (mm)', bundle.effective_diameter_mm, 3),
      kv('d_eff (mm)', geom.d_bundle_mm_eff, 3),
      kv('R20/m (ohm)', bundle.R20_ohm_per_m, 5),
      kv('Jreal (A/mm2)', result.wire_current_density_a_per_mm2, 3),
    ],
  ));

  equations.push(formulaCard(
    '3. Sargi geometrisi',
    'Ic pencere kullanimi, katman sayisi ve toplam tel uzunlugu burada olusur.',
    eq([
      'N<sub>layer</sub> = floor(&pi; &middot; ID / d<sub>eff</sub>)',
      'layers = ceil(N / N<sub>layer</sub>)',
      'K<sub>u</sub> = N &middot; A<sub>bundle</sub> / (ID &middot; h)',
      'MLT &asymp; 2 &middot; (((OD - ID) / 2) + h + (layers - 1) &middot; d<sub>eff</sub>)',
      'l<sub>total</sub> = MLT &middot; N',
    ]),
    'Burada d_eff = 1.05 * d_bundle. Tek katman icin MLT yaklasimi dogrudan 2 * (((OD - ID) / 2) + h) olur.',
    [
      kv('OD (mm)', core.od_mm, 2),
      kv('ID (mm)', core.id_mm, 2),
      kv('Height (mm)', core.height_mm, 2),
      kv('Radial span (mm)', result.radial_span_mm ?? geom.radial_span_mm, 2),
      kv('Turns/layer', geom.turns_per_layer, 0),
      kv('Layers', geom.layers, 0),
      kv('MLT (mm)', result.mean_turn_length_mm ?? geom.mean_turn_length_mm, 2),
      kv('Radial build (mm)', result.radial_build_mm ?? geom.radial_build_mm, 2),
      kv('Ku', geom.ku_inner, 3),
      kv('Wire length (m)', geom.length_m, 3),
    ],
  ));

  equations.push(formulaCard(
    '4. Manyetik alan',
    'Akimin olusturdugu manyetik alan cekirdegin ortalama yol uzunluguna bolunur ve Oersted cinsine cevrilir.',
    eq([
      'H(A/m) = N &middot; I<sub>pk</sub> / l<sub>e</sub>',
      'H(Oe) = H(A/m) / 79.577',
    ]),
    'Bias fonksiyonlari H degerini Oe olarak bekler.',
    [
      kv('N', data.turns, 0),
      kv('Ipk (A)', op.i_pk_a, 2),
      kv('le (mm)', core.le_mm, 2),
      kv('H (Oe)', result.h_oe, 3),
    ],
  ));

  equations.push(formulaCard(
    '5. DC bias gecirgenlik orani',
    'Bias altinda etkin permeabilite orani Kool Mu katsayilariyla bulunur.',
    eq([
      '&mu;<sub>bias</sub> = max((1 / (a + b &middot; H<sup>c</sup>)) / 100, 0.05)',
    ]),
    `Katsayilar: a=${fmt(dcBias.a, 6)}, b=${fmt(dcBias.b, 6)}, c=${fmt(dcBias.c, 6)}`,
    [
      kv('mu_bias', result.mu_bias_ratio, 4),
      kv('AL25 (nH/T2)', core.al_nh_t2, 2),
    ],
  ));

  equations.push(formulaCard(
    '6. Sicaklik gecirgenlik orani',
    'Sicaklikla permeabilite duzeltmesi polinom olarak uygulanir.',
    eq([
      '&mu;<sub>temp</sub> = max(1 + a + bT + cT<sup>2</sup> + dT<sup>3</sup> + eT<sup>4</sup>, 0.1)',
    ]),
    `Katsayilar: a=${fmt(temp.a, 6)}, b=${fmt(temp.b, 6)}, c=${fmt(temp.c, 6)}, d=${fmt(temp.d, 6)}, e=${fmt(temp.e, 6)}`,
    [
      kv('Tcore (C)', result.t_core_c, 2),
      kv('mu_temp', result.mu_temp_ratio, 4),
      kv('AL_eff (nH/T2)', result.al_eff_nh_t2, 2),
    ],
  ));

  equations.push(formulaCard(
    '7. Enduktans',
    'Yuk altindaki enduktans, bias ve sicaklik duzeltilmis AL ile maksimum akim noktasinda hesaplanir.',
    eq([
      'L<sub>loaded</sub>(&micro;H) = A<sub>L,eff</sub> &middot; N<sup>2</sup> / 1000',
    ]),
    'Bu sayfada bakilan ana kosul: Ipk altinda elde edilen L_loaded hedefe yakin mi?',
    [
      kv('AL_eff (nH/T2)', result.al_eff_nh_t2, 2),
      kv('N', data.turns, 0),
      kv('L_loaded (uH)', result.l_uH, 2),
      kv('L error (%)', result.l_error_pct, 2),
    ],
  ));

  equations.push(formulaCard(
    '8. DC ve AC aki yogunlugu',
    'DC bias ve ripple bilesenleri ayri ayri bulunup toplam tepe akiya eklenir.',
    eq([
      'B<sub>dc</sub> = ((a + bH + cH<sup>2</sup>) / (1 + dH + eH<sup>2</sup>))<sup>x</sup>',
      'B<sub>ac,pk</sub> = L &middot; &Delta;I<sub>pp</sub> / (2 &middot; N &middot; A<sub>e</sub>)',
      'B<sub>pk</sub> = B<sub>dc</sub> + B<sub>ac,pk</sub>',
    ]),
    `BH katsayilari: a=${fmt(magnet.a, 6)}, b=${fmt(magnet.b, 6)}, c=${fmt(magnet.c, 6)}, d=${fmt(magnet.d, 6)}, e=${fmt(magnet.e, 6)}, x=${fmt(magnet.x, 6)}`,
    [
      kv('Ae (mm2)', core.ae_mm2, 2),
      kv('Bdc (T)', result.b_dc_t, 4),
      kv('Bac,pk (T)', result.b_ac_pk_t, 4),
      kv('Btotal,pk (T)', result.b_total_pk_t, 4),
    ],
  ));

  equations.push(formulaCard(
    '9. Steinmetz cekirdek kaybi',
    'Ripple akisindan hacimsel ve toplam cekirdek kaybi hesaplanir.',
    eq([
      'P<sub>v</sub>(mW/cm<sup>3</sup>) = a &middot; B<sup>b</sup> &middot; f(kHz)<sup>c</sup>',
      'P<sub>v</sub>(W/m<sup>3</sup>) = 1000 &middot; P<sub>v</sub>(mW/cm<sup>3</sup>)',
      'P<sub>core</sub> = P<sub>v</sub>(W/m<sup>3</sup>) &middot; V<sub>e</sub>',
    ]),
    `Steinmetz katsayilari: a=${fmt(loss.a, 6)}, b=${fmt(loss.b, 6)}, c=${fmt(loss.c, 6)}`,
    [
      kv('f (kHz)', op.f_sw_hz / 1000, 2),
      kv('Ve (mm3)', core.ve_mm3, 1),
      kv('Pv (W/m3)', result.pv_wpm3, 1),
      kv('Pcore (W)', result.p_core_w, 3),
    ],
  ));

  equations.push(formulaCard(
    '10. Dowell bakir kaybi',
    'Skin depth ve Dowell Fr carpani ile AC direnc ve bakir kaybi bulunur.',
    eq([
      '&delta; = &radic;(&rho; / (&pi; &middot; &mu;<sub>0</sub> &middot; f))',
      'R<sub>ac</sub> = F<sub>r</sub> &middot; R<sub>dc</sub>',
      'P<sub>cu</sub> = I<sub>rms</sub><sup>2</sup> &middot; R<sub>ac</sub>',
    ]),
    'Dowell detaylari backend icinde hesaplanir; burada ana ciktilar dogrudan gosterilir.',
    [
      kv('Skin depth (mm)', result.loss_details?.skin_depth_mm, 4),
      kv('Rdc total (ohm)', result.loss_details?.Rdc_total_ohm, 5),
      kv('Fr', result.fr, 4),
      kv('Rac total (ohm)', result.rac_total_ohm, 5),
      kv('Pcu (W)', result.p_cu_w, 3),
    ],
  ));

  equations.push(formulaCard(
    '11. Termal model',
    'Hurley yaklasimi ile termal direnc ve cekirdek sicakligi tahmin edilir.',
    eq([
      'R<sub>th</sub> = (k / &radic;V<sub>c</sub>) &middot; scale',
      'T<sub>core</sub> = T<sub>amb</sub> + R<sub>th</sub> &middot; P<sub>total</sub>',
    ]),
    `V<sub>c</sub> burada m<sup>3</sup> cinsindendir. Bu nedenle k boyutsuz degildir; ampirik olarak ${result.thermal_details?.k_units || 'C*m^(3/2)/W'} birimi tasir. Kaynak=${result.thermal_details?.k_source || '-'}, ventilation=${result.thermal_details?.Ventilation || '-'}`,
    [
      kv('Vc (m3)', result.thermal_details?.Vc_m3, 8),
      kv('k', result.thermal_details?.k_used, 4),
      kv('Rth (C/W)', result.rth_c_per_w, 3),
      kv('Ptotal (W)', result.p_tot_w, 3),
      kv('Tcore (C)', result.t_core_c, 2),
    ],
  ));

  equations.push(formulaCard(
    '12. Gecerlilik kontrolu',
    'Aday; maksimum akimdaki enduktans, sicaklik, akis ve mekanik sinirlara gore kabul veya red edilir.',
    eq([
      'feasible = |L<sub>err</sub>| &le; L<sub>tol</sub>',
      'and T<sub>core</sub> &le; T<sub>amb</sub> + riseLimit',
      'and B<sub>pk</sub> &le; B<sub>limit</sub>',
      'and winding fits',
    ]),
    'Buradaki Lerr, Ipk altinda hesaplanan yuklu enduktans ile hedef arasindaki farktir.',
    [
      kv('L tol (%)', Number(testForm.elements.l_tolerance_pct.value || 0), 2),
      kv('B limit (T)', Number(testForm.elements.b_limit_t.value || 0), 3),
      kv('Fits', geom.fits ? 1 : 0, 0),
      kv('Feasible', result.feasible ? 1 : 0, 0),
    ],
  ));

  formulaSections.innerHTML = equations.join('');
}

async function loadCatalog() {
  const response = await fetch('/api/catalog');
  const catalog = await response.json();
  state.catalog = catalog;
  coreSelect.innerHTML = catalog.cores.map((core) => `<option value="${core.id}">${core.part_number} / ${core.permeability} | Ve ${fmt(core.ve_mm3, 0)} mm3</option>`).join('');
  wireSelect.innerHTML = catalog.wires.map((wire) => `<option value="${wire.id}">AWG ${wire.awg} | ${fmt(wire.area_mm2, 3)} mm2</option>`).join('');
  coreSelect.value = catalog.defaults.core_id;
  wireSelect.value = catalog.defaults.wire_id;
  renderFunctionMap();
  modePanels(designMode.value);
  loadDerivedCurrents();
  summary.textContent = 'Hazir. Hesaplar sadece sen butona bastiginda calisir.';
  formulaSections.innerHTML = '';
}

async function runTest(event) {
  event?.preventDefault();
  statusBox.textContent = 'Manyetik test hesaplaniyor...';
  const response = await fetch('/api/candidate-detail', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payloadFromForm()),
  });
  const result = await response.json();
  if (!response.ok) {
    summary.className = 'summary empty';
    summary.textContent = result.error || 'Hesap basarisiz';
    formulaSections.innerHTML = '';
    statusBox.textContent = 'Hesap basarisiz oldu.';
    return;
  }
  renderSummary(result);
  renderSections(result);
  statusBox.textContent = 'Ayni backend fonksiyonlariyla detayli test tamamlandi.';
}

designMode.addEventListener('change', () => modePanels(designMode.value));
testForm.addEventListener('submit', runTest);
testForm.elements.i_pk_a?.addEventListener('input', loadDerivedCurrents);
testForm.elements.delta_i_pp_a?.addEventListener('input', loadDerivedCurrents);
turnsInput.addEventListener('input', () => {
  if (Number(turnsInput.value) < 1) turnsInput.value = 1;
});

loadCatalog().catch((error) => {
  summary.textContent = `Katalog yuklenemedi: ${error}`;
  statusBox.textContent = 'Baslangic yuklemesi basarisiz.';
});
