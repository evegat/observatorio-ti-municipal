"""
Test: test_responsive_layout_m2.py
Purpose: Empirically stress-test responsive layout and media queries across mobile, tablet, and desktop viewports:
- Mobile: 360px, 480px, 640px (target)
- Tablet: 768px, 860px (target), 900px (target)
- Desktop: 1024px, 1280px, 1400px (target)

Evaluates:
1. Document level horizontal scroll: doc_scroll_w <= inner_w
2. Element level overflow: detects elements spilling beyond window boundary (excluding Leaflet transformed canvas)
3. Media query visibility rules: .a11y-hide-sm (<=640px) and .a11y-hide-md (<=860px)
4. Interactive modal cards fitting within viewport
5. Clipped text detection on buttons and headers
"""

import sys
import os
import http.server
import threading
import time
from playwright.sync_api import sync_playwright

class QuietHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

def run_responsive_tests():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)

    server_port = 8899
    server = http.server.ThreadingHTTPServer(('127.0.0.1', server_port), QuietHTTPHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    viewports = [
        {"name": "Mobile Small (360px)", "width": 360, "height": 740, "is_target": False},
        {"name": "Mobile Standard (480px)", "width": 480, "height": 800, "is_target": False},
        {"name": "Mobile Breakpoint (640px)", "width": 640, "height": 900, "is_target": True},
        {"name": "Tablet Portrait (768px)", "width": 768, "height": 1024, "is_target": False},
        {"name": "Tablet A11y Breakpoint (860px)", "width": 860, "height": 1024, "is_target": True},
        {"name": "Tablet Podiums Breakpoint (900px)", "width": 900, "height": 900, "is_target": True},
        {"name": "Desktop Small / Stage (1024px)", "width": 1024, "height": 800, "is_target": False},
        {"name": "Desktop Standard (1280px)", "width": 1280, "height": 900, "is_target": False},
        {"name": "Desktop Large (1400px)", "width": 1400, "height": 900, "is_target": True},
    ]

    results = []

    print("=" * 90)
    print("RESPONSIVE LAYOUT & MEDIA QUERY EMPIRICAL STRESS TEST (Milestone 2)")
    print("=" * 90)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)

        for vp in viewports:
            page = browser.new_page(viewport={"width": vp["width"], "height": vp["height"]})
            page.goto(f"http://127.0.0.1:{server_port}/index.html")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(400)

            doc_scroll_w = page.evaluate("document.documentElement.scrollWidth")
            body_scroll_w = page.evaluate("document.body.scrollWidth")
            inner_w = page.evaluate("window.innerWidth")

            has_doc_overflow = (doc_scroll_w > inner_w + 1) or (body_scroll_w > inner_w + 1)
            overflow_diff = max(doc_scroll_w - inner_w, body_scroll_w - inner_w, 0)

            # Detect DOM elements overflowing outside the window boundary
            # Ignore Leaflet internal map layers which are clipped by #chile-map overflow:hidden
            overflowing_elements = page.evaluate("""() => {
                const innerW = window.innerWidth;
                const badEls = [];
                const all = document.querySelectorAll('header, nav, section, footer, div, table, h1, h2, h3, p');
                all.forEach(el => {
                    if (el.classList.contains('skip-link') || el.closest('.skip-link')) return;
                    if (el.closest('.leaflet-container')) return; // Clipped by leaflet-container overflow:hidden
                    if (el.closest('.obs-modal-backdrop') && !el.closest('.obs-modal-backdrop.active')) return;
                    // Skip elements inside a designated scroll container (e.g. .table-responsive)
                    const scrollParent = el.parentElement ? window.getComputedStyle(el.parentElement).overflowX : '';
                    if (scrollParent === 'auto' || scrollParent === 'scroll' || el.closest('.table-responsive') || el.closest('.nav-links')) return;
                    const style = window.getComputedStyle(el);
                    if (style.display === 'none' || style.visibility === 'hidden' || parseFloat(style.opacity) === 0) return;
                    const rect = el.getBoundingClientRect();
                    if (rect.right > innerW + 2) {
                        badEls.push({
                            tag: el.tagName.toLowerCase(),
                            className: el.className,
                            id: el.id,
                            rectRight: Math.round(rect.right),
                            overflow: Math.round(rect.right - innerW)
                        });
                    }
                });
                return badEls.slice(0, 5);
            }""")

            # Check media query hide classes behavior
            sm_check_pass = True
            if vp["width"] <= 640:
                sm_visible = page.evaluate("() => { const el = document.querySelector('.a11y-hide-sm'); return el ? window.getComputedStyle(el).display : 'none'; }")
                sm_check_pass = (sm_visible == "none")

            md_check_pass = True
            if vp["width"] <= 860:
                md_visible = page.evaluate("() => { const el = document.querySelector('.a11y-hide-md'); return el ? window.getComputedStyle(el).display : 'none'; }")
                md_check_pass = (md_visible == "none")

            # Modal card fit test
            page.evaluate("() => { const m = document.getElementById('modal-como-usar'); if (m) m.classList.add('active'); }")
            page.wait_for_timeout(150)
            modal_fits = page.evaluate("""() => {
                const card = document.querySelector('#modal-como-usar .obs-modal-card');
                if (!card) return { widthFits: true, heightFits: true, width: 0, height: 0 };
                const rect = card.getBoundingClientRect();
                return {
                    widthFits: rect.width <= window.innerWidth,
                    heightFits: rect.height <= window.innerHeight,
                    width: Math.round(rect.width),
                    height: Math.round(rect.height)
                };
            }""")
            page.evaluate("() => { const m = document.getElementById('modal-como-usar'); if (m) m.classList.remove('active'); }")

            # Clipped text check on buttons and headings
            clipped_text = page.evaluate("""() => {
                const clipped = [];
                document.querySelectorAll('button, h1, h2, h3, .btn-pill, .btn-hero-primary').forEach(el => {
                    const style = window.getComputedStyle(el);
                    if (style.display === 'none' || style.visibility === 'hidden') return;
                    if (el.scrollWidth > el.clientWidth + 2 && style.overflow === 'hidden') {
                        clipped.push({ tag: el.tagName, text: el.innerText.slice(0, 30) });
                    }
                });
                return clipped;
            }""")

            passed = (not has_doc_overflow and len(overflowing_elements) == 0 and sm_check_pass and md_check_pass and modal_fits["widthFits"] and modal_fits["heightFits"] and len(clipped_text) == 0)

            results.append({
                "viewport": vp["name"],
                "width": vp["width"],
                "doc_scroll_w": doc_scroll_w,
                "inner_w": inner_w,
                "overflow_diff": overflow_diff,
                "status": "PASS" if passed else "FAIL",
                "is_target": vp["is_target"],
                "overflowing_elements": overflowing_elements,
                "sm_check": sm_check_pass,
                "md_check": md_check_pass,
                "modal_fits": modal_fits,
                "clipped_text": clipped_text
            })

            page.close()

        browser.close()

    server.shutdown()

    # Report table
    print(f"{'Viewport':<36} | {'Target?':<7} | {'Width':<7} | {'ScrollW':<8} | {'Overflow':<10} | {'Status'}")
    print("-" * 90)
    target_failures = 0
    boundary_failures = 0

    for r in results:
        target_str = "YES" if r['is_target'] else "no"
        diff_str = f"{r['overflow_diff']}px" if r['overflow_diff'] > 0 else "0px"
        print(f"{r['viewport']:<36} | {target_str:<7} | {r['width']:>5}px | {r['doc_scroll_w']:>6}px | {diff_str:>10} | {r['status']}")
        if r['status'] == "FAIL":
            if r['is_target']:
                target_failures += 1
            else:
                boundary_failures += 1
            if r['overflow_diff'] > 0:
                print(f"   -> Window horizontal overflow: scrollWidth ({r['doc_scroll_w']}px) > innerWidth ({r['inner_w']}px)")
            if r['overflowing_elements']:
                print(f"   -> Elements spilling: {r['overflowing_elements']}")
            if not r['sm_check']:
                print("   -> .a11y-hide-sm is NOT hidden at <= 640px")
            if not r['md_check']:
                print("   -> .a11y-hide-md is NOT hidden at <= 860px")
            if not r['modal_fits']['widthFits'] or not r['modal_fits']['heightFits']:
                print(f"   -> Modal card overflow: {r['modal_fits']}")
            if r['clipped_text']:
                print(f"   -> Clipped text: {r['clipped_text']}")

    print("-" * 90)
    print(f"Target Breakpoints Tested (640px, 860px, 900px, 1400px): {sum(1 for r in results if r['is_target'])}")
    print(f"Target Breakpoints Failed: {target_failures}")
    print(f"Boundary Viewports Failed (< 640px): {boundary_failures}")

    if target_failures > 0 or boundary_failures > 0:
        return False
    return True

if __name__ == "__main__":
    success = run_responsive_tests()
    if not success:
        sys.exit(1)
    sys.exit(0)
