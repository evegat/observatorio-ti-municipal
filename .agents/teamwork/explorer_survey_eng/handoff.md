# Handoff Report — Survey Explorer 1 (Engineering & Client-Side Architecture)

**Author:** Survey Explorer 1  
**Project:** Observatorio de Capacidades Tecnológicas Municipales de Chile (PUB021)  
**Date:** 2026-10-16T22:18:00Z  
**Target:** orchestrator_1 (Conversation ID: 42937d0a-1682-41ea-a81f-2074f9f7a858)  
**Status:** Complete (Hard Handoff)  

---

## 1. Observation

Direct, verbatim technical observations of files, lines, and system behaviors in the repository:

### 1.1 Codebase & Asset Map
- **Project Structure**: Pure static client-side web application deployed to `https://observatoriotimunicipal.evegat.cl`. No build step, bundler, or `package.json` at root.
  - `index.html` (793 lines, 49,506 bytes): HTML5 document declaring semantic tags, accessibility topbar, scrollytelling section, Leaflet map container, drawer, RRHH module, ranking tables, 3 dialog modals, and vendor scripts.
  - `app.js` (1,922 lines, 96,984 bytes): Single monolithic script enclosed in `document.addEventListener("DOMContentLoaded", () => { ... })` managing state, Leaflet circle markers, scrollytelling chapters, filters, comparison drawer, CSV generation, modal interceptions, and TTS.
  - `style.css` (1,978 lines, 40,086 bytes): CSS design system conforming to `evegat.cl` editorial style (Georgia serif, Inter sans, monospace, warm paper `#faf8f5`, navy `#002b49`, gold `#b38209`, teal `#146e66`, crimson `#9b2226`). Includes dark (`html[data-theme="dark"]`, line 1902) and high contrast (`html[data-theme="contrast"]`, line 1957) themes.
  - `assets/leaflet/`: Contains `leaflet.js` (147,552 bytes) and `leaflet.css` (14,806 bytes). The folder lacks an `images/` directory (`marker-icon.png`, `layers.png`).
  - `data/`:
    - `comunas.geojson` (1,677,967 bytes) & `regiones.geojson` (1,454,860 bytes): Present in `data/`, but never fetched, referenced, or loaded in `app.js` or `index.html`.
    - `comunas_enriched.json` (1,581,832 bytes): Eagerly loaded at startup via `Promise.all` in `app.js` line 72. Contains 397 objects rather than 346 unique municipalities.
    - `regiones_enriched.json` (19,009 bytes): Eagerly loaded at startup.
    - `national_kpis.json` (4,361 bytes): Eagerly loaded at startup.
    - `proveedores_ranking.json` (8,628 bytes): Loaded with `.catch(() => null)`.

### 1.2 Critical Functional & Architectural Bugs Observed

1. **Map Layer Inconsistency (7 declared buttons vs 5 implemented layers)**:
   - In `index.html` (lines 252–258), 7 layer buttons are defined:
     ```html
     <button class="layer-btn active" data-layer="madurez">🌡️ Madurez TI (0-100)</button>
     <button class="layer-btn" data-layer="gasto_pc">💰 Gasto Per Cápita</button>
     <button class="layer-btn" data-layer="ret">🏛️ Capacidad Estatal (RET)</button>
     <button class="layer-btn" data-layer="rrhh">👥 RRHH &amp; Honorarios</button>
     <button class="layer-btn" data-layer="lockin">🚨 Dependencia ERP</button>
     <button class="layer-btn" data-layer="foss">🐧 Software Libre</button>
     <button class="layer-btn" data-layer="infra">🖥️ Infra Propia</button>
     ```
   - In `app.js`, `getMarkerStyle(comuna)` (lines 390–435) only contains conditional branches for `madurez`, `gasto_pc`, `lockin`, `foss`, and `infra`. Layers `ret` and `rrhh` are completely unhandled and fall through to default `color = "#146e66"; radius = 6;`.
   - In `app.js`, `updateLegend()` (lines 479–528) only contains conditionals for `madurez`, `gasto_pc`, `lockin`, `foss`, and `infra`. When the user clicks `ret` or `rrhh`, `updateLegend()` matches nothing; the legend element `#map-legend` retains stale HTML from the previous layer.

