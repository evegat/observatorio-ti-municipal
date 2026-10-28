import duckdb
import glob

con = duckdb.connect()
files_2014 = glob.glob("D:/Proyectos/P049 - Compras publicas tecnologicas e IA publica/DataCompleta/oc_2014-*.csv")
print(f"Checking {len(files_2014)} files for 2014...")

# Let's inspect columns and check if any match municipal buyers
query = f"""
    SELECT count(*) 
    FROM read_csv_auto('D:/Proyectos/P049 - Compras publicas tecnologicas e IA publica/DataCompleta/oc_2014-*.csv', union_by_name=true, ignore_errors=true)
    WHERE lower(OrganismoPublico) LIKE '%municipal%' 
       OR lower(OrganismoPublico) LIKE '%muni%'
"""
try:
    total_2014_muni = con.execute(query).fetchone()[0]
    print(f"Total 2014 municipal items: {total_2014_muni}")
except Exception as e:
    print("Error:", e)
