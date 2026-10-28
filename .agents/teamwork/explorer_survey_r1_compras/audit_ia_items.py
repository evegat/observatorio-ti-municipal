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
        codigo_producto_onu,
        nombre_producto_generico,
        monto_linea,
        texto_descriptivo
    FROM read_parquet('{parquet_path}')
    WHERE flag_ia_automatizacion = true
    ORDER BY monto_linea DESC
    LIMIT 10
""").df()

print("--- TOP 10 ÍTEMS CLASIFICADOS COMO IA / AUTOMATIZACIÓN ---")
for idx, r in df.iterrows():
    print(f"[{idx+1}] OC: {r['codigo_orden']} ({r['anio']}) | Monto: ${r['monto_linea']:,.0f} CLP")
    print(f"    Comprador: {r['nombre_comprador']} | Prov: {r['nombre_proveedor']}")
    print(f"    ONU: {r['codigo_producto_onu']} - {r['nombre_producto_generico']}")
    print(f"    Texto: {r['texto_descriptivo'][:130]}...\n")