2. **Data Duplication in `comunas_enriched.json` (397 items vs 346 comunas)**:
   - Node audit script execution confirmed:
     `comunas.length = 397`. 50 comuna names have duplicates (51 duplicate records).
     Sample duplicates: `Ovalle` (2), `Santiago Centro` (3), `Talca` (2), `Puerto Montt` (2), `Quillón` (3).
   - In each duplicate case, one record possesses full aggregated OCs and spending (e.g. Ovalle: 1,214 OCs, $5,014,715,084 CLP), while the duplicate possesses a single fragmented OC or tiny sum (e.g. Ovalle 2nd record: 1 OC, $770 CLP; Santiago Centro 2nd record: 6 OCs, $11.2M with `lat: null, lng: null`; Santiago Centro 3rd record: 2 OCs, $24,807 CLP).
   - `Santiago Centro` has a record with `lat: null, lng: null`. While guarded in `renderMapMarkers` by `if (c.lat && c.lng)`, the remaining 50 duplicates create duplicate circle markers stacked directly over each other.
   - In `renderCuadrantesSummary()` (`app.js` lines 1329–1335) and `national_kpis.json` (lines 147–153), the cuadrante counts sum to 397:
     `198 + 5 + 99 + 46 + 49 = 397` (distorting national capacity proportions).
   - In `state.comunas.find(c => c.comuna === name)` during hash routing (`#comuna=`, `#comparar=`), row clicks in table, or select dropdowns, the first matching entry is returned. Depending on array order, users can be served the ghost fragment rather than the actual municipality data.

3. **Data Loading & Network Failure Handling**:
   - In `app.js` (`init()` lines 69–82):
     ```javascript
     const [comunasRes, regionesRes, kpisRes, provRes] = await Promise.all([
       fetch("data/comunas_enriched.json"),
       fetch("data/regiones_enriched.json"),
       fetch("data/national_kpis.json"),
       fetch("data/proveedores_ranking.json").catch(() => null)
     ]);
     ```
   - No `.ok` check is performed on `comunasRes`, `regionesRes`, or `kpisRes`. If a 404, 502, or network failure occurs, the catch block (line 103) executes:
     `catch (err) { console.error("Error al inicializar la aplicación:", err); }`
   - The UI shows no error banner, retry button, or fallback message; the page remains in an uninitialized, unresponsive state with empty tables and empty drawer.
   - Initial payload transfer: 1.61 MB raw JSON fetched synchronously before any visual component renders.

4. **Leaflet Implementation & Tile Providers**:
   - Map initialized in `initMap()` (`app.js` lines 332–377):
     ```javascript
     const esriLightBase = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}", ...);
     const esriDarkBase = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}", ...);
     ```
   - No external API key required. No commercial watermarks displayed. Clean attribution.
   - Map uses `L.circleMarker` based on centroid coordinates (`c.lat`, `c.lng`). Because default `L.marker` is not used, the absence of `assets/leaflet/images/marker-icon.png` causes no 404 network errors in the current code.
   - `scrollWheelZoom` is disabled by default to avoid page scroll hijacking, and enabled on map click/focus (lines 341–343).
   - In `updateMapTheme(theme)` (lines 379–388), switching to `"contrast"` falls into the `else` branch which serves `esriLightGroup`.

5. **Download Interception & Telemetry Flow**:
   - In `app.js` (lines 1524–1650), all elements with `.btn-intercept-download` (`index.html` lines 103, 393, 433, 546–548) are intercepted via `e.preventDefault()`.
   - The user's lead is retrieved from `localStorage.getItem("evegat_registered_lead")` to auto-populate form inputs.
   - Form submission validates required fields:
     `!nombre || !email || !institucion || !perfil || !proposito || !email.includes("@")`.
   - Lead data is saved to `localStorage` under `"evegat_registered_lead"`.
   - Remote persistence request dispatched to `https://brujulaiaedusuperior.evegat.cl/api/register-download`:
     - Method: POST
     - Header: `Content-Type: application/json`
     - Attribute: `keepalive: true`
     - Error handling: Wrapped in `.catch(() => {})`, ensuring CORS or network issues do not block the user download.
     - Live endpoint test: An HTTP OPTIONS preflight against `https://brujulaiaedusuperior.evegat.cl/api/register-download` returned HTTP 204 with `Access-Control-Allow-Origin: *`.
     - Non-blocking Umami event tracked: `lead_descarga_datos`.
     - File download triggered immediately: CSV files generated via `Blob` with UTF-8 BOM (`\uFEFF`) and `;` delimiter; JSON files downloaded via programmatic `<a>` click.
   - *Bug observed in registration payload*: In line 1570, `contacto` is read from checkbox `#reg-contacto`, but in `apiPayload` (line 1607), `consentimiento: true` is hardcoded, disregarding if the user unchecked the consent box.

