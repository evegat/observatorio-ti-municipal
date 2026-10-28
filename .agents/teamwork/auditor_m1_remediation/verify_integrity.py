import duckdb
import pathlib
import json

p_in = pathlib.Path(r"D:\Proyectos\PUB021 - Paper Adopcion IA y Tecnologias en Municipios\data\catastro_ti_municipal_completo_clasificado.parquet")
p_out = pathlib.Path(r"D:\Proyectos\observatorio-ti-municipal\data\catastro_ti_saneado.parquet")
p_json = pathlib.Path(r"D:\Proyectos\observatorio-ti-municipal\data\comunas_enriched.json")
p_compras = pathlib.Path(r"D:\Proyectos\observatorio-ti-municipal\data\compras_saneadas_por_comuna.json")

print(f"p_in exists: {p_in.exists()}, size: {p_in.stat().st_size:,} bytes")
print(f"p_out exists: {p_out.exists()}, size: {p_out.stat().st_size:,} bytes")

con = duckdb.connect()

in_stats = con.execute(f"SELECT count(*), count(distinct codigo_orden), round(sum(monto_linea), 0) FROM read_parquet('{str(p_in).replace('\\', '/')}')").fetchone()
print(f"Input Raw: rows={in_stats[0]:,}, ocs={in_stats[1]:,}, monto=${in_stats[2]:,.0f} CLP")

out_stats = con.execute(f"SELECT count(*), count(distinct codigo_orden), round(sum(monto_linea), 0) FROM read_parquet('{str(p_out).replace('\\', '/')}')").fetchone()
print(f"Output Saneado: rows={out_stats[0]:,}, ocs={out_stats[1]:,}, monto=${out_stats[2]:,.0f} CLP")

# Verify all comunas in comunas_enriched.json vs parquet
with open(p_json, encoding="utf-8") as f:
    comunas = json.load(f)

json_total_monto = sum(c["monto_total"] for c in comunas)
json_total_ocs = sum(c["total_ocs"] for c in comunas)
print(f"JSON Aggregates: comunas={len(comunas)}, sum_monto=${json_total_monto:,.0f} CLP, sum_ocs={json_total_ocs:,}")

# Check 68 comunas fragmentation root cause:
# Did duckdb group by comuna_comprador have multiple regions in raw data?
multi_reg = con.execute(f"""
    SELECT comuna_comprador, count(distinct region_comprador) as n_reg, list(distinct region_comprador) as regs
    FROM read_parquet('{str(p_in).replace('\\', '/')}')
    WHERE comuna_comprador IS NOT NULL AND comuna_comprador NOT IN ('Sin comuna', 'NA')
    GROUP BY comuna_comprador
    HAVING count(distinct region_comprador) > 1
""").df()
print(f"Comunas with multiple regions in raw data: {len(multi_reg)}")
print("Sample multi-region comunas in raw:")
print(multi_reg.head(10))

# Check Ovalle and Puerto Montt specifically in raw data
ov_raw = con.execute(f"""
    SELECT comuna_comprador, region_comprador, count(*) as rows, count(distinct codigo_orden) as ocs, round(sum(monto_linea), 0) as monto
    FROM read_parquet('{str(p_in).replace('\\', '/')}')
    WHERE comuna_comprador = 'Ovalle'
    GROUP BY comuna_comprador, region_comprador
""").df()
print("\nOvalle in raw data by region:")
print(ov_raw)

pm_raw = con.execute(f"""
    SELECT comuna_comprador, region_comprador, count(*) as rows, count(distinct codigo_orden) as ocs, round(sum(monto_linea), 0) as monto
    FROM read_parquet('{str(p_in).replace('\\', '/')}')
    WHERE comuna_comprador = 'Puerto Montt'
    GROUP BY comuna_comprador, region_comprador
""").df()
print("\nPuerto Montt in raw data by region:")
print(pm_raw)
