#!/usr/bin/env python3
"""
Inspect non-TI items in catastro_ti_saneado.parquet
"""
from pathlib import Path
import duckdb

DATA_DIR = Path("D:/Proyectos/observatorio-ti-municipal/data")
PARQUET_FILE = DATA_DIR / "catastro_ti_saneado.parquet"
con = duckdb.connect()

print("=" * 80)
print("INSPECTING 'zapato / bota seguridad' IN PARQUET:")
print("=" * 80)
rows = con.execute(f"""
    SELECT codigo_orden, fecha_aceptacion, comuna_comprador, nombre_proveedor,
           codigo_producto_onu, nombre_producto_generico, monto_linea, texto_descriptivo
    FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')
    WHERE lower(texto_descriptivo) LIKE '%zapato%' 
       OR lower(texto_descriptivo) LIKE '%calzado%' 
       OR lower(texto_descriptivo) LIKE '%bota%'
    LIMIT 10
""").fetchall()
for r in rows:
    print(r)

print("\n" + "=" * 80)
print("INSPECTING 'camioneta' IN PARQUET:")
print("=" * 80)
rows = con.execute(f"""
    SELECT codigo_orden, fecha_aceptacion, comuna_comprador, nombre_proveedor,
           codigo_producto_onu, nombre_producto_generico, monto_linea, texto_descriptivo
    FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')
    WHERE lower(texto_descriptivo) LIKE '%camioneta%'
""").fetchall()
for r in rows:
    print(r)
