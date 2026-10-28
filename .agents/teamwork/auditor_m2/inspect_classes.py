import re
import os

with open(r"D:\Proyectos\observatorio-ti-municipal\index.html", encoding="utf-8") as f:
    html = f.read()

with open(r"D:\Proyectos\observatorio-ti-municipal\style.css", encoding="utf-8") as f:
    css = f.read()

classes = set()
for m in re.finditer(r'class=["\']([^"\']+)["\']', html):
    for c in m.group(1).split():
        classes.add(c)

print(f"Total classes in index.html: {len(classes)}")

# Let's inspect each class in CSS:
# Look for regex pattern: r'\.' + re.escape(c) + r'[\s\.:,>{\[#]'
results = []
for c in sorted(classes):
    pattern = r'\.' + re.escape(c) + r'[\s\.:,>{\[#]'
    found = bool(re.search(pattern, css))
    # extract rule body if found
    body = ""
    if found:
        # find matching block
        rule_pat = r'([^{}]*?\.' + re.escape(c) + r'[^{}]*?)\{([^}]*)\}'
        matches = re.findall(rule_pat, css)
        if matches:
            body = "; ".join([p.strip() for p in matches[0][1].split(";") if p.strip()][:3])
    results.append((c, found, body))

print("\n--- Classes summary ---")
missing = [c for c, found, _ in results if not found]
print(f"Missing count: {len(missing)}")
if missing:
    print("Missing classes:", missing)

# Check classes with empty bodies
no_body = [c for c, found, body in results if found and not body]
print(f"Found without direct body extraction (e.g. nested or multi-selector): {len(no_body)}")
for c in no_body:
    print(f"  {c}")

# Let's check git diff of style.css to see what classes were newly added or modified in style.css
import subprocess
diff = subprocess.check_output(["git", "diff", "HEAD", "--", "style.css"], cwd=r"D:\Proyectos\observatorio-ti-municipal", encoding="utf-8")
print(f"\nGit diff style.css total characters: {len(diff)}")
