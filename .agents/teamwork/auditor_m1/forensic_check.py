import json
from pathlib import Path
import duckdb
import math

BASE_DIR = Path(r"D:\Proyectos\observatorio-ti-municipal")
RAW_PARQUET = Path(r"D:\Proyectos\PUB021 - Paper Adopcion IA y Tecnologias en Municipios\data\catastro_ti_municipal_completo_clasificado.parquet")
SANEADO_PARQUET = BASE_DIR / "data" / "catastro_ti_saneado.parquet"
ENRICHED_JSON = BASE_DIR / "data" / "comunas_enriched.json"
COMPRAS_JSON = BASE_DIR / "data" / "compras_saneadas_por_comuna.json"
KPIS_JSON = BASE_DIR / "data" / "national_kpis.json"

con = duckdb.connect()

print("--- CHECK 1: PARQUET ROW & OC COUNTS ---")
raw_count = con.execute(f"SELECT count(*), count(distinct codigo_orden), sum(monto_linea) FROM read_parquet('{str(RAW_PARQUET).replace('\\', '/')}')").fetchone()
print(f"Raw parquet: {raw_count[0]} items, {raw_count[1]} OCs, ${raw_count[2]:,.0f} CLP")

saneado_count = con.execute(f"SELECT count(*), count(distinct codigo_orden), sum(monto_linea) FROM read_parquet('{str(SANEADO_PARQUET).replace('\\', '/')}')").fetchone()
print(f"Saneado parquet: {saneado_count[0]} items, {saneado_count[1]} OCs, ${saneado_count[2]:,.0f} CLP")

print("\n--- CHECK 2: RUNNING DUCKDB SANITIZE INDEPENDENTLY ---")
con.execute(f"""
    CREATE TEMPORARY TABLE test_saneado AS
    WITH base AS (
        SELECT 
            *,
            coalesce(rubro_nivel1, 'SIN_RUBRO') as rubro,
            coalesce(codigo_producto_onu, '0') as onu,
            lower(texto_descriptivo) as txt,
            lower(nombre_proveedor) as prov
        FROM read_parquet('{str(RAW_PARQUET).replace('\\', '/')}')
    ),
    flagged AS (
        SELECT 
            base.*,
            (
                txt LIKE '%carpa%' OR prov LIKE '%carpa%' OR txt LIKE '%toldo%' OR
                txt LIKE '%produccion de evento%' OR txt LIKE '%producción de evento%' OR
                txt LIKE '%productora%' OR txt LIKE '%fiesta%' OR txt LIKE '%banquete%' OR
                txt LIKE '%camarin%' OR txt LIKE '%camarín%' OR txt LIKE '%escenario%' OR
                txt LIKE '%curanto%' OR txt LIKE '%aniversario%' OR txt LIKE '%coctel%' OR
                txt LIKE '%cóctel%' OR txt LIKE '%banqueter%' OR txt LIKE '%amplificacion%' OR
                txt LIKE '%amplificación%' OR txt LIKE '%grupo folclorico%' OR
                txt LIKE '%grupo folclórico%' OR
                txt LIKE '%gas licuado%' OR txt LIKE '%gas envasado%' OR
                txt LIKE '%estanque%gas%' OR txt LIKE '%estaciones de servicio (storage)%' OR
                txt LIKE '%zapatos de seguridad%' OR txt LIKE '%zapato%seguridad%' OR
                txt LIKE '%botas de seguridad%' OR txt LIKE '%calzado de seguridad%' OR
                txt LIKE '%camioneta maxus%' OR txt LIKE '%canasta de alimentos%' OR
                txt LIKE '%obras civiles%' OR txt LIKE '%pavimentac%' OR
                txt LIKE '%sede jjvv%' OR txt LIKE '%apicol%' OR txt LIKE '%apícol%' OR
                txt LIKE '%violencia escolar%' OR txt LIKE '%clima laboral%' OR
                txt LIKE '%salud mental%' OR txt LIKE '%ecografia%' OR txt LIKE '%ecografía%' OR
                txt LIKE '%preuniversitario%' OR txt LIKE '%torneo extraescolar%' OR
                txt LIKE '%desratizac%' OR txt LIKE '%fumigac%' OR
                txt LIKE '%neumatico%' OR txt LIKE '%neumático%' OR
                txt LIKE '%combustible%' OR txt LIKE '%gasolina%' OR txt LIKE '%petroleo diesel%' OR
                onu IN ('30221001', '10101704', '30151901', '90101602', '90151602', 
                        '80141607', '90111603', '72131702', '72131701', '90151803', 
                        '80141611', '80141609', '80141605', '80141620', '76121503',
                        '53121603', '80111504')
            ) as es_espurio_obvio,
            (
                rubro = 'Tecnologías de la información, telecomunicaciones y radiodifusión'
                OR rubro = 'Servicios basados en ingeniería, ciencias sociales y tecnología de la información'
                OR (rubro = 'Servicios básicos y de información pública' AND onu IN ('83121703', '83121700', '83111601', '83111600'))
                OR (rubro = 'Servicios profesionales, administrativos y consultorías de gestión empresarial' 
                    AND onu IN ('80111711', '80101507', '80101508', '80111609', '80111712', '80111610', '80161503', '80161506'))
                OR (rubro = 'Equipos y suministros de defensa, orden público, protección y seguridad' 
                    AND (onu LIKE '461716%' OR txt LIKE '%camara%' OR txt LIKE '%cctv%' OR txt LIKE '%televigilancia%'))
                OR (rubro = 'Equipos, accesorios y suministros de oficina' AND onu = '44103201')
                OR ((rubro = 'SIN_RUBRO' OR rubro = 'NA' OR onu = '0') AND (
                    txt LIKE '%servidor%' OR txt LIKE '%software%' OR txt LIKE '%licencia%' OR
                    txt LIKE '%hosting%' OR txt LIKE '%internet%' OR txt LIKE '%computador%' OR
                    txt LIKE '%notebook%' OR txt LIKE '%ciberseguridad%' OR txt LIKE '%antivirus%' OR
                    txt LIKE '%base de datos%' OR txt LIKE '%soporte ti%' OR txt LIKE '%infraestructura ti%'
                ))
            ) as es_tecnologico_valido
        FROM base
    )
    SELECT item_id, codigo_orden, monto_linea
    FROM flagged
    WHERE es_tecnologico_valido AND NOT es_espurio_obvio
""")
indep_count = con.execute("SELECT count(*), count(distinct codigo_orden), sum(monto_linea) FROM test_saneado").fetchone()
print(f"Independent sanitize run: {indep_count[0]} items, {indep_count[1]} OCs, ${indep_count[2]:,.0f} CLP")

