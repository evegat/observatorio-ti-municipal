import re

with open(r"D:\Proyectos\observatorio-ti-municipal\app.js", encoding="utf-8") as f:
    js = f.read()

with open(r"D:\Proyectos\observatorio-ti-municipal\style.css", encoding="utf-8") as f:
    css = f.read()

classes_in_js = set()
for match in re.finditer(r'class=["\']([^"\']+)["\']', js):
    for c in match.group(1).split():
        # exclude template variables like ${...}
        if "${" in c or "}" in c:
            continue
        classes_in_js.add(c)

missing_classes = []
present_classes = []

for c in sorted(classes_in_js):
    pattern = r'\.' + re.escape(c) + r'[\s\.:,>{\[#]'
    if re.search(pattern, css):
        present_classes.append(c)
    else:
        missing_classes.append(c)

print(f"Total unique static classes in app.js: {len(classes_in_js)}")
print(f"Classes found in CSS: {len(present_classes)}")
print(f"Classes MISSING in CSS: {len(missing_classes)}")
print("\nMissing classes from app.js:")
for c in missing_classes:
    print(f" - {c}")
