import duckdb
import glob

con = duckdb.connect()
oc_2014 = glob.glob("D:/Proyectos/P049 - Compras publicas tecnologicas e IA publica/DataCompleta/oc_2014-*.csv")
print(f"Found {len(oc_2014)} files for oc_2014")

if oc_2014:
    # check first file schema
    print("Reading first 2014 file:", oc_2014[0])
    try:
        sample = con.execute(f"SELECT * FROM read_csv_auto('{oc_2014[0]}', ignore_errors=true) LIMIT 3").df()
        print("Columns:", sample.columns.tolist())
        # Check if any municipal
        muni_count = con.execute(f"""
            SELECT count(*) 
            FROM read_csv_auto('{oc_2014[0]}', ignore_errors=true)
            WHERE lower(NombreComprador) LIKE '%municipal%'
        """).fetchone()[0]
        print("Municipal purchases in month 1:", muni_count)
    except Exception as e:
        print("Error reading 2014 file:", e)

# Also check candidatos_tecnologicos.parquet: why did it start at 2015?
cand_path = "D:/Proyectos/P049 - Compras publicas tecnologicas e IA publica/data/processed/candidatos_tecnologicos.parquet"
sample_cand = con.execute(f"SELECT min(fecha_aceptacion), max(fecha_aceptacion) FROM read_parquet('{cand_path}')").fetchall()
print("candidatos_tecnologicos min/max date:", sample_cand)
