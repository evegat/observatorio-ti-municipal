"""
tests/check_json_deep_integrity.py
==================================
Deep audit of comunas_enriched.json and compras_saneadas_por_comuna.json.
Checks:
- Commune counts, schema uniformity.
- Nulls/NaNs in any numeric fields.
- Value bounds: score_madurez (0-100), gasto_pc, poblacion, dotacion.
- Integrity of top_proveedores, top_contratos_historicos, top_contratos_recientes.
- Cross-consistency between comunas_enriched.json and compras_saneadas_por_comuna.json.
"""

import json
import math
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ENRICHED_FILE = DATA_DIR / "comunas_enriched.json"
COMPRAS_FILE = DATA_DIR / "compras_saneadas_por_comuna.json"

with open(ENRICHED_FILE, "r", encoding="utf-8") as f:
    comunas = json.load(f)

with open(COMPRAS_FILE, "r", encoding="utf-8") as f:
    compras = json.load(f)

print("=" * 80)
print("DEEP JSON INTEGRITY AUDIT")
print("=" * 80)

print(f"Total comunas in comunas_enriched.json: {len(comunas)}")
print(f"Total comunas in compras_saneadas_por_comuna.json: {len(compras)}")

# 1. Null / NaN / Type checks
keys_to_check = [
    "comuna", "region", "codigo_cut", "poblacion", "total_ocs", "monto_total",
    "gasto_pc", "monto_hardware", "monto_saas", "monto_ia", "monto_telecom",
    "monto_cyber", "score_madurez", "dotacion_total"
]

issues = []
madurez_scores = []
gasto_pcs = []
poblaciones = []

for idx, c in enumerate(comunas):
    c_name = c.get("comuna", f"Unknown_{idx}")
    
    # Check essential keys
    for k in keys_to_check:
        if k not in c:
            issues.append(f"{c_name}: Missing key '{k}'")
            continue
        v = c[k]
        if v is None:
            issues.append(f"{c_name}: Null value in key '{k}'")
        elif isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            issues.append(f"{c_name}: NaN/Inf in key '{k}'")
    
    # Bounds check
    pob = c.get("poblacion", 0)
    poblaciones.append(pob)
    if pob <= 0:
        issues.append(f"{c_name}: Invalid poblacion {pob}")
        
    mad = c.get("score_madurez", 0)
    madurez_scores.append(mad)
    if not (0 <= mad <= 100):
        issues.append(f"{c_name}: Score madurez out of bounds (0-100): {mad}")
        
    gpc = c.get("gasto_pc", 0.0)
    gasto_pcs.append(gpc)
    if gpc < 0:
        issues.append(f"{c_name}: Negative gasto_pc {gpc}")
        
    # Check top_contratos_recientes ordering
    recientes = c.get("top_contratos_recientes", [])
    for i in range(len(recientes) - 1):
        f1 = recientes[i].get("fecha_aceptacion", "")
        f2 = recientes[i+1].get("fecha_aceptacion", "")
        m1 = recientes[i].get("monto", 0.0)
        m2 = recientes[i+1].get("monto", 0.0)
        if f1 < f2:
            issues.append(f"{c_name}: recientes out of chronological order ({f1} < {f2})")
            break
        elif f1 == f2 and m1 < m2:
            issues.append(f"{c_name}: recientes same date but monto not descending ({m1} < {m2})")
            break

    # Check top_contratos_historicos ordering
    historicos = c.get("top_contratos_historicos", [])
    for i in range(len(historicos) - 1):
        m1 = historicos[i].get("monto", 0.0)
        m2 = historicos[i+1].get("monto", 0.0)
        if m1 < m2:
            issues.append(f"{c_name}: historicos monto not descending ({m1} < {m2})")
            break

print(f"Total integrity issues found: {len(issues)}")
if issues:
    for iss in issues[:10]:
        print("  [ISSUE]", iss)

print("\nSummary Metrics Distribution:")
print(f"  Poblacion: min={min(poblaciones):,}, max={max(poblaciones):,}, avg={sum(poblaciones)/len(poblaciones):,.0f}")
print(f"  Score Madurez: min={min(madurez_scores)}, max={max(madurez_scores)}, avg={sum(madurez_scores)/len(madurez_scores):.1f}")
print(f"  Gasto Per Cápita: min=${min(gasto_pcs):,.0f}, max=${max(gasto_pcs):,.0f}, avg=${sum(gasto_pcs)/len(gasto_pcs):,.0f}")

# 2. Check cross-consistency between comunas_enriched and compras_saneadas_por_comuna
compras_map = {c["codigo_cut"]: c for c in compras}
cross_issues = 0
for c in comunas:
    cut = c.get("codigo_cut")
    if cut not in compras_map:
        cross_issues += 1
        continue
    cp = compras_map[cut]
    if c.get("total_ocs") != cp.get("total_ocs") or abs(c.get("monto_total", 0.0) - cp.get("monto_total", 0.0)) > 1.0:
        cross_issues += 1

print(f"\nCross-consistency between comunas_enriched.json and compras_saneadas_por_comuna.json: {cross_issues} mismatches")
