const fs = require('fs');
const appCode = fs.readFileSync('app.js', 'utf8');
const raw = JSON.parse(fs.readFileSync('data/comunas_enriched.json', 'utf8'));

const vm = require('vm');
const sandbox = { console, Map, Set, Array, Math, String, Boolean, Date, RegExp };

// Load code from normalizeText to showErrorBanner, and provider/filtering helpers
const part1 = appCode.slice(appCode.indexOf('function normalizeText'), appCode.indexOf('function showErrorBanner'));
const part2 = appCode.slice(appCode.indexOf('function findProviderMatch'), appCode.indexOf('// -------------------------------------------------------------------------\n  // 6. RANKING'));
const part3 = appCode.slice(appCode.indexOf('function getMarkerStyle'), appCode.indexOf('function renderMapMarkers'));

vm.runInNewContext(part1 + '\n' + part2 + '\n' + part3 + '\n' +
  'this.norm = normalizeText;\n' +
  'this.resolve = resolveComunaName;\n' +
  'this.findComuna = findComunaByName;\n' +
  'this.dedup = deduplicateComunas;\n' +
  'this.findProv = findProviderMatch;\n' +
  'this.getFiltered = getFilteredComunas;\n' +
  'this.getMarker = getMarkerStyle;\n',
  sandbox
);

const comunas = sandbox.dedup(raw);
sandbox.state = {
  comunas: comunas,
  proveedores: [
    { proveedor: "CAS-CHILE S.A.", rut: "96.543.210-K", monto_total: 1000000 },
    { proveedor: "Opciones S.A.", rut: "78.123.456-7", monto_total: 500000 }
  ],
  searchQuery: "",
  selectedRegion: "",
  selectedCuadrante: "",
  currentLayer: "ret"
};

let testsPassed = 0;
let testsFailed = 0;

function assert(condition, message) {
  if (!condition) {
    console.error("FAIL:", message);
    testsFailed++;
  } else {
    testsPassed++;
  }
}

console.log("=== 1. ADVERSARIAL STRESS TEST: normalizeText ===");
assert(sandbox.norm("") === "", "empty string produces empty string");
assert(sandbox.norm(null) === "", "null produces empty string");
assert(sandbox.norm(undefined) === "", "undefined produces empty string");
assert(sandbox.norm(12345) === "12345", "number converts to string");
assert(sandbox.norm("   MAIPÚ   ") === "maipu", "trims and strips accents");
assert(sandbox.norm("Añuñuy") === "anunuy", "folds ñ to n canonical form for seamless search");
assert(sandbox.norm(".*+?^${}()|[]\\") === ".*+?^${}()|[]\\", "handles regex metacharacters safely");
assert(sandbox.norm("🚀 Valparaíso 🌟") === "🚀 valparaiso 🌟", "handles unicode emojis safely");

console.log("=== 2. ADVERSARIAL STRESS TEST: deduplicateComunas ===");
assert(sandbox.dedup(null).length === 0, "null input returns empty array");
assert(sandbox.dedup("invalid").length === 0, "string input returns empty array");
assert(comunas.length === 346, "exactly 346 unique municipalities");

const stgo = comunas.find(c => c.comuna === "Santiago Centro");
assert(stgo !== undefined, "Santiago Centro exists");
assert(stgo.lat === -33.4489 && stgo.lng === -70.6693, "Santiago Centro coordinates exact match");

const nullCoords = comunas.filter(c => c.lat === null || c.lng === null || isNaN(c.lat) || isNaN(c.lng));
assert(nullCoords.length === 0, "zero ghost or null coordinates in entire dataset");

const uniqueCuts = new Set(comunas.map(c => c.codigo_cut));
assert(uniqueCuts.size === 346, "all 346 CUT codes are strictly unique");

