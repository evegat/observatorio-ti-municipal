#!/usr/bin/env python3
"""
Investigate Ovalle and Puerto Montt in parquet
"""
from pathlib import Path
import duckdb

DATA_DIR = Path("D:/Proyectos/observatorio-ti-municipal/data")
PARQUET_FILE = DATA_DIR / "catastro_ti_saneado.parquet"
con = duckdb.connect()

print("OVALLE ROWS IN GROUP BY:")
rows = con.execute(f"""
    SELECT comuna_comprador, region_comprador, count(distinct codigo_orden) as ocs, round(sum(monto_linea), 0) as monto
    FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')
    WHERE lower(comuna_comprador) LIKE '%ovalle%'
    GROUP BY comuna_comprador, region_comprador
""").fetchall()
for r in rows:
    print(r)

print("\nPUERTO MONTT ROWS IN GROUP BY:")
rows = con.execute(f"""
    SELECT comuna_comprador, region_comprador, count(distinct codigo_orden) as ocs, round(sum(monto_linea), 0) as monto
    FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')
    WHERE lower(comuna_comprador) LIKE '%puerto montt%'
    GROUP BY comuna_comprador, region_comprador
""").fetchall()
for r in rows:
    print(r)

print("\nLA CISTERNA ROWS IN GROUP BY:")
rows = con.execute(f"""
    SELECT comuna_comprador, region_comprador, count(distinct codigo_orden) as ocs, round(sum(monto_linea), 0) as monto
    FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')
    WHERE lower(comuna_comprador) LIKE '%la cisterna%'
    GROUP BY comuna_comprador, region_comprador
""").fetchall()
for r in rows:
    print(r)
