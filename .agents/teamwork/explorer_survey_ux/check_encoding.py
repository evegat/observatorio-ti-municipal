with open(r"D:\Proyectos\observatorio-ti-municipal\data\comunas_enriched.json", "rb") as f:
    content = f.read()

import re
matches = re.findall(b'Estado H[^"]+ Dependiente', content)
if matches:
    print("Raw byte matches for Estado Hibrido:", set(matches))
