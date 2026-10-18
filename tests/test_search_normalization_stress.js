/**
 * tests/test_search_normalization_stress.js
 * =========================================
 * Empirical Stress Test Suite for Observatorio TI Municipal
 * Milestone 1 - Challenger 2
 */

const fs = require('fs');
const path = require('path');
const vm = require('vm');

// 1. Load app.js and data
const appJsPath = path.resolve(__dirname, '..', 'app.js');
const rawComunasPath = path.resolve(__dirname, '..', 'data', 'comunas_enriched.json');
const provsPathPath = path.resolve(__dirname, '..', 'data', 'proveedores_ranking.json');

const appSource = fs.readFileSync(appJsPath, 'utf8');
const rawComunas = JSON.parse(fs.readFileSync(rawComunasPath, 'utf8'));
const rawProvs = JSON.parse(fs.readFileSync(provsPathPath, 'utf8'));

// Extract core logic functions from app.js to create an isolated test sandbox
const sandbox = {
  console,
  Array,
  Map,
  Set,
  Math,
  JSON,
  Boolean,
  String,
  decodeURIComponent,
  encodeURIComponent,
  window: { location: { hash: '' } },
  document: {
    getElementById: () => null,
    querySelector: () => null,
    querySelectorAll: () => []
  },
  state: {
    comunas: [],
    proveedores: rawProvs,
    searchQuery: '',
    selectedRegion: '',
    selectedCuadrante: '',
    currentLayer: 'madurez',
    isCompareMode: false,
    selectedComuna: null,
    compareComuna: null
  },
  selectComuna: (c) => { sandbox.state.selectedComuna = c; },
  openComparison: (a, b) => { sandbox.state.selectedComuna = a; sandbox.state.compareComuna = b; sandbox.state.isCompareMode = true; }
};

const scriptCode = 
  appSource.slice(appSource.indexOf('function normalizeText'), appSource.indexOf('function initScrollytelling')) + '\n' +
  appSource.slice(appSource.indexOf('function findProviderMatch'), appSource.indexOf('// 6. RANKING & TABLA DE DATOS')) + '\n' +
  appSource.slice(appSource.indexOf('function handleHashRoute'), appSource.indexOf('async function init()')) + '\n' +
  'this.normalizeText = normalizeText;\n' +
  'this.COMUNA_ALIASES = COMUNA_ALIASES;\n' +
  'this.resolveComunaName = resolveComunaName;\n' +
  'this.findComunaByName = findComunaByName;\n' +
  'this.deduplicateComunas = deduplicateComunas;\n' +
  'this.findProviderMatch = findProviderMatch;\n' +
  'this.getFilteredComunas = getFilteredComunas;\n' +
  'this.handleHashRoute = handleHashRoute;\n';

const vmContext = vm.createContext(sandbox);
new vm.Script(scriptCode).runInContext(vmContext);

// Deduplicate comunas to populate state.comunas
sandbox.state.comunas = sandbox.deduplicateComunas(rawComunas);

console.log('======================================================================');
console.log('CHALLENGER 2: EMPIRICAL STRESS SUITE - SEARCH NORMALIZATION & RESILIENCE');
console.log('======================================================================');
console.log('Total deduplicated comunas in state:', sandbox.state.comunas.length);
console.log('Total providers in state:', sandbox.state.proveedores.length);

const results = {
  passed: 0,
  failed: 0,
  failures: []
};

function assert(condition, message, details = {}) {
  if (condition) {
    results.passed++;
  } else {
    results.failed++;
    results.failures.push({ message, details });
    console.error('[FAIL] ' + message, details);
  }
}

// ======================================================================
// TEST 1: ALL 79+ CHILEAN COMMUNES WITH ACCENTS/Ñ (STRESS COVERAGE)
// ======================================================================
console.log('\n--- TEST 1: All Accented/Ñ Communes (79 Raw + 2 Injected = 81 Total) ---');

