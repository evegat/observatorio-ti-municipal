import os
import http.server
import threading
from playwright.sync_api import sync_playwright

PORT = 8997
server = http.server.ThreadingHTTPServer(('127.0.0.1', PORT), http.server.SimpleHTTPRequestHandler)
threading.Thread(target=server.serve_forever, daemon=True).start()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(f"http://127.0.0.1:{PORT}/index.html")
    page.wait_for_timeout(1500)

    # Set seen guide in localStorage of this origin
    page.evaluate("() => localStorage.setItem('evegat_seen_guide_v3', '1')")
    
    # Close any open modal
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    # Open legal modal
    legal_btn = page.locator("#btn-open-legal-top")
    legal_btn.click()
    page.wait_for_timeout(300)

    print("Modal opened. Active element immediately after open:", page.evaluate("() => document.activeElement.outerHTML.substring(0, 80)"))

    for i in range(6):
        page.keyboard.press("Tab")
        active_html = page.evaluate("() => document.activeElement ? document.activeElement.outerHTML.substring(0, 80) : 'null'")
        is_inside = page.evaluate("() => document.querySelector('#legal-modal .obs-modal-card').contains(document.activeElement)")
        print(f"Tab {i+1}: is_inside={is_inside} | activeElement={active_html}")

    browser.close()
server.shutdown()
