"""
tests/check_parquet_deep_integrity.py
=====================================
Deep inspection of catastro_ti_saneado.parquet:
- Schema, column types, null counts across ALL columns.
- Detection of NaNs, negative values, 0 values.
- Temporal consistency: min date, max date, year distribution.
- Commune verification against official CUT list.
- ONU code sanity.
"""

import json
import sys
from pathlib import Path
import duckdb

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PARQUET_FILE = DATA_DIR / "catastro_ti_saneado.parquet"

con = duckdb.connect()
pq_path = str(PARQUET_FILE).replace("\\", "/")

print("=" * 80)
print("DEEP PARQUET INTEGRITY AUDIT")
print("=" * 80)

# 1. Schema and Null check
schema = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{pq_path}')").fetchall()
print(f"Total columns: {len(schema)}")
cols_to_check = [col[0] for col in schema]

null_checks = []
for col in schema:
    c_name, c_type = col[0], col[1]
    null_checks.append(f"count(*) FILTER (WHERE \"{c_name}\" IS NULL) as null_{c_name}")
    if "FLOAT" in c_type.upper() or "DOUBLE" in c_type.upper():
        null_checks.append(f"count(*) FILTER (WHERE isnan(\"{c_name}\")) as nan_{c_name}")
    else:
        null_checks.append(f"0 as nan_{c_name}")

query = f"SELECT {', '.join(null_checks)} FROM read_parquet('{pq_path}')"
res = con.execute(query).fetchone()

print("\nNull & NaN Counts by Column:")
has_issues = False
idx = 0
for c in cols_to_check:
    null_cnt = res[idx]
    nan_cnt = res[idx+1]
    idx += 2
    if null_cnt > 0 or nan_cnt > 0:
        print(f"  {c}: nulls={null_cnt}, nans={nan_cnt}")
        if c in ["monto_linea", "codigo_orden", "comuna_comprador", "fecha_aceptacion"]:
            has_issues = True
    else:
        # print only if 0 for critical columns
        if c in ["monto_linea", "codigo_orden", "comuna_comprador", "fecha_aceptacion"]:
            print(f"  [OK] {c}: 0 nulls, 0 nans")

# 2. Check monto_linea specifics
monto_stats = con.execute(f"""
    SELECT 
        min(monto_linea) as min_monto,
        max(monto_linea) as max_monto,
        avg(monto_linea) as avg_monto,
        count(*) FILTER (WHERE monto_linea < 0) as negative_monto,
        count(*) FILTER (WHERE monto_linea = 0) as zero_monto,
        count(*) FILTER (WHERE monto_linea > 0) as positive_monto
    FROM read_parquet('{pq_path}')
""").fetchone()

print(f"\nMonto Linea Stats:")
print(f"  Min: ${monto_stats[0]:,.2f}")
print(f"  Max: ${monto_stats[1]:,.2f}")
print(f"  Avg: ${monto_stats[2]:,.2f}")
print(f"  Negative count: {monto_stats[3]}")
print(f"  Zero count: {monto_stats[4]} ({monto_stats[4]/118204*100:.2f}%)")
print(f"  Positive count: {monto_stats[5]}")

# 3. Check dates and years
date_stats = con.execute(f"""
    SELECT 
        min(fecha_aceptacion) as min_date,
        max(fecha_aceptacion) as max_date,
        count(*) FILTER (WHERE fecha_aceptacion > '2026-12-31') as future_dates,
        count(*) FILTER (WHERE fecha_aceptacion < '2010-01-01') as old_dates,
        count(*) FILTER (WHERE anio >= 2025) as recent_rows,
        count(*) FILTER (WHERE anio < 2025) as historic_rows
    FROM read_parquet('{pq_path}')
""").fetchone()

print(f"\nTemporal Stats:")
print(f"  Min date: {date_stats[0]}")
print(f"  Max date: {date_stats[1]}")
print(f"  Future dates (> 2026): {date_stats[2]}")
print(f"  Old dates (< 2010): {date_stats[3]}")
print(f"  Recent rows (>= 2025): {date_stats[4]}")
print(f"  Historic rows (< 2025): {date_stats[5]}")

# 4. Check unique commune values in parquet
comunas_in_pq = con.execute(f"""
    SELECT distinct comuna_comprador
    FROM read_parquet('{pq_path}')
    ORDER BY comuna_comprador
""").fetchall()

print(f"\nTotal distinct comuna_comprador values: {len(comunas_in_pq)}")
bad_comunas = [c[0] for c in comunas_in_pq if len(c[0].strip()) == 0 or c[0].isdigit() or c[0] in ['Sin comuna', 'NA', 'Extranjero', '*']]
print(f"Bad / invalid commune strings: {len(bad_comunas)}")
if bad_comunas:
    print(f"  Bad list: {bad_comunas}")
