import duckdb
con = duckdb.connect()
parquet_path = "D:/Proyectos/PUB021 - Paper Adopcion IA y Tecnologias en Municipios/data/catastro_ti_municipal_completo_clasificado.parquet"
res = con.execute(f"""
    SELECT distinct comuna_comprador, nombre_comprador 
    FROM read_parquet('{parquet_path}') 
    WHERE lower(comuna_comprador) LIKE '%combar%' OR lower(nombre_comprador) LIKE '%combar%'
""").fetchall()
print("Matches for combar:", res)
