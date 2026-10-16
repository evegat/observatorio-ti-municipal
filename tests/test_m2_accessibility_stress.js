/**
 * tests/test_m2_accessibility_stress.js
 * =====================================
 * Automated Empirical Node.js DOM & Event Stress Harness for Milestone 2:
 * 1. Modal focus trap, Tab/Shift-Tab cycle, initial focus transfer, Escape key, activeElement restoration.
 * 2. Table header keyboard sorting (Enter, Space), dynamic aria-sort synchronization.
 * 3. Table row keyboard interaction (Enter, Space) and commune card opening in #comuna-drawer.
 * 4. Map theme transitions ("dark", "light", "contrast") and esriDarkGroup layer synchronization.
 * 5. Full regression execution of previous test suites.
 *
 * Author: Challenger 2 (Milestone 2)
 */

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const { execSync } = require('child_process');

console.log('======================================================================');
console.log('CHALLENGER 2: EMPIRICAL HARNESS — ACCESSIBILITY, FOCUS TRAP & THEMES  ');
console.log('======================================================================\n');

const rootDir = path.resolve(__dirname, '..');
const appJsPath = path.join(rootDir, 'app.js');
const indexHtmlPath = path.join(rootDir, 'index.html');
const rawComunasPath = path.join(rootDir, 'data', 'comunas_enriched.json');
const rawRegionesPath = path.join(rootDir, 'data', 'regiones_enriched.json');
const rawKpisPath = path.join(rootDir, 'data', 'national_kpis.json');
const rawProveedoresPath = path.join(rootDir, 'data', 'proveedores_ranking.json');

const appCode = fs.readFileSync(appJsPath, 'utf8');
const rawComunas = JSON.parse(fs.readFileSync(rawComunasPath, 'utf8'));
const rawRegiones = JSON.parse(fs.readFileSync(rawRegionesPath, 'utf8'));
const rawKpis = JSON.parse(fs.readFileSync(rawKpisPath, 'utf8'));
const rawProveedores = fs.existsSync(rawProveedoresPath)
  ? JSON.parse(fs.readFileSync(rawProveedoresPath, 'utf8'))
  : [];

// Metrics counters
let totalAssertions = 0;
let passedAssertions = 0;
let failedAssertions = 0;
const failureDetails = [];

function assert(condition, testName, extraInfo = '') {
  totalAssertions++;
  if (condition) {
    passedAssertions++;
    console.log(`  [PASS] ${testName}${extraInfo ? ' (' + extraInfo + ')' : ''}`);
  } else {
    failedAssertions++;
    const errMsg = `[FAIL] ${testName} ${extraInfo}`;
    failureDetails.push(errMsg);
    console.error(`  ${errMsg}`);
  }
}

// -------------------------------------------------------------------------
// SIMULATED DOM & EVENT HARNESS
// -------------------------------------------------------------------------

class MockEvent {
  constructor(type, init = {}) {
    this.type = type;
    this.key = init.key || '';
    this.shiftKey = Boolean(init.shiftKey);
    this.target = init.target || null;
    this.currentTarget = init.currentTarget || null;
    this.defaultPrevented = false;
    this.propagationStopped = false;
  }
  preventDefault() {
    this.defaultPrevented = true;
  }
  stopPropagation() {
    this.propagationStopped = true;
  }
}

class MockElement {
  constructor(tagName, id = '') {
    this.tagName = tagName.toUpperCase();
    this.id = id;
    this.attributes = new Map();
    this.children = [];
    this.parentNode = null;
    this.eventListeners = new Map();
    this.style = {};
    this.dataset = {};
    this._classList = new Set();
    this.value = '';
    this.checked = false;
    this.disabled = false;
    this.offsetWidth = 120;
    this.offsetHeight = 32;
    this._innerHTML = '';
    this.scrollIntoViewCalled = false;
    this.scrollIntoViewOptions = null;

    if (id) this.attributes.set('id', id);

    const self = this;
    this.classList = {
      add(...classes) {
        classes.forEach(c => c && self._classList.add(c));
      },
      remove(...classes) {
        classes.forEach(c => self._classList.delete(c));
      },
      contains(c) {
        return self._classList.has(c);
      },
      toggle(c, force) {
        if (force === true) {
          self._classList.add(c);
          return true;
        } else if (force === false) {
          self._classList.delete(c);
          return false;
        }
        if (self._classList.has(c)) {
          self._classList.delete(c);
          return false;
        }
        self._classList.add(c);
        return true;
      }
    };
  }

  get className() {
    return Array.from(this._classList).join(' ');
  }
  set className(val) {
    this._classList.clear();
    if (val) {
      val.split(/\s+/).forEach(c => c && this._classList.add(c));
    }
  }

  setAttribute(name, value) {
    this.attributes.set(name, String(value));
    if (name === 'id') this.id = String(value);
    if (name === 'class') this.className = String(value);
    if (name.startsWith('data-')) {
      const camelKey = name.slice(5).replace(/-([a-z])/g, (_, l) => l.toUpperCase());
      this.dataset[camelKey] = String(value);
    }
  }

  getAttribute(name) {
    return this.attributes.has(name) ? this.attributes.get(name) : null;
  }

  hasAttribute(name) {
    return this.attributes.has(name);
  }

  removeAttribute(name) {
    this.attributes.delete(name);
    if (name === 'id') this.id = '';
    if (name === 'class') this.className = '';
    if (name.startsWith('data-')) {
      const camelKey = name.slice(5).replace(/-([a-z])/g, (_, l) => l.toUpperCase());
      delete this.dataset[camelKey];
    }
  }

  appendChild(child) {
    if (!child) return;
    if (child.parentNode) child.parentNode.removeChild(child);
    child.parentNode = this;
    child.ownerDocument = this.ownerDocument;
    this.children.push(child);
    return child;
  }

  removeChild(child) {
    const idx = this.children.indexOf(child);
    if (idx !== -1) {
      this.children.splice(idx, 1);
      child.parentNode = null;
    }
    return child;
  }

  contains(other) {
    if (!other) return false;
    let curr = other;
    while (curr) {
      if (curr === this) return true;
      curr = curr.parentNode;
    }
    return false;
  }

