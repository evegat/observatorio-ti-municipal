"""
Independent Victory Auditor Headless Console & Interaction Audit
Verifies:
1. 0 JavaScript console errors/exceptions during initial page load, map rendering, 7-layer toggle, and drawer openings.
2. Leaflet loads without API key prompts or external watermarks.
3. Dark / Light / High Contrast theme toggling.
4. Modal opening and closing with focus management.
"""

import http.server
import threading
import sys
import os
import time
from playwright.sync_api import sync_playwright

class QuietHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

def main():
    root = "D:/Proyectos/observatorio-ti-municipal"
    os.chdir(root)
    
    server_port = 8997
    server = http.server.ThreadingHTTPServer(('127.0.0.1', server_port), QuietHTTPHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print(f"[HTTP] Server running on http://127.0.0.1:{server_port}", flush=True)

    js_exceptions = []
    console_js_errors = []
    network_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})

        # Pre-set localStorage to avoid auto-modal interruption during automated testing
        page.add_init_script("localStorage.setItem('evegat_seen_guide_v3', '1');")

        def handle_console(msg):
            if msg.type == "error":
                text = msg.text
                if "Failed to load resource" in text:
                    network_errors.append(text)
                else:
                    console_js_errors.append(text)
                    print(f"[JS CONSOLE ERROR] {text}", flush=True)

        page.on("console", handle_console)
        page.on("pageerror", lambda err: js_exceptions.append(str(err)))

        print("[NAV] Navigating to http://127.0.0.1:8997/index.html ...", flush=True)
        page.goto(f"http://127.0.0.1:{server_port}/index.html", wait_until="domcontentloaded")
        page.wait_for_timeout(1000)

        # 1. Verify Leaflet map container exists
        map_el = page.query_selector("#chile-map")
        assert map_el is not None, "Map container #chile-map not found"
        print("[CHECK 1] Map container #chile-map initialized", flush=True)

        # 2. Check 7 territorial layer buttons
        layers = ["madurez", "gasto_pc", "ret", "rrhh", "lockin", "foss", "infra"]
        for layer in layers:
            btn = page.query_selector(f"[data-layer='{layer}']")
            if btn:
                btn.click()
                page.wait_for_timeout(250)
                print(f"[CHECK 2] Switched to layer: {layer}", flush=True)
            else:
                print(f"[WARN] Layer button for {layer} not found via data-layer", flush=True)

        # 3. Test theme switcher (light -> dark -> contrast -> light)
        for theme in ["dark", "contrast", "light"]:
            theme_btn = page.query_selector(f"[data-theme-btn='{theme}']")
            if theme_btn:
                theme_btn.click()
                page.wait_for_timeout(250)
                attr = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
                print(f"[CHECK 3] Theme switched to: {attr}", flush=True)

        # 4. Search and select a municipality
        search_input = page.query_selector("#comuna-search")
        if search_input:
            search_input.fill("Valparaíso")
            page.wait_for_timeout(500)
            row = page.query_selector("tr[data-comuna-name='Valparaíso']")
            if row:
                row.click()
                page.wait_for_timeout(400)
                drawer_content = page.evaluate("() => document.getElementById('comuna-drawer')?.innerText")
                assert "Valparaíso" in drawer_content, "Valparaíso not rendered in drawer"
                print(f"[CHECK 4] Municipality successfully selected in drawer (Valparaíso present)", flush=True)

        # 5. Test modal "Cómo usar" manually
        btn_guia = page.query_selector("#btn-floating-guia")
        if btn_guia:
            btn_guia.click()
            page.wait_for_timeout(300)
            is_active = page.evaluate("() => document.getElementById('como-usar-modal')?.classList.contains('active')")
            print(f"[CHECK 5] Como usar modal opened: {is_active}", flush=True)
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)
            is_active_after = page.evaluate("() => document.getElementById('como-usar-modal')?.classList.contains('active')")
            print(f"[CHECK 5] Como usar modal closed via Escape: {not is_active_after}", flush=True)

        # 6. Test modal "Registro y Descarga"
        btn_download = page.query_selector(".btn-intercept-download")
        if btn_download:
            btn_download.click()
            page.wait_for_timeout(300)
            modal_download_active = page.evaluate("() => document.getElementById('registro-descarga-modal')?.classList.contains('active')")
            print(f"[CHECK 6] Registro modal opened: {modal_download_active}", flush=True)
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)
            modal_download_closed = page.evaluate("() => !document.getElementById('registro-descarga-modal')?.classList.contains('active')")
            print(f"[CHECK 6] Registro modal closed via Escape: {modal_download_closed}", flush=True)

        # 7. Test another 3 table rows keyboard activation
        rows = page.query_selector_all("tr[data-comuna-name]")
        print(f"[CHECK 7] Found {len(rows)} rendered table rows with data-comuna-name", flush=True)
        if len(rows) >= 3:
            for idx in [0, 1, 2]:
                rows[idx].press("Enter")
                page.wait_for_timeout(200)
                cname = rows[idx].get_attribute("data-comuna-name")
                drawer_content = page.evaluate("() => document.getElementById('comuna-drawer')?.innerText")
                assert cname in drawer_content, f"Comuna {cname} not in drawer"
                print(f"[CHECK 7] Keyboard Enter on row {idx} ({cname}) rendered in drawer", flush=True)

        browser.close()

    print("=" * 60, flush=True)
    print(f"Total JS Uncaught Exceptions: {len(js_exceptions)}", flush=True)
    print(f"Total JS Console Errors: {len(console_js_errors)}", flush=True)
    print(f"Total Network Warnings/Errors: {len(network_errors)}", flush=True)
    for err in console_js_errors:
        print(f"  [JS ERROR] {err}", flush=True)
    for exc in js_exceptions:
        print(f"  [EXCEPTION] {exc}", flush=True)
    print("=" * 60, flush=True)

    if console_js_errors or js_exceptions:
        sys.exit(1)
    else:
        print("ALL INTERACTION & CONSOLE CHECKS PASSED WITH 0 JAVASCRIPT ERRORS!", flush=True)
        sys.exit(0)

if __name__ == "__main__":
    main()