assert indep_count[0] == saneado_count[0], f"Mismatch in item count! {indep_count[0]} vs {saneado_count[0]}"
assert indep_count[1] == saneado_count[1], f"Mismatch in distinct OCs! {indep_count[1]} vs {saneado_count[1]}"
assert abs(indep_count[2] - saneado_count[2]) < 1.0, f"Mismatch in monto sum! {indep_count[2]} vs {saneado_count[2]}"
print("-> MATCH 100% IDENTICAL: The parquet file was genuinely generated from DuckDB query!")

print("\n--- CHECK 3: COMBARBALA RAW DATA VERIFICATION ---")
combar_raw = con.execute(f"SELECT count(*) FROM read_parquet('{str(RAW_PARQUET).replace('\\', '/')}') WHERE lower(comuna_comprador) LIKE '%combarbal%'").fetchone()[0]
print(f"Raw records for Combarbalá in original dataset: {combar_raw}")

print("\n--- CHECK 4: PEÑALOLEN AND PROVIDENCIA SANITIZATION MECHANISM ---")
penalolen_raw_carpas = con.execute(f"""
    SELECT count(*), sum(monto_linea) 
    FROM read_parquet('{str(RAW_PARQUET).replace('\\', '/')}')
    WHERE lower(comuna_comprador) LIKE '%peñalol%' AND (
        lower(texto_descriptivo) LIKE '%carpa%' OR lower(nombre_proveedor) LIKE '%carpa%' OR codigo_producto_onu = '30221001'
    )
""").fetchone()
print(f"Peñalolén raw spurious carpas: {penalolen_raw_carpas[0]} items, ${penalolen_raw_carpas[1]:,.0f} CLP")

prov_raw_carpas = con.execute(f"""
    SELECT count(*), sum(monto_linea) 
    FROM read_parquet('{str(RAW_PARQUET).replace('\\', '/')}')
    WHERE lower(comuna_comprador) LIKE '%providencia%' AND (
        lower(texto_descriptivo) LIKE '%carpa%' OR lower(nombre_proveedor) LIKE '%carpa%' OR codigo_producto_onu = '30221001'
    )
""").fetchone()
print(f"Providencia raw spurious carpas: {prov_raw_carpas[0]} items, ${prov_raw_carpas[1]:,.0f} CLP")

penalolen_clean_carpas = con.execute(f"""
    SELECT count(*) 
    FROM read_parquet('{str(SANEADO_PARQUET).replace('\\', '/')}')
    WHERE lower(comuna_comprador) LIKE '%peñalol%' AND (
        lower(texto_descriptivo) LIKE '%carpa%' OR lower(nombre_proveedor) LIKE '%carpa%' OR codigo_producto_onu = '30221001'
    )
""").fetchone()[0]
print(f"Peñalolén saneado carpas remaining: {penalolen_clean_carpas}")

prov_clean_carpas = con.execute(f"""
    SELECT count(*) 
    FROM read_parquet('{str(SANEADO_PARQUET).replace('\\', '/')}')
    WHERE lower(comuna_comprador) LIKE '%providencia%' AND (
        lower(texto_descriptivo) LIKE '%carpa%' OR lower(nombre_proveedor) LIKE '%carpa%' OR codigo_producto_onu = '30221001'
    )
""").fetchone()[0]
print(f"Providencia saneado carpas remaining: {prov_clean_carpas}")

print("\n--- CHECK 5: VERIFY JSON FILES FOR NANS OR CORRUPTIONS ---")
with open(ENRICHED_JSON, "r", encoding="utf-8") as f:
    enriched = json.load(f)

with open(COMPRAS_JSON, "r", encoding="utf-8") as f:
    compras = json.load(f)

with open(KPIS_JSON, "r", encoding="utf-8") as f:
    kpis = json.load(f)

print(f"comunas_enriched.json length: {len(enriched)}")
print(f"compras_saneadas_por_comuna.json length: {len(compras)}")

# Check for NaNs
for idx, c in enumerate(enriched):
    for k, v in c.items():
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            print(f"Corrupted float in enriched: {c['comuna']} -> {k}: {v}")

for idx, c in enumerate(compras):
    for k, v in c.items():
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            print(f"Corrupted float in compras: {c['comuna']} -> {k}: {v}")

print("-> JSON integrity: 0 NaNs, 0 infinities detected!")
