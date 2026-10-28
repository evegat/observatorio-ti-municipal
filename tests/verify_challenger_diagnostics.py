"""
tests/verify_challenger_diagnostics.py
======================================
Detailed empirical diagnosis script for challenger_m1_1.
"""

import json
from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PARQUET_FILE = DATA_DIR / "catastro_ti_saneado.parquet"
ENRICHED_FILE = DATA_DIR / "comunas_enriched.json"

con = duckdb.connect()

print("=" * 80)
print("1. PROBING PARQUET FOR TARGET AND ADVERSARIAL KEYWORDS")
print("=" * 80)

keywords = [
    "carpa", "toldo", "escenario", "gas licuado", "gas envasado",
    "zapatos", "apicultura", "banquete", "curso de guitarra", "guitarra",
    "curanto", "amplificacion", "amplificación", "coctel", "cóctel",
    "alimentos", "catering", "bano quimico", "baño químico", "pirotecnia",
    "desratizac", "fumigac", "neumatico", "neumático", "gasolina",
    "diesel", "camioneta", "obra civil", "pavimentac"
]

pq_path = str(PARQUET_FILE).replace("\\", "/")

for kw in keywords:
    cnt = con.execute(f"""
        SELECT count(*)
        FROM read_parquet('{pq_path}')
        WHERE lower(coalesce(texto_descriptivo, '')) LIKE '%{kw}%'
           OR lower(coalesce(nombre_proveedor, '')) LIKE '%{kw}%'
           OR lower(coalesce(nombre_producto_generico, '')) LIKE '%{kw}%'
    """).fetchone()[0]
    if cnt > 0:
        print(f"  [FOUND] '{kw}': {cnt} matches")
    else:
        print(f"  [CLEAN] '{kw}': 0 matches")

print("\n" + "=" * 80)
print("2. DETAILS ON FOUND SUSPICIOUS KEYWORDS IN PARQUET")
print("=" * 80)

for kw in ["guitarra", "amplificacion", "amplificación", "alimentos", "catering", "camioneta"]:
    rows = con.execute(f"""
        SELECT codigo_orden, fecha_aceptacion, comuna_comprador, nombre_proveedor, codigo_producto_onu, monto_linea, texto_descriptivo
        FROM read_parquet('{pq_path}')
        WHERE lower(coalesce(texto_descriptivo, '')) LIKE '%{kw}%'
           OR lower(coalesce(nombre_proveedor, '')) LIKE '%{kw}%'
        LIMIT 5
    """).fetchall()
    if rows:
        print(f"\n--- Keyword '{kw}' (showing up to 5 of {len(rows)}) ---")
        for r in rows:
            print(f"OC: {r[0]} | Comuna: {r[2]} | Prov: {r[3]} | ONU: {r[4]} | Monto: {r[5]}")
            print(f"   Desc: {repr(r[6][:100])}")

print("\n" + "=" * 80)
print("3. PROBING comunas_enriched.json FOR SUSPICIOUS ITEMS ACROSS 345 COMUNAS")
print("=" * 80)

with open(ENRICHED_FILE, "r", encoding="utf-8") as f:
    comunas = json.load(f)

print(f"Total comunas in JSON: {len(comunas)}")

suspicious_vendors = []
suspicious_contracts = []

non_ti_vendor_cues = [
    "carpa", "toldo", "evento", "banquet", "constructora", "seguridad privada",
    "guardia", "alimento", "transporte", "libreria", "librería", "mueble",
    "guitarra", "musica", "música", "gastronom", "agricol", "agrícol"
]