const accentedComunas = sandbox.state.comunas.filter(c => /[áéíóúÁÉÍÓÚñÑüÜ]/.test(c.comuna));
console.log('Identified accented/ñ communes count:', accentedComunas.length);
assert(accentedComunas.length >= 79, 'Expected at least 79 accented communes, found ' + accentedComunas.length);

function stripAccents(str) {
  return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
}

accentedComunas.forEach(c => {
  const official = c.comuna;
  const unaccented = stripAccents(official);

  const variations = [
    { type: 'official_exact', input: official },
    { type: 'unaccented_lower', input: unaccented.toLowerCase() },
    { type: 'unaccented_upper', input: unaccented.toUpperCase() },
    { type: 'accented_lower', input: official.toLowerCase() },
    { type: 'accented_upper', input: official.toUpperCase() },
    { type: 'whitespace_padded', input: '   ' + unaccented.toLowerCase() + '   ' },
    { type: 'tab_newline_padded', input: '\t' + official + '\n' }
  ];

  variations.forEach(v => {
    // 1. normalizeText verification
    const norm = sandbox.normalizeText(v.input);
    const expectedNorm = sandbox.normalizeText(official);
    assert(norm === expectedNorm, 'normalizeText failed for ' + official + ' [' + v.type + ']', {
      input: v.input,
      got: norm,
      expected: expectedNorm
    });

    // 2. findComunaByName lookup
    const found = sandbox.findComunaByName(v.input);
    assert(found !== null && found !== undefined, 'findComunaByName returned null for ' + official + ' [' + v.type + ']', {
      input: v.input
    });
    if (found) {
      assert(found.comuna === official, 'findComunaByName matched wrong comuna for ' + official + ' [' + v.type + ']', {
        input: v.input,
        got: found.comuna,
        expected: official
      });
    }

    // 3. getFilteredComunas search bar filtering
    sandbox.state.searchQuery = v.input;
    const filtered = sandbox.getFilteredComunas();
    const containsTarget = filtered.some(fc => fc.comuna === official);
    assert(containsTarget, 'getFilteredComunas did not contain ' + official + ' [' + v.type + ']', {
      input: v.input,
      resultsCount: filtered.length
    });
  });
});

console.log('[TEST 1 COMPLETED] ' + accentedComunas.length + ' accented communes tested across 7 variations each (' + (accentedComunas.length * 7 * 3) + ' checks).');

// ======================================================================
// TEST 2: TOPONYMIC ALIASES & HASH ROUTING LOOKUP
// ======================================================================
console.log('\n--- TEST 2: Toponymic Aliases & Hash Routing ---');

const aliasTestCases = [
  { input: 'coyhaique', expectedComuna: 'Coihaique' },
  { input: 'Coyhaique', expectedComuna: 'Coihaique' },
  { input: 'COYHAIQUE', expectedComuna: 'Coihaique' },
  { input: '  coyhaique  ', expectedComuna: 'Coihaique' },
  { input: 'coihaique', expectedComuna: 'Coihaique' },
  { input: 'marchigue', expectedComuna: 'Marchihue' },
  { input: 'Marchigüe', expectedComuna: 'Marchihue' },
  { input: 'MARCHIGÜE', expectedComuna: 'Marchihue' },
  { input: 'marchihue', expectedComuna: 'Marchihue' },
  { input: 'navarino', expectedComuna: 'Cabo de Hornos' },
  { input: 'Navarino', expectedComuna: 'Cabo de Hornos' },
  { input: 'puerto williams', expectedComuna: 'Cabo de Hornos' },
  { input: 'Puerto Williams', expectedComuna: 'Cabo de Hornos' },
  { input: 'PUERTO WILLIAMS', expectedComuna: 'Cabo de Hornos' },
  { input: 'cabo de hornos', expectedComuna: 'Cabo de Hornos' },
  { input: 'santiago', expectedComuna: 'Santiago Centro' },
  { input: 'Santiago', expectedComuna: 'Santiago Centro' },
  { input: 'SANTIAGO', expectedComuna: 'Santiago Centro' },
  { input: 'santiago centro', expectedComuna: 'Santiago Centro' },
  { input: 'llay-llay', expectedComuna: 'Llaillay' },
  { input: 'Llay-Llay', expectedComuna: 'Llaillay' },
  { input: 'llaillay', expectedComuna: 'Llaillay' },
  { input: 'trehuaco', expectedComuna: 'Treguaco' },
  { input: 'Trehuaco', expectedComuna: 'Treguaco' },
  { input: 'treguaco', expectedComuna: 'Treguaco' }
];

