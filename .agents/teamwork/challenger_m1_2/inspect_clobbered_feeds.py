#!/usr/bin/env python3
"""
Inspect feeds for clobbered comunas
"""
import json
from pathlib import Path

ENRICHED_FILE = Path("D:/Proyectos/observatorio-ti-municipal/data/comunas_enriched.json")
with open(ENRICHED_FILE, "r", encoding="utf-8") as f:
    enriched = json.load(f)

check_comunas = ["Ovalle", "Puerto Montt", "La Cisterna", "Cañete", "Longaví", "Penco", "Los Muermos", "Pelarco", "Pitrufquén", "Corral"]

for name in check_comunas:
    c = next((item for item in enriched if item["comuna"] == name), None)
    if not c:
        print(f"{name}: NOT FOUND")
        continue
    print(f"==================================================")
    print(f"COMUNA: {name}")
    print(f"  total_ocs: {c.get('total_ocs')}")
    print(f"  monto_total: {c.get('monto_total'):,.0f} CLP")
    print(f"  gasto_pc: {c.get('gasto_pc')}")
    print(f"  top_proveedores count: {len(c.get('top_proveedores', []))}")
    print(f"  top_contratos_recientes count: {len(c.get('top_contratos_recientes', []))}")
    print(f"  top_contratos_historicos count: {len(c.get('top_contratos_historicos', []))}")
    if c.get('top_contratos_historicos'):
        print(f"  Top Hist 1: {c['top_contratos_historicos'][0]}")
    if c.get('top_contratos_recientes'):
        print(f"  Top Rec 1: {c['top_contratos_recientes'][0]}")
