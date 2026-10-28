import duckdb

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
        (
            txt LIKE '%carpa%' OR prov LIKE '%carpa%' OR txt LIKE '%toldo%' OR
            txt LIKE '%produccion de evento%' OR txt LIKE '%producción de evento%' OR
            txt LIKE '%productora%' OR txt LIKE '%fiesta%' OR txt LIKE '%banquete%' OR
            txt LIKE '%camarin%' OR txt LIKE '%camarín%' OR txt LIKE '%escenario%' OR
            txt LIKE '%curanto%' OR txt LIKE '%aniversario%' OR txt LIKE '%coctel%' OR
            txt LIKE '%cóctel%' OR txt LIKE '%banqueter%' OR txt LIKE '%amplificacion%' OR
            txt LIKE '%amplificación%' OR txt LIKE '%grupo folclorico%' OR
            txt LIKE '%grupo folclórico%' OR
            txt LIKE '%gas licuado%' OR txt LIKE '%gas envasado%' OR
            txt LIKE '%estanque%gas%' OR txt LIKE '%estaciones de servicio (storage)%' OR
            txt LIKE '%zapatos de seguridad%' OR txt LIKE '%zapato%seguridad%' OR
            txt LIKE '%botas de seguridad%' OR txt LIKE '%calzado de seguridad%' OR
            txt LIKE '%camioneta maxus%' OR txt LIKE '%canasta de alimentos%' OR
            txt LIKE '%obras civiles%' OR txt LIKE '%pavimentac%' OR
            txt LIKE '%sede jjvv%' OR txt LIKE '%apicol%' OR txt LIKE '%apícol%' OR
            txt LIKE '%violencia escolar%' OR txt LIKE '%clima laboral%' OR
            txt LIKE '%salud mental%' OR txt LIKE '%ecografia%' OR txt LIKE '%ecografía%' OR
            txt LIKE '%preuniversitario%' OR txt LIKE '%torneo extraescolar%' OR
            txt LIKE '%desratizac%' OR txt LIKE '%fumigac%' OR
            txt LIKE '%neumatico%' OR txt LIKE '%neumático%' OR
            txt LIKE '%combustible%' OR txt LIKE '%gasolina%' OR txt LIKE '%petroleo diesel%' OR
            onu IN ('30221001', '10101704', '30151901', '90101602', '90151602', 
                    '80141607', '90111603', '72131702', '72131701', '90151803', 
                    '80141611', '80141609', '80141605', '80141620', '76121503',
                    '53121603', '80111504')
        ) as es_espurio_obvio,
        (
            rubro = 'Tecnologías de la información, telecomunicaciones y radiodifusión'
            OR rubro = 'Servicios basados en ingeniería, ciencias sociales y tecnología de la información'
            OR (rubro = 'Servicios básicos y de información pública' AND onu IN ('83121703', '83121700', '83111601', '83111600'))
            OR (rubro = 'Servicios profesionales, administrativos y consultorías de gestión empresarial' 
                AND onu IN ('80111711', '80101507', '80101508', '80111609', '80111712', '80111610', '80161503', '80161506'))
            OR (rubro = 'Equipos y suministros de defensa, orden público, protección y seguridad' 
                AND (onu LIKE '461716%' OR txt LIKE '%camara%' OR txt LIKE '%cctv%' OR txt LIKE '%televigilancia%'))
            OR (rubro = 'Equipos, accesorios y suministros de oficina' AND onu = '44103201')
            OR ((rubro = 'SIN_RUBRO' OR rubro = 'NA' OR onu = '0') AND (
                txt LIKE '%servidor%' OR txt LIKE '%software%' OR txt LIKE '%licencia%' OR
                txt LIKE '%hosting%' OR txt LIKE '%internet%' OR txt LIKE '%computador%' OR
                txt LIKE '%notebook%' OR txt LIKE '%ciberseguridad%' OR txt LIKE '%antivirus%' OR
                txt LIKE '%base de datos%' OR txt LIKE '%soporte ti%' OR txt LIKE '%infraestructura ti%'
            ))
        ) as es_tecnologico_valido,
        (
            regexp_matches(txt, '\\b(inteligencia artificial|machine learning|aprendizaje automatico|aprendizaje automático|deep learning|ia generativa)\\b')
            OR regexp_matches(txt, '\\b(chatbot|asistente virtual|vision artificial|visión artificial|reconocimiento facial|analitica de video|analítica de video|vision computacional|visión computacional)\\b')
            OR regexp_matches(txt, '\\b(rpa|robotic process automation|automatizacion de procesos|automatización de procesos|automatizacion documental|automatización documental)\\b')
        ) as flag_ia_saneada,
        (
            onu LIKE '4321%' OR onu LIKE '4322%' OR onu LIKE '4320%' OR
            txt LIKE '%servidor%' OR txt LIKE '%server%' OR txt LIKE '%computador%' OR 
            txt LIKE '%desktop%' OR txt LIKE '%notebook%' OR txt LIKE '%laptop%' OR 
            txt LIKE '%tablet%' OR txt LIKE '%all in one%' OR txt LIKE '%pantalla%' OR 
            txt LIKE '%monitor%' OR txt LIKE '%disco duro%' OR txt LIKE '%ssd%' OR 
            txt LIKE '%ups%' OR txt LIKE '%rack%' OR txt LIKE '%datacenter%' OR 
            txt LIKE '%almacenamiento san%' OR txt LIKE '%storage%'
        ) as flag_hardware_saneada,
        (
            onu LIKE '4323%' OR onu IN ('81112105', '81111812', '81111503', '81111508') OR
            txt LIKE '%saas%' OR txt LIKE '%software as a service%' OR txt LIKE '%suscripci%' OR 
            txt LIKE '%licenciamiento anual%' OR txt LIKE '%nube%' OR txt LIKE '%cloud%' OR 
            txt LIKE '%microsoft 365%' OR txt LIKE '%office 365%' OR txt LIKE '%m365%' OR 
            txt LIKE '%azure%' OR txt LIKE '%google workspace%' OR txt LIKE '%g suite%' OR 
            txt LIKE '%aws%' OR txt LIKE '%amazon web services%' OR txt LIKE '%hosting%' OR 
            txt LIKE '%vps%' OR prov LIKE '%microsoft%' OR prov LIKE '%amazon%' OR prov LIKE '%google%'
        ) as flag_saas_saneada,
        (
            onu LIKE '8312%' OR onu LIKE '8311%' OR onu IN ('83121703', '83121700', '83111601', '83111600') OR
            txt LIKE '%enlace%' OR txt LIKE '%fibra optica%' OR txt LIKE '%fibra óptica%' OR 
            txt LIKE '%internet dedicado%' OR txt LIKE '%conexion de internet%' OR 
            txt LIKE '%telefonia ip%' OR txt LIKE '%telefonía ip%' OR 
            txt LIKE '%central telefonica%' OR txt LIKE '%central telefónica%' OR 
            prov LIKE '%gtd%' OR prov LIKE '%entel%' OR prov LIKE '%telefonica%' OR 
            prov LIKE '%telefónica%' OR prov LIKE '%claro%' OR prov LIKE '%mundo pacifico%' OR prov LIKE '%vtr%'
        ) as flag_telecom_saneada,
        (
            txt LIKE '%ciberseguridad%' OR txt LIKE '%seguridad de la informacion%' OR 
            txt LIKE '%seguridad informatica%' OR txt LIKE '%seguridad informática%' OR 
            txt LIKE '%firewall%' OR txt LIKE '%fortinet%' OR txt LIKE '%palo alto%' OR 
            txt LIKE '%antivirus%' OR txt LIKE '%soc%' OR txt LIKE '%edr%' OR 
            txt LIKE '%pentesting%' OR txt LIKE '%hacking etico%' OR txt LIKE '%hacking ético%' OR 
            txt LIKE '%veeam%'
        ) as flag_cyber_saneada
    FROM base
)
SELECT 
    count(*) as total_items,
    count(distinct codigo_orden) as total_ocs,
    round(sum(monto_linea), 0) as total_monto,
    round(sum(case when flag_hardware_saneada then monto_linea else 0 end), 0) as hardware_monto,
    round(sum(case when flag_saas_saneada then monto_linea else 0 end), 0) as saas_monto,
    round(sum(case when flag_telecom_saneada then monto_linea else 0 end), 0) as telecom_monto,
    round(sum(case when flag_cyber_saneada then monto_linea else 0 end), 0) as cyber_monto,
    round(sum(case when flag_ia_saneada then monto_linea else 0 end), 0) as ia_monto
FROM flagged
WHERE es_tecnologico_valido AND NOT es_espurio_obvio
"""

res = con.execute(sql).df()
print(res.to_string())
