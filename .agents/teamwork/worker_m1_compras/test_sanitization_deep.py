import duckdb
import sys
sys.stdout.reconfigure(encoding='utf-8')

con = duckdb.connect()
parquet_path = "D:/Proyectos/PUB021 - Paper Adopcion IA y Tecnologias en Municipios/data/catastro_ti_municipal_completo_clasificado.parquet"

sql = f"""
WITH base AS (
    SELECT 
        *,
        coalesce(rubro_nivel1, 'SIN_RUBRO') as rubro,
        coalesce(codigo_producto_onu, '0') as onu,
        lower(texto_descriptivo) as txt,
        lower(nombre_proveedor) as prov
    FROM read_parquet('{parquet_path}')
),
flagged AS (
    SELECT 
        base.*,
        
        -- Blacklist de términos espurios no-TI
        (
            txt LIKE '%carpa%' OR prov LIKE '%carpa%' OR txt LIKE '%toldo%' OR
            txt LIKE '%produccion de evento%' OR txt LIKE '%producción de evento%' OR
            txt LIKE '%productora%' OR txt LIKE '%fiesta%' OR txt LIKE '%banquete%' OR
            txt LIKE '%camarin%' OR txt LIKE '%camarín%' OR txt LIKE '%escenario%' OR
            txt LIKE '%curanto%' OR txt LIKE '%aniversario%' OR txt LIKE '%coctel%' OR
            txt LIKE '%cóctel%' OR txt LIKE '%banqueter%' OR txt LIKE '%amplificacion%' OR
            txt LIKE '%amplificación%' OR txt LIKE '%grupo folclorico%' OR
            txt LIKE '%gas licuado%' OR txt LIKE '%gas envasado%' OR
            txt LIKE '%estanque%gas%' OR txt LIKE '%estaciones de servicio (storage)%' OR
            txt LIKE '%zapatos de seguridad%' OR txt LIKE '%zapato%seguridad%' OR
            txt LIKE '%camioneta maxus%' OR txt LIKE '%canasta de alimentos%' OR
            txt LIKE '%obras civiles%' OR txt LIKE '%pavimentac%' OR
            txt LIKE '%sede jjvv%' OR txt LIKE '%apicol%' OR txt LIKE '%apícol%' OR
            txt LIKE '%violencia escolar%' OR txt LIKE '%clima laboral%' OR
            txt LIKE '%salud mental%' OR txt LIKE '%ecografia%' OR txt LIKE '%ecografía%' OR
            txt LIKE '%preuniversitario%' OR txt LIKE '%torneo extraescolar%' OR
            onu IN ('30221001', '10101704', '30151901', '90101602', '90151602', 
                    '80141607', '90111603', '72131702', '72131701', '90151803', 
                    '80141611', '80141609', '80141605', '80141620', '76121503',
                    '53121603', '80111504')
        ) as es_espurio_obvio,

        -- Whitelist de rubros y ONUs tecnológicos
        (
            -- 1. Rubro TI principal
            rubro = 'Tecnologías de la información, telecomunicaciones y radiodifusión'
            
            -- 2. Rubro Servicios TI e Ingeniería
            OR rubro = 'Servicios basados en ingeniería, ciencias sociales y tecnología de la información'
            
            -- 3. Servicios básicos: SOLO Internet y Telecom
            OR (rubro = 'Servicios básicos y de información pública' AND onu IN ('83121703', '83121700', '83111601', '83111600'))
            
            -- 4. Servicios profesionales: SOLO desarrollo de software, consultoría TI, BI, bases de datos
            OR (rubro = 'Servicios profesionales, administrativos y consultorías de gestión empresarial' 
                AND onu IN ('80111711', '80101507', '80101508', '80111609', '80111712', '80111610', '80161503', '80161506'))
            
            -- 5. Equipos de seguridad: SOLO CCTV / Televigilancia / Control acceso
            OR (rubro = 'Equipos y suministros de defensa, orden público, protección y seguridad' 
                AND (onu LIKE '461716%' OR txt LIKE '%camara%' OR txt LIKE '%cctv%' OR txt LIKE '%televigilancia%'))
            
            -- 6. Oficina: SOLO reloj control biométrico
            OR (rubro = 'Equipos, accesorios y suministros de oficina' AND onu = '44103201')
            
            -- 7. Registros con rubro NA / Sin rubro: SOLO si tienen descripción técnica TI inequívoca
            OR ((rubro = 'SIN_RUBRO' OR rubro = 'NA') AND (
                txt LIKE '%servidor%' OR txt LIKE '%software%' OR txt LIKE '%licencia%' OR
                txt LIKE '%hosting%' OR txt LIKE '%internet%' OR txt LIKE '%computador%' OR
                txt LIKE '%notebook%' OR txt LIKE '%ciberseguridad%' OR txt LIKE '%antivirus%' OR
                txt LIKE '%base de datos%' OR txt LIKE '%soporte ti%' OR txt LIKE '%infraestructura ti%'
            ))
        ) as es_tecnologico_valido,

        -- Banderas reclasificadas con IA estricta (sin bug %rpa%)
        (
            regexp_matches(txt, '\\b(inteligencia artificial|machine learning|aprendizaje automatico|aprendizaje automático|deep learning|ia generativa)\\b')
            OR regexp_matches(txt, '\\b(chatbot|asistente virtual|vision artificial|visión artificial|reconocimiento facial|analitica de video|analítica de video|vision computacional|visión computacional)\\b')
            OR regexp_matches(txt, '\\b(rpa|robotic process automation|automatizacion de procesos|automatización de procesos|automatizacion documental|automatización documental)\\b')
        ) as flag_ia_saneada

    FROM base
)
SELECT * FROM flagged
"""

