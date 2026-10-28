#!/usr/bin/env python3
"""
Investigate the 13.6 billion CLP gap between parquet and comunas_enriched
"""
import json
from pathlib import Path
import duckdb

DATA_DIR = Path("D:/Proyectos/observatorio-ti-municipal/data")
PARQUET_FILE = DATA_DIR / "catastro_ti_saneado.parquet"
ENRICHED_FILE = DATA_DIR / "comunas_enriched.json"
con = duckdb.connect()

with open(ENRICHED_FILE, "r", encoding="utf-8") as f:
    enriched = json.load(f)

# Let's check grouping by comuna_comprador alone vs comuna_comprador + region_comprador
by_comuna_only = con.execute(f"""
    SELECT round(sum(monto_linea), 0)
    FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')
    WHERE comuna_comprador IS NOT NULL 
      AND comuna_comprador NOT IN ('Sin comuna', 'NA', 'Extranjero', '*')
      AND NOT regexp_matches(comuna_comprador, '^[0-9 *]+$')
""").fetchone()[0]

print(f"Total monto with WHERE filters: {by_comuna_only:,.0f} CLP")

# Check multiple rows in GROUP BY comuna_comprador, region_comprador
grouped = con.execute(f"""
    SELECT comuna_comprador, count(*), sum(monto_linea)
    FROM (
        SELECT comuna_comprador, region_comprador, sum(monto_linea) as monto_linea
        FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')
        WHERE comuna_comprador IS NOT NULL 
          AND comuna_comprador NOT IN ('Sin comuna', 'NA', 'Extranjero', '*')
          AND NOT regexp_matches(comuna_comprador, '^[0-9 *]+$')
        GROUP BY comuna_comprador, region_comprador
    )
    GROUP BY comuna_comprador
    HAVING count(*) > 1
""").fetchall()

print(f"Comunas with multiple regions in parquet: {len(grouped)}")
mult_monto = sum(g[2] for g in grouped)
print(f"Total monto in multi-region comunas: {mult_monto:,.0f} CLP")
for g in grouped[:10]:
    print(f"  {g[0]}: {g[1]} regions, sum={g[2]:,.0f} CLP")

# Now let's compare comuna by comuna between DuckDB query and comunas_enriched
duck_comunas = con.execute(f"""
    SELECT comuna_comprador, round(sum(monto_linea), 0) as monto, count(distinct codigo_orden) as ocs
    FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')
    WHERE comuna_comprador IS NOT NULL 
      AND comuna_comprador NOT IN ('Sin comuna', 'NA', 'Extranjero', '*')
      AND NOT regexp_matches(comuna_comprador, '^[0-9 *]+$')
    GROUP BY comuna_comprador
""").df()

enriched_map = {c["comuna"].lower(): c for c in enriched}
enriched_raw_map = {c.get("comuna_raw", "").lower(): c for c in enriched if c.get("comuna_raw")}

print("\nDiscrepancies per comuna between DuckDB aggregated by comuna_comprador and comunas_enriched:")
discrepancies = []
for _, row in duck_comunas.iterrows():
    c_name = str(row["comuna_comprador"]).strip()
    duck_monto = float(row["monto"])
    duck_ocs = int(row["ocs"])
    
    # find in enriched
    matched_c = enriched_map.get(c_name.lower()) or enriched_raw_map.get(c_name.lower())
    if not matched_c:
        discrepancies.append((c_name, "NOT_FOUND_IN_ENRICHED", duck_monto, 0, duck_ocs, 0))
    else:
        enr_monto = float(matched_c["monto_total"])
        enr_ocs = int(matched_c["total_ocs"])
        diff_monto = duck_monto - enr_monto
        diff_ocs = duck_ocs - enr_ocs
        if abs(diff_monto) > 1000 or diff_ocs != 0:
            discrepancies.append((c_name, matched_c["comuna"], duck_monto, enr_monto, duck_ocs, enr_ocs))

print(f"Total comunas with discrepancies: {len(discrepancies)}")
discrepancies.sort(key=lambda x: abs(x[2] - x[3]), reverse=True)
for d in discrepancies[:25]:
    print(f"  {d[0]} -> {d[1]}: DuckDB={d[2]:,.0f} (OCs:{d[4]}) vs Enriched={d[3]:,.0f} (OCs:{d[5]}) | Diff={d[2]-d[3]:,.0f} CLP")
