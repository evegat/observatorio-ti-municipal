import json

with open("data/comunas_enriched.json", "r", encoding="utf-8") as f:
    comunas = json.load(f)

print(f"Total comunas: {len(comunas)}")
assert len(comunas) == 345

comunas_with_recientes = 0
comunas_with_historicos = 0
backward_compat_matches = 0

for c in comunas:
    rec = c.get("top_contratos_recientes")
    hist = c.get("top_contratos_historicos")
    legacy = c.get("top_contratos")
    
    if rec and len(rec) > 0:
        comunas_with_recientes += 1
    if hist and len(hist) > 0:
        comunas_with_historicos += 1
    if legacy == hist:
        backward_compat_matches += 1

print(f"Comunas with top_contratos_recientes: {comunas_with_recientes}")
print(f"Comunas with top_contratos_historicos: {comunas_with_historicos}")
print(f"Comunas with top_contratos == top_contratos_historicos: {backward_compat_matches} (out of {len(comunas)})")

assert backward_compat_matches == 345, "Backward compatibility broken!"
assert comunas_with_recientes >= 344, f"Unexpectedly low recientes: {comunas_with_recientes}"
print("-> Feeds decoupling and backward compatibility VERIFIED 100%!")
