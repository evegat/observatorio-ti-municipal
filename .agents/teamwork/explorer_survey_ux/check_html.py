import re
from collections import Counter

with open(r"D:\Proyectos\observatorio-ti-municipal\index.html", encoding="utf-8") as f:
    html = f.read()

ids = re.findall(r'id=["\']([^"\']+)["\']', html)
counts = Counter(ids)
duplicates = {k: v for k, v in counts.items() if v > 1}
print("Duplicate IDs in index.html:", duplicates)
print("Total IDs found:", len(ids))
