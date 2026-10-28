import duckdb
import sys
sys.stdout.reconfigure(encoding='utf-8')

con = duckdb.connect()

# Reutilizar evaluacion_ti desde simulate_sanitized_basket o re-crear
from simulate_sanitized_basket import sanitization_sql

df_years = con.execute(f"""
    WITH evaluacion_ti AS ({sanitization_sql})
    SELECT 
        anio,
        count(*) as items,
        count(distinct codigo_orden) as ocs,
        round(sum(monto_linea)/1e9, 2) as mm_clp
    FROM evaluacion_ti
    WHERE es_tecnologico_valido AND NOT es_espurio_obvio
    GROUP BY anio
    ORDER BY anio
""").df()

print("--- DISTRIBUCIÓN TEMPORAL DE COMPRAS TI SANEADAS ---")
print(df_years.to_string())

# Ver cobertura de comunas en 2025 y 2026
df_comunas_recientes = con.execute(f"""
    WITH evaluacion_ti AS ({sanitization_sql})
    SELECT 
        count(distinct case when anio >= 2025 then comuna_comprador end) as comunas_con_2025_2026,
        count(distinct comuna_comprador) as total_comunas
    FROM evaluacion_ti
    WHERE es_tecnologico_valido AND NOT es_espurio_obvio
      AND comuna_comprador IS NOT NULL AND comuna_comprador NOT IN ('Sin comuna', 'NA', 'Extranjero', '*')
""").df()
print("\n--- COBERTURA COMUNAL RECIENTE (2025-2026) EN BASE SANEADA ---")
print(df_comunas_recientes.to_string())
