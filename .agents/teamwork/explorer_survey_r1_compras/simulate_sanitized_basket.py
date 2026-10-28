import duckdb
import sys
sys.stdout.reconfigure(encoding='utf-8')

con = duckdb.connect()
parquet_path = "D:/Proyectos/PUB021 - Paper Adopcion IA y Tecnologias en Municipios/data/catastro_ti_municipal_completo_clasificado.parquet"

print("=================================================================")
print("SIMULACIÓN DE CANASTA TECNOLÓGICA SANEADA (FILTRO AUDITABLE ONU/TI)")
print("=================================================================")

# Definir reglas de inclusión positiva y exclusión negativa
sanitization_sql = f"""
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
                    '80141611', '80141609', '80141605', '80141620')
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
        ) as es_tecnologico_valido
    FROM base
)
SELECT * FROM flagged
"""

con.execute(f"CREATE TEMP TABLE evaluacion_ti AS {sanitization_sql}")

total_raw = con.execute("SELECT count(*), count(distinct codigo_orden), sum(monto_linea) FROM evaluacion_ti").fetchone()
total_espurio = con.execute("SELECT count(*), count(distinct codigo_orden), sum(monto_linea) FROM evaluacion_ti WHERE es_espurio_obvio OR NOT es_tecnologico_valido").fetchone()
total_valido = con.execute("SELECT count(*), count(distinct codigo_orden), sum(monto_linea) FROM evaluacion_ti WHERE es_tecnologico_valido AND NOT es_espurio_obvio").fetchone()

print(f"Total Base Original: {total_raw[0]:,} ítems | {total_raw[1]:,} OCs | ${total_raw[2]/1e9:,.2f} MM CLP")
print(f"Total Espurio/No-TI: {total_espurio[0]:,} ítems | {total_espurio[1]:,} OCs | ${total_espurio[2]/1e9:,.2f} MM CLP ({total_espurio[2]*100/total_raw[2]:.1f}% del monto)")
print(f"Total TI Saneado:   {total_valido[0]:,} ítems | {total_valido[1]:,} OCs | ${total_valido[2]/1e9:,.2f} MM CLP ({total_valido[2]*100/total_raw[2]:.1f}% del monto)")

print("\n--- CASO PEÑALOLÉN TRAS SANEAMIENTO ---")
pena_top = con.execute("""
    SELECT codigo_orden, anio, nombre_proveedor, monto_linea, texto_descriptivo
    FROM evaluacion_ti
    WHERE (lower(comuna_comprador) LIKE '%peñalol%' OR lower(nombre_comprador) LIKE '%peñalol%')
      AND es_tecnologico_valido AND NOT es_espurio_obvio
    ORDER BY monto_linea DESC
    LIMIT 5
""").df()
for idx, r in pena_top.iterrows():
    print(f"[{idx+1}] OC: {r['codigo_orden']} ({r['anio']}) | Prov: {r['nombre_proveedor']} | ${r['monto_linea']:,.0f} CLP")
    print(f"    {r['texto_descriptivo'][:120]}...")

print("\n--- CASO PROVIDENCIA TRAS SANEAMIENTO (TOP PROVEEDORES) ---")
provi_prov = con.execute("""
    SELECT nombre_proveedor, count(distinct codigo_orden) as ocs, sum(monto_linea) as monto
    FROM evaluacion_ti
    WHERE lower(comuna_comprador) = 'providencia'
      AND es_tecnologico_valido AND NOT es_espurio_obvio
    GROUP BY nombre_proveedor
    ORDER BY monto DESC
    LIMIT 5
""").df()
print(provi_prov.to_string())
