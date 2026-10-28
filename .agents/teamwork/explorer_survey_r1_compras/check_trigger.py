import duckdb
import sys
sys.stdout.reconfigure(encoding='utf-8')

con = duckdb.connect()
parquet_candidatos = "D:/Proyectos/P049 - Compras publicas tecnologicas e IA publica/data/processed/candidatos_tecnologicos.parquet"

q = f"""
SELECT 
    item_id,
    codigo_orden,
    fecha_aceptacion,
    nombre_comprador,
    comuna_comprador,
    nombre_proveedor,
    codigo_producto_onu,
    nombre_producto_generico,
    rubro_nivel1,
    rubro_nivel2,
    rubro_nivel3,
    monto_linea,
    texto_descriptivo,
    reglas_gatillo,
    score
FROM read_parquet('{parquet_candidatos}')
WHERE codigo_orden = '2403-315-SE22'
"""

df = con.execute(q).df()
print(df.to_dict(orient='records'))
