import duckdb

con = duckdb.connect()
p = 'data/catastro_ti_saneado.parquet'
res = con.execute(f"""
    SELECT anio, count(*), count(distinct codigo_orden), sum(monto_linea)
    FROM read_parquet('{p}')
    GROUP BY anio
    ORDER BY anio
""").fetchall()

print("Year breakdown in catastro_ti_saneado.parquet:")
for r in res:
    print(f"Year {r[0]}: {r[1]:>6} items | {r[2]:>6} OCs | ${r[3]:>15,.0f} CLP")
