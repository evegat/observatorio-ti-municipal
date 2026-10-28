import json
import duckdb
import unicodedata
import re

def norm(s):
    if not s:
        return ""
    s = str(s).lower().strip()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9 ]", "", s)
    return s.strip()

with open("D:/Proyectos/observatorio-ti-municipal/data/comunas_enriched.json", "r", encoding="utf-8") as f:
    comunas_enriched = json.load(f)

print(f"Loaded {len(comunas_enriched)} comunas from comunas_enriched.json")

con = duckdb.connect()
parquet_path = "D:/Proyectos/PUB021 - Paper Adopcion IA y Tecnologias en Municipios/data/catastro_ti_municipal_completo_clasificado.parquet"

# Get distinct comuna_comprador in parquet
raw_comunas = con.execute(f"""
    SELECT distinct comuna_comprador, region_comprador
    FROM read_parquet('{parquet_path}')
    WHERE comuna_comprador IS NOT NULL 
      AND comuna_comprador NOT IN ('Sin comuna', 'NA', 'Extranjero', '*')
      AND NOT regexp_matches(comuna_comprador, '^[0-9 *]+$')
""").fetchall()

print(f"Found {len(raw_comunas)} distinct comuna_comprador in parquet")

# Check matches with comunas_enriched
enriched_cuts = {c["codigo_cut"]: c for c in comunas_enriched}
enriched_by_norm = {norm(c["comuna"]): c for c in comunas_enriched}
enriched_by_raw_norm = {norm(c.get("comuna_raw", "")): c for c in comunas_enriched}

# Check aliases
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

unmatched_enriched = []
for c in comunas_enriched:
    c_norm = norm(c["comuna"])
    c_raw_norm = norm(c.get("comuna_raw", ""))
    # see if any raw_comuna matches
    found = False
    for rc, reg in raw_comunas:
        rc_norm = norm(rc)
        resolved = aliases.get(rc_norm, rc_norm)
        if resolved == c_norm or rc_norm == c_norm or rc_norm == c_raw_norm:
            found = True
            break
    if not found:
        unmatched_enriched.append(c["comuna"])

print(f"Comunas in enriched with NO direct purchase match in parquet: {len(unmatched_enriched)}")
print("Unmatched comunas:", unmatched_enriched)
