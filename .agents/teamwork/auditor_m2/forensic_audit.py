"""
Forensic Audit Suite for Milestone 2 - Observatorio TI Municipal
"""
import subprocess
import re
import os
import sys

PROJECT_DIR = r"D:\Proyectos\observatorio-ti-municipal"

def check_url_and_trackers():
    print("=== CHECK 1: URL and External Trackers in Git Diff ===")
    files = ["index.html", "app.js", "style.css"]
    all_urls = {}
    for f in files:
        out = subprocess.check_output(["git", "diff", "HEAD", "--", f], cwd=PROJECT_DIR, encoding="utf-8")
        added = [line[1:] for line in out.splitlines() if line.startswith("+") and not line.startswith("+++")]
        found = []
        for line in added:
            m = re.findall(r"https?://[^\s\"\'\)\>]+", line)
            if m:
                found.extend(m)
        all_urls[f] = list(set(found))
    
    clean = True
    for f, urls in all_urls.items():
        print(f"File: {f}")
        for u in urls:
            print(f"  Found URL: {u}")
            # Check against authorized endpoints
            # Authorized: https://brujulaiaedusuperior.evegat.cl/api/register-download
            # esri/leaflet tile URLs if any
            if "brujulaiaedusuperior.evegat.cl" in u:
                print(f"    -> [AUTHORIZED] Official API endpoint for download registration")
            elif "evegat.cl" in u:
                print(f"    -> [AUTHORIZED] Internal evegat.cl domain")
            elif "server.arcgisonline.com" in u:
                print(f"    -> [AUTHORIZED] Esri basemap service")
            else:
                print(f"    -> [FLAG] Unexpected external URL!")
                clean = False
        if not urls:
            print("  No new URLs added.")
    return clean

def audit_classes_authenticity():
    print("\n=== CHECK 2: All 140 CSS Classes in index.html Genuinely Styled ===")
    with open(os.path.join(PROJECT_DIR, "index.html"), encoding="utf-8") as f:
        html = f.read()
    
    classes_html = set()
    for m in re.finditer(r'class="([^"]+)"', html):
        for c in m.group(1).split():
            c = c.strip()
            if c:
                classes_html.add(c)
                
    print(f"Total unique classes in index.html: {len(classes_html)}")
    
    with open(os.path.join(PROJECT_DIR, "style.css"), encoding="utf-8") as f:
        css = f.read()

    # Strip comments from CSS
    css_no_comments = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
    
    missing = []
    dummy_or_empty = []
    genuine = []

    for c in sorted(classes_html):
        # Match selector like .classname, .classname:hover, etc.
        # regex for class selector
        pattern = r'(?:^|[,\s\}\{>+~])\.' + re.escape(c) + r'(?:[,\s\}\{>+~:\.\[]|$)'
        matches = list(re.finditer(pattern, css_no_comments))
        if not matches:
            # Also check if part of complex selector or exact class rule
            if f".{c}" not in css_no_comments:
                missing.append(c)
                continue
        
        # Let's verify rule body is not empty {} or just comments
        # Find where .{c} appears and get its enclosing or following block {...}
        # We can extract all CSS rules
        class_regex = r'\.' + re.escape(c) + r'[\s\w\-\:\,\.\#\[\]\=\>+~]*\{([^}]*)\}'
        rule_matches = re.findall(class_regex, css_no_comments)
        
        has_real_decl = False
        for body in rule_matches:
            body_clean = body.strip()
            # check if body has real CSS properties (not empty, not just a comment)
            props = [p.strip() for p in body_clean.split(';') if p.strip()]
            if len(props) > 0:
                has_real_decl = True
                break
                
        if not rule_matches and f".{c}" in css_no_comments:
            # might be in multi-selector e.g. .a, .b { ... }
            # Let's search broadly for rule containing .{c}
            multi_regex = r'([^{}]*?\.' + re.escape(c) + r'[^{}]*?)\{([^}]*)\}'
            for m_sel, m_body in re.findall(multi_regex, css_no_comments):
                if len([p.strip() for p in m_body.strip().split(';') if p.strip()]) > 0:
                    has_real_decl = True
                    break

        if has_real_decl:
            genuine.append(c)
        else:
            if c in missing:
                pass
            else:
                dummy_or_empty.append(c)

    print(f"Genuine styled classes: {len(genuine)}")
    print(f"Missing classes: {len(missing)} -> {missing}")
    print(f"Dummy/empty classes: {len(dummy_or_empty)} -> {dummy_or_empty}")
    
    clean = (len(missing) == 0 and len(dummy_or_empty) == 0)
    return clean, len(classes_html), genuine, missing, dummy_or_empty

def audit_contrast_math():
    print("\n=== CHECK 3: WCAG 2.1 AA Contrast Ratios Verification ===")
    def lum(h):
        rgb = [int(h.lstrip('#')[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
        rgb = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
        return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]

    def ratio(c1, c2):
        l1, l2 = lum(c1), lum(c2)
        return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)

    pairs = [
        ("--muted on --paper (light)", "#556265", "#faf8f5", 4.5),
        ("--muted on --paper-soft (light)", "#556265", "#f4efe6", 4.5),
        ("--gold-text on --paper (light)", "#875f00", "#faf8f5", 4.5),
        ("--gold-text on --gold-bg (light)", "#875f00", "#fbf4e4", 4.5),
        (":focus-visible ring light", "#002b49", "#faf8f5", 3.0),
        (":focus-visible ring dark", "#38bdf8", "#04142b", 3.0),
        (":focus-visible ring contrast", "#ffff00", "#000000", 3.0),
        ("Dark mode input text", "#f8fafc", "#071f43", 4.5),
        ("Dark mode table th", "#38bdf8", "#071f43", 4.5),
        ("Dark mode table hover td", "#f8fafc", "#0d3166", 4.5),
        ("Contrast mode text", "#ffffff", "#000000", 4.5),
        ("Contrast mode yellow text", "#ffff00", "#000000", 4.5),
    ]

    all_pass = True
    for name, c1, c2, threshold in pairs:
        r = ratio(c1, c2)
        passed = r >= threshold
        if not passed:
            all_pass = False
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {name}: {c1} on {c2} -> {r:.2f}:1 (Target >= {threshold}:1)")
        
    return all_pass

if __name__ == "__main__":
    c1 = check_url_and_trackers()
    c2, total_cls, genuine, missing, dummy = audit_classes_authenticity()
    c3 = audit_contrast_math()
    print(f"\nAudit Summary: URLs/Trackers={c1}, Classes={c2}, Contrast={c3}")
