/**
 * tests/stress_test_m1.js
 * =======================
 * Standalone stress-test harness for Milestone 1:
 * - Map layer marker styling and dynamic radius (getMarkerStyle)
 * - Map legend generation and consistency (updateLegend)
 * - Data deduplication, coordinate validity, and commune integrity (deduplicateComunas)
 * - Full corpus validation across all 346 unique Chilean municipalities
 */

const fs = require('fs');
const path = require('path');
const vm = require('vm');

console.log('================================================================');
console.log('   OBSERVATORIO TI MUNICIPAL — EMPIRICAL STRESS TEST (M1)       ');
console.log('================================================================\n');

// 1. Read app.js and raw data
const rootDir = path.resolve(__dirname, '..');
const appJsPath = path.join(rootDir, 'app.js');
const rawDataPath = path.join(rootDir, 'data', 'comunas_enriched.json');

if (!fs.existsSync(appJsPath)) {
  console.error('FATAL: app.js not found at:', appJsPath);
  process.exit(1);
}
if (!fs.existsSync(rawDataPath)) {
  console.error('FATAL: data/comunas_enriched.json not found at:', rawDataPath);
  process.exit(1);
}

const appCode = fs.readFileSync(appJsPath, 'utf8');
const rawComunas = JSON.parse(fs.readFileSync(rawDataPath, 'utf8'));

console.log(`[INFO] Loaded app.js (${appCode.length} bytes)`);
console.log(`[INFO] Loaded raw data: ${rawComunas.length} records\n`);

// 2. Set up execution sandbox for app.js functions
// Extract helper and layer functions
const fnNormalizer = appCode.slice(
  appCode.indexOf('function normalizeText'),
  appCode.indexOf('function showErrorBanner')
);

const markerCode = appCode.slice(
  appCode.indexOf('function getMarkerStyle'),
  appCode.indexOf('function renderMapMarkers')
);

const legendCode = appCode.slice(
  appCode.indexOf('function updateLegend'),
  appCode.indexOf('// -------------------------------------------------------------------------') > 0
    ? appCode.indexOf('// -------------------------------------------------------------------------\n  // 4. RADIOGRAFÍA')
    : appCode.indexOf('function renderGaugeSvg')
);

// Mock DOM & Leaflet minimal context
let mockLegendHtml = '';
const mockDocument = {
  getElementById: (id) => {
    if (id === 'map-legend') {
      return {
        set innerHTML(val) { mockLegendHtml = val; },
        get innerHTML() { return mockLegendHtml; }
      };
    }
    return null;
  }
};

const sandbox = {
  Array,
  Map,
  Set,
  Math,
  Number,
  String,
  Boolean,
  console,
  document: mockDocument,
  state: {
    comunas: [],
    currentLayer: 'madurez'
  }
};

vm.createContext(sandbox);

// Evaluate extracted logic inside the sandbox
const script = new vm.Script(`
  ${fnNormalizer}
  ${markerCode}
  ${legendCode}
  this.normalizeText = normalizeText;
  this.resolveComunaName = resolveComunaName;
  this.findComunaByName = findComunaByName;
  this.deduplicateComunas = deduplicateComunas;
  this.getMarkerStyle = getMarkerStyle;
  this.updateLegend = updateLegend;
`);

script.runInContext(sandbox);

let failures = [];
let warnings = [];
let passCount = 0;

function assert(cond, msg, isWarning = false) {
  if (cond) {
    passCount++;
  } else {
    if (isWarning) {
      warnings.push(msg);
      console.warn(`  [WARN] ${msg}`);
    } else {
      failures.push(msg);
      console.error(`  [FAIL] ${msg}`);
    }
  }
}

// ============================================================================
// SUITE 1: Deduplication & Data Integrity Stress Tests
// ============================================================================
console.log('----------------------------------------------------------------');
console.log('SUITE 1: Deduplication & Data Integrity (deduplicateComunas)');
console.log('----------------------------------------------------------------');

// (a) Execute deduplication on raw dataset
const consolidated = sandbox.deduplicateComunas(rawComunas);
sandbox.state.comunas = consolidated;