aliasTestCases.forEach(tc => {
  // Test resolveComunaName
  const resolved = sandbox.resolveComunaName(tc.input);
  const expectedResolved = sandbox.normalizeText(tc.expectedComuna);
  assert(resolved === expectedResolved, 'resolveComunaName for ' + tc.input + ' got ' + resolved + ', expected ' + expectedResolved);

  // Test findComunaByName
  const found = sandbox.findComunaByName(tc.input);
  assert(found && found.comuna === tc.expectedComuna, 'findComunaByName for alias "' + tc.input + '" failed', {
    input: tc.input,
    got: found ? found.comuna : null,
    expected: tc.expectedComuna
  });

  // Test getFilteredComunas
  sandbox.state.searchQuery = tc.input;
  const filtered = sandbox.getFilteredComunas();
  assert(filtered.some(c => c.comuna === tc.expectedComuna), 'getFilteredComunas for alias "' + tc.input + '" did not include ' + tc.expectedComuna, {
    input: tc.input,
    resultsCount: filtered.length
  });
});

// Hash Routing Unit Tests
console.log('Testing Hash Routing (handleHashRoute):');
const hashTestCases = [
  { hash: '#comuna=maipu', expectComuna: 'Maipú' },
  { hash: '#comuna=Valpara%C3%ADso', expectComuna: 'Valparaíso' },
  { hash: '#comuna=santiago', expectComuna: 'Santiago Centro' },
  { hash: '#comuna=Coyhaique', expectComuna: 'Coihaique' },
  { hash: '#comuna=Puerto%20Williams', expectComuna: 'Cabo de Hornos' },
  { hash: '#comparar=Maipu,nunoa', expectCompare: ['Maipú', 'ÑuÑoa'] },
  { hash: '#comparar=Coyhaique,Santiago', expectCompare: ['Coihaique', 'Santiago Centro'] }
];

hashTestCases.forEach(tc => {
  sandbox.window.location.hash = tc.hash;
  const res = sandbox.handleHashRoute();
  assert(res === true, 'handleHashRoute for ' + tc.hash + ' should return true');
  if (tc.expectComuna) {
    assert(sandbox.state.selectedComuna && sandbox.state.selectedComuna.comuna === tc.expectComuna,
      'handleHashRoute ' + tc.hash + ' selected wrong comuna', {
        got: sandbox.state.selectedComuna ? sandbox.state.selectedComuna.comuna : null,
        expected: tc.expectComuna
      });
  }
  if (tc.expectCompare) {
    assert(sandbox.state.isCompareMode === true, 'handleHashRoute ' + tc.hash + ' should set isCompareMode=true');
    assert(sandbox.state.selectedComuna && sandbox.state.selectedComuna.comuna === tc.expectCompare[0],
      'handleHashRoute ' + tc.hash + ' compare A mismatch');
    assert(sandbox.state.compareComuna && sandbox.state.compareComuna.comuna === tc.expectCompare[1],
      'handleHashRoute ' + tc.hash + ' compare B mismatch');
  }
});

// Non-existent hash route
sandbox.window.location.hash = '#comuna=atlantida';
const nonExistentRes = sandbox.handleHashRoute();
assert(nonExistentRes === false, 'handleHashRoute for non-existent comuna should return false');

console.log('[TEST 2 COMPLETED] Alias and Hash Routing validated successfully.');

// ======================================================================
// TEST 3: PROVIDER CROSS-SUGGESTION
// ======================================================================
console.log('\n--- TEST 3: Provider Cross-Suggestion ---');

