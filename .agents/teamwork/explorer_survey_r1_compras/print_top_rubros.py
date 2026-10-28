import duckdb
import sys
sys.stdout.reconfigure(encoding='utf-8')

con = duckdb.connect()
parquet_path = "D:/Proyectos/PUB021 - Paper Adopcion IA y Tecnologias en Municipios/data/catastro_ti_municipal_completo_clasificado.parquet"

df = con.execute(f"""
    SELECT 
        coalesce(rubro_nivel1, 'SIN_RUBRO') as rubro,
        count(*) as items,
        count(distinct codigo_orden) as ocs,
        round(sum(monto_linea) / 1e9, 2) as mm_clp,
        round(sum(monto_linea) * 100.0 / sum(sum(monto_linea)) over(), 2) as pct
    FROM read_parquet('{parquet_path}')
    GROUP BY coalesce(rubro_nivel1, 'SIN_RUBRO')
    ORDER BY sum(monto_linea) DESC
    LIMIT 20
""").df()

print(df.to_string())