console.log(`[TEST 1.1] Consolidated count: ${consolidated.length} (expected: 346)`);
assert(consolidated.length === 346, `Expected exactly 346 unique municipalities, got ${consolidated.length}`);

// (b) Unique CUT codes check
const cutSet = new Set();
const duplicateCuts = [];
consolidated.forEach(c => {
  if (cutSet.has(c.codigo_cut)) duplicateCuts.push(c.codigo_cut);
  cutSet.add(c.codigo_cut);
});
console.log(`[TEST 1.2] Unique CUT codes: ${cutSet.size} / ${consolidated.length}`);
assert(duplicateCuts.length === 0, `Found duplicate CUT codes: ${duplicateCuts.join(', ')}`);

// (c) Unique comuna names check
const nameSet = new Set();
const duplicateNames = [];
consolidated.forEach(c => {
  const norm = sandbox.normalizeText(c.comuna);
  if (nameSet.has(norm)) duplicateNames.push(c.comuna);
  nameSet.add(norm);
});
console.log(`[TEST 1.3] Unique normalized comuna names: ${nameSet.size} / ${consolidated.length}`);
assert(duplicateNames.length === 0, `Found duplicate comuna names: ${duplicateNames.join(', ')}`);

// (d) Geolocation validity (lat/lng not null, not undefined, not NaN, finite, within Chile)
let invalidCoords = [];
consolidated.forEach(c => {
  const latValid = typeof c.lat === 'number' && !Number.isNaN(c.lat) && Number.isFinite(c.lat);
  const lngValid = typeof c.lng === 'number' && !Number.isNaN(c.lng) && Number.isFinite(c.lng);
  if (!latValid || !lngValid) {
    invalidCoords.push({ comuna: c.comuna, cut: c.codigo_cut, lat: c.lat, lng: c.lng });
  }
});
console.log(`[TEST 1.4] Municipalities with invalid/NaN coordinates: ${invalidCoords.length}`);
assert(invalidCoords.length === 0, `Found ${invalidCoords.length} municipalities with invalid coordinates: ${JSON.stringify(invalidCoords)}`);

// Check coordinate geographic plausibility (Chile approx: lat -65 to -17, lng -110 to -55)
let outOfBoundsCoords = [];
consolidated.forEach(c => {
  if (c.lat < -65 || c.lat > -17 || c.lng < -110 || c.lng > -55) {
    outOfBoundsCoords.push({ comuna: c.comuna, lat: c.lat, lng: c.lng });
  }
});
console.log(`[TEST 1.5] Geographic boundaries check (Chile): ${outOfBoundsCoords.length} outliers`);
assert(outOfBoundsCoords.length === 0, `Coordinates outside Chilean territorial bounds: ${JSON.stringify(outOfBoundsCoords)}`);

// (e) Specific edge-case communes inspection
const santiago = consolidated.find(c => c.codigo_cut === 13101 || c.comuna === 'Santiago Centro');
console.log(`[TEST 1.6] Santiago Centro coordinates: [${santiago?.lat}, ${santiago?.lng}]`);
assert(santiago && santiago.lat === -33.4489 && santiago.lng === -70.6693, 'Santiago Centro coordinates are incorrect');

const ovalle = consolidated.find(c => c.codigo_cut === 4301 || c.comuna === 'Ovalle');
console.log(`[TEST 1.7] Ovalle record: total_ocs=${ovalle?.total_ocs}, monto_total=$${ovalle?.monto_total}`);
assert(ovalle && ovalle.total_ocs > 1 && ovalle.monto_total > 1000000, `Ovalle deduplication resolved to corrupted micro-fragment: total_ocs=${ovalle?.total_ocs}, monto=${ovalle?.monto_total}`);

const combarbala = consolidated.find(c => c.codigo_cut === 4302 || sandbox.normalizeText(c.comuna) === 'combarbala');
console.log(`[TEST 1.8] Combarbalá presence: found=${!!combarbala}, lat=${combarbala?.lat}, lng=${combarbala?.lng}`);
assert(combarbala && typeof combarbala.lat === 'number' && typeof combarbala.lng === 'number', 'Combarbalá (CUT 4302) is missing or has invalid coordinates');

