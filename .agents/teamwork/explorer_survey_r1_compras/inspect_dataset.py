import duckdb
import sys
sys.stdout.reconfigure(encoding='utf-8')

con = duckdb.connect()

p049_parquet = "D:/Proyectos/P049 - Compras publicas tecnologicas e IA publica/data/processed/candidatos_tecnologicos.parquet"
pub021_parquet = "D:/Proyectos/PUB021 - Paper Adopcion IA y Tecnologias en Municipios/data/catastro_ti_municipal_completo_clasificado.parquet"

print("--- P049 candidatos_tecnologicos.parquet ---")
p049_count = con.execute(f"SELECT count(*) FROM read_parquet('{p049_parquet}')").fetchone()[0]
p049_muni_count = con.execute(f"""
    SELECT count(*) FROM read_parquet('{p049_parquet}')
    WHERE lower(nombre_comprador) LIKE '%municipal%' 
       OR lower(nombre_comprador) LIKE '%muni%'
       OR lower(coalesce(tipo_organismo, '')) LIKE '%municipal%'
""").fetchone()[0]
print(f"Total registros P049: {p049_count:,}")
print(f"Total registros municipales P049: {p049_muni_count:,}")

print("\n--- PUB021 catastro_ti_municipal_completo_clasificado.parquet ---")
pub_count = con.execute(f"SELECT count(*) FROM read_parquet('{pub021_parquet}')").fetchone()[0]
pub_ocs = con.execute(f"SELECT count(distinct codigo_orden) FROM read_parquet('{pub021_parquet}')").fetchone()[0]
pub_comunas = con.execute(f"SELECT count(distinct comuna_comprador) FROM read_parquet('{pub021_parquet}')").fetchone()[0]
print(f"Total registros PUB021: {pub_count:,}")
print(f"Total órdenes de compra únicas (OCs): {pub_ocs:,}")
print(f"Total comunas únicas: {pub_comunas:,}")

# Distribución por años en PUB021
print("\n--- DISTRIBUCIÓN POR AÑO EN PUB021 ---")
anios_df = con.execute(f"""
    SELECT anio, count(*) as items, count(distinct codigo_orden) as ocs, sum(monto_linea) as monto
    FROM read_parquet('{pub021_parquet}')
    GROUP BY anio
    ORDER BY anio
""").df()
print(anios_df.to_string())