console.log("=== 3. ADVERSARIAL STRESS TEST: findComunaByName & Aliases ===");
assert(sandbox.findComuna("santiago")?.comuna === "Santiago Centro", "alias: santiago -> Santiago Centro");
assert(sandbox.findComuna("SANTIAGO")?.comuna === "Santiago Centro", "alias: SANTIAGO -> Santiago Centro");
assert(sandbox.findComuna("coyhaique")?.comuna === "Coihaique", "alias: coyhaique -> Coihaique");
assert(sandbox.findComuna("coihaique")?.comuna === "Coihaique", "direct: coihaique -> Coihaique");
assert(sandbox.findComuna("marchigue")?.comuna === "Marchihue", "alias: marchigue -> Marchihue");
assert(sandbox.findComuna("Marchigüe")?.comuna === "Marchihue", "alias: Marchigüe -> Marchihue");
assert(sandbox.findComuna("navarino")?.comuna === "Cabo de Hornos", "alias: navarino -> Cabo de Hornos");
assert(sandbox.findComuna("puerto williams")?.comuna === "Cabo de Hornos", "alias: puerto williams -> Cabo de Hornos");
assert(sandbox.findComuna("llay-llay")?.comuna === "Llaillay", "alias: llay-llay -> Llaillay");
assert(sandbox.findComuna("trehuaco")?.comuna === "Treguaco", "alias: trehuaco -> Treguaco");
assert(sandbox.findComuna("ñuñoa")?.codigo_cut === 13120, "accent: ñuñoa -> CUT 13120");
assert(sandbox.findComuna("NUNOA")?.codigo_cut === 13120, "unaccented: NUNOA -> CUT 13120");
assert(sandbox.findComuna("maipu")?.comuna === "Maipú", "unaccented: maipu -> Maipú");
assert(sandbox.findComuna("MAIPU")?.comuna === "Maipú", "uppercase: MAIPU -> Maipú");
assert(sandbox.findComuna(null) === null, "null input returns null safely");
assert(sandbox.findComuna("") === null, "empty input returns null safely");
assert(sandbox.findComuna("ComunaInexistente999") === undefined, "unknown returns undefined");

console.log("=== 4. ADVERSARIAL STRESS TEST: findProviderMatch ===");
assert(sandbox.findProv("CAS-CHILE")?.proveedor === "CAS-CHILE S.A.", "exact match provider");
assert(sandbox.findProv("cas-chile")?.proveedor === "CAS-CHILE S.A.", "case-insensitive match provider");
assert(sandbox.findProv("cas")?.proveedor === "CAS-CHILE S.A.", "partial match provider");
assert(sandbox.findProv("opciones")?.proveedor === "Opciones S.A.", "match opciones provider");
assert(sandbox.findProv("x") === null, "short query (<2 chars) returns null");
assert(sandbox.findProv("") === null, "empty query returns null");
assert(sandbox.findProv(null) === null, "null query returns null");

console.log("=== 5. ADVERSARIAL STRESS TEST: Map Layers (ret & rrhh) ===");
sandbox.state.currentLayer = "ret";
assert(sandbox.getMarker({ ret_ratio: 2.5 }).color === "#146e66", "ret >= 2.0 is Teal");
assert(sandbox.getMarker({ ret_ratio: 1.5 }).color === "#2b5c8f", "ret 1.0-1.9 is Steel Blue");
assert(sandbox.getMarker({ ret_ratio: 0.7 }).color === "#b38209", "ret 0.5-0.9 is Gold");
assert(sandbox.getMarker({ ret_ratio: 0.2 }).color === "#9b2226", "ret < 0.5 is Crimson");
assert(sandbox.getMarker({ ret_ratio: 2.5 }).radius === 10, "ret radius Math.round(2.5*4) = 10");

sandbox.state.currentLayer = "rrhh";
assert(sandbox.getMarker({ pct_honorarios: 65 }).color === "#9b2226", "rrhh > 60 is Crimson");
assert(sandbox.getMarker({ pct_honorarios: 45 }).color === "#b38209", "rrhh 40-60 is Gold");
assert(sandbox.getMarker({ pct_honorarios: 25 }).color === "#146e66", "rrhh < 40 is Teal");

console.log("\n=================================");
console.log(`TOTAL TESTS: ${testsPassed + testsFailed}`);
console.log(`PASSED: ${testsPassed}`);
console.log(`FAILED: ${testsFailed}`);
console.log("=================================");

if (testsFailed > 0) process.exit(1);