const providerCases = [
  // Vendor Name Matches
  { query: 'CAS-CHILE', expectedProvName: 'CAS-CHILE S. A. de I.', shouldMatch: true },
  { query: 'cas-chile', expectedProvName: 'CAS-CHILE S. A. de I.', shouldMatch: true },
  { query: 'Opciones', expectedProvName: 'OPCIONES SA SISTEMAS DE INFORMACION', shouldMatch: true },
  { query: 'opciones', expectedProvName: 'OPCIONES SA SISTEMAS DE INFORMACION', shouldMatch: true },
  { query: 'OPCIONES SA', expectedProvName: 'OPCIONES SA SISTEMAS DE INFORMACION', shouldMatch: true },
  { query: 'Technosystems', expectedProvName: 'TECHNOSYSTEMS CHILE SPA', shouldMatch: true },
  { query: 'technosystems', expectedProvName: 'TECHNOSYSTEMS CHILE SPA', shouldMatch: true },
  { query: 'telefónica', expectedProvName: 'CIA NACIONAL DE TELEFONOS TELEFONICA DEL SUR S.A.', shouldMatch: true },
  { query: 'telefonica', expectedProvName: 'CIA NACIONAL DE TELEFONOS TELEFONICA DEL SUR S.A.', shouldMatch: true },
  { query: 'COPEC', expectedProvName: 'COMPANIA DE PETROLEOS DE CHILE COPEC SA', shouldMatch: true },
  { query: 'GTD', expectedProvName: 'GTD TELEDUCTOS S.A', shouldMatch: true },
  { query: 'pcinbox', expectedProvName: 'PCINBOX SPA', shouldMatch: true },
  { query: 'Hernán', expectedProvName: 'Hernán Felix', shouldMatch: true },
  { query: 'hernan', expectedProvName: 'Hernán Felix', shouldMatch: true },

  // RUT Matches
  { query: '96.525.030-1', expectedProvName: 'CAS-CHILE S. A. de I.', shouldMatch: true },
  { query: '96.523.180-3', expectedProvName: 'OPCIONES SA SISTEMAS DE INFORMACION', shouldMatch: true },
  { query: '96.678.350-8', expectedProvName: 'TECHNOSYSTEMS CHILE SPA', shouldMatch: true },

  // Non-matching Gibberish
  { query: 'nonexistentvendor_xyz123', shouldMatch: false },
  { query: 'gibberish_string_999', shouldMatch: false },
  { query: 'qwertyuiop', shouldMatch: false },
  { query: '123456789999999', shouldMatch: false },

  // Short & Empty Inputs
  { query: '', shouldMatch: false },
  { query: 'a', shouldMatch: false },
  { query: '  ', shouldMatch: false },
  { query: 'z', shouldMatch: false }
];

providerCases.forEach(tc => {
  const match = sandbox.findProviderMatch(tc.query);
  if (tc.shouldMatch) {
    assert(match !== null && match !== undefined, 'findProviderMatch failed for valid query "' + tc.query + '"');
    if (match && tc.expectedProvName) {
      assert(match.proveedor === tc.expectedProvName, 'findProviderMatch for "' + tc.query + '" matched wrong provider', {
        got: match.proveedor,
        expected: tc.expectedProvName
      });
    }
  } else {
    assert(!match, 'findProviderMatch for "' + tc.query + '" should be falsy, got ' + (match && match.proveedor));
  }
});

// Test interaction between Commune match and Provider suggestion:
sandbox.state.searchQuery = 'Maipú';
const filteredM = sandbox.getFilteredComunas();
assert(filteredM.length > 0, 'Maipú must return commune results');

console.log('[TEST 3 COMPLETED] Provider cross-suggestion validated.');

// ======================================================================
// TEST 4: REGEX INJECTION, REDOS, XSS & EXCEPTION RESILIENCE
// ======================================================================
console.log('\n--- TEST 4: Regex Injection & Adversarial Fuzzing ---');

