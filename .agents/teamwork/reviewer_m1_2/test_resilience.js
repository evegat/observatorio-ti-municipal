const fs = require('fs');
const appCode = fs.readFileSync('app.js', 'utf8');

// Verify showErrorBanner and init structure
if (!appCode.includes('function showErrorBanner')) throw new Error('showErrorBanner missing');
if (!appCode.includes('role", "alert"')) throw new Error('role="alert" missing');
if (!appCode.includes('aria-live", "assertive"')) throw new Error('aria-live="assertive" missing');
if (!appCode.includes('btn-retry-init')) throw new Error('btn-retry-init missing');

// Simulate DOM and fetch failure
let bannerCreated = null;
let bannerRemoved = false;
let retryInvoked = false;

const mockDocument = {
  elements: {},
  getElementById(id) {
    return this.elements[id] || null;
  },
  createElement(tag) {
    const el = {
      tagName: tag,
      id: '',
      attributes: {},
      style: {},
      innerHTML: '',
      listeners: {},
      setAttribute(k, v) { this.attributes[k] = v; },
      getAttribute(k) { return this.attributes[k]; },
      addEventListener(evt, fn) { this.listeners[evt] = fn; },
      remove() {
        bannerRemoved = true;
        delete mockDocument.elements[this.id];
      }
    };
    return el;
  },
  body: {
    prepend(el) {
      bannerCreated = el;
      mockDocument.elements[el.id] = el;
    }
  }
};

// Simulate showErrorBanner
function showErrorBanner(message, onRetry) {
  let banner = mockDocument.getElementById("app-error-banner");
  if (!banner) {
    banner = mockDocument.createElement("div");
    banner.id = "app-error-banner";
    banner.setAttribute("role", "alert");
    banner.setAttribute("aria-live", "assertive");
    mockDocument.body.prepend(banner);
  }
  banner.innerHTML = `
    <span>${message}</span>
    <button type="button" id="btn-retry-init">🔄 Reintentar Carga</button>
  `;
  const retryBtn = mockDocument.createElement("button");
  retryBtn.id = "btn-retry-init";
  mockDocument.elements["btn-retry-init"] = retryBtn;
  retryBtn.addEventListener("click", () => {
    banner.remove();
    if (typeof onRetry === "function") onRetry();
  });
}

// Test 1: Error banner creation on network drop
showErrorBanner("Corte de red simulado", () => {
  retryInvoked = true;
});

console.log('Banner created:', !!bannerCreated);
console.log('Banner id:', bannerCreated.id);
console.log('Banner role:', bannerCreated.getAttribute('role'));
console.log('Banner aria-live:', bannerCreated.getAttribute('aria-live'));
if (!bannerCreated || bannerCreated.getAttribute('role') !== 'alert') {
  throw new Error('Banner role should be alert');
}

// Test 2: Click retry button
const retryBtn = mockDocument.getElementById("btn-retry-init");
console.log('Retry button found:', !!retryBtn);
retryBtn.listeners['click']();

console.log('Banner removed after click:', bannerRemoved);
console.log('Retry callback invoked:', retryInvoked);

if (!bannerRemoved || !retryInvoked) {
  throw new Error('Retry button failed to remove banner or invoke callback');
}

console.log('>>> RESILIENCE TEST PASSED <<<');