const antartica = consolidated.find(c => c.codigo_cut === 12202 || sandbox.normalizeText(c.comuna) === 'antartica');
console.log(`[TEST 1.9] Antártica presence: found=${!!antartica}, lat=${antartica?.lat}, lng=${antartica?.lng}`);
assert(antartica && typeof antartica.lat === 'number' && typeof antartica.lng === 'number', 'Antártica (CUT 12202) is missing or has invalid coordinates');

// (f) Adversarial inputs to deduplicateComunas
console.log('[TEST 1.10] Adversarial inputs to deduplicateComunas:');
assert(Array.isArray(sandbox.deduplicateComunas(null)) && sandbox.deduplicateComunas(null).length === 0, 'deduplicateComunas(null) should return empty array');
assert(Array.isArray(sandbox.deduplicateComunas(undefined)) && sandbox.deduplicateComunas(undefined).length === 0, 'deduplicateComunas(undefined) should return empty array');
assert(Array.isArray(sandbox.deduplicateComunas([])), 'deduplicateComunas([]) should return an array');
assert(Array.isArray(sandbox.deduplicateComunas([{}])), 'deduplicateComunas([{}]) should not throw');
assert(Array.isArray(sandbox.deduplicateComunas([
  { codigo_cut: 9999, comuna: 'Test A', lat: null, lng: null, monto_total: 100 },
  { codigo_cut: 9999, comuna: 'Test B', lat: null, lng: null, monto_total: 500 }
])), 'deduplicateComunas with all-null coordinates should not throw');


// ============================================================================
// SUITE 2: Map Layer Styles (getMarkerStyle) Stress Tests
// ============================================================================
console.log('\n----------------------------------------------------------------');
console.log('SUITE 2: Map Layer Marker Styles (getMarkerStyle) Stress Tests');
console.log('----------------------------------------------------------------');

// Helper to validate style object
function validateStyle(layer, inputDesc, style, expectedColor, expectedMinRadius, expectedMaxRadius) {
  const isColorValid = typeof style.color === 'string' && /^#[0-9a-fA-F]{6}$/.test(style.color);
  const isRadiusValid = typeof style.radius === 'number' && !Number.isNaN(style.radius) && Number.isFinite(style.radius) && style.radius > 0;

  assert(isColorValid, `[${layer}] [${inputDesc}] Color is not a valid hex string: ${style.color}`);
  assert(isRadiusValid, `[${layer}] [${inputDesc}] Radius is invalid or NaN: ${style.radius}`);

  if (expectedColor) {
    assert(style.color.toLowerCase() === expectedColor.toLowerCase(), `[${layer}] [${inputDesc}] Expected color ${expectedColor}, got ${style.color}`);
  }
  if (expectedMinRadius !== undefined && expectedMaxRadius !== undefined) {
    assert(style.radius >= expectedMinRadius && style.radius <= expectedMaxRadius,
      `[${layer}] [${inputDesc}] Radius ${style.radius} outside expected range [${expectedMinRadius}, ${expectedMaxRadius}]`);
  }
}

// 2.1 Layer "ret" (Tecnoestructura Estatal)
console.log('\n--- 2.1 Layer: ret (Ratio Tecnoestructura Estatal) ---');
sandbox.state.currentLayer = 'ret';

