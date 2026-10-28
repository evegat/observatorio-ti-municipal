"""
tests/check_5_specific_comunas.py
=================================
Deep inspection of the 5 key communes from challenger reports:
1. Olmué: Ensure Mauricio Guerra Contardo and electrical inspections are absent.
2. Paillaco: Ensure Neubacar and vehicle maintenance are absent.
3. Lumaco: Ensure Agroveterinaria Santa Lucía is absent.
4. Nueva Imperial: Ensure Toyota Hilux ECU is absent.
5. Los Lagos: Ensure Mobil oil and steering bar are absent.
"""

import json
import sys
from pathlib import Path
import duckdb

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PARQUET_FILE = DATA_DIR / "catastro_ti_saneado.parquet"
ENRICHED_FILE = DATA_DIR / "comunas_enriched.json"

con = duckdb.connect()
pq_path = str(PARQUET_FILE).replace("\\", "/")

with open(ENRICHED_FILE, "r", encoding="utf-8") as f:
    enriched = json.load(f)

targets = ["Olmué", "Paillaco", "Lumaco", "Nueva Imperial", "Los Lagos"]

for t in targets:
    print("=" * 80)
    print(f"TARGET COMMUNE: {t}")
    print("=" * 80)
    
    # 1. Parquet stats
    pq_stats = con.execute(f"""
        SELECT 
            count(*) as rows,
            count(distinct codigo_orden) as ocs,
            round(sum(monto_linea), 0) as monto
        FROM read_parquet('{pq_path}')
        WHERE lower(comuna_comprador) = '{t.lower()}'
    """).fetchone()
    print(f"Parquet stats: rows={pq_stats[0]}, OCs={pq_stats[1]}, monto=${pq_stats[2]:,.0f} CLP")
    
    # 2. JSON stats
    c_json = next((c for c in enriched if c["comuna"].lower() == t.lower()), None)
    if not c_json:
        print("  [ERROR] Commune not found in comunas_enriched.json!")
        continue
    
    print(f"JSON stats: OCs={c_json.get('total_ocs')}, monto=${c_json.get('monto_total'):,.0f} CLP, gasto_pc=${c_json.get('gasto_pc'):,.0f} CLP")
    
    # Top 3 providers
    print("Top Proveedores:")
    for p in c_json.get("top_proveedores", [])[:3]:
        print(f"  - {p['proveedor']}: ${p['monto']:,.0f} CLP ({p.get('ocs', 0)} OCs)")
        
    # Top 3 historical contracts
    print("Top Contratos Históricos:")
    for h in c_json.get("top_contratos_historicos", [])[:3]:
        print(f"  - [{h.get('codigo_orden')}] ({h.get('anio', '')}): {h.get('nombre_proveedor', '')} - ${h.get('monto', 0):,.0f} CLP | Desc: {h.get('descripcion', '')[:80]}")

    # Top 3 recent contracts
    print("Top Contratos Recientes (2025-2026):")
    for r in c_json.get("top_contratos_recientes", [])[:3]:
        print(f"  - [{r.get('codigo_orden')}] ({r.get('anio', '')}): {r.get('nombre_proveedor', '')} - ${r.get('monto', 0):,.0f} CLP | Desc: {r.get('descripcion', '')[:80]}")
