#!/usr/bin/env python3
"""
Inspect Ovalle and Puerto Montt in enriched
"""
import json
from pathlib import Path

ENRICHED_FILE = Path("D:/Proyectos/observatorio-ti-municipal/data/comunas_enriched.json")
with open(ENRICHED_FILE, "r", encoding="utf-8") as f:
    enriched = json.load(f)

for name in ["Ovalle", "Puerto Montt"]:
    c = next((item for item in enriched if item["comuna"] == name), None)
    print(f"==================================================")
    print(f"COMUNA: {name}")
    print(f"  total_ocs: {c.get('total_ocs')}")
    print(f"  monto_total: {c.get('monto_total'):,.0f} CLP")
    print(f"  gasto_pc: {c.get('gasto_pc')}")
    print(f"  top_proveedores: {c.get('top_proveedores')}")
    print(f"  top_contratos_historicos: {c.get('top_contratos_historicos')}")
    print(f"  top_contratos_recientes: {c.get('top_contratos_recientes')}")