const retTestCases = [
  { val: null, desc: 'null', expColor: '#9b2226', minR: 5, maxR: 5 },
  { val: undefined, desc: 'undefined', expColor: '#9b2226', minR: 5, maxR: 5 },
  { val: 0, desc: '0', expColor: '#9b2226', minR: 5, maxR: 5 },
  { val: 0.1, desc: '0.1', expColor: '#9b2226', minR: 5, maxR: 5 },
  { val: 0.49, desc: '0.49 (boundary < 0.5)', expColor: '#9b2226', minR: 5, maxR: 5 },
  { val: 0.49999, desc: '0.49999 (boundary < 0.5)', expColor: '#9b2226', minR: 5, maxR: 5 },
  { val: 0.5, desc: '0.5 (boundary >= 0.5)', expColor: '#b38209', minR: 5, maxR: 5 },
  { val: 0.75, desc: '0.75 (mid-artesanal)', expColor: '#b38209', minR: 5, maxR: 5 },
  { val: 0.99, desc: '0.99 (boundary < 1.0)', expColor: '#b38209', minR: 5, maxR: 5 },
  { val: 1.0, desc: '1.0 (boundary >= 1.0)', expColor: '#2b5c8f', minR: 5, maxR: 5 },
  { val: 1.5, desc: '1.5 (mid-hibrido)', expColor: '#2b5c8f', minR: 6, maxR: 6 },
  { val: 1.99, desc: '1.99 (boundary < 2.0)', expColor: '#2b5c8f', minR: 8, maxR: 8 },
  { val: 2.0, desc: '2.0 (boundary >= 2.0)', expColor: '#146e66', minR: 8, maxR: 8 },
  { val: 2.5, desc: '2.5 (strong)', expColor: '#146e66', minR: 10, maxR: 10 },
  { val: 3.5, desc: '3.5 (high)', expColor: '#146e66', minR: 14, maxR: 14 },
  { val: 100.0, desc: '100.0 (extreme high)', expColor: '#146e66', minR: 14, maxR: 14 },
  { val: -1.0, desc: '-1.0 (negative edge)', expColor: '#9b2226', minR: 5, maxR: 5 },
  { val: NaN, desc: 'NaN', expColor: '#9b2226', minR: 5, maxR: 5 },
  { val: Infinity, desc: 'Infinity', expColor: '#146e66', minR: 14, maxR: 14 }
];

retTestCases.forEach(tc => {
  const style = sandbox.getMarkerStyle({ ret_ratio: tc.val });
  validateStyle('ret', `ret_ratio=${tc.desc}`, style, tc.expColor, tc.minR, tc.maxR);
});

// 2.2 Layer "rrhh" (Dotación Honorarios)
console.log('\n--- 2.2 Layer: rrhh (Dotación a Honorarios) ---');
sandbox.state.currentLayer = 'rrhh';

const rrhhTestCases = [
  { val: null, desc: 'null', expColor: '#146e66', minR: 5, maxR: 5 },
  { val: undefined, desc: 'undefined', expColor: '#146e66', minR: 5, maxR: 5 },
  { val: 0, desc: '0%', expColor: '#146e66', minR: 5, maxR: 5 },
  { val: 20, desc: '20% (low honorarios)', expColor: '#146e66', minR: 5, maxR: 5 },
  { val: 39, desc: '39% (boundary < 40%)', expColor: '#146e66', minR: 6, maxR: 6 },
  { val: 39.9, desc: '39.9% (boundary < 40%)', expColor: '#146e66', minR: 6, maxR: 6 },
  { val: 40, desc: '40% (boundary >= 40%)', expColor: '#b38209', minR: 6, maxR: 6 },
  { val: 50, desc: '50% (mid alerta)', expColor: '#b38209', minR: 8, maxR: 8 },
  { val: 59, desc: '59% (boundary < 60%)', expColor: '#b38209', minR: 9, maxR: 9 },
  { val: 60, desc: '60% (boundary <= 60%)', expColor: '#b38209', minR: 9, maxR: 9 },
  { val: 60.1, desc: '60.1% (boundary > 60%)', expColor: '#9b2226', minR: 9, maxR: 9 },
  { val: 75, desc: '75% (critica)', expColor: '#9b2226', minR: 11, maxR: 11 },
  { val: 100, desc: '100% (max honorarios)', expColor: '#9b2226', minR: 13, maxR: 13 },
  { val: 200, desc: '200% (extreme high)', expColor: '#9b2226', minR: 13, maxR: 13 },
  { val: -10, desc: '-10% (negative edge)', expColor: '#146e66', minR: 5, maxR: 5 },
  { val: NaN, desc: 'NaN', expColor: '#146e66', minR: 5, maxR: 5 }
];