6. **Harness & Existing Testing Setup**:
   - `MYWORLD-HARNESS.json`: Product `PUB021`, type `static_site`.
   - Quality command: `node -c app.js` (Pass, exit 0).
   - Test command: `node -c app.js` (Pass, exit 0).
   - Harness runner: `.myworld-harness/harness.ps1 preflight` and `quality` pass contract validation.
   - Automated design engine: `.myworld-harness/myworld_design_engine.py` runs 15 checks: 11 pass, 3 pending (`design.responsive.breakpoints`, `design.anti_slop.tabular_data`, `design.jev.hierarchy_clarity`).
   - JEV Judge (`.myworld-harness/jev_design_judge.py`):
     - `Modal Descarga`: Status "pass" (hierarchy: clara 2.0, density: equilibrada, friction_prob: 0.150, slop_risk: bajo).
     - `Modal Guia`: Status "pass" (hierarchy: clara 2.0, density: equilibrada, friction_prob: 0.150, slop_risk: bajo).
     - `Topbar`: Status "pass" (hierarchy: aceptable 1.0, density: equilibrada, friction_prob: 0.150, slop_risk: bajo).
     - `Full Page`: Status "needs_review" (hierarchy: clara 2.0, density: hacinada due to monolithic page weight).
   - Unit/Integration test suites: Zero unit tests (Jest/Vitest) or end-to-end browser tests (Playwright/Cypress) currently exist in the repository.

---

## 2. Logic Chain

1. **Premise 1 (Map UI vs Logic)**: Observation 1.2.1 shows `index.html` declaring 7 layer buttons including `data-layer="ret"` and `data-layer="rrhh"`. Observation 1.2.1 also shows `getMarkerStyle` and `updateLegend` in `app.js` inspecting only 5 layer keys. Therefore, whenever a user toggles to the RET or RRHH layer, the map displays generic unstyled dots and retains a misleading or stale legend, violating Acceptance Criterion R1/Integrity ("0 errores de consola al inicializar el mapa, alternar las 7 capas territoriales").

2. **Premise 2 (Data Integrity & Aggregation)**: Observation 1.2.2 shows that `comunas_enriched.json` contains 397 rows instead of the official 346 Chilean municipalities due to split supplier entities in the raw procurement ingestion. Because 50 municipalities have duplicate records, national distributions (198 Soberano + 5 Híbrido + 99 Artesanal + 46 Cautivo + 49 Desconectado = 397) are inflated, and `state.comunas.find()` risks resolving a micro-fragment record with $770 CLP rather than the true $5B municipal budget.

3. **Premise 3 (Performance & Lazy Loading)**: Observation 1.1 shows 3.13 MB of GeoJSON files (`comunas.geojson` and `regiones.geojson`) committed in `data/`, but unused by Leaflet. Meanwhile, 1.58 MB of `comunas_enriched.json` (including full contractual text for all 346 comunas) is loaded eagerly via a single non-resilient `Promise.all`. Therefore, initial page load is unnecessarily delayed on low-bandwidth connections, while boundary polygons are completely absent from the visual cartography.

4. **Premise 4 (Resilience & Error Handling)**: Observation 1.2.3 shows that failure of `comunas_enriched.json` causes silent failure with no UI recovery mechanism. In contrast, Observation 1.2.5 demonstrates that the download modal and telemetry API (`https://brujulaiaedusuperior.evegat.cl/api/register-download`) is properly isolated with `.catch(() => {})`, `keepalive: true`, and local fallback, ensuring download fulfillment even during network anomalies.

5. **Premise 5 (Harness & Testing Maturity)**: Observation 1.2.6 confirms that `MYWORLD-HARNESS.json` enforces syntax checking (`node -c app.js`), and JEV design scripts validate UI anti-slop and accessibility. However, absence of automated runtime tests leaves regressions in map layer switching and data filtering undetectable by `harness.ps1 quality`.

---

## 3. Caveats

1. **Read-Only Investigation**: In accordance with the Explorer role and system instructions, no source files (`app.js`, `index.html`, `style.css`, `data/`) were modified. Proposed fixes are detailed below for the implementer agent.
2. **Dataset Upstream Origin**: The duplication in `comunas_enriched.json` originates from data ingestion (P166 / Mercado Público scraper pipeline). Deduplication can be handled either upstream in data generation or client-side during `init()`.
3. **CORS & Adblockers in Real Environments**: While preflight to `https://brujulaiaedusuperior.evegat.cl/api/register-download` succeeded from the test environment, client-side browser extensions (e.g. uBlock Origin) may block the domain. The existing non-blocking design safely prevents user disruption.

---

## 4. Conclusion

The client-side architecture of the Observatorio TI Municipal is structurally solid, following a clean vanilla JavaScript event-driven architecture, sober editorial design conforming to `evegat.cl`, and robust download flow telemetry.

However, three primary technical debt and risk items must be addressed:

| Severity | Issue | Impact | Root Cause & Location |
|---|---|---|---|
| **Critical** | Missing Map Layers `ret` and `rrhh` | Map markers default to generic green; legend does not update. Broken requirement. | `app.js:390-435` (`getMarkerStyle`) and `app.js:479-528` (`updateLegend`). |
| **High** | 51 Duplicate records in `comunas_enriched.json` | 397 entries instead of 346; distorted KPI sums; risk of `#comuna=` returning $770 ghost records. | `data/comunas_enriched.json` duplicate CUTs; unhandled in `init()` (`app.js:78`). |
| **Medium** | Unused 3.13 MB GeoJSON files | Unnecessary disk footprint; expectation mismatch for polygon choropleths. | `data/comunas.geojson` and `regiones.geojson` unreferenced. |
| **Medium** | Blocking initial fetch without user error UI | Blank/broken screen if initial fetch drops. | `app.js:69-106` (`init` bare `Promise.all` and console-only catch). |
| **Low** | Table slice at 100 rows without pagination | Comunas ranked 101–346 unreachable in table unless filtered. | `app.js:1186` (`filtered.slice(0, 100)`). |
| **Low** | Hardcoded consent flag in download API payload | Checkbox value not respected in API payload. | `app.js:1607` (`consentimiento: true`). |

### Concrete Proposals for Implementer:

1. **Map Layer Handlers**:
   - In `getMarkerStyle(comuna)`:
     - Add `state.currentLayer === "ret"`: color by RET ratio (e.g. `<= 1.0` Forest `#2d6a4f` Soberano; `1.0-1.8` Teal `#146e66`; `> 1.8` Crimson `#9b2226` Cautivo/Dependiente).
     - Add `state.currentLayer === "rrhh"`: color by `% Honorarios` (e.g. `< 30%` Forest, `30-50%` Gold, `> 50%` Crimson).
   - In `updateLegend()`:
     - Add branches rendering title and color items for `ret` and `rrhh`.
2. **Client-Side Data Deduplication**:
   - In `app.js` `init()`, after fetching `comunas_enriched.json`, merge or filter duplicate municipalities keeping the entry with `total_ocs > 1` (or highest `monto_total`), filtering out records with `lat: null`.
3. **Resilient Initialization**:
   - Wrap `init()` data loading in a structured loader that displays a retry banner if `fetch` fails.
4. **Consent Checkbox Sync**:
   - Replace line 1607 in `app.js`: `consentimiento: contacto`.

---

## 5. Verification Method

To independently reproduce and verify every finding:

1. **JavaScript Syntax Verification**:
   ```powershell
   node -c app.js
   ```
   *Expected result*: Exit code 0, no syntax errors.

2. **MyWorld Harness Gates**:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .myworld-harness\harness.ps1 preflight
   powershell -ExecutionPolicy Bypass -File .myworld-harness\harness.ps1 quality
   ```
   *Expected result*: Quality check executes `node -c app.js` with exit code 0.

3. **Data Duplication Verification**:
   ```powershell
   node -e "const fs = require('fs'); const d = JSON.parse(fs.readFileSync('data/comunas_enriched.json')); console.log('Total:', d.length); const counts = {}; d.forEach(c => counts[c.comuna] = (counts[c.comuna] || 0) + 1); const dupes = Object.entries(counts).filter(([k, v]) => v > 1); console.log('Dupes count:', dupes.length); const nullCoords = d.filter(c => !c.lat || !c.lng); console.log('Null coords:', nullCoords.map(c => c.comuna));"
   ```
   *Expected result*: Total: 397. Dupes count: 50. Null coords: `['Santiago Centro']`.

4. **Missing Layers Verification**:
   ```powershell
   rg -n "data-layer=\"(ret|rrhh)\"" index.html
   rg -n "currentLayer === \"(ret|rrhh)\"" app.js
   ```
   *Expected result*: Found in `index.html` (lines 254-255); 0 matches in `app.js`.

5. **Remote API Preflight Check**:
   ```powershell
   node -e "const https = require('https'); const req = https.request('https://brujulaiaedusuperior.evegat.cl/api/register-download', { method: 'OPTIONS' }, (res) => console.log('Status:', res.statusCode)); req.end();"
   ```
   *Expected result*: Status 204.

6. **JEV Design Gate Verification**:
   ```powershell
   python -c "import sys; from pathlib import Path; sys.path.insert(0, '.myworld-harness'); from myworld_design_engine import MyWorldDesignEngine; res = MyWorldDesignEngine(Path('.')).run_full_design_gate(semantic_authorized=True); print('Status:', res['jev_summary']['status'])"
   ```
   *Expected result*: Status: pass.
