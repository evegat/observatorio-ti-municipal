import duckdb

con = duckdb.connect()
parquet_path = "D:/Proyectos/PUB021 - Paper Adopcion IA y Tecnologias en Municipios/data/catastro_ti_municipal_completo_clasificado.parquet"

q = f"""
SELECT 
    count(*) as total_carpas,
    count(case when flag_ia_automatizacion then 1 end) as carpas_as_ia,
    sum(case when flag_ia_automatizacion then monto_linea else 0 end) as monto_carpas_as_ia
FROM read_parquet('{parquet_path}')
WHERE lower(texto_descriptivo) LIKE '%carpa%'
"""

res = con.execute(q).fetchone()
print(f"Total registros con carpa: {res[0]:,}")
print(f"Registros con carpa clasificados como IA: {res[1]:,} ({res[1]*100/res[0]:.1f}%)")
print(f"Monto de carpas clasificado como IA: ${res[2]/1e9:,.2f} MM CLP")