rrhhTestCases.forEach(tc => {
  const style = sandbox.getMarkerStyle({ pct_honorarios: tc.val });
  validateStyle('rrhh', `pct_honorarios=${tc.desc}`, style, tc.expColor, tc.minR, tc.maxR);
});

// 2.3 Layer "madurez"
console.log('\n--- 2.3 Layer: madurez (Termómetro de Madurez TI) ---');
sandbox.state.currentLayer = 'madurez';

const madurezTestCases = [
  { val: 100, desc: '100 (Avanzada)', expColor: '#146e66', minR: 12, maxR: 12 },
  { val: 80, desc: '80 (Boundary Avanzada)', expColor: '#146e66', minR: 9, maxR: 10 },
  { val: 79.9, desc: '79.9 (Intermedia)', expColor: '#2b5c8f', minR: 9, maxR: 10 },
  { val: 60, desc: '60 (Boundary Intermedia)', expColor: '#2b5c8f', minR: 7, maxR: 8 },
  { val: 59.9, desc: '59.9 (Inicial)', expColor: '#b38209', minR: 7, maxR: 8 },
  { val: 40, desc: '40 (Boundary Inicial)', expColor: '#b38209', minR: 5, maxR: 5 },
  { val: 39.9, desc: '39.9 (Rezago)', expColor: '#a3492e', minR: 5, maxR: 5 },
  { val: 0, desc: '0 (Rezago mínimo)', expColor: '#a3492e', minR: 5, maxR: 5 },
  { val: null, desc: 'null', expColor: '#a3492e', minR: 5, maxR: 5 },
  { val: -10, desc: '-10', expColor: '#a3492e', minR: 5, maxR: 5 }
];

madurezTestCases.forEach(tc => {
  const style = sandbox.getMarkerStyle({ score_madurez: tc.val });
  validateStyle('madurez', `score_madurez=${tc.desc}`, style, tc.expColor, tc.minR, tc.maxR);
});

// Adversarial test for madurez: undefined score_madurez
const styleMadurezUndef = sandbox.getMarkerStyle({});
if (Number.isNaN(styleMadurezUndef.radius)) {
  assert(false, `[madurez] score_madurez=undefined produces radius=NaN!`, true);
} else {
  assert(true, `[madurez] score_madurez=undefined handled cleanly`);
}

// 2.4 Layer "gasto_pc"
console.log('\n--- 2.4 Layer: gasto_pc (Gasto TI Per Cápita) ---');
sandbox.state.currentLayer = 'gasto_pc';

const gastoTestCases = [
  { val: 50000, desc: '$50.000 (>30k)', expColor: '#002b49', minR: 15, maxR: 15 },
  { val: 30001, desc: '$30.001 (>30k)', expColor: '#002b49', minR: 12, maxR: 13 },
  { val: 30000, desc: '$30.000 (boundary)', expColor: '#146e66', minR: 12, maxR: 13 },
  { val: 15001, desc: '$15.001 (>15k)', expColor: '#146e66', minR: 8, maxR: 9 },
  { val: 15000, desc: '$15.000 (boundary)', expColor: '#b38209', minR: 8, maxR: 9 },
  { val: 5001, desc: '$5.001 (>5k)', expColor: '#b38209', minR: 5, maxR: 6 },
  { val: 5000, desc: '$5.000 (boundary)', expColor: '#dcd7cc', minR: 5, maxR: 5 },
  { val: 1000, desc: '$1.000 (rezago)', expColor: '#dcd7cc', minR: 4, maxR: 4 },
  { val: 0, desc: '$0', expColor: '#dcd7cc', minR: 4, maxR: 4 },
  { val: null, desc: 'null', expColor: '#dcd7cc', minR: 4, maxR: 4 },
  { val: undefined, desc: 'undefined', expColor: '#dcd7cc', minR: 4, maxR: 4 }
];

gastoTestCases.forEach(tc => {
  const style = sandbox.getMarkerStyle({ gasto_pc: tc.val });
  validateStyle('gasto_pc', `gasto_pc=${tc.desc}`, style, tc.expColor, tc.minR, tc.maxR);
});

