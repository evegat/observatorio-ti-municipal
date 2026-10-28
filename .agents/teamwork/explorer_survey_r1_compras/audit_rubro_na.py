import duckdb
import sys
sys.stdout.reconfigure(encoding='utf-8')

con = duckdb.connect()
parquet_path = "D:/Proyectos/PUB021 - Paper Adopcion IA y Tecnologias en Municipios/data/catastro_ti_municipal_completo_clasificado.parquet"

df = con.execute(f"""
    SELECT 
        codigo_producto_onu,
        nombre_producto_generico,
        count(*) as items,
        count(distinct codigo_orden) as ocs,
        round(sum(monto_linea) / 1e6, 1) as millones_clp
    FROM read_parquet('{parquet_path}')
    WHERE rubro_nivel1 IS NULL OR rubro_nivel1 = 'NA'
    GROUP BY codigo_producto_onu, nombre_producto_generico
    ORDER BY sum(monto_linea) DESC
    LIMIT 25
""").df()

print("--- TOP CÓDIGOS ONU DONDE RUBRO ES NULL / NA ---")
print(df.to_string())
