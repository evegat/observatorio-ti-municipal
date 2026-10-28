import duckdb

con = duckdb.connect()
p = 'data/catastro_ti_saneado.parquet'
words = ['toldo', 'banquete', 'fiesta', 'curanto', 'gas licuado', 'zapato', 'camioneta maxus', 'obras civiles', 'pavimentac', 'apicol', 'desratizac']
for w in words:
    c = con.execute(f"SELECT count(*) FROM read_parquet('{p}') WHERE lower(texto_descriptivo) LIKE '%{w}%'").fetchone()[0]
    print(f"Check {w}: {c}")

# Check ONU codes that are blacklisted
blacklisted_onu = ['30221001', '10101704', '30151901', '90101602', '90151602', '80141607', '90111603', '72131702', '72131701', '90151803', '80141611', '80141609', '80141605', '80141620', '76121503', '53121603', '80111504']
for onu in blacklisted_onu:
    c = con.execute(f"SELECT count(*) FROM read_parquet('{p}') WHERE codigo_producto_onu = '{onu}'").fetchone()[0]
    assert c == 0, f"Leaked ONU {onu}: {c}"
print("All blacklisted ONU codes: 0 in parquet!")