// Adversarial test for gasto_pc: negative gasto_pc
const styleGastoNeg = sandbox.getMarkerStyle({ gasto_pc: -500 });
if (Number.isNaN(styleGastoNeg.radius)) {
  assert(false, `[gasto_pc] gasto_pc=-500 produces radius=NaN via Math.sqrt(-2.5)!`, true);
} else {
  assert(true, `[gasto_pc] negative gasto_pc handled cleanly`);
}

// 2.5 Layer "lockin"
console.log('\n--- 2.5 Layer: lockin (Vendor Lock-in Legado) ---');
sandbox.state.currentLayer = 'lockin';
validateStyle('lockin', 'tiene_lockin_legado=true', sandbox.getMarkerStyle({ tiene_lockin_legado: true }), '#9b2226', 8, 8);
validateStyle('lockin', 'tiene_lockin_legado=false', sandbox.getMarkerStyle({ tiene_lockin_legado: false }), '#e5eee9', 4, 4);
validateStyle('lockin', 'tiene_lockin_legado=null', sandbox.getMarkerStyle({ tiene_lockin_legado: null }), '#e5eee9', 4, 4);
validateStyle('lockin', 'tiene_lockin_legado=undefined', sandbox.getMarkerStyle({}), '#e5eee9', 4, 4);

// 2.6 Layer "foss"
console.log('\n--- 2.6 Layer: foss (Software Libre) ---');
sandbox.state.currentLayer = 'foss';
validateStyle('foss', 'tiene_foss=true', sandbox.getMarkerStyle({ tiene_foss: true }), '#2d6a4f', 9, 9);
validateStyle('foss', 'tiene_foss=false', sandbox.getMarkerStyle({ tiene_foss: false }), '#ded8cb', 4, 4);
validateStyle('foss', 'tiene_foss=null', sandbox.getMarkerStyle({ tiene_foss: null }), '#ded8cb', 4, 4);
validateStyle('foss', 'tiene_foss=undefined', sandbox.getMarkerStyle({}), '#ded8cb', 4, 4);

// 2.7 Layer "infra"
console.log('\n--- 2.7 Layer: infra (Infraestructura Propia) ---');
sandbox.state.currentLayer = 'infra';
validateStyle('infra', 'tiene_infra_propia=true', sandbox.getMarkerStyle({ tiene_infra_propia: true }), '#002b49', 8, 8);
validateStyle('infra', 'tiene_infra_propia=false', sandbox.getMarkerStyle({ tiene_infra_propia: false }), '#ded8cb', 4, 4);
validateStyle('infra', 'tiene_infra_propia=null', sandbox.getMarkerStyle({ tiene_infra_propia: null }), '#ded8cb', 4, 4);
validateStyle('infra', 'tiene_infra_propia=undefined', sandbox.getMarkerStyle({}), '#ded8cb', 4, 4);

// 2.8 Default / Fallback Layer
console.log('\n--- 2.8 Layer: fallback (Unknown Layer) ---');
sandbox.state.currentLayer = 'non_existent_layer';
validateStyle('fallback', 'unknown_layer', sandbox.getMarkerStyle({}), '#146e66', 6, 6);


// ============================================================================
// SUITE 3: Map Legend (updateLegend) Consistency Tests
// ============================================================================
console.log('\n----------------------------------------------------------------');
console.log('SUITE 3: Map Legend (updateLegend) Consistency Across All 7 Layers');
console.log('----------------------------------------------------------------');

const allLayers = ['madurez', 'gasto_pc', 'ret', 'rrhh', 'lockin', 'foss', 'infra'];

