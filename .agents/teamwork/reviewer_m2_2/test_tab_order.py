import http.server
import threading
from playwright.sync_api import sync_playwright

PORT = 8995
server = http.server.ThreadingHTTPServer(('127.0.0.1', PORT), http.server.SimpleHTTPRequestHandler)
threading.Thread(target=server.serve_forever, daemon=True).start()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(f'http://127.0.0.1:{PORT}/index.html')
    page.wait_for_timeout(1000)
    print('Before Tab activeElement:', page.evaluate('() => document.activeElement ? document.activeElement.outerHTML.substring(0, 100) : null'))
    
    # Press tab
    page.keyboard.press('Tab')
    print('After 1st Tab activeElement:', page.evaluate('() => document.activeElement ? document.activeElement.outerHTML.substring(0, 100) : null'))

    # Check direct focus on skip-link
    page.locator('a.skip-link').focus()
    page.wait_for_timeout(300)
    print('After direct focus on skip-link:', page.evaluate('() => document.activeElement ? document.activeElement.outerHTML.substring(0, 100) : null'))
    print('Skip link top style:', page.evaluate('() => window.getComputedStyle(document.querySelector(".skip-link")).top'))

    browser.close()
server.shutdown()
