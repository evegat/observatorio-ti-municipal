import duckdb

con = duckdb.connect()
query = """
SELECT count(*), count(distinct Codigo)
FROM read_csv_auto('D:/Proyectos/P049 - Compras publicas tecnologicas e IA publica/DataCompleta/oc_2014-*.csv', union_by_name=true, ignore_errors=true)
WHERE (lower(OrganismoPublico) LIKE '%municipal%' OR lower(OrganismoPublico) LIKE '%muni%')
  AND (
    RubroN1 = 'Tecnolog\u00edas de la informaci\u00f3n, telecomunicaciones y radiodifusi\u00f3n'
    OR codigoProductoONU LIKE '4321%'
    OR codigoProductoONU LIKE '4323%'
    OR codigoProductoONU LIKE '8111%'
  )
"""
try:
    res = con.execute(query).fetchall()
    print("2014 tech items in DataCompleta:", res)
except Exception as e:
    print("Error:", e)
