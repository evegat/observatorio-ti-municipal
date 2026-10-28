import duckdb

con = duckdb.connect()
cand_path = "D:/Proyectos/P049 - Compras publicas tecnologicas e IA publica/data/processed/candidatos_tecnologicos.parquet"
res = con.execute(f"""
    SELECT substring(archivo_origen, 1, 10) as prefix, min(fecha_aceptacion), max(fecha_aceptacion), count(*)
    FROM read_parquet('{cand_path}')
    GROUP BY prefix
    ORDER BY prefix
""").fetchall()
for r in res:
    print(r)
