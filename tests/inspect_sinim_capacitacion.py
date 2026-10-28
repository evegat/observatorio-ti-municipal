import duckdb

con = duckdb.connect()

q = """
    SELECT DISTINCT variable_id, variable, variable_desc, area, subarea
    FROM 'D:/Proyectos/P166 - Personal Municipal de Chile/data/sinim_2019-2023.parquet'
    WHERE variable ILIKE '%capacita%' OR variable_desc ILIKE '%capacita%'
       OR variable ILIKE '%formaci%' OR variable_desc ILIKE '%formaci%'
    ORDER BY variable
"""
vars_cap = con.execute(q).fetchall()
print(f"Variables de capacitación en SINIM ({len(vars_cap)}):")
for v in vars_cap:
    print(f"  [{v[0]}] {v[1]} ({v[3]} / {v[4]})")