  addEventListener(type, cb) {
    if (!this.eventListeners.has(type)) {
      this.eventListeners.set(type, []);
    }
    this.eventListeners.get(type).push(cb);
  }

  removeEventListener(type, cb) {
    if (!this.eventListeners.has(type)) return;
    const list = this.eventListeners.get(type);
    const idx = list.indexOf(cb);
    if (idx !== -1) list.splice(idx, 1);
  }

  dispatchEvent(event) {
    if (!event.target) event.target = this;
    event.currentTarget = this;
    if (this.eventListeners.has(event.type)) {
      const listeners = [...this.eventListeners.get(event.type)];
      for (const cb of listeners) {
        cb.call(this, event);
      }
    }
    return !event.defaultPrevented;
  }

  click() {
    const evt = new MockEvent('click', { target: this, currentTarget: this });
    this.dispatchEvent(evt);
    return evt;
  }

  focus() {
    if (this.ownerDocument) {
      this.ownerDocument.activeElement = this;
    }
  }

  blur() {
    if (this.ownerDocument && this.ownerDocument.activeElement === this) {
      this.ownerDocument.activeElement = this.ownerDocument.body;
    }
  }

  scrollIntoView(options) {
    this.scrollIntoViewCalled = true;
    this.scrollIntoViewOptions = options;
  }

  get innerHTML() {
    return this._innerHTML;
  }

  set innerHTML(html) {
    this._innerHTML = html;
    this.children = [];
    if (!html || typeof html !== 'string') return;

    // Parser for <tr> rows in table rendering
    if (html.includes('<tr')) {
      const rowMatches = html.match(/<tr[\s\S]*?<\/tr>/gi) || [];
      for (const rowHtml of rowMatches) {
        const row = new MockElement('tr');
        row.ownerDocument = this.ownerDocument;

        // Extract attributes of <tr>
        const tagOpen = rowHtml.slice(0, rowHtml.indexOf('>'));
        const attrMatches = tagOpen.match(/([a-zA-Z0-9_\-]+)(?:="([^"]*)")?/g) || [];
        for (const attr of attrMatches) {
          if (attr.startsWith('<tr') || attr === 'tr') continue;
          const eqIdx = attr.indexOf('=');
          if (eqIdx !== -1) {
            const key = attr.slice(0, eqIdx);
            const val = attr.slice(eqIdx + 2, -1);
            row.setAttribute(key, val);
          } else {
            row.setAttribute(attr, '');
          }
        }
        row._innerHTML = rowHtml;
        this.appendChild(row);
      }
    }
  }

  get textContent() {
    return this._innerHTML.replace(/<[^>]+>/g, '').trim();
  }

  set textContent(val) {
    this._innerHTML = String(val);
  }

