import json

with open("data/comunas_enriched.json", "r", encoding="utf-8") as f:
    comunas = json.load(f)

missing_coords = 0
missing_pob = 0
missing_rrhh = 0

for c in comunas:
    if c.get("lat") is None or c.get("lng") is None:
        missing_coords += 1
    if not c.get("poblacion") or c["poblacion"] <= 0:
        missing_pob += 1
    if "dotacion_total" not in c or "ret_ratio" not in c:
        missing_rrhh += 1

print(f"Missing coords: {missing_coords}")
print(f"Missing poblacion: {missing_pob}")
print(f"Missing RRHH fields: {missing_rrhh}")

assert missing_coords == 0
assert missing_pob == 0
assert missing_rrhh == 0
print("-> Preserved all existing RRHH, demographic, and geospatial attributes!")
