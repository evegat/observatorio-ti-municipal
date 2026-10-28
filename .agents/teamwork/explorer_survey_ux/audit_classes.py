import re

with open(r"D:\Proyectos\observatorio-ti-municipal\index.html", encoding="utf-8") as f:
    html = f.read()

with open(r"D:\Proyectos\observatorio-ti-municipal\style.css", encoding="utf-8") as f:
    css = f.read()

classes_in_html = set()
for match in re.finditer(r'class=["\']([^"\']+)["\']', html):
    for c in match.group(1).split():
        classes_in_html.add(c)

missing_classes = []
present_classes = []

for c in sorted(classes_in_html):
    pattern = r'\.' + re.escape(c) + r'[\s\.:,>{\[#]'
    if re.search(pattern, css):
        present_classes.append(c)
    else:
        missing_classes.append(c)

print(f"Total unique classes in index.html: {len(classes_in_html)}")
print(f"Classes found in CSS: {len(present_classes)}")
print(f"Classes MISSING in CSS: {len(missing_classes)}")
print("\nMissing classes list:")
for c in missing_classes:
    print(f" - {c}")
