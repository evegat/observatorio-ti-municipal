import json
from collections import Counter
from pathlib import Path

enriched_path = Path("data/comunas_enriched.json")
with open(enriched_path, "r", encoding="utf-8") as f:
    comunas = json.load(f)

print(f"Total comunas en comunas_enriched.json: {len(comunas)}")

contratos_anios = Counter()
comunas_max_anio = Counter()
comunas_con_2025_2026 = 0
comunas_solo_hasta_2024 = 0

for c in comunas:
    contratos = c.get("top_contratos", [])
    anios_c = [ct.get("anio") for ct in contratos if ct.get("anio")]
    for a in anios_c:
        contratos_anios[a] += 1
    if anios_c:
        max_a = max(anios_c)
        comunas_max_anio[max_a] += 1
        if max_a >= 2025:
            comunas_con_2025_2026 += 1
        else:
            comunas_solo_hasta_2024 += 1
    else:
        comunas_max_anio["SIN_CONTRATOS"] += 1

print("\n--- DISTRIBUCIÓN DE AÑOS EN top_contratos DE comunas_enriched.json ---")
for a, cnt in sorted(contratos_anios.items(), key=lambda x: str(x[0])):
    print(f"  Año {a}: {cnt} contratos")

print("\n--- AÑO MÁXIMO EN top_contratos POR COMUNA ---")
for a, cnt in sorted(comunas_max_anio.items(), key=lambda x: str(x[0])):
    print(f"  Año máx {a}: {cnt} comunas")

print(f"\nComunas con al menos un contrato en 2025-2026: {comunas_con_2025_2026}")
print(f"Comunas rezagadas con contratos solo hasta 2024 o antes: {comunas_solo_hasta_2024}")
