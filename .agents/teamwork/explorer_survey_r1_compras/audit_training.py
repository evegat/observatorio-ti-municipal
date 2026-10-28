import duckdb
import sys
sys.stdout.reconfigure(encoding='utf-8')

con = duckdb.connect()
parquet_path = "D:/Proyectos/PUB021 - Paper Adopcion IA y Tecnologias en Municipios/data/catastro_ti_municipal_completo_clasificado.parquet"

df = con.execute(f"""
    SELECT 
        codigo_orden,
        anio,
        nombre_comprador,
        nombre_proveedor,
        monto_linea,
        texto_descriptivo
    FROM read_parquet('{parquet_path}')
    WHERE codigo_producto_onu = '80111504'
    ORDER BY monto_linea DESC
    LIMIT 15
""").df()

for idx, r in df.iterrows():
    print(f"[{idx+1}] OC: {r['codigo_orden']} | Anio: {r['anio']} | Monto: ${r['monto_linea']:,.0f} CLP")
    print(f"    Comprador: {r['nombre_comprador']}")
    print(f"    Proveedor: {r['nombre_proveedor']}")
    print(f"    Texto: {r['texto_descriptivo'][:180]}...\n")
