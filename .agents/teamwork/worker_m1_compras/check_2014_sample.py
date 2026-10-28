import duckdb

con = duckdb.connect()
sample = con.execute("SELECT OrganismoPublico, UnidadCompra, codigoProductoONU, RubroN1, FechaAceptacion FROM read_csv_auto('D:/Proyectos/P049 - Compras publicas tecnologicas e IA publica/DataCompleta/oc_2014-01.csv', ignore_errors=true) LIMIT 5").df()
print(sample.to_string())
