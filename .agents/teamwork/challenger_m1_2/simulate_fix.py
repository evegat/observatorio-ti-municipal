#!/usr/bin/env python3
"""
Simulate fix for compute_comuna_metrics
"""
from pathlib import Path
import duckdb

DATA_DIR = Path("D:/Proyectos/observatorio-ti-municipal/data")
PARQUET_FILE = DATA_DIR / "catastro_ti_saneado.parquet"
con = duckdb.connect()

res = con.execute(f"""
    SELECT 
        count(distinct comuna_comprador),
        round(sum(monto_linea), 0) as total_monto,
        count(distinct codigo_orden) as total_ocs
    FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')
    WHERE comuna_comprador IS NOT NULL 
      AND comuna_comprador NOT IN ('Sin comuna', 'NA', 'Extranjero', '*')
      AND NOT regexp_matches(comuna_comprador, '^[0-9 *]+$')
""").fetchone()

print(f"Grouping by comuna_comprador alone:")
print(f"  Distinct comunas: {res[0]}")
print(f"  Total monto: {res[1]:,.0f} CLP")
print(f"  Total OCs: {res[2]}")

# Check Ovalle
ovalle = con.execute(f"""
    SELECT comuna_comprador, round(sum(monto_linea), 0), count(distinct codigo_orden)
    FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')
    WHERE lower(comuna_comprador) = 'ovalle'
    GROUP BY comuna_comprador
""").fetchone()
print(f"Ovalle aggregated: {ovalle}")

# Check Puerto Montt
pm = con.execute(f"""
    SELECT comuna_comprador, round(sum(monto_linea), 0), count(distinct codigo_orden)
    FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')
    WHERE lower(comuna_comprador) = 'puerto montt'
    GROUP BY comuna_comprador
""").fetchone()
print(f"Puerto Montt aggregated: {pm}")
