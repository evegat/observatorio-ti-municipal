import json
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

con = duckdb.connect()
df = con.execute("""
    SELECT 
        comuna_comprador as comuna,
        count(distinct codigo_orden) as total_ocs,
        round(coalesce(sum(monto_linea), 0), 0) as monto_total
    FROM read_parquet('data/catastro_ti_saneado.parquet')
    GROUP BY comuna_comprador
""").df()

metrics = {}
for _, row in df.iterrows():
    raw_name = str(row["comuna"]).strip()
    norm_name = normalize_text(raw_name)
    resolved = COMUNA_ALIASES.get(norm_name, norm_name)
    monto = float(row["monto_total"])
    d = row.to_dict()
    if resolved not in metrics or monto > metrics[resolved]["monto_total"]:
        metrics[resolved] = d
    if norm_name not in metrics or monto > metrics[norm_name]["monto_total"]:
        metrics[norm_name] = d

with open("data/comunas_enriched.json", encoding="utf-8") as f:
    enriched = json.load(f)

mismatches = []
zero_comunas = []

for c in enriched:
    name = c["comuna"]
    c_raw = c.get("comuna_raw", name)
    norm = normalize_text(name)
    norm_raw = normalize_text(c_raw)
    res = COMUNA_ALIASES.get(norm, norm)
    
    match = metrics.get(res) or metrics.get(norm) or metrics.get(norm_raw)
    if not match:
        zero_comunas.append(name)
        assert c["total_ocs"] == 0 and c["monto_total"] == 0, f"Expected 0 for unmatched {name}"
    else:
        diff_monto = abs(float(c["monto_total"]) - float(match["monto_total"]))
        diff_ocs = abs(int(c["total_ocs"]) - int(match["total_ocs"]))
        if diff_monto > 1.0 or diff_ocs > 0:
            mismatches.append((name, c["total_ocs"], match["total_ocs"], c["monto_total"], match["monto_total"]))

print(f"Total comunas checked: {len(enriched)}")
print(f"Comunas with zero purchases in catastro: {len(zero_comunas)} -> {zero_comunas}")
print(f"Mismatches against build algorithm: {len(mismatches)}")
if mismatches:
    for m in mismatches:
        print("  Mismatch:", m)
else:
    print("PERFECT 100% MATCH across all 345 comunas in comunas_enriched.json!")