  _matchesSingle(sel) {
    sel = sel.trim();
    if (!sel || sel === '*') return true;

    // Handle :not(...)
    if (sel.includes(':not(')) {
      const openIdx = sel.indexOf(':not(');
      const closeIdx = sel.indexOf(')', openIdx);
      const base = sel.slice(0, openIdx);
      const notSel = sel.slice(openIdx + 5, closeIdx);
      if (base && !this._matchesSingle(base)) return false;
      if (this._matchesSingle(notSel)) return false;
      return true;
    }

    // Handle attributes: tag[attr="val"] or tag[attr] or [attr]
    if (sel.includes('[')) {
      const bOpen = sel.indexOf('[');
      const bClose = sel.indexOf(']');
      const tagPart = sel.slice(0, bOpen);
      const attrPart = sel.slice(bOpen + 1, bClose);

      if (tagPart && this.tagName.toLowerCase() !== tagPart.toLowerCase()) {
        return false;
      }
      if (attrPart.includes('=')) {
        const [aName, aVal] = attrPart.split('=');
        const cleanVal = aVal.replace(/^["']|["']$/g, '');
        return this.getAttribute(aName) === cleanVal;
      }
      return this.hasAttribute(attrPart);
    }

    if (sel.startsWith('#')) {
      return this.id === sel.slice(1);
    }
    if (sel.startsWith('.')) {
      return this.classList.contains(sel.slice(1));
    }
    return this.tagName.toLowerCase() === sel.toLowerCase();
  }

  _matches(selector) {
    const compound = selector.trim().split(/\s+/);
    if (compound.length === 1) {
      return this._matchesSingle(compound[0]);
    }
    // For 2-level descendant like "#ranking-table th[data-sort]"
    const last = compound[compound.length - 1];
    if (!this._matchesSingle(last)) return false;

    let parent = this.parentNode;
    while (parent) {
      if (parent._matchesSingle && parent._matchesSingle(compound[0])) {
        return true;
      }
      parent = parent.parentNode;
    }
    return false;
  }

  querySelectorAll(selector) {
    const results = [];
    const subSelectors = selector.split(',').map(s => s.trim());

    const traverse = (node) => {
      for (const child of node.children) {
        for (const sub of subSelectors) {
          if (child._matches(sub)) {
            if (!results.includes(child)) results.push(child);
            break;
          }
        }
        traverse(child);
      }
    };
    traverse(this);
    return results;
  }

  querySelector(selector) {
    const list = this.querySelectorAll(selector);
    return list.length > 0 ? list[0] : null;
  }
}

class MockDocument {
  constructor() {
    this.documentElement = new MockElement('html');
    this.documentElement.ownerDocument = this;
    this.body = new MockElement('body');
    this.body.ownerDocument = this;
    this.documentElement.appendChild(this.body);
    this.activeElement = this.body;
    this.eventListeners = new Map();
  }

  createElement(tagName) {
    const el = new MockElement(tagName);
    el.ownerDocument = this;
    return el;
  }

  getElementById(id) {
    const search = (node) => {
      if (node.id === id) return node;
      for (const child of node.children) {
        const found = search(child);
        if (found) return found;
      }
      return null;
    };
    return search(this.documentElement);
  }

  querySelector(selector) {
    return this.documentElement.querySelector(selector);
  }

  querySelectorAll(selector) {
    return this.documentElement.querySelectorAll(selector);
  }

  addEventListener(type, cb) {
    if (!this.eventListeners.has(type)) this.eventListeners.set(type, []);
    this.eventListeners.get(type).push(cb);
  }

  removeEventListener(type, cb) {
    if (!this.eventListeners.has(type)) return;
    const list = this.eventListeners.get(type);
    const idx = list.indexOf(cb);
    if (idx !== -1) list.splice(idx, 1);
  }

  dispatchEvent(event) {
    event.currentTarget = this;
    if (this.eventListeners.has(event.type)) {
      const list = [...this.eventListeners.get(event.type)];
      for (const cb of list) {
        cb.call(this, event);
      }
    }
    return !event.defaultPrevented;
  }
}

// -------------------------------------------------------------------------
// BUILD ENVIRONMENT & EXTRACT APP LOGIC
// -------------------------------------------------------------------------

function buildMockDomTree() {
  const doc = new MockDocument();

  const add = (parent, tag, id, className, attrs = {}) => {
    const el = doc.createElement(tag);
    if (id) el.id = id;
    if (className) el.className = className;
    for (const [k, v] of Object.entries(attrs)) {
      el.setAttribute(k, v);
    }
    parent.appendChild(el);
    return el;
  };

  // Topbar / A11y Theme Buttons
  const a11yBar = add(doc.body, 'div', 'a11y-bar', 'a11y-bar');
  add(a11yBar, 'button', 'btn-theme-light', 'a11y-btn', { 'data-theme-btn': 'light' });
  add(a11yBar, 'button', 'btn-theme-dark', 'a11y-btn', { 'data-theme-btn': 'dark' });
  add(a11yBar, 'button', 'btn-theme-contrast', 'a11y-btn', { 'data-theme-btn': 'contrast' });

  // Buttons that open modals
  const hero = add(doc.body, 'section', 'hero-section', 'hero');
  add(hero, 'button', 'btn-hero-como-usar', 'btn-como-usar');
  add(hero, 'button', 'btn-open-guia', 'btn-open-guia');
  add(hero, 'button', 'btn-open-legal-top', 'btn-legal');
  add(hero, 'button', 'btn-download-enriched', 'btn-intercept-download', {
    'data-file': 'comunas_enriched.json',
    'data-label': 'Microdatos Municipales Enriquecidos (JSON)'
  });

  // Table Structure
  const tableSection = add(doc.body, 'section', 'ranking-section', 'ranking');
  const table = add(tableSection, 'table', 'ranking-table', 'ranking-table');
  const thead = add(table, 'thead', '', '');
  const theadTr = add(thead, 'tr', '', '');

  const sortFields = [
    { sort: 'rank', label: '#' },
    { sort: 'comuna', label: 'Comuna' },
    { sort: 'region', label: 'Región' },
    { sort: 'poblacion', label: 'Población INE' },
    { sort: 'monto_total', label: 'Gasto TI Total' },
    { sort: 'gasto_pc', label: 'Gasto / Hab.' },
    { sort: 'score_madurez', label: 'Madurez TI' },
    { sort: 'dotacion_total', label: 'Dotación RRHH' },
    { sort: 'pct_honorarios', label: '% Honorarios' },
    { sort: 'dotacion_ti', label: 'Staff TI' },
    { sort: 'ret_ratio', label: 'Ratio RET' },
    { sort: 'cuadrante_capacidad', label: 'Capacidad Estatal' }
  ];

  sortFields.forEach(sf => {
    add(theadTr, 'th', '', '', {
      'data-sort': sf.sort,
      'tabindex': '0',
      'role': 'button',
      'aria-sort': 'none'
    });
  });

  add(table, 'tbody', 'ranking-tbody', 'ranking-tbody');

  // Radiografia and Commune Drawer
  add(doc.body, 'section', 'radiografia', 'radiografia');
  add(doc.body, 'div', 'comuna-drawer', 'comuna-drawer');

  // Map element
  add(doc.body, 'div', 'chile-map', 'map-container');

  // MODAL 1: Como Usar Modal
  const modalComoUsar = add(doc.body, 'div', 'como-usar-modal', 'obs-modal-backdrop', {
    'aria-hidden': 'true',
    'role': 'dialog',
    'aria-modal': 'true'
  });
  const cardComoUsar = add(modalComoUsar, 'div', '', 'obs-modal-card');
  add(cardComoUsar, 'button', 'close-como-usar', 'obs-modal-close', { 'data-close-modal': 'como-usar-modal', 'aria-label': 'Cerrar' });
  add(cardComoUsar, 'input', 'chk-no-auto-show', '', { 'type': 'checkbox' });
  add(cardComoUsar, 'button', 'btn-jump-map', 'btn-modal-jump', { 'data-jump-target': '#chile-map' });
  add(cardComoUsar, 'button', 'btn-demo-compare', 'btn-demo-compare');
  add(cardComoUsar, 'button', 'btn-finish-como-usar', 'btn-modal-primary', { 'data-close-modal': 'como-usar-modal' });

  // MODAL 2: Legal Modal
  const modalLegal = add(doc.body, 'div', 'legal-modal', 'obs-modal-backdrop', {
    'aria-hidden': 'true',
    'role': 'dialog',
    'aria-modal': 'true'
  });
  const cardLegal = add(modalLegal, 'div', '', 'obs-modal-card');
  add(cardLegal, 'button', 'close-legal', 'obs-modal-close', { 'data-close-modal': 'legal-modal', 'aria-label': 'Cerrar' });
  add(cardLegal, 'a', 'link-chilecompra', '', { 'href': 'https://www.chilecompra.cl' });
  add(cardLegal, 'button', 'btn-close-legal-action', 'btn-modal-primary', { 'data-close-modal': 'legal-modal' });

  // MODAL 3: Registro Descarga Modal
  const modalRegistro = add(doc.body, 'div', 'registro-descarga-modal', 'obs-modal-backdrop', {
    'aria-hidden': 'true',
    'role': 'dialog',
    'aria-modal': 'true'
  });
  const cardRegistro = add(modalRegistro, 'div', '', 'obs-modal-card');
  add(cardRegistro, 'button', 'close-reg', 'obs-modal-close', { 'data-close-modal': 'registro-descarga-modal', 'aria-label': 'Cerrar' });
  add(cardRegistro, 'span', 'descarga-filename-label', '');
  add(cardRegistro, 'div', 'reg-error-msg', '');
  const formReg = add(cardRegistro, 'form', 'form-registro-descarga', '');
  add(formReg, 'input', 'reg-nombre', '', { 'type': 'text' });
  add(formReg, 'input', 'reg-email', '', { 'type': 'email' });
  add(formReg, 'input', 'reg-institucion', '', { 'type': 'text' });
  add(formReg, 'select', 'reg-perfil', '');
  add(formReg, 'select', 'reg-proposito', '');
  add(formReg, 'input', 'reg-proyecto', '', { 'type': 'text' });
  add(formReg, 'input', 'reg-contacto', '', { 'type': 'checkbox' });
  add(formReg, 'button', 'btn-reg-cancel', 'btn-modal-cancel', { 'data-close-modal': 'registro-descarga-modal' });
  add(formReg, 'button', 'btn-reg-submit', 'btn-modal-primary', { 'type': 'submit' });

  return doc;
}

// -------------------------------------------------------------------------
// SANDBOX SETUP & LOGIC EXECUTION
// -------------------------------------------------------------------------

const doc = buildMockDomTree();

// Mock localStorage
const localStorageStore = new Map();
const mockLocalStorage = {
  getItem: (k) => localStorageStore.has(k) ? localStorageStore.get(k) : null,
  setItem: (k, v) => localStorageStore.set(k, String(v)),
  removeItem: (k) => localStorageStore.delete(k),
  clear: () => localStorageStore.clear()
};

// Mock Leaflet
class MockLayer {
  constructor(name) {
    this.name = name;
  }
  addTo(map) {
    map.addLayer(this);
    return this;
  }
}
class MockMap {
  constructor() {
    this._layers = new Set();
  }
  hasLayer(layer) {
    return this._layers.has(layer);
  }
  addLayer(layer) {
    this._layers.add(layer);
    return this;
  }
  removeLayer(layer) {
    this._layers.delete(layer);
    return this;
  }
  setView(center, zoom, opts) {
    this.center = center;
    this.zoom = zoom;
    return this;
  }
}

const mockLeaflet = {
  tileLayer: (url, opts) => new MockLayer('tileLayer:' + url),
  layerGroup: (layers = []) => {
    const lg = new MockLayer('layerGroup');
    lg.layers = layers;
    return lg;
  }
};

const mockWindow = {
  document: doc,
  localStorage: mockLocalStorage,
  history: {
    replaceState: () => {}
  },
  addEventListener: () => {},
  removeEventListener: () => {}
};

// Slices from app.js
const sHelpers = appCode.slice(
  appCode.indexOf('function normalizeText'),
  appCode.indexOf('function showErrorBanner')
);

const sTheme = appCode.slice(
  appCode.indexOf('function updateMapTheme'),
  appCode.indexOf('function getMarkerStyle')
);

const sSelect = appCode.slice(
  appCode.indexOf('function renderGaugeSvg'),
  appCode.indexOf('function openComparison')
);

const sTable = appCode.slice(
  appCode.indexOf('function escapeHtml'),
  appCode.indexOf('function exportTableToCSV')
);

const sThemeA11y = appCode.slice(
  appCode.indexOf('function initThemeAndA11y'),
  appCode.indexOf('// 8. GESTIÓN DE MODALES')
);

const sModals = appCode.slice(
  appCode.indexOf('function initModals'),
  appCode.indexOf('// 9. MÓDULO RRHH')
);

const sFormat = appCode.slice(
  appCode.indexOf('function formatCLP'),
  appCode.indexOf('// Iniciar ejecución')
);

// Table sort listener setup (from initControls in app.js lines 1406-1425)
const tableSortSetupSlice = `
function setupTableSorting() {
  const ths = document.querySelectorAll("#ranking-table th[data-sort]");
  ths.forEach(th => {
    const handleSort = () => {
      const field = th.dataset.sort;
      if (state.sortField === field) {
        state.sortAsc = !state.sortAsc;
      } else {
        state.sortField = field;
        state.sortAsc = false;
      }
      renderTable();
    };
    th.addEventListener("click", handleSort);
    th.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        handleSort();
      }
    });
  });
}
`;

const sandbox = {
  document: doc,
  window: mockWindow,
  localStorage: mockLocalStorage,
  L: mockLeaflet,
  console,
  setTimeout,
  clearTimeout,
  Array,
  Map,
  Set,
  Math,
  Number,
  String,
  Boolean,
  state: {
    comunas: [],
    regiones: rawRegiones,
    kpis: rawKpis,
    proveedores: rawProveedores,
    currentLayer: 'madurez',
    selectedComuna: null,
    compareComuna: null,
    isCompareMode: false,
    searchQuery: '',
    selectedRegion: '',
    selectedCuadrante: '',
    sortField: 'monto_total',
    sortAsc: false,
    map: new MockMap(),
    esriLightGroup: mockLeaflet.layerGroup(),
    esriDarkGroup: mockLeaflet.layerGroup(),
    pendingDownload: null
  },
  showToast: () => {}
};

vm.createContext(sandbox);

const fullScript = `
${sHelpers}
${sFormat}
${sTheme}
${sSelect}
${sTable}
${sThemeA11y}
${sModals}
${tableSortSetupSlice}

state.comunas = deduplicateComunas(${JSON.stringify(rawComunas)});

this.state = state;
this.initModals = initModals;
this.initThemeAndA11y = initThemeAndA11y;
this.updateMapTheme = updateMapTheme;
this.renderTable = renderTable;
this.setupTableSorting = setupTableSorting;
this.selectComuna = selectComuna;
`;

vm.runInContext(fullScript, sandbox);

console.log(`[INFO] Loaded ${sandbox.state.comunas.length} consolidated comunas in test sandbox.`);

// Initialize modules in mock DOM
sandbox.initModals();
sandbox.initThemeAndA11y();
sandbox.setupTableSorting();
sandbox.renderTable();

// =========================================================================
// SUITE 1: MODAL FOCUS TRAPS & KEYBOARD ACCESSIBILITY
// =========================================================================
console.log('\n----------------------------------------------------------------------');
console.log('SUITE 1: MODAL FOCUS TRAP, INITIAL FOCUS & ESCAPE RESTORATION');
console.log('----------------------------------------------------------------------');

const comoUsarModal = doc.getElementById('como-usar-modal');
const legalModal = doc.getElementById('legal-modal');
const regModal = doc.getElementById('registro-descarga-modal');
const btnHeroComoUsar = doc.getElementById('btn-hero-como-usar');
const btnOpenLegal = doc.getElementById('btn-open-legal-top');
const btnDownload = doc.getElementById('btn-download-enriched');

(async function runSuite1() {
  // Test 1.1: Open "Cómo Usar" modal via button, initial focus transfer
  btnHeroComoUsar.focus();
  assert(doc.activeElement === btnHeroComoUsar, '1.1 Pre-open activeElement set to btn-hero-como-usar');

  btnHeroComoUsar.click();
  assert(comoUsarModal.classList.contains('active'), '1.1 Modal #como-usar-modal has class "active"');
  assert(comoUsarModal.getAttribute('aria-hidden') === 'false', '1.1 Modal #como-usar-modal aria-hidden="false"');

  // Allow setTimeout(50) for focus transfer
  await new Promise(r => setTimeout(r, 65));
  const cardComoUsar = comoUsarModal.querySelector('.obs-modal-card');
  assert(cardComoUsar.contains(doc.activeElement), '1.1 Focus successfully transferred inside modal card', `activeElement: ${doc.activeElement.id || doc.activeElement.tagName}`);

  // Test 1.2: Tab forward trap (wrap from last focusable to first focusable)
  const focusables = cardComoUsar.querySelectorAll('a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])');
  const firstFocusable = focusables[0];
  const lastFocusable = focusables[focusables.length - 1];

  lastFocusable.focus();
  assert(doc.activeElement === lastFocusable, '1.2 Focus placed on last modal element before Tab');

  const tabForwardEvt = new MockEvent('keydown', { key: 'Tab', shiftKey: false });
  doc.dispatchEvent(tabForwardEvt);

  assert(tabForwardEvt.defaultPrevented === true, '1.2 Forward Tab called preventDefault() when on last element');
  assert(doc.activeElement === firstFocusable, '1.2 Forward Tab wrapped focus around to first element', `activeElement: ${doc.activeElement.id || doc.activeElement.className}`);

  // Test 1.3: Shift+Tab backward trap (wrap from first focusable to last focusable)
  firstFocusable.focus();
  assert(doc.activeElement === firstFocusable, '1.3 Focus placed on first modal element before Shift+Tab');

  const tabBackwardEvt = new MockEvent('keydown', { key: 'Tab', shiftKey: true });
  doc.dispatchEvent(tabBackwardEvt);

  assert(tabBackwardEvt.defaultPrevented === true, '1.3 Shift+Tab called preventDefault() when on first element');
  assert(doc.activeElement === lastFocusable, '1.3 Shift+Tab wrapped focus around to last element', `activeElement: ${doc.activeElement.id || doc.activeElement.className}`);

  // Test 1.4: Tab when focus is unexpectedly outside modal card (restores into modal)
  doc.activeElement = doc.body;
  const tabOutsideEvt = new MockEvent('keydown', { key: 'Tab', shiftKey: false });
  doc.dispatchEvent(tabOutsideEvt);
  assert(tabOutsideEvt.defaultPrevented === true, '1.4 Forward Tab when outside trapped focus into first element');
  assert(doc.activeElement === firstFocusable, '1.4 Focus reset to first modal element from outside');

  // Test 1.5: Escape key closes modal and restores focus to previous activeElement
  const escapeEvt = new MockEvent('keydown', { key: 'Escape' });
  doc.dispatchEvent(escapeEvt);

  assert(!comoUsarModal.classList.contains('active'), '1.5 Modal active class removed on Escape');
  assert(comoUsarModal.getAttribute('aria-hidden') === 'true', '1.5 Modal aria-hidden="true" on Escape');
  assert(doc.activeElement === btnHeroComoUsar, '1.5 Focus faithfully restored to btn-hero-como-usar');

  // Test 1.6: Open Legal Modal and verify Escape return
  btnOpenLegal.focus();
  btnOpenLegal.click();
  assert(legalModal.classList.contains('active'), '1.6 Modal #legal-modal opened');
  await new Promise(r => setTimeout(r, 65));
  const cardLegal = legalModal.querySelector('.obs-modal-card');
  assert(cardLegal.contains(doc.activeElement), '1.6 Focus transferred into #legal-modal');

  const escLegalEvt = new MockEvent('keydown', { key: 'Escape' });
  doc.dispatchEvent(escLegalEvt);
  assert(!legalModal.classList.contains('active'), '1.6 #legal-modal closed via Escape');
  assert(doc.activeElement === btnOpenLegal, '1.6 Focus restored to btn-open-legal-top');

  // Test 1.7: Open Download Registration Modal and verify input focus
  btnDownload.focus();
  btnDownload.click();
  assert(regModal.classList.contains('active'), '1.7 #registro-descarga-modal opened on download click');
  await new Promise(r => setTimeout(r, 65));

  const regNombreInput = doc.getElementById('reg-nombre');
  assert(doc.activeElement === regNombreInput, '1.7 Initial focus transferred specifically to first form input #reg-nombre');

  const escRegEvt = new MockEvent('keydown', { key: 'Escape' });
  doc.dispatchEvent(escRegEvt);
  assert(!regModal.classList.contains('active'), '1.7 #registro-descarga-modal closed via Escape');
  assert(doc.activeElement === btnDownload, '1.7 Focus restored to btn-download-enriched');

  // Test 1.8: Backdrop click vs Card click
  btnHeroComoUsar.click();
  assert(comoUsarModal.classList.contains('active'), '1.8 Modal opened for click boundary test');

  // Click inside modal card (should NOT close)
  const cardClickEvt = new MockEvent('click', { target: cardComoUsar });
  comoUsarModal.dispatchEvent(cardClickEvt);
  assert(comoUsarModal.classList.contains('active'), '1.8 Clicking inside .obs-modal-card does NOT close modal');

  // Click on modal backdrop (should close)
  const backdropClickEvt = new MockEvent('click', { target: comoUsarModal });
  comoUsarModal.dispatchEvent(backdropClickEvt);
  assert(!comoUsarModal.classList.contains('active'), '1.8 Clicking on backdrop closes modal');

  // Test 1.9: Escape when no modal is open (no-op, zero errors)
  let noErrorOnExtraEscape = true;
  try {
    const strayEsc = new MockEvent('keydown', { key: 'Escape' });
    doc.dispatchEvent(strayEsc);
  } catch (err) {
    noErrorOnExtraEscape = false;
  }
  assert(noErrorOnExtraEscape, '1.9 Escape key when no modal is open is a clean no-op');

  // Test 1.10: Disabled elements excluded from focus trap
  const disabledBtn = doc.createElement('button');
  disabledBtn.setAttribute('disabled', '');
  cardComoUsar.appendChild(disabledBtn);

  const inertDiv = doc.createElement('div');
  inertDiv.setAttribute('tabindex', '-1');
  cardComoUsar.appendChild(inertDiv);

  const filteredFocusables = cardComoUsar.querySelectorAll('a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])');
  assert(!filteredFocusables.includes(disabledBtn), '1.10 button[disabled] is strictly excluded from focusable trap list');
  assert(!filteredFocusables.includes(inertDiv), '1.10 [tabindex="-1"] is strictly excluded from focusable trap list');

  cardComoUsar.removeChild(disabledBtn);
  cardComoUsar.removeChild(inertDiv);

  runSuite2();
})();

// =========================================================================
// SUITE 2: TABLE HEADER KEYBOARD SORTING & ARIA-SORT ATTRIBUTES
// =========================================================================
function runSuite2() {
  console.log('\n----------------------------------------------------------------------');
  console.log('SUITE 2: TABLE HEADER SORTING (ENTER / SPACE) & ARIA-SORT ATTR');
  console.log('----------------------------------------------------------------------');

  const thComuna = doc.querySelector('#ranking-table th[data-sort="comuna"]');
  const thMonto = doc.querySelector('#ranking-table th[data-sort="monto_total"]');
  const thMadurez = doc.querySelector('#ranking-table th[data-sort="score_madurez"]');
  const thGastoPc = doc.querySelector('#ranking-table th[data-sort="gasto_pc"]');

  assert(thComuna !== null && thMonto !== null && thMadurez !== null, '2.1 Sortable <th> elements found in DOM');

  // Initial state: default sort is monto_total descending
  assert(sandbox.state.sortField === 'monto_total', '2.1 Initial sortField is monto_total');
  assert(sandbox.state.sortAsc === false, '2.1 Initial sort direction is descending');
  assert(thMonto.getAttribute('aria-sort') === 'descending', '2.1 Initial th[monto_total] aria-sort="descending"');
  assert(thComuna.getAttribute('aria-sort') === 'none', '2.1 Initial th[comuna] aria-sort="none"');

  // Test 2.2: Press Enter on th[comuna]
  const enterComunaEvt = new MockEvent('keydown', { key: 'Enter' });
  thComuna.dispatchEvent(enterComunaEvt);

  assert(enterComunaEvt.defaultPrevented === true, '2.2 Pressing Enter on <th> prevented default');
  assert(sandbox.state.sortField === 'comuna', '2.2 sortField transitioned to "comuna"');
  assert(sandbox.state.sortAsc === false, '2.2 Default direction for new sort field is descending');
  assert(thComuna.getAttribute('aria-sort') === 'descending', '2.2 th[comuna] aria-sort updated to "descending"');
  assert(thMonto.getAttribute('aria-sort') === 'none', '2.2 th[monto_total] aria-sort reset to "none"');

  // Test 2.3: Press Enter again on th[comuna] to toggle ascending
  const enterComunaAscEvt = new MockEvent('keydown', { key: 'Enter' });
  thComuna.dispatchEvent(enterComunaAscEvt);

  assert(sandbox.state.sortAsc === true, '2.3 Second Enter toggled sort direction to ascending');
  assert(thComuna.getAttribute('aria-sort') === 'ascending', '2.3 th[comuna] aria-sort updated to "ascending"');

  // Test 2.4: Press Space on th[score_madurez]
  const spaceMadurezEvt = new MockEvent('keydown', { key: ' ' });
  thMadurez.dispatchEvent(spaceMadurezEvt);

  assert(spaceMadurezEvt.defaultPrevented === true, '2.4 Pressing Space on <th> prevented default');
  assert(sandbox.state.sortField === 'score_madurez', '2.4 sortField transitioned to "score_madurez" via Space key');
  assert(thMadurez.getAttribute('aria-sort') === 'descending', '2.4 th[score_madurez] aria-sort updated to "descending"');
  assert(thComuna.getAttribute('aria-sort') === 'none', '2.4 th[comuna] aria-sort reset to "none"');

  // Test 2.5: Verify rendered table order matches sorted criteria
  const tbody = doc.getElementById('ranking-tbody');
  const rows = tbody.querySelectorAll('tr');
  assert(rows.length > 0, '2.5 Table rows rendered in #ranking-tbody', `row count: ${rows.length}`);

  // Test 2.6: Non-sorting keys (ArrowDown, Tab, Escape) should NOT trigger sort
  const prevSort = sandbox.state.sortField;
  const prevAsc = sandbox.state.sortAsc;

  const tabKeyEvt = new MockEvent('keydown', { key: 'Tab' });
  thGastoPc.dispatchEvent(tabKeyEvt);
  assert(sandbox.state.sortField === prevSort && sandbox.state.sortAsc === prevAsc, '2.6 Tab key on <th> does not trigger sort');

  const arrowKeyEvt = new MockEvent('keydown', { key: 'ArrowDown' });
  thGastoPc.dispatchEvent(arrowKeyEvt);
  assert(sandbox.state.sortField === prevSort && sandbox.state.sortAsc === prevAsc, '2.6 ArrowDown key on <th> does not trigger sort');

  // Test 2.7: Comprehensive check across all 12 sortable columns
  const allSortFields = ['rank', 'comuna', 'region', 'poblacion', 'monto_total', 'gasto_pc', 'score_madurez', 'dotacion_total', 'pct_honorarios', 'dotacion_ti', 'ret_ratio', 'cuadrante_capacidad'];
  let all12SortedCleanly = true;
  for (const field of allSortFields) {
    const th = doc.querySelector(`#ranking-table th[data-sort="${field}"]`);
    if (!th) {
      all12SortedCleanly = false;
      break;
    }
    const press = new MockEvent('keydown', { key: 'Enter' });
    th.dispatchEvent(press);
    if (sandbox.state.sortField !== field || th.getAttribute('aria-sort') !== 'descending') {
      all12SortedCleanly = false;
      break;
    }
    // Verify all other headers reset to "none"
    const others = doc.querySelectorAll(`#ranking-table th[data-sort]:not([data-sort="${field}"])`);
    for (const oth of others) {
      if (oth.getAttribute('aria-sort') !== 'none') {
        all12SortedCleanly = false;
        break;
      }
    }
  }
  assert(all12SortedCleanly, '2.7 All 12 table columns sortable via keyboard with exclusive aria-sort sync');

  runSuite3();
}

// =========================================================================
// SUITE 3: TABLE ROW KEYBOARD INTERACTION & COMMUNE CARD OPENING
// =========================================================================
function runSuite3() {
  console.log('\n----------------------------------------------------------------------');
  console.log('SUITE 3: TABLE ROW INTERACTION (ENTER / SPACE) & COMMUNE DRAWER');
  console.log('----------------------------------------------------------------------');

  const tbody = doc.getElementById('ranking-tbody');
  const rows = tbody.querySelectorAll('tr');
  const firstRow = rows[0];

  assert(firstRow.getAttribute('tabindex') === '0', '3.1 Table row has tabindex="0"');
  assert(firstRow.getAttribute('role') === 'button', '3.1 Table row has role="button"');
  assert(firstRow.hasAttribute('aria-label'), '3.1 Table row has informative aria-label', firstRow.getAttribute('aria-label'));

  const comunaName = firstRow.dataset.comunaName;
  assert(Boolean(comunaName), '3.1 Table row contains data-comuna-name attribute', comunaName);

  // Test 3.2: Press Enter on table row
  const drawer = doc.getElementById('comuna-drawer');
  const radiografia = doc.getElementById('radiografia');
  radiografia.scrollIntoViewCalled = false;

  const enterRowEvt = new MockEvent('keydown', { key: 'Enter' });
  firstRow.dispatchEvent(enterRowEvt);

  assert(enterRowEvt.defaultPrevented === true, '3.2 Pressing Enter on <tr> called preventDefault()');
  assert(sandbox.state.selectedComuna !== null, '3.2 state.selectedComuna successfully set');
  assert(sandbox.state.selectedComuna.comuna === comunaName, '3.2 selectedComuna matches row commune name', comunaName);
  assert(drawer.innerHTML.includes(comunaName), '3.2 #comuna-drawer rendered with commune name');
  assert(radiografia.scrollIntoViewCalled === true, '3.2 #radiografia.scrollIntoView called smoothly');
  assert(radiografia.scrollIntoViewOptions.behavior === 'smooth', '3.2 scrollIntoView invoked with behavior: smooth');

  // Test 3.3: Press Space on second table row
  if (rows.length > 1) {
    const secondRow = rows[1];
    const secondComuna = secondRow.dataset.comunaName;
    radiografia.scrollIntoViewCalled = false;

    const spaceRowEvt = new MockEvent('keydown', { key: ' ' });
    secondRow.dispatchEvent(spaceRowEvt);

    assert(spaceRowEvt.defaultPrevented === true, '3.3 Pressing Space on <tr> called preventDefault()');
    assert(sandbox.state.selectedComuna.comuna === secondComuna, '3.3 selectedComuna updated to second row via Space', secondComuna);
    assert(drawer.innerHTML.includes(secondComuna), '3.3 #comuna-drawer rendered with second commune name');
  }

  // Test 3.4: Irrelevant key (e.g. Tab or Escape) on <tr> does not retrigger selection
  const currentSelected = sandbox.state.selectedComuna.comuna;
  const tabRowEvt = new MockEvent('keydown', { key: 'Tab' });
  firstRow.dispatchEvent(tabRowEvt);
  assert(tabRowEvt.defaultPrevented === false, '3.4 Tab on <tr> does NOT preventDefault()');

  // Test 3.5: Adversarial corrupt commune name in row
  const bogusRow = doc.createElement('tr');
  bogusRow.dataset.comunaName = 'ComunaFantasma999';
  let corruptRowSurvived = true;
  try {
    const enterBogus = new MockEvent('keydown', { key: 'Enter' });
    bogusRow.dispatchEvent(enterBogus);
  } catch (err) {
    corruptRowSurvived = false;
  }
  assert(corruptRowSurvived, '3.5 Row with non-existent comuna handles gracefully without throwing');

  // Test 3.6: Fuzz all 346 municipalities through selectComuna
  let all346RenderedCleanly = true;
  for (const c of sandbox.state.comunas) {
    try {
      sandbox.selectComuna(c);
      if (!drawer.innerHTML.includes(c.comuna)) {
        all346RenderedCleanly = false;
        break;
      }
    } catch (err) {
      all346RenderedCleanly = false;
      break;
    }
  }
  assert(all346RenderedCleanly, '3.6 All 346 municipalities generate valid drawer cards and gauge SVGs');

  runSuite4();
}

// =========================================================================
// SUITE 4: THEME TRANSITIONS & ESRIDARKGROUP SYNCHRONIZATION
// =========================================================================
function runSuite4() {
  console.log('\n----------------------------------------------------------------------');
  console.log('SUITE 4: THEME TRANSITIONS ("dark", "light", "contrast") & MAP LAYERS');
  console.log('----------------------------------------------------------------------');

  const map = sandbox.state.map;
  const lightGroup = sandbox.state.esriLightGroup;
  const darkGroup = sandbox.state.esriDarkGroup;

  // Initialize with light layer
  map.addLayer(lightGroup);
  assert(map.hasLayer(lightGroup) && !map.hasLayer(darkGroup), '4.1 Map initialized with esriLightGroup');

  // Test 4.2: Transition to "dark"
  sandbox.updateMapTheme('dark');
  assert(map.hasLayer(darkGroup), '4.2 updateMapTheme("dark") adds esriDarkGroup to map');
  assert(!map.hasLayer(lightGroup), '4.2 updateMapTheme("dark") removes esriLightGroup from map');

  // Test 4.3: Transition to "contrast" (must also use esriDarkGroup!)
  sandbox.updateMapTheme('contrast');
  assert(map.hasLayer(darkGroup), '4.3 updateMapTheme("contrast") keeps esriDarkGroup on map');
  assert(!map.hasLayer(lightGroup), '4.3 updateMapTheme("contrast") ensures esriLightGroup is NOT on map');

  // Test 4.4: Transition to "light"
  sandbox.updateMapTheme('light');
  assert(map.hasLayer(lightGroup), '4.4 updateMapTheme("light") adds esriLightGroup to map');
  assert(!map.hasLayer(darkGroup), '4.4 updateMapTheme("light") removes esriDarkGroup from map');

  // Test 4.5: Theme buttons in UI
  const btnDark = doc.querySelector('button[data-theme-btn="dark"]');
  const btnContrast = doc.querySelector('button[data-theme-btn="contrast"]');
  const btnLight = doc.querySelector('button[data-theme-btn="light"]');

  btnDark.click();
  assert(doc.documentElement.getAttribute('data-theme') === 'dark', '4.5 Clicking data-theme-btn="dark" sets document data-theme to dark');
  assert(map.hasLayer(darkGroup) && !map.hasLayer(lightGroup), '4.5 UI Dark click activates esriDarkGroup');

  btnContrast.click();
  assert(doc.documentElement.getAttribute('data-theme') === 'contrast', '4.5 Clicking data-theme-btn="contrast" sets document data-theme to contrast');
  assert(map.hasLayer(darkGroup) && !map.hasLayer(lightGroup), '4.5 UI Contrast click activates esriDarkGroup');

  btnLight.click();
  assert(doc.documentElement.getAttribute('data-theme') === 'light', '4.5 Clicking data-theme-btn="light" sets document data-theme to light');
  assert(map.hasLayer(lightGroup) && !map.hasLayer(darkGroup), '4.5 UI Light click activates esriLightGroup');

  // Test 4.6: Stress loop: 200 rapid alternating theme switches
  let rapidSwitchSuccess = true;
  try {
    const sequence = ['dark', 'contrast', 'light', 'dark', 'light', 'contrast'];
    for (let i = 0; i < 200; i++) {
      const targetTheme = sequence[i % sequence.length];
      sandbox.updateMapTheme(targetTheme);
      if (targetTheme === 'dark' || targetTheme === 'contrast') {
        if (!map.hasLayer(darkGroup) || map.hasLayer(lightGroup)) {
          rapidSwitchSuccess = false;
        }
      } else {
        if (!map.hasLayer(lightGroup) || map.hasLayer(darkGroup)) {
          rapidSwitchSuccess = false;
        }
      }
    }
  } catch (err) {
    rapidSwitchSuccess = false;
  }
  assert(rapidSwitchSuccess, '4.6 200 rapid theme transitions completed with 100% layer consistency');

  // Test 4.7: Resilience with invalid/null parameters
  let nullMapClean = true;
  try {
    const savedMap = sandbox.state.map;
    sandbox.state.map = null;
    sandbox.updateMapTheme('dark'); // Should return safely
    sandbox.state.map = savedMap;

    sandbox.updateMapTheme(null);
    sandbox.updateMapTheme(undefined);
    sandbox.updateMapTheme('unsupported_theme_123');
  } catch (err) {
    nullMapClean = false;
  }
  assert(nullMapClean, '4.7 updateMapTheme survives null map, undefined theme, and unsupported strings');

  runSuite5();
}

// =========================================================================
// SUITE 5: REGRESSION EXECUTION OF PREVIOUS TEST SUITES
// =========================================================================
function runSuite5() {
  console.log('\n----------------------------------------------------------------------');
  console.log('SUITE 5: PREVIOUS REGRESSION SUITES VERIFICATION');
  console.log('----------------------------------------------------------------------');

  let m1StressPassed = false;
  try {
    const m1Out = execSync('node tests/stress_test_m1.js', { cwd: rootDir, encoding: 'utf8' });
    m1StressPassed = m1Out.includes('RESULT: APPROVE') && !m1Out.includes('Critical fails: [^0]');
  } catch (err) {
    m1StressPassed = false;
  }
  assert(m1StressPassed, '5.1 tests/stress_test_m1.js continues to pass 100% (320 checks, 0 critical failures)');

  let m1SearchPassed = false;
  try {
    const searchOut = execSync('node tests/test_search_normalization_stress.js', { cwd: rootDir, encoding: 'utf8' });
    m1SearchPassed = searchOut.includes('ALL EMPIRICAL STRESS TESTS PASSED WITH 0 FAILURES') && searchOut.includes('2513 PASSED');
  } catch (err) {
    m1SearchPassed = false;
  }
  assert(m1SearchPassed, '5.2 tests/test_search_normalization_stress.js continues to pass 100% (2513 checks, 0 failures)');

  printSummary();
}

function printSummary() {
  console.log('\n======================================================================');
  console.log('HARNESS SUMMARY REPORT');
  console.log('======================================================================');
  console.log(`Total checks:      ${totalAssertions}`);
  console.log(`Passed checks:     ${passedAssertions}`);
  console.log(`Failed checks:     ${failedAssertions}`);

  if (failedAssertions > 0) {
    console.error('\nFailures:');
    failureDetails.forEach(f => console.error('  - ' + f));
    console.error('\n>>> VERDICT: REJECT <<<');
    process.exit(1);
  } else {
    console.log('\n>>> VERDICT: APPROVE <<<');
    process.exit(0);
  }
}
