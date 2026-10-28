import duckdb
import sys
sys.stdout.reconfigure(encoding='utf-8')

con = duckdb.connect()
parquet_path = "D:/Proyectos/PUB021 - Paper Adopcion IA y Tecnologias en Municipios/data/catastro_ti_municipal_completo_clasificado.parquet"

# Agrupar por rubro_nivel1 y ver totales
rubros = con.execute(f"""
    SELECT 
        coalesce(rubro_nivel1, 'SIN_RUBRO') as rubro,
        count(distinct codigo_orden) as ocs,
        round(sum(monto_linea)/1e9, 2) as monto_mm,
        count(distinct codigo_producto_onu) as distinct_onus
    FROM read_parquet('{parquet_path}')
    GROUP BY coalesce(rubro_nivel1, 'SIN_RUBRO')
    ORDER BY sum(monto_linea) DESC
""").df()

print("--- TODOS LOS RUBROS EN EL CATASTRO MUNICIPAL ---")
for idx, r in rubros.iterrows():
    print(f"{r['rubro']:<75} | {r['ocs']:>6} OCs | ${r['monto_mm']:>7.2f} MM | ONUs: {r['distinct_onus']}")
