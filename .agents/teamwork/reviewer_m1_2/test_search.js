const fs = require('fs');
const appCode = fs.readFileSync('app.js', 'utf8');
const raw = JSON.parse(fs.readFileSync('data/comunas_enriched.json', 'utf8'));

const vm = require('vm');
const sandbox = { console, Map, Set, Array, Math };

// Load normalizeText, COMUNA_ALIASES, deduplicateComunas, getFilteredComunas
const p1 = appCode.slice(appCode.indexOf('function normalizeText'), appCode.indexOf('function showErrorBanner'));
const p2 = appCode.slice(appCode.indexOf('function getFilteredComunas'), appCode.indexOf('// -------------------------------------------------------------------------\n  // 6. RANKING'));

vm.runInNewContext(p1 + '\n' + p2 + '\nthis.dedup = deduplicateComunas; this.getFiltered = getFilteredComunas;', sandbox);

const comunas = sandbox.dedup(raw);
sandbox.state = {
  comunas: comunas,
  searchQuery: '',
  selectedRegion: '',
  selectedCuadrante: ''
};

// Test empty search
console.log('Empty search count:', sandbox.getFiltered().length, '(expected 346)');
if (sandbox.getFiltered().length !== 346) throw new Error('Expected 346 comunas on empty search');

// Test queries
const queries = [
  ['maipu', 'Maipú'],
  ['Maipú', 'Maipú'],
  ['conchali', 'Conchalí'],
  ['coyhaique', 'Coihaique'],
  ['marchigue', 'Marchihue'],
  ['navarino', 'Cabo de Hornos'],
  ['puerto williams', 'Cabo de Hornos'],
  ['santiago', 'Santiago Centro'],
  ['llay-llay', 'Llaillay'],
  ['trehuaco', 'Treguaco']
];

for (const [q, expected] of queries) {
  sandbox.state.searchQuery = q;
  const res = sandbox.getFiltered();
  const found = res.some(c => c.comuna === expected);
  console.log(`Query "${q}": returned ${res.length} results. Contains "${expected}": ${found}`);
  if (!found) throw new Error(`Search failed for: ${q}`);
}

// Test region filter
sandbox.state.searchQuery = '';
sandbox.state.selectedRegion = 'Región de Valparaíso';
const valpo = sandbox.getFiltered();
console.log('Region filter "Región de Valparaíso": count =', valpo.length);
if (valpo.length === 0 || !valpo.every(c => c.region === 'Región de Valparaíso')) throw new Error('Region filter failed');

// Test cuadrante filter
sandbox.state.selectedRegion = '';
sandbox.state.selectedCuadrante = 'Estado Artesanal';
const art = sandbox.getFiltered();
console.log('Cuadrante filter "Estado Artesanal": count =', art.length);
if (art.length === 0 || !art.every(c => c.cuadrante_capacidad === 'Estado Artesanal')) throw new Error('Cuadrante filter failed');

console.log('>>> ALL getFilteredComunas TESTS PASSED <<<');
