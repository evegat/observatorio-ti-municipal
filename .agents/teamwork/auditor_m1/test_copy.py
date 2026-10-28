import duckdb
from pathlib import Path

con = duckdb.connect()
con.execute('CREATE TABLE t AS SELECT 1 as a')
out = Path('data/catastro_ti_saneado_test.parquet')
out.write_text('dummy')
try:
    con.execute(f"COPY t TO '{str(out).replace('\\', '/')}' (FORMAT PARQUET)")
    print("Success overwriting!")
except Exception as e:
    print("Caught exception:", type(e), e)
if out.exists():
    out.unlink()
