import duckdb

parquet_path = "D:/Proyectos/PUB021 - Paper Adopcion IA y Tecnologias en Municipios/data/catastro_ti_municipal_completo_clasificado.parquet"
con = duckdb.connect()

query = f"""
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
    rubro_nivel3,
    monto_linea,
    texto_descriptivo
FROM read_parquet('{parquet_path}')
WHERE lower(texto_descriptivo) LIKE '%carpa%' 
   OR lower(nombre_proveedor) LIKE '%carpa%'
ORDER BY monto_linea DESC
LIMIT 15
"""

df = con.execute(query).df()
print(f"Total registros con carpa: {len(df)}")
for idx, r in df.iterrows():
    print(f"\n[{idx+1}] OC: {r['codigo_orden']} | Anio: {r['anio']} | Comuna: {r['comuna_comprador']}")
    print(f"    Comprador: {r['nombre_comprador']}")
    print(f"    Proveedor: {r['nombre_proveedor']}")
    print(f"    ONU: {r['codigo_producto_onu']} - {r['nombre_producto_generico']}")
    print(f"    Rubro: {r['rubro_nivel1']} -> {r['rubro_nivel2']} -> {r['rubro_nivel3']}")
    print(f"    Monto: ${r['monto_linea']:,.0f} CLP")
    print(f"    Texto: {str(r['texto_descriptivo'])[:180]}...")