const adversarialPayloads = [
  // Regex metacharacters
  '.*',
  '.+',
  '(a|b|c)*',
  '^$',
  '[a-z]+',
  '\\\\',
  '\\\\d+',
  '(?=.*[a-z])',
  '((((((((a))))))))',
  '*',
  '?',
  '+',
  '[',
  ']',
  '(',
  ')',
  '{1,100}',
  '^',
  '$',
  '|',
  '/test/g',
  '/(.*)/',

  // ReDoS attempts
  'a'.repeat(2000),
  'a'.repeat(1000) + '!',
  '((a+)+)+$',

  // XSS & Markup
  '<script>alert(1)</script>',
  '<img src=x onerror=alert(1)>',
  '"><svg onload=alert(1)>',
  'javascript:alert(1)',
  '\'; DROP TABLE comunas; --',
  '{"$gt": ""}',

  // Unicode edge cases & Control chars
  '\x00\x01\x02',
  '\r\n\t',
  '\u200B\u200C\u200D',
  '\uFEFF',
  '\uD83D\uDCA9',
  'M̷a̷i̷p̷ú̷',
  '🇨🇱 Santiago 💻',

  // Long string
  'Z'.repeat(10000),

  // Whitespace-only
  '     ',
  '\t\t\t',
  '\n\n'
];

adversarialPayloads.forEach(payload => {
  // 1. normalizeText should never throw
  try {
    const normRes = sandbox.normalizeText(payload);
    assert(typeof normRes === 'string', 'normalizeText(' + payload.slice(0, 20) + ') must return string');
  } catch (err) {
    assert(false, 'normalizeText threw exception on payload: ' + err.message, { payload });
  }

  // 2. findComunaByName should never throw
  try {
    const fRes = sandbox.findComunaByName(payload);
    if (fRes) {
      assert(typeof fRes === 'object', 'findComunaByName returned non-object');
    }
  } catch (err) {
    assert(false, 'findComunaByName threw exception on payload: ' + err.message, { payload });
  }

  // 3. getFilteredComunas should never throw
  try {
    sandbox.state.searchQuery = payload;
    const gRes = sandbox.getFilteredComunas();
    assert(Array.isArray(gRes), 'getFilteredComunas must return array');
  } catch (err) {
    assert(false, 'getFilteredComunas threw exception on payload: ' + err.message, { payload });
  }

  // 4. findProviderMatch should never throw
  try {
    const pRes = sandbox.findProviderMatch(payload);
    if (pRes) {
      assert(typeof pRes === 'object', 'findProviderMatch returned non-object');
    }
  } catch (err) {
    assert(false, 'findProviderMatch threw exception on payload: ' + err.message, { payload });
  }
});

// Type coercion stress tests
const nonStringTypes = [
  null,
  undefined,
  0,
  123,
  -1,
  true,
  false,
  {},
  [],
  NaN,
  Infinity
];

nonStringTypes.forEach(val => {
  try {
    const n = sandbox.normalizeText(val);
    assert(typeof n === 'string', 'normalizeText with ' + String(val) + ' should return string');
  } catch (err) {
    assert(false, 'normalizeText threw on non-string input ' + String(val) + ': ' + err.message);
  }

  try {
    const fc = sandbox.findComunaByName(val);
    assert(fc === null || fc === undefined || typeof fc === 'object', 'findComunaByName with ' + String(val) + ' should not throw');
  } catch (err) {
    assert(false, 'findComunaByName threw on non-string input ' + String(val) + ': ' + err.message);
  }
});

console.log('\n======================================================================');
console.log('STRESS SUITE SUMMARY: ' + results.passed + ' PASSED, ' + results.failed + ' FAILED');
console.log('======================================================================');

if (results.failed > 0) {
  console.error('\nFAILURES SUMMARY (' + results.failed + ' errors):');
  results.failures.slice(0, 10).forEach((f, idx) => {
    console.error((idx + 1) + '. ' + f.message, f.details);
  });
  process.exit(1);
} else {
  console.log('\n>>> ALL EMPIRICAL STRESS TESTS PASSED WITH 0 FAILURES <<<');
  process.exit(0);
}
