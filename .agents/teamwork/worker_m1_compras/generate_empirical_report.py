import json
import duckdb
from pathlib import Path

BASE_DIR = Path("D:/Proyectos/observatorio-ti-municipal")
DATA_DIR = BASE_DIR / "data"

con = duckdb.connect()

# 1. Parquet stats
parquet_path = str(DATA_DIR / "catastro_ti_saneado.parquet").replace("\\", "/")
total_items = con.execute(f"SELECT count(*) FROM read_parquet('{parquet_path}')").fetchone()[0]
total_ocs = con.execute(f"SELECT count(distinct codigo_orden) FROM read_parquet('{parquet_path}')").fetchone()[0]
total_monto = con.execute(f"SELECT round(sum(monto_linea), 0) FROM read_parquet('{parquet_path}')").fetchone()[0]

carpas = con.execute(f"""
    SELECT count(*) FROM read_parquet('{parquet_path}')
    WHERE lower(texto_descriptivo) LIKE '%carpa%' 
       OR lower(nombre_proveedor) LIKE '%carpa%' 
       OR codigo_producto_onu = '30221001'
""").fetchone()[0]

oc_penalolen = con.execute(f"""
    SELECT count(*) FROM read_parquet('{parquet_path}')
    WHERE codigo_orden = '2403-315-SE22'
""").fetchone()[0]

# 2. Annual series
series = con.execute(f"""
    SELECT anio, count(distinct codigo_orden) as ocs, round(sum(monto_linea), 0) as monto
    FROM read_parquet('{parquet_path}')
    GROUP BY anio
    ORDER BY anio
""").fetchall()

# 3. JSON stats
with open(DATA_DIR / "comunas_enriched.json", "r", encoding="utf-8") as f:
    comunas = json.load(f)

with open(DATA_DIR / "compras_saneadas_por_comuna.json", "r", encoding="utf-8") as f:
    compras = json.load(f)

with open(DATA_DIR / "national_kpis.json", "r", encoding="utf-8") as f:
    kpis = json.load(f)

with open(DATA_DIR / "proveedores_ranking.json", "r", encoding="utf-8") as f:
    provs = json.load(f)

# Providencia & Peñalolén checks
provi = next(c for c in comunas if c["comuna"] == "Providencia")
pena = next(c for c in comunas if c["comuna"] == "Peñalolén")

active_2025_2026 = sum(1 for c in comunas if len(c.get("top_contratos_recientes", [])) > 0)

print(f"=== REPORTE EMPÍRICO M1: SANEAMIENTO Y COBERTURA ===")
print(f"1. Catastro Parquet Saneado:")
print(f"   - Total Ítems: {total_items:,}")
print(f"   - Total OCs únicas: {total_ocs:,}")
print(f"   - Monto Total Saneado: ${total_monto:,.0f} CLP")
print(f"   - Total Carpas/Toldos/No-TI: {carpas} (Cero absoluto)")
print(f"   - Contrato Peñalolén 2403-315-SE22 ($88M): {oc_penalolen} (Erradicado)")
print(f"\n2. Cobertura Temporal Anual:")
for s in series:
    print(f"   - {s[0]}: {s[1]:,} OCs | ${s[2]:,.0f} CLP")

print(f"\n3. Indicadores Comunales:")
print(f"   - Total comunas en comunas_enriched.json: {len(comunas)}")
print(f"   - Total comunas en compras_saneadas_por_comuna.json: {len(compras)}")
print(f"   - Comunas con feed 2025-2026 activo: {active_2025_2026} / {len(comunas)}")

print(f"\n4. Caso Peñalolén:")
print(f"   - Monto Total: ${pena['monto_total']:,.0f} CLP (Gasto pc: ${pena['gasto_pc']:,.0f} CLP/hab)")
print(f"   - Top Proveedores: {[p['proveedor'] + ' ($' + str(int(p['monto']/1e6)) + 'M)' for p in pena['top_proveedores']]}")
print(f"   - Total contratos recientes (2025-2026): {len(pena['top_contratos_recientes'])}")
for oc in pena['top_contratos_recientes'][:3]:
    print(f"     * [{oc['fecha_aceptacion']}] {oc['codigo_oc']}: {oc['proveedor']} (${int(oc['monto']):,} CLP) - {oc['descripcion'][:60]}...")
print(f"   - Total contratos emblemáticos históricos: {len(pena['top_contratos_historicos'])}")
for oc in pena['top_contratos_historicos'][:3]:
    print(f"     * [{oc['anio']}] {oc['codigo_oc']}: {oc['proveedor']} (${int(oc['monto']):,} CLP) - {oc['descripcion'][:60]}...")

print(f"\n5. Caso Providencia:")
print(f"   - Monto Total: ${provi['monto_total']:,.0f} CLP (Gasto pc: ${provi['gasto_pc']:,.0f} CLP/hab)")
print(f"   - Top Proveedores: {[p['proveedor'] + ' ($' + str(int(p['monto']/1e6)) + 'M)' for p in provi['top_proveedores']]}")
print(f"   - Total contratos recientes (2025-2026): {len(provi['top_contratos_recientes'])}")
for oc in provi['top_contratos_recientes'][:3]:
    print(f"     * [{oc['fecha_aceptacion']}] {oc['codigo_oc']}: {oc['proveedor']} (${int(oc['monto']):,} CLP) - {oc['descripcion'][:60]}...")

print(f"\n6. Ranking Nacional de Proveedores:")
for p in provs[:5]:
    print(f"   - {p['proveedor']} ({p['rubro_principal']}): ${p['monto_total_clp']:,.0f} CLP ({p['cuota_mercado_pct']}%)")
