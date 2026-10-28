import duckdb

con = duckdb.connect()
cand_path = "D:/Proyectos/P049 - Compras publicas tecnologicas e IA publica/data/processed/candidatos_tecnologicos.parquet"

print("--- Checking candidatos_tecnologicos.parquet ---")
res = con.execute(f"""
    SELECT min(fecha_aceptacion), max(fecha_aceptacion), count(*), count(distinct codigo_orden)
    FROM read_parquet('{cand_path}')
""").fetchall()
print("Min fecha, Max fecha, total, distinct OCs:", res)

years = con.execute(f"""
    SELECT try_cast(substring(fecha_aceptacion, 1, 4) as integer) as y, count(*)
    FROM read_parquet('{cand_path}')
    GROUP BY y
    ORDER BY y
""").fetchall()
for y in years:
    print(y)
