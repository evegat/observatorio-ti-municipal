import json
import unicodedata
import re
import duckdb

def norm(s):
    if not s:
        return ""
    s = str(s).lower().strip()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9 ]", "", s)
    return s.strip()

with open("D:/Proyectos/observatorio-ti-municipal/data/comunas_enriched.json", "r", encoding="utf-8") as f:
    comunas_enriched = json.load(f)

# Build matching index for each of the 345 comunas
# A comuna can match by norm(comuna) or norm(comuna_raw) or alias
aliases = {
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

con = duckdb.connect()
parquet_path = "D:/Proyectos/PUB021 - Paper Adopcion IA y Tecnologias en Municipios/data/catastro_ti_municipal_completo_clasificado.parquet"

# Check how many distinct comuna_comprador exist in parquet
raw_comunas = con.execute(f"""
    SELECT comuna_comprador, count(*) as count, sum(monto_linea) as monto
    FROM read_parquet('{parquet_path}')
    WHERE comuna_comprador IS NOT NULL 
      AND comuna_comprador NOT IN ('Sin comuna', 'NA', 'Extranjero', '*')
      AND NOT regexp_matches(comuna_comprador, '^[0-9 *]+$')
    GROUP BY comuna_comprador
""").fetchall()

enriched_map = {}
for c in comunas_enriched:
    k = norm(c["comuna"])
    k_raw = norm(c.get("comuna_raw", ""))
    enriched_map[k] = c["codigo_cut"]
    if k_raw:
        enriched_map[k_raw] = c["codigo_cut"]

matched_rc = 0
unmatched_rc = []
for rc, cnt, m in raw_comunas:
    rc_norm = norm(rc)
    resolved = aliases.get(rc_norm, rc_norm)
    if resolved in enriched_map or rc_norm in enriched_map:
        matched_rc += 1
    else:
        unmatched_rc.append((rc, cnt, m))

print(f"Matched raw comunas: {matched_rc} / {len(raw_comunas)}")
print(f"Unmatched raw comunas: {len(unmatched_rc)}")
if unmatched_rc:
    print("Top 10 unmatched raw comunas by monto:")
    unmatched_rc.sort(key=lambda x: x[2] if x[2] else 0, reverse=True)
    for u in unmatched_rc[:10]:
        print(f"  {u[0]}: {u[1]} lines, ${u[2]/1e6:,.1f}M CLP")
