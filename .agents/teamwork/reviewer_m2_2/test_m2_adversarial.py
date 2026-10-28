import sys
import os
import time
import http.server
import threading
from playwright.sync_api import sync_playwright

def run_tests():
    PORT = 8993
    os.chdir(r"D:\Proyectos\observatorio-ti-municipal")
    server = http.server.ThreadingHTTPServer(('127.0.0.1', PORT), http.server.SimpleHTTPRequestHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    results = []
    console_errors = []

    def log_result(name, passed, detail=""):
        status = "PASS" if passed else "FAIL"
        results.append((name, passed, detail))
        print(f"[{status}] {name} - {detail}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Listen for console errors (ignoring analytics/telemetry network blocks)
        def handle_console(msg):
            if msg.type == "error":
                text = msg.text
                if "analytics.evegat.cl" not in text and "400" not in text:
                    console_errors.append(text)
        page.on("console", handle_console)
        page.on("pageerror", lambda err: console_errors.append(str(err)))

        print(f"Navigating to http://127.0.0.1:{PORT}/index.html...")
        page.goto(f"http://127.0.0.1:{PORT}/index.html")
        page.wait_for_timeout(800)

        # Set localStorage on origin so auto-open guide does not interrupt keyboard tests
        page.evaluate("() => localStorage.setItem('evegat_seen_guide_v3', '1')")
        page.goto(f"http://127.0.0.1:{PORT}/index.html")
        page.wait_for_timeout(1000)

        # ---------------------------------------------------------------------
        # TEST 1: Skip-link & Landmarks
        # ---------------------------------------------------------------------
        skip_link = page.locator("a.skip-link")
        log_result("Skip-link exists", skip_link.count() == 1, f"Found {skip_link.count()}")
        
        href = skip_link.get_attribute("href")
        log_result("Skip-link points to #main-content", href == "#main-content", f"href='{href}'")

        # Focus skip-link via keyboard Tab from document start
        page.keyboard.press("Tab")
        page.wait_for_timeout(350)
        is_focused = page.evaluate("() => document.activeElement === document.querySelector('.skip-link')")
        log_result("Skip-link receives first Tab focus", is_focused, f"activeElement tag={page.evaluate('() => document.activeElement.tagName')}, class={page.evaluate('() => document.activeElement.className')}")

        skip_top = page.evaluate("() => parseInt(window.getComputedStyle(document.querySelector('.skip-link')).top, 10)")
        log_result("Skip-link becomes visible when focused", skip_top >= 0, f"top={skip_top}px")

        # Check landmarks
        main_el = page.locator("main#main-content")
        log_result("Main landmark exists with id 'main-content'", main_el.count() == 1, f"Found {main_el.count()}")
        tabindex = main_el.get_attribute("tabindex")
        log_result("Main landmark has tabindex='-1'", tabindex == "-1", f"tabindex='{tabindex}'")

        header_el = page.locator("header.topbar")
        footer_el = page.locator("footer.site-footer")
        log_result("Header landmark exists", header_el.count() == 1, f"Found {header_el.count()}")
        log_result("Footer landmark exists", footer_el.count() == 1, f"Found {footer_el.count()}")

        # ---------------------------------------------------------------------
        # TEST 2: Modal Focus Trap & Restoration
        # ---------------------------------------------------------------------
        legal_btn = page.locator("#btn-open-legal-top")
        legal_btn.focus()
        page.keyboard.press("Enter")
        page.wait_for_timeout(300)

        legal_modal = page.locator("#legal-modal")
        is_legal_active = legal_modal.evaluate("el => el.classList.contains('active')")
        log_result("Legal modal opens on Enter key", is_legal_active, f"active={is_legal_active}")

        in_modal = page.evaluate("() => document.querySelector('#legal-modal .obs-modal-card').contains(document.activeElement)")
        log_result("Focus transferred inside legal modal card", in_modal, f"activeElement: {page.evaluate('() => document.activeElement.className')}")

        # Check Tab cycle forward inside modal card
        focusables_count = page.evaluate("""() => {
            const card = document.querySelector('#legal-modal .obs-modal-card');
            return Array.from(card.querySelectorAll('a[href], button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])')).length;
        }""")
        for _ in range(focusables_count + 2):
            page.keyboard.press("Tab")
            trapped = page.evaluate("() => document.querySelector('#legal-modal .obs-modal-card').contains(document.activeElement)")
            if not trapped:
                log_result("Focus trapped during forward Tab", False, "Focus escaped modal card")
                break
        else:
            log_result("Focus trapped during forward Tab", True, f"Cycled through {focusables_count} elements successfully")

        # Check Shift+Tab backward cycle
        page.keyboard.press("Shift+Tab")
        trapped_back = page.evaluate("() => document.querySelector('#legal-modal .obs-modal-card').contains(document.activeElement)")
        log_result("Focus trapped during Shift+Tab backward cycle", trapped_back, "Focus remained inside modal card")

        # Test Escape key closes modal and restores focus
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        is_closed = not legal_modal.evaluate("el => el.classList.contains('active')")
        log_result("Legal modal closes on Escape key", is_closed, f"active={not is_closed}")

        restored_focus = page.evaluate("() => document.activeElement.id === 'btn-open-legal-top'")
        log_result("Focus restored to trigger element (#btn-open-legal-top)", restored_focus, f"activeElement.id={page.evaluate('() => document.activeElement.id')}")

        # Test Download intercept modal
        download_btn = page.locator(".btn-intercept-download").first
        download_btn.focus()
        page.keyboard.press("Enter")
        page.wait_for_timeout(300)

        reg_modal = page.locator("#registro-descarga-modal")
        is_reg_active = reg_modal.evaluate("el => el.classList.contains('active')")
        log_result("Download intercept modal opens on Enter", is_reg_active, f"active={is_reg_active}")

        active_input = page.evaluate("() => document.activeElement.id")
        log_result("Focus placed on first interactive input in registration modal", active_input in ["reg-nombre", "reg-close"], f"Focused element: {active_input}")

        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        restored_dl_focus = page.evaluate("() => document.activeElement.classList.contains('btn-intercept-download')")
        log_result("Focus restored to download button on Escape", restored_dl_focus, f"activeElement class: {page.evaluate('() => document.activeElement.className')}")

        # ---------------------------------------------------------------------
        # TEST 3: Theme Synchronization & Basemap Swap
        # ---------------------------------------------------------------------
        btn_dark = page.locator("button[data-theme-btn='dark']")
        btn_dark.click()
        page.wait_for_timeout(400)

        theme_attr = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
        log_result("Dark theme attribute set on root", theme_attr == "dark", f"data-theme='{theme_attr}'")

        map_bg = page.evaluate("() => window.getComputedStyle(document.getElementById('chile-map')).backgroundColor")
        log_result("Chile map container background is dark (#04142b)", map_bg in ["rgb(4, 20, 43)", "#04142b"], f"bg={map_bg}")

        dark_tiles_present = page.evaluate("""() => {
            const tiles = Array.from(document.querySelectorAll('#chile-map img.leaflet-tile'));
            return tiles.some(img => img.src.includes('World_Dark_Gray'));
        }""")
        log_result("Leaflet loads Esri World_Dark_Gray tiles in dark mode", dark_tiles_present, f"found dark tiles={dark_tiles_present}")

        # Switch to contrast theme
        btn_contrast = page.locator("button[data-theme-btn='contrast']")
        btn_contrast.click()
        page.wait_for_timeout(400)

        theme_contrast = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
        log_result("Contrast theme attribute set on root", theme_contrast == "contrast", f"data-theme='{theme_contrast}'")

        map_contrast_bg = page.evaluate("() => window.getComputedStyle(document.getElementById('chile-map')).backgroundColor")
        log_result("Chile map container background is black in contrast theme", map_contrast_bg in ["rgb(0, 0, 0)", "#000000"], f"bg={map_contrast_bg}")

        dark_tiles_in_contrast = page.evaluate("""() => {
            const tiles = Array.from(document.querySelectorAll('#chile-map img.leaflet-tile'));
            return tiles.some(img => img.src.includes('World_Dark_Gray'));
        }""")
        log_result("Leaflet maintains Esri World_Dark_Gray tiles in contrast mode", dark_tiles_in_contrast, f"found dark tiles={dark_tiles_in_contrast}")

        # Switch back to light theme
        btn_light = page.locator("button[data-theme-btn='light']")
        btn_light.click()
        page.wait_for_timeout(400)

        theme_light = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
        log_result("Light theme attribute restored", theme_light == "light", f"data-theme='{theme_light}'")

        light_tiles_present = page.evaluate("""() => {
            const tiles = Array.from(document.querySelectorAll('#chile-map img.leaflet-tile'));
            return tiles.some(img => img.src.includes('World_Light_Gray'));
        }""")
        log_result("Leaflet loads Esri World_Light_Gray tiles in light mode", light_tiles_present, f"found light tiles={light_tiles_present}")

        # ---------------------------------------------------------------------
        # TEST 4: Table Keyboard Sorting & Selection
        # ---------------------------------------------------------------------
        # Sortable th elements
        sort_th = page.locator("#ranking-table th[data-sort='gasto_pc']")
        sort_th.focus()

        # Press Enter to sort
        page.keyboard.press("Enter")
        page.wait_for_timeout(300)

        new_aria_sort = sort_th.get_attribute("aria-sort")
        log_result("Table header responds to Enter and sets aria-sort", new_aria_sort in ["ascending", "descending"], f"aria-sort={new_aria_sort}")

        # Press Space to reverse sort
        page.keyboard.press("Space")
        page.wait_for_timeout(300)
        reversed_aria_sort = sort_th.get_attribute("aria-sort")
        log_result("Table header responds to Space and flips aria-sort", reversed_aria_sort != new_aria_sort and reversed_aria_sort in ["ascending", "descending"], f"prev={new_aria_sort}, new={reversed_aria_sort}")

        # Non-active th aria-sort
        comuna_th = page.locator("#ranking-table th[data-sort='comuna']")
        log_result("Non-active th has aria-sort='none'", comuna_th.get_attribute("aria-sort") == "none", f"comuna aria-sort={comuna_th.get_attribute('aria-sort')}")

        # Row selection via keyboard Enter
        first_row = page.locator("#ranking-tbody tr").first
        first_row_name = first_row.get_attribute("data-comuna-name")
        first_row.focus()
        page.keyboard.press("Enter")
        page.wait_for_timeout(400)

        # Check drawer title reflects the selected commune (.drawer-comuna-name)
        drawer_title = page.locator(".drawer-comuna-name").inner_text()
        log_result("Pressing Enter on table row opens drawer with commune data", drawer_title.strip() == first_row_name.strip(), f"drawer title='{drawer_title}', row='{first_row_name}'")

        # ---------------------------------------------------------------------
        # TEST 5: Dynamic SVG Gauge Readability Across Themes
        # ---------------------------------------------------------------------
        gauge_score_text = page.locator(".drawer-thermometer-box .gauge-svg text").first
        text_fill = gauge_score_text.get_attribute("fill")
        log_result("Gauge score text fill is 'currentColor'", text_fill == "currentColor", f"fill='{text_fill}'")

        # Light theme computed fill
        btn_light.click()
        page.wait_for_timeout(300)
        light_color = page.evaluate("() => window.getComputedStyle(document.querySelector('.drawer-thermometer-box .gauge-svg text')).fill")
        log_result("Gauge text computed fill in light theme is ink (#14171a)", light_color in ["rgb(20, 23, 26)", "#14171a"], f"fill={light_color}")

        # Dark theme computed fill
        btn_dark.click()
        page.wait_for_timeout(300)
        dark_color = page.evaluate("() => window.getComputedStyle(document.querySelector('.drawer-thermometer-box .gauge-svg text')).fill")
        log_result("Gauge text computed fill in dark theme is light (#f8fafc)", dark_color in ["rgb(248, 250, 252)", "#f8fafc"], f"fill={dark_color}")

        # Contrast theme computed fill
        btn_contrast.click()
        page.wait_for_timeout(300)
        contrast_color = page.evaluate("() => window.getComputedStyle(document.querySelector('.drawer-thermometer-box .gauge-svg text')).fill")
        log_result("Gauge text computed fill in contrast theme is white (#ffffff)", contrast_color in ["rgb(255, 255, 255)", "#ffffff"], f"fill={contrast_color}")

        # ---------------------------------------------------------------------
        # TEST 6: Initial Load in Contrast Theme Edge Case
        # ---------------------------------------------------------------------
        context2 = browser.new_context()
        page2 = context2.new_page()
        page2.goto(f"http://127.0.0.1:{PORT}/index.html")
        page2.wait_for_timeout(500)
        page2.evaluate("() => { localStorage.setItem('evegat_seen_guide_v3', '1'); localStorage.setItem('evegat_theme', 'contrast'); }")
        page2.goto(f"http://127.0.0.1:{PORT}/index.html")
        page2.wait_for_timeout(1500)

        init_contrast_root = page2.evaluate("() => document.documentElement.getAttribute('data-theme')")
        init_dark_tiles = page2.evaluate("""() => {
            const tiles = Array.from(document.querySelectorAll('#chile-map img.leaflet-tile'));
            return tiles.some(img => img.src.includes('World_Dark_Gray'));
        }""")
        init_light_tiles = page2.evaluate("""() => {
            const tiles = Array.from(document.querySelectorAll('#chile-map img.leaflet-tile'));
            return tiles.some(img => img.src.includes('World_Light_Gray'));
        }""")

        log_result("Initial reload in contrast theme sets data-theme='contrast'", init_contrast_root == "contrast", f"data-theme={init_contrast_root}")
        log_result("Initial reload in contrast theme loads dark basemap tiles (Edge Case Check)", init_dark_tiles and not init_light_tiles, f"dark_tiles={init_dark_tiles}, light_tiles={init_light_tiles}")

        # ---------------------------------------------------------------------
        # SUMMARY & CONSOLE ERRORS
        # ---------------------------------------------------------------------
        print("\n=================================================================")
        print("PLAYWRIGHT REAL-BROWSER TEST SUMMARY")
        print("=================================================================")
        pass_count = sum(1 for _, p, _ in results if p)
        fail_count = sum(1 for _, p, _ in results if not p)
        print(f"Total Tests: {len(results)} | Passed: {pass_count} | Failed: {fail_count}")

        if console_errors:
            print("\nCaptured Console Errors:")
            for err in console_errors:
                print(f"  - {err}")
        else:
            print("\nZero console errors captured.")

        browser.close()
        server.shutdown()

if __name__ == "__main__":
    run_tests()
