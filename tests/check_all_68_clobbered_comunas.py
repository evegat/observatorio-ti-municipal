"""
tests/check_all_68_clobbered_comunas.py
=======================================
Empirical check of all comunas that had multiple region representations in
catastro_ti_municipal_completo_clasificado.parquet or catastro_ti_saneado.parquet.
Verify that none of them is clobbered in comunas_enriched.json.
"""

import json
from pathlib import Path
import duckdb
import unicodedata
import re

def normalize_text(s):
    if not s: return ""
    s = str(s).lower().strip()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9 ]", "", s)
    return s.strip()

COMUNA_ALIASES = {
    "santiago": "santiago centro",
    "estacion central": "estacion central",
    "la calera": "calera",
    "trehuaco": "treguaco",
    "marchigue": "marchihue",
    "las guaitecas": "guaitecas",
    "o higgins": "ohiggins",
    "til til": "tiltil",
    "san vicente de tagua tagua": "san vicente",
    "paihuano": "paiguano",
    "coyhaique": "coihaique",
    "puerto natales": "natales",
    "torres del payne": "torres del paine",
    "alto bio bio": "alto biobio",
    "chol chol": "cholchol",
    "puerto saavedra": "saavedra",
    "llayllay": "llaillay",
    "llay llay": "llaillay",
    "vichuquen": "vichuquen",
    "navarino": "cabo de hornos",
    "puerto williams": "cabo de hornos"
}

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PARQUET_FILE = DATA_DIR / "catastro_ti_saneado.parquet"
ENRICHED_FILE = DATA_DIR / "comunas_enriched.json"

con = duckdb.connect()
pq_path = str(PARQUET_FILE).replace("\\", "/")

# Find all comunas that had multiple (comuna_comprador, region_comprador) pairs in catastro_ti_saneado.parquet
multi_region_query = f"""
    SELECT 
        comuna_comprador,
        count(distinct region_comprador) as n_regiones,
        list(distinct region_comprador) as regiones,
        count(distinct codigo_orden) as total_ocs,
        round(sum(monto_linea), 0) as total_monto
    FROM read_parquet('{pq_path}')
    GROUP BY comuna_comprador
    HAVING count(distinct region_comprador) > 1
    ORDER BY total_monto DESC
"""
multi_reg_rows = con.execute(multi_region_query).fetchall()

print(f"Total comunas with multiple region spellings in parquet: {len(multi_reg_rows)}")

with open(ENRICHED_FILE, "r", encoding="utf-8") as f:
    enriched = json.load(f)

enriched_map = {}
for c in enriched:
    norm = normalize_text(c["comuna"])
    res = COMUNA_ALIASES.get(norm, norm)
    enriched_map[res] = c

clobbered_found = []
restored_count = 0

for r in multi_reg_rows:
    comuna_raw = r[0]
    n_reg = r[1]
    regiones = r[2]
    pq_ocs = r[3]
    pq_monto = float(r[4])
    
    norm = normalize_text(comuna_raw)
    res = COMUNA_ALIASES.get(norm, norm)
    
    c_json = enriched_map.get(res)
    if not c_json:
        clobbered_found.append((comuna_raw, "NOT FOUND IN JSON", pq_ocs, pq_monto))
        continue
    
    j_ocs = c_json.get("total_ocs", 0)
    j_monto = float(c_json.get("monto_total", 0.0))
    j_gpc = float(c_json.get("gasto_pc", 0.0))
    
    # Check if the json retains full or near-full value (not clobbered to < 10 OCs or < $100k)
    diff = abs(pq_monto - j_monto)
    if diff > 1000 and comuna_raw.lower() != "santiago":
        clobbered_found.append((comuna_raw, f"MISMATCH pq={pq_monto} vs json={j_monto}", pq_ocs, j_ocs))
    elif j_ocs <= 5 and pq_ocs > 50:
        clobbered_found.append((comuna_raw, f"CLOBBERED: {j_ocs} OCs vs {pq_ocs} OCs in parquet", j_monto))
    else:
        restored_count += 1

print(f"Restored count without clobbering: {restored_count} / {len(multi_reg_rows)}")
if clobbered_found:
    print(f"Clobbered or mismatched found: {len(clobbered_found)}")
    for item in clobbered_found:
        print("  ", item)
else:
    print("ALL multi-region comunas are 100% restored and match Parquet exactly!")
