import duckdb
import sys
sys.stdout.reconfigure(encoding='utf-8')

con = duckdb.connect()
p049_parquet = "D:/Proyectos/P049 - Compras publicas tecnologicas e IA publica/data/processed/candidatos_tecnologicos.parquet"

df = con.execute(f"""
    SELECT 
        codigo_orden, 
        codigo_producto_onu, 
        nombre_producto_generico,
        texto_descriptivo, 
        reglas_gatillo,
        archivo_origen
    FROM read_parquet('{p049_parquet}')
    WHERE codigo_producto_onu IN ('30221001', '90101602', '10101704', '80141607')
      AND (lower(nombre_comprador) LIKE '%municipal%' OR lower(coalesce(tipo_organismo, '')) LIKE '%municipal%')
    LIMIT 10
""").df()

for idx, r in df.iterrows():
    print(f"[{idx+1}] OC: {r['codigo_orden']} | ONU: {r['codigo_producto_onu']} - {r['nombre_producto_generico']}")
    print(f"    Gatillo: {r['reglas_gatillo']}")
    print(f"    Origen: {r['archivo_origen']}")
    print(f"    Texto: {r['texto_descriptivo'][:140]}...\n")
