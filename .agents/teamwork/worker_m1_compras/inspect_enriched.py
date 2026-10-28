import json
from pathlib import Path

data_path = Path("D:/Proyectos/observatorio-ti-municipal/data/comunas_enriched.json")
if data_path.exists():
    with open(data_path, "r", encoding="utf-8") as f:
        comunas = json.load(f)
    print(f"Total comunas in comunas_enriched.json: {len(comunas)}")
    sample = comunas[0]
    print("Sample keys:", list(sample.keys()))
    print("Sample comuna:", sample["comuna"], sample["codigo_cut"], sample["poblacion"])
else:
    print("comunas_enriched.json not found!")