con.execute(f"CREATE TABLE saneado AS {sql} WHERE es_tecnologico_valido AND NOT es_espurio_obvio")

print("--- TOP PROVEEDORES PEÑALOLÉN ---")
pena_prov = con.execute("""
    SELECT nombre_proveedor, count(distinct codigo_orden) as ocs, round(sum(monto_linea), 0) as monto
    FROM saneado
    WHERE lower(comuna_comprador) LIKE '%peñalol%'
    GROUP BY nombre_proveedor
    ORDER BY monto DESC
    LIMIT 5
""").df()
print(pena_prov.to_string())

print("\n--- TOP CONTRATOS HISTÓRICOS PEÑALOLÉN ---")
pena_top = con.execute("""
    SELECT codigo_orden, anio, fecha_aceptacion, nombre_proveedor, round(sum(monto_linea),0) as monto, arbitrary(texto_descriptivo) as descr
    FROM saneado
    WHERE lower(comuna_comprador) LIKE '%peñalol%'
    GROUP BY codigo_orden, anio, fecha_aceptacion, nombre_proveedor
    ORDER BY monto DESC
    LIMIT 5
""").df()
print(pena_top.to_string())

print("\n--- TOP CONTRATOS RECIENTES 2025-2026 PEÑALOLÉN ---")
pena_rec = con.execute("""
    SELECT codigo_orden, anio, fecha_aceptacion, nombre_proveedor, round(sum(monto_linea),0) as monto, arbitrary(texto_descriptivo) as descr
    FROM saneado
    WHERE lower(comuna_comprador) LIKE '%peñalol%' AND anio >= 2025
    GROUP BY codigo_orden, anio, fecha_aceptacion, nombre_proveedor
    ORDER BY fecha_aceptacion DESC, monto DESC
    LIMIT 5
""").df()
print(pena_rec.to_string())

print("\n--- TOP PROVEEDORES PROVIDENCIA ---")
provi_prov = con.execute("""
    SELECT nombre_proveedor, count(distinct codigo_orden) as ocs, round(sum(monto_linea),0) as monto
    FROM saneado
    WHERE lower(comuna_comprador) = 'providencia'
    GROUP BY nombre_proveedor
    ORDER BY monto DESC
    LIMIT 5
""").df()
print(provi_prov.to_string())
