import duckdb

con = duckdb.connect()
PARQUET_IN = r"D:\Proyectos\PUB021 - Paper Adopcion IA y Tecnologias en Municipios\data\catastro_ti_municipal_completo_clasificado.parquet"

q_test = f"""
WITH base AS (
    SELECT 
        *,
        lower(coalesce(texto_descriptivo, '')) as txt,
        coalesce(codigo_producto_onu, '0') as onu,
        lower(coalesce(nombre_proveedor, '')) as prov,
        coalesce(rubro_nivel1, 'SIN_RUBRO') as rubro
    FROM '{PARQUET_IN}'
),
flagged AS (
    SELECT 
        *,
        -- Espurios
        (
            txt LIKE '%carpa%' OR txt LIKE '%toldos%' OR txt LIKE '%banqueter%' OR
            txt LIKE '%coffee%' OR txt LIKE '%coffe break%' OR txt LIKE '%colacion%' OR
            onu IN ('30221001', '10101704', '90101602', '80141607')
        ) as es_espurio,

        -- Whitelist
        (
            rubro = 'Tecnologías de la información, telecomunicaciones y radiodifusión'
            OR (rubro = 'Servicios basados en ingeniería, ciencias sociales y tecnología de la información' AND onu LIKE '8111%')
            OR (rubro = 'Servicios básicos y de información pública' AND onu IN ('83121703', '83121700', '83111601', '83111600'))
            OR (rubro = 'Servicios profesionales, administrativos y consultorías de gestión empresarial' AND (
                onu IN ('80111711', '80101507', '80111609', '80111712', '80111610', '80161503', '80161506')
                OR (onu = '80101508' AND (txt LIKE '%inteligencia artificial%' OR txt LIKE '%software%' OR txt LIKE '%datos%'))
            ))
            OR (rubro = 'Equipos y suministros de defensa, orden público, protección y seguridad' AND (onu LIKE '461716%' OR txt LIKE '%camara%' OR txt LIKE '%televigilancia%'))
            OR (rubro = 'Equipos, accesorios y suministros de oficina' AND onu = '44103201')
            OR ((rubro = 'SIN_RUBRO' OR rubro = 'NA' OR onu = '0') AND (
                txt LIKE '%servidor%' OR txt LIKE '%software%' OR txt LIKE '%licencia%' OR
                txt LIKE '%hosting%' OR txt LIKE '%internet%' OR txt LIKE '%computador%'
            ))
            -- CAPACITACIONES TI
            OR (
                (onu LIKE '8613%' OR onu IN ('86132100', '86132101', '86132102', '86101700', '80111600') OR
                 rubro = 'Servicios educativos y de formación' OR
                 txt LIKE '%capacita%' OR txt LIKE '%curso%' OR txt LIKE '%taller%' OR txt LIKE '%alfabetiza%digital%')
                AND (
                    txt LIKE '%excel%' OR txt LIKE '%ofimat%' OR txt LIKE '%word%' OR txt LIKE '%computac%' OR 
                    txt LIKE '%informat%' OR txt LIKE '%software%' OR txt LIKE '%ciberseguridad%' OR 
                    txt LIKE '%seguridad de la informac%' OR txt LIKE '%siaper%' OR txt LIKE '%erp%' OR 
                    txt LIKE '%cas-chile%' OR txt LIKE '%gestion documental%' OR txt LIKE '%docdigital%' OR 
                    txt LIKE '%transformacion digital%' OR txt LIKE '%inteligencia artificial%' OR 
                    txt LIKE '%programac%' OR txt LIKE '%redes%'
                )
            )
        ) as es_tecnologico_valido,

        -- Flag Capacitacion
        (
            (onu LIKE '8613%' OR onu IN ('86132100', '86132101', '86132102', '86101700', '80111600') OR
             txt LIKE '%capacita%' OR txt LIKE '%curso%' OR txt LIKE '%taller%' OR txt LIKE '%alfabetiza%digital%')
            AND (
                txt LIKE '%excel%' OR txt LIKE '%ofimat%' OR txt LIKE '%word%' OR txt LIKE '%computac%' OR 
                txt LIKE '%informat%' OR txt LIKE '%software%' OR txt LIKE '%ciberseguridad%' OR 
                txt LIKE '%seguridad de la informac%' OR txt LIKE '%siaper%' OR txt LIKE '%erp%' OR 
                txt LIKE '%cas-chile%' OR txt LIKE '%gestion documental%' OR txt LIKE '%docdigital%' OR 
                txt LIKE '%transformacion digital%' OR txt LIKE '%inteligencia artificial%' OR 
                txt LIKE '%programac%' OR txt LIKE '%redes%'
            )
        ) as flag_capacitacion_ti,

        CASE 
            WHEN (txt LIKE '%alfabetizacion digital%' OR txt LIKE '%adulto mayor%' OR txt LIKE '%adultos mayores%' OR txt LIKE '%comunitaria%' OR txt LIKE '%vecinos%' OR txt LIKE '%junta de vecinos%') 
            THEN 'alfabetizacion_comunitaria'
            ELSE 'institucional_funcionarios'
        END as subcategoria_capacitacion

    FROM base
)
SELECT 
    COUNT(*) as total_filas,
    COUNT(DISTINCT codigo_orden) as total_ocs,
    ROUND(SUM(monto_linea), 0) as monto_total_clp,
    COUNT(CASE WHEN flag_capacitacion_ti THEN 1 END) as filas_cap,
    COUNT(DISTINCT CASE WHEN flag_capacitacion_ti THEN codigo_orden END) as ocs_cap,
    ROUND(SUM(CASE WHEN flag_capacitacion_ti THEN monto_linea ELSE 0 END), 0) as monto_cap_clp,
    ROUND(SUM(CASE WHEN flag_capacitacion_ti AND subcategoria_capacitacion = 'institucional_funcionarios' THEN monto_linea ELSE 0 END), 0) as cap_funcionarios,
    ROUND(SUM(CASE WHEN flag_capacitacion_ti AND subcategoria_capacitacion = 'alfabetizacion_comunitaria' THEN monto_linea ELSE 0 END), 0) as cap_comunitaria
FROM flagged
WHERE es_tecnologico_valido AND NOT es_espurio
"""

res = con.execute(q_test).df()
print("--- RESULTADOS INTEGRACIÓN DE CAPACITACIONES EN CATASTRO TI ---")
print(res.to_string())
