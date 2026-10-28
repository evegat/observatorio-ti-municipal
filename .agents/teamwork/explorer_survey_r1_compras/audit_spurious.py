import duckdb
import sys

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

parquet_path = "D:/Proyectos/PUB021 - Paper Adopcion IA y Tecnologias en Municipios/data/catastro_ti_municipal_completo_clasificado.parquet"
con = duckdb.connect()

print("--- TOP 10 REGISTROS DE PEÑALOLÉN ---")
query_pena = f"""
SELECT 
    codigo_orden,
    anio,
    nombre_comprador,
    comuna_comprador,
    nombre_proveedor,
    codigo_producto_onu,
    nombre_producto_generico,
    rubro_nivel1,
    rubro_nivel2,
    monto_linea,
    texto_descriptivo
FROM read_parquet('{parquet_path}')
WHERE lower(comuna_comprador) LIKE '%peñalol%' OR lower(nombre_comprador) LIKE '%peñalol%'
ORDER BY monto_linea DESC
LIMIT 10
"""

df_pena = con.execute(query_pena).df()
for idx, r in df_pena.iterrows():
    print(f"\n[{idx+1}] OC: {r['codigo_orden']} | Anio: {r['anio']} | Monto: ${r['monto_linea']:,.0f} CLP")
    print(f"    Proveedor: {r['nombre_proveedor']}")
    print(f"    ONU: {r['codigo_producto_onu']} - {r['nombre_producto_generico']}")
    print(f"    Rubro: {r['rubro_nivel1']} -> {r['rubro_nivel2']}")
    print(f"    Texto: {r['texto_descriptivo'][:120]}...")

