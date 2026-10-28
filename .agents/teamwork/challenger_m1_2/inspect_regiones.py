#!/usr/bin/env python3
"""
Inspect regiones_enriched.json
"""
import json
from pathlib import Path

REGIONES_FILE = Path("D:/Proyectos/observatorio-ti-municipal/data/regiones_enriched.json")
with open(REGIONES_FILE, "r", encoding="utf-8") as f:
    regiones = json.load(f)

total_reg_monto = sum(r.get("monto_total", 0) for r in regiones)
total_reg_ocs = sum(r.get("total_ocs", 0) for r in regiones)

print(f"Total monto in regiones_enriched.json: {total_reg_monto:,.0f} CLP")
print(f"Total OCs in regiones_enriched.json: {total_reg_ocs}")
print(f"Gap with national_kpis.json: {172240070566 - total_reg_monto:,.0f} CLP")
