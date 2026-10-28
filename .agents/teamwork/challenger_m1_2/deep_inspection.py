#!/usr/bin/env python3
"""
Deep inspection of anomalies found by challenger_m1_2
"""
import json
import re
from pathlib import Path
import duckdb

DATA_DIR = Path("D:/Proyectos/observatorio-ti-municipal/data")
PARQUET_FILE = DATA_DIR / "catastro_ti_saneado.parquet"
ENRICHED_FILE = DATA_DIR / "comunas_enriched.json"
con = duckdb.connect()

print("=" * 80)
print("DEEP DIVE: PAILLACO CAMIONETA")
print("=" * 80)
paillaco_rows = con.execute(f"""
    SELECT item_id, codigo_orden, fecha_aceptacion, anio, rut_proveedor, nombre_proveedor,
           codigo_producto_onu, nombre_producto_generico, rubro_nivel1, rubro_nivel2,
           monto_linea, texto_descriptivo
    FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')
    WHERE codigo_orden = '3789-7023-SE25'
""").fetchall()
for r in paillaco_rows:
    print(r)

print("\n" + "=" * 80)
print("DEEP DIVE: VITACURA PREUNIVERSITARIO")
print("=" * 80)
vitacura_rows = con.execute(f"""
    SELECT item_id, codigo_orden, fecha_aceptacion, anio, rut_proveedor, nombre_proveedor,
           codigo_producto_onu, nombre_producto_generico, rubro_nivel1, rubro_nivel2,
           monto_linea, texto_descriptivo
    FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')
    WHERE codigo_orden = '1480067-62-AG26'
""").fetchall()
for r in vitacura_rows:
    print(r)

print("\n" + "=" * 80)
print("DEEP DIVE: UNMATCHED COMUNAS & 13.6 BILLION CLP GAP")
print("=" * 80)
with open(ENRICHED_FILE, "r", encoding="utf-8") as f:
    enriched = json.load(f)
enriched_names = {c["comuna"].lower(): c["comuna"] for c in enriched}
enriched_raws = {c.get("comuna_raw", "").lower(): c["comuna"] for c in enriched if c.get("comuna_raw")}

all_parquet_comunas = con.execute(f"""
    SELECT comuna_comprador, count(distinct codigo_orden) as ocs, round(sum(monto_linea), 0) as monto,
           count(distinct rut_comprador) as ruts, arbitrary(nombre_comprador) as sample_buyer
    FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')
    GROUP BY comuna_comprador
    ORDER BY monto DESC
""").fetchall()

unmatched_real_comunas = []
unmatched_garbage = []

for c_comp, ocs, monto, ruts, sample_buyer in all_parquet_comunas:
    c_str = str(c_comp).strip().lower()
    if c_str in enriched_names or c_str in enriched_raws:
        continue
    # Check if it looks like a real comuna or muni
    unmatched_real_comunas.append((c_comp, ocs, monto, sample_buyer))

print(f"Total unmatched entries in parquet: {len(unmatched_real_comunas)}")
total_unmatched_monto = sum(x[2] or 0 for x in unmatched_real_comunas)
print(f"Total unmatched monto: {total_unmatched_monto:,.0f} CLP")
print("\nTop 30 unmatched by monto:")
for c_comp, ocs, monto, sample_buyer in unmatched_real_comunas[:30]:
    m = monto or 0
    print(f"  '{c_comp}': OCs={ocs}, Monto={m:,.0f} CLP | Sample Buyer: '{sample_buyer}'")

print("\n" + "=" * 80)
print("SEARCH FOR MORE SPURIOUS NON-TI IN PARQUET")
print("=" * 80)
# Let's search catastro_ti_saneado.parquet for camioneta, vehiculo, catering, banquete, vestuario, etc.
spurious_queries = [
    ("camioneta", "lower(texto_descriptivo) LIKE '%camioneta%'"),
    ("automovil / vehiculo", "(lower(texto_descriptivo) LIKE '%vehiculo%' OR lower(texto_descriptivo) LIKE '%vehículo%') AND lower(texto_descriptivo) NOT LIKE '%gps%' AND lower(texto_descriptivo) NOT LIKE '%flota%' AND lower(texto_descriptivo) NOT LIKE '%patente%'"),
    ("catering / banquete", "lower(texto_descriptivo) LIKE '%banquet%' OR lower(texto_descriptivo) LIKE '%catering%'"),
    ("preuniversitario", "lower(texto_descriptivo) LIKE '%preuniversitario%' OR lower(nombre_proveedor) LIKE '%preuniversitario%'"),
    ("gas licuado / envasado", "lower(texto_descriptivo) LIKE '%gas licuado%' OR lower(texto_descriptivo) LIKE '%gas envasado%'"),
    ("zapato / bota seguridad", "lower(texto_descriptivo) LIKE '%zapato%' OR lower(texto_descriptivo) LIKE '%calzado%' OR lower(texto_descriptivo) LIKE '%bota%'"),
    ("obra civil / pavimentacion", "lower(texto_descriptivo) LIKE '%pavimentac%' OR lower(texto_descriptivo) LIKE '%obra civil%' OR lower(texto_descriptivo) LIKE '%obras civiles%'"),
    ("apicola", "lower(texto_descriptivo) LIKE '%apicol%' OR lower(texto_descriptivo) LIKE '%apícol%'"),
    ("desratizacion / fumigacion", "lower(texto_descriptivo) LIKE '%desratizac%' OR lower(texto_descriptivo) LIKE '%fumigac%'"),
    ("curanto / fiesta", "lower(texto_descriptivo) LIKE '%curanto%' OR lower(texto_descriptivo) LIKE '%fiesta de fin de ano%'"),
    ("arriendo carpas", "lower(texto_descriptivo) LIKE '%carpa%' OR lower(nombre_proveedor) LIKE '%carpa%'")
]

for label, cond in spurious_queries:
    res = con.execute(f"SELECT count(*), round(sum(monto_linea), 0) FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}') WHERE {cond}").fetchone()
    count = res[0]
    monto = res[1] or 0
    print(f"  {label:<30}: {count:>5} rows, {monto:>15,.0f} CLP")