for c in comunas:
    c_name = c["comuna"]
    for p in c.get("top_proveedores", []):
        p_name = p.get("proveedor", "").lower()
        for cue in non_ti_vendor_cues:
            if cue in p_name:
                suspicious_vendors.append((c_name, p["proveedor"], p["monto"], cue))

    for oc in c.get("top_contratos_historicos", []):
        desc = oc.get("descripcion", "").lower()
        p_name = oc.get("proveedor", "").lower()
        for kw in keywords:
            if kw in desc or kw in p_name:
                suspicious_contracts.append((c_name, "historico", oc["codigo_oc"], oc["proveedor"], oc["monto"], kw, desc[:80]))

    for oc in c.get("top_contratos_recientes", []):
        desc = oc.get("descripcion", "").lower()
        p_name = oc.get("proveedor", "").lower()
        for kw in keywords:
            if kw in desc or kw in p_name:
                suspicious_contracts.append((c_name, "reciente", oc["codigo_oc"], oc["proveedor"], oc["monto"], kw, desc[:80]))

print(f"Suspicious vendors in top_proveedores across 345 comunas: {len(suspicious_vendors)}")
for sv in suspicious_vendors[:15]:
    print(f"  {sv[0]}: {sv[1]} (${sv[2]:,.0f} CLP) [cue: {sv[3]}]")

print(f"\nSuspicious contracts in top_contratos across 345 comunas: {len(suspicious_contracts)}")
for sc in suspicious_contracts[:15]:
    print(f"  {sc[0]} [{sc[1]}]: {sc[2]} - {sc[3]} (${sc[4]:,.0f} CLP) [kw: {sc[5]}] - {sc[6]}")

print("\n" + "=" * 80)
print("4. CHECKING UNSPSC CODES AND RUBROS IN SANEADO PARQUET")
print("=" * 80)

onu_summary = con.execute(f"""
    SELECT 
        codigo_producto_onu,
        arbitrary(nombre_producto_generico) as nombre_onu,
        count(*) as ocs,
        round(sum(coalesce(monto_linea, 0)), 0) as total_monto
    FROM read_parquet('{pq_path}')
    GROUP BY codigo_producto_onu
    ORDER BY total_monto DESC
    LIMIT 25
""").df()
print("Top 25 ONU codes by total amount:")
print(onu_summary.to_string())

print("\nCheck ONU code families outside 43xxxxxx, 81xxxxxx, 83xxxxxx, 46xxxxxx, 44xxxxxx, 80xxxxxx:")
strange_onus = con.execute(f"""
    SELECT 
        substring(codigo_producto_onu, 1, 2) as prefix,
        count(*) as count,
        round(sum(coalesce(monto_linea, 0)), 0) as total_monto
    FROM read_parquet('{pq_path}')
    GROUP BY prefix
    ORDER BY total_monto DESC
""").df()
print(strange_onus.to_string())

print("\n" + "=" * 80)
print("5. EDGE CASES AND MISSING VALUES SUMMARY IN PARQUET")
print("=" * 80)

edge_summary = con.execute(f"""
    SELECT 
        count(*) as total_rows,
        count(distinct codigo_orden) as unique_ocs,
        count(CASE WHEN monto_linea IS NULL THEN 1 END) as null_monto,
        count(CASE WHEN isnan(monto_linea) THEN 1 END) as nan_monto,
        count(CASE WHEN monto_linea = 0 THEN 1 END) as zero_monto,
        count(CASE WHEN monto_linea < 0 THEN 1 END) as negative_monto,
        count(CASE WHEN comuna_comprador IS NULL OR trim(comuna_comprador) = '' THEN 1 END) as blank_comuna,
        count(CASE WHEN comuna_comprador IN ('Sin comuna', 'NA', '*', 'Extranjero') THEN 1 END) as placeholder_comuna,
        count(CASE WHEN nombre_proveedor IS NULL OR trim(nombre_proveedor) = '' THEN 1 END) as blank_proveedor,
        count(CASE WHEN texto_descriptivo IS NULL OR trim(texto_descriptivo) = '' THEN 1 END) as blank_texto
    FROM read_parquet('{pq_path}')
""").df()
print(edge_summary.to_string())
con.close()
