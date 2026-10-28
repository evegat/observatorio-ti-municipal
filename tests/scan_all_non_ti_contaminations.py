"""
tests/scan_all_non_ti_contaminations.py
======================================
Exhaustive empirical scan of all 345 comunas for non-TI contaminations in
top_proveedores, top_contratos_historicos, and top_contratos_recientes.
"""

import json
from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PARQUET_FILE = DATA_DIR / "catastro_ti_saneado.parquet"
ENRICHED_FILE = DATA_DIR / "comunas_enriched.json"

con = duckdb.connect()
pq_path = str(PARQUET_FILE).replace("\\", "/")

with open(ENRICHED_FILE, "r", encoding="utf-8") as f:
    comunas = json.load(f)

print("=" * 80)
print("SCANNING 345 COMUNAS FOR NON-TI ONU CODES IN HISTORIC AND RECENT CONTRACTS")
print("=" * 80)

# Build a lookup of all contracts in parquet to check their ONU code, rubro and descriptions
contract_metadata = {}
rows = con.execute(f"""
    SELECT 
        codigo_orden, 
        codigo_producto_onu, 
        nombre_producto_generico, 
        rubro_nivel1, 
        nombre_proveedor, 
        monto_linea, 
        texto_descriptivo
    FROM read_parquet('{pq_path}')
""").fetchall()

for r in rows:
    cod = r[0]
    if cod not in contract_metadata:
        contract_metadata[cod] = []
    contract_metadata[cod].append({
        "onu": r[1],
        "onu_name": r[2],
        "rubro": r[3],
        "prov": r[4],
        "monto": r[5],
        "desc": r[6]
    })

# Non-TI ONU codes or groups:
# 8114xxxx: Manufacturing & maintenance (electric, plumbing, sewer)
# 8115xxxx: Earth sciences (topography, photogrammetry)
# 8110xxxx: Engineering civil/mechanical
# 8014xxxx: Marketing & advertising
# 60xxxxxx: Musical / games / sports
# 10xxxxxx: Live animal / plant supplies (or misclassified mochilas)
non_ti_onu_prefixes = ("8114", "8115", "8110", "8113", "8014", "60", "10")

# Suspicious words in description
non_ti_words = [
    "gasfiter", "alcantarillado", "fosas septicas", "fosa septica", "fosas sépticas",
    "matriz de agua", "filtracion", "filtración", "camioneta", "vehiculo", "vehículo",
    "guitarra", "amplificador", "iluminacion", "iluminación", "electrica", "eléctrica",
    "topografia", "topografía", "fotogrametria", "fotogrametría", "campana publicitaria",
    "campaña publicitaria", "marketing", "difusion", "difusión", "recuperacion de fondos",
    "recuperación de fondos", "licencias medicas", "licencias médicas", "agroveterinaria",
    "pladeco", "aguas servidas", "cañeria", "cañería"
]

contaminated_comunas = {}

for c in comunas:
    c_name = c["comuna"]
    issues = []

    # Check top_contratos_historicos
    for oc in c.get("top_contratos_historicos", []):
        cod = oc["codigo_oc"]
        meta_list = contract_metadata.get(cod, [])
        for m in meta_list:
            onu = str(m["onu"])
            desc = str(m["desc"]).lower()
            onu_name = str(m["onu_name"]).lower()
            
            # Check ONU prefix
            if any(onu.startswith(pre) for pre in non_ti_onu_prefixes):
                issues.append(f"Histórico OC {cod} ({m['prov']}, ${m['monto']:,.0f}): ONU no-TI {onu} ({m['onu_name']})")
                break
            # Check non-TI words
            matched_words = [w for w in non_ti_words if w in desc]
            if matched_words:
                issues.append(f"Histórico OC {cod} ({m['prov']}, ${m['monto']:,.0f}): Términos no-TI {matched_words} en desc: {desc[:70]}")
                break

    # Check top_contratos_recientes
    for oc in c.get("top_contratos_recientes", []):
        cod = oc["codigo_oc"]
        meta_list = contract_metadata.get(cod, [])
        for m in meta_list:
            onu = str(m["onu"])
            desc = str(m["desc"]).lower()
            if any(onu.startswith(pre) for pre in non_ti_onu_prefixes):
                issues.append(f"Reciente OC {cod} ({m['prov']}, ${m['monto']:,.0f}): ONU no-TI {onu} ({m['onu_name']})")
                break
            matched_words = [w for w in non_ti_words if w in desc]
            if matched_words:
                issues.append(f"Reciente OC {cod} ({m['prov']}, ${m['monto']:,.0f}): Términos no-TI {matched_words} en desc: {desc[:70]}")
                break

    # Check top_proveedores
    for p in c.get("top_proveedores", []):
        p_name = p["proveedor"].lower()
        if "mauricio esteban guerra" in p_name or "servintal" in p_name or "agroveterinaria" in p_name or "wetland" in p_name:
            issues.append(f"Proveedor no-TI en top_proveedores: {p['proveedor']} (${p['monto']:,.0f})")

    if issues:
        contaminated_comunas[c_name] = issues

print(f"Total contaminated comunas found: {len(contaminated_comunas)}")
for c_name, iss in sorted(contaminated_comunas.items()):
    print(f"\n[COMUNA: {c_name}] ({len(iss)} hallazgos):")
    for item in iss:
        print(f"  - {item}")
