import duckdb
import sys
sys.stdout.reconfigure(encoding='utf-8')

con = duckdb.connect()
parquet_path = "D:/Proyectos/PUB021 - Paper Adopcion IA y Tecnologias en Municipios/data/catastro_ti_municipal_completo_clasificado.parquet"

print("--- TOP 25 RUBROS NIVEL 1 EN PUB021 ---")
r1_df = con.execute(f"""
    SELECT 
        rubro_nivel1,
        count(*) as items,
        count(distinct codigo_orden) as ocs,
        round(sum(monto_linea) / 1e9, 2) as monto_mil_millones
    FROM read_parquet('{parquet_path}')
    GROUP BY rubro_nivel1
    ORDER BY items DESC
    LIMIT 25
""").df()
print(r1_df.to_string())

print("\n--- TOP 30 CÓDIGOS ONU EN PUB021 ---")
onu_df = con.execute(f"""
    SELECT 
        codigo_producto_onu,
        nombre_producto_generico,
        rubro_nivel1,
        count(*) as items,
        count(distinct codigo_orden) as ocs,
        round(sum(monto_linea) / 1e9, 2) as monto_mil_millones
    FROM read_parquet('{parquet_path}')
    GROUP BY codigo_producto_onu, nombre_producto_generico, rubro_nivel1
    ORDER BY items DESC
    LIMIT 30
""").df()
print(onu_df.to_string())