allLayers.forEach(layer => {
  sandbox.state.currentLayer = layer;
  mockLegendHtml = '';
  sandbox.updateLegend();

  const hasTitle = mockLegendHtml.includes('map-legend-title');
  const hasItems = mockLegendHtml.includes('map-legend-items');
  const hasColorBox = mockLegendHtml.includes('legend-color-box');

  console.log(`[TEST 3.${allLayers.indexOf(layer)+1}] Layer "${layer}" legend output: title=${hasTitle}, items=${hasItems}, colorBox=${hasColorBox}`);
  assert(hasTitle, `[updateLegend] Missing title for layer "${layer}"`);
  assert(hasItems, `[updateLegend] Missing items container for layer "${layer}"`);
  assert(hasColorBox, `[updateLegend] Missing color boxes for layer "${layer}"`);

  // Verify color consistency with marker styles:
  // e.g. for ret, verify teal (#146e66), steel blue (#2b5c8f), gold (#b38209), crimson (#9b2226)
  if (layer === 'ret') {
    assert(mockLegendHtml.includes('#146e66'), 'ret legend missing sovereign teal #146e66');
    assert(mockLegendHtml.includes('#2b5c8f'), 'ret legend missing hybrid steel blue #2b5c8f');
    assert(mockLegendHtml.includes('#b38209'), 'ret legend missing artesanal gold #b38209');
    assert(mockLegendHtml.includes('#9b2226'), 'ret legend missing cautivo crimson #9b2226');
  } else if (layer === 'rrhh') {
    assert(mockLegendHtml.includes('#9b2226'), 'rrhh legend missing critical crimson #9b2226');
    assert(mockLegendHtml.includes('#b38209'), 'rrhh legend missing alert gold #b38209');
    assert(mockLegendHtml.includes('#146e66'), 'rrhh legend missing stable teal #146e66');
  }
});

// Test updateLegend when DOM element is missing
const oldDoc = sandbox.document;
sandbox.document = { getElementById: () => null };
try {
  sandbox.updateLegend();
  assert(true, 'updateLegend() handled missing DOM element gracefully without throwing');
} catch (e) {
  assert(false, `updateLegend() threw with missing DOM element: ${e.message}`);
}
sandbox.document = oldDoc;


// ============================================================================
// SUITE 4: Full Corpus In-Vivo Validation (All 346 Consolidated Municipalities)
// ============================================================================
console.log('\n----------------------------------------------------------------');
console.log('SUITE 4: Full Corpus Validation (346 Real Municipalities x 7 Layers)');
console.log('----------------------------------------------------------------');

let corpusFailures = [];
let totalCorpusChecks = 0;

allLayers.forEach(layer => {
  sandbox.state.currentLayer = layer;
  consolidated.forEach(comuna => {
    totalCorpusChecks++;
    try {
      const style = sandbox.getMarkerStyle(comuna);
      const isColorValid = typeof style.color === 'string' && /^#[0-9a-fA-F]{6}$/.test(style.color);
      const isRadiusValid = typeof style.radius === 'number' && !Number.isNaN(style.radius) && Number.isFinite(style.radius) && style.radius > 0;

      if (!isColorValid || !isRadiusValid) {
        corpusFailures.push({
          comuna: comuna.comuna,
          cut: comuna.codigo_cut,
          layer: layer,
          style: style
        });
      }
    } catch (e) {
      corpusFailures.push({
        comuna: comuna.comuna,
        cut: comuna.codigo_cut,
        layer: layer,
        error: e.message
      });
    }
  });
});

console.log(`[TEST 4.1] Evaluated ${totalCorpusChecks} marker styles across 346 municipalities x 7 layers`);
console.log(`[TEST 4.2] Corpus anomalies / NaN radius count: ${corpusFailures.length}`);
assert(corpusFailures.length === 0, `Corpus style validation failures: ${JSON.stringify(corpusFailures.slice(0, 5))}`);


// ============================================================================
// FINAL SUMMARY & VERDICT
// ============================================================================
console.log('\n================================================================');
console.log('STRESS TEST SUMMARY');
console.log('================================================================');
console.log(`Passed checks:   ${passCount}`);
console.log(`Warnings:        ${warnings.length}`);
console.log(`Critical fails:  ${failures.length}`);

if (warnings.length > 0) {
  console.log('\nWarnings list:');
  warnings.forEach(w => console.log(`  - ${w}`));
}

if (failures.length > 0) {
  console.log('\nFailures list:');
  failures.forEach(f => console.log(`  - ${f}`));
  console.log('\n>>> RESULT: REJECT <<<');
  process.exit(1);
} else {
  console.log('\n>>> RESULT: APPROVE <<<');
  process.exit(0);
}
