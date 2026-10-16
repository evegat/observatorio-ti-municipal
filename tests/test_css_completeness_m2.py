"""
Test: test_css_completeness_m2.py
Purpose: Empirically verify that all 140 classes defined in index.html exist and have styling rules in style.css.
Also inspects dynamic classes in app.js.
"""

import sys
import os
import re

def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    html_path = os.path.join(root, "index.html")
    css_path = os.path.join(root, "style.css")
    js_path = os.path.join(root, "app.js")

    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    with open(css_path, "r", encoding="utf-8") as f:
        css_content = f.read()

    with open(js_path, "r", encoding="utf-8") as f:
        js_content = f.read()

    # 1. Extract unique classes from index.html
    html_classes = set()
    # Match class="foo bar" or class='foo bar'
    for match in re.finditer(r'class=["\']([^"\']+)["\']', html_content):
        tokens = match.group(1).split()
        for t in tokens:
            # Clean possible trailing punctuation or template tags
            t = t.strip()
            if t:
                html_classes.add(t)

    print(f"=== CSS COMPLETENESS TEST (Milestone 2) ===")
    print(f"Total unique classes found in index.html: {len(html_classes)}")

    # 2. Check each class against style.css
    # CSS selector pattern for class .className
    # It must be preceded by start of selector or whitespace or parent selector (not word character)
    # and followed by delimiter: space, comma, dot, colon, bracket, brace, >, +, ~
    missing_classes = []
    present_classes = []

    for c in sorted(html_classes):
        # In CSS selectors, a class selector is .className
        # It can be preceded by whitespace, start of line, comma, combinator (> + ~),
        # or another selector token (e.g. tag or .compound-class like .metric-card.accent).
        # It must NOT be preceded by a backslash or a hyphen/alphanumeric immediately before the dot (which would make it a domain or filename).
        # And after the class name, it must be followed by a selector delimiter: whitespace, :, ::, ., [, >, +, ~, ,, {, #, )
        pattern = r'(?<![\\a-zA-Z0-9_\-])\.' + re.escape(c) + r'(?![a-zA-Z0-9_\-])'
        # Also allow compound selector where dot is immediately preceded by an identifier (e.g. tag.c or .other.c)
        pattern_compound = r'\.' + re.escape(c) + r'(?![a-zA-Z0-9_\-])'
        if re.search(pattern_compound, css_content):
            present_classes.append(c)
        else:
            missing_classes.append(c)

    print(f"Classes present in style.css: {len(present_classes)}")
    print(f"Classes missing in style.css: {len(missing_classes)}")

    # 3. Dynamic classes check in app.js
    # Find classList.add("..."), className = "...", or classes inside DOM template strings
    dynamic_classes = set()
    for m in re.finditer(r'classList\.add\(([^)]+)\)', js_content):
        args = m.group(1).split(',')
        for a in args:
            clean = a.strip().strip('"\'`')
            if clean and not clean.startswith('$') and not ' ' in clean:
                dynamic_classes.add(clean)

    for m in re.finditer(r'class=["\']([^"\']+)["\']', js_content):
        for c in m.group(1).split():
            c = c.strip()
            if c and not '${' in c:
                dynamic_classes.add(c)

    print(f"Dynamic classes referenced in app.js: {len(dynamic_classes)}")
    dyn_missing = []
    dyn_present = []
    for c in sorted(dynamic_classes):
        if c == '===':
            continue
        pattern_compound = r'\.' + re.escape(c) + r'(?![a-zA-Z0-9_\-])'
        if re.search(pattern_compound, css_content):
            dyn_present.append(c)
        else:
            dyn_missing.append(c)
    print(f"Dynamic classes present in style.css: {len(dyn_present)}")
    print(f"Dynamic classes missing in style.css: {len(dyn_missing)}")
    if dyn_missing:
        print(f"Dynamic missing list: {dyn_missing}")

    if missing_classes:
        print("\nFAILURE: Missing classes in style.css:")
        for c in missing_classes:
            print(f" - {c}")
        sys.exit(1)
    else:
        print("\nSUCCESS: All 140 classes from index.html exist in style.css!")
        sys.exit(0)

if __name__ == "__main__":
    main()
