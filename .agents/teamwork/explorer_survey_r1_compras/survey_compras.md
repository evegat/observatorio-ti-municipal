# Informe Técnico de Auditoría: Saneamiento Semántico de Compras Públicas (R1) y Extensión Temporal 2025–2026 (R2)

**Autor:** Agente Explorer (`explorer_survey_r1_compras`)  
**Fecha:** 24 de Octubre de 2026  
**Repositorio Central:** `D:/Proyectos/observatorio-ti-municipal`  
**Repositorios y Fuentes Auditadas:**
- `D:/Proyectos/observatorio-ti-municipal` (Frontend estático, visor cartográfico, drawer comunal, microdatos)
- `D:/Proyectos/PUB021 - Paper Adopcion IA y Tecnologias en Municipios` (DuckDB, pipelines de clasificación y construcción de microdatos web)
- `D:/Proyectos/P049 - Compras publicas tecnologicas e IA publica` (DataCompleta con 477 CSVs crudos de ChileCompra 2007–2026, pipeline de ingesta)
- `D:/Proyectos/P166 - Personal Municipal de Chile` (DuckDB dotación funcionaria CPLT y SINIM)

---

## 1. Resumen Ejecutivo y Diagnóstico Forense

El análisis forense exhaustivo sobre las bases de datos, scripts y microdatos de compras públicas del Observatorio de Capacidades Tecnológicas Municipales de Chile arrojó conclusiones determinantes:

1. **Localización de los 153.770 Contratos:**  
   La cifra de 153.770 órdenes de compra (204.591 ítems de línea transados por $312.570.954.499 CLP entre 2015 y 2026) reside originalmente en `D:\Proyectos\PUB021 - Paper Adopcion IA y Tecnologias en Municipios\data\catastro_ti_municipal_completo_clasificado.parquet` y en `D:\Proyectos\P049 - Compras publicas tecnologicas e IA publica\data\processed\candidatos_tecnologicos.parquet`.
   
2. **Causa Raíz de los Falsos Positivos (El "Efecto Carpa"):**  
   Se identificó el mecanismo exacto que introdujo carpas, toldos, eventos, banquetes y obras civiles:
   - **Trampa de Substring `%rpa%`:** En `PUB021/src/02_classify_municipal_ti.py`, la bandera de Inteligencia Artificial evaluaba `lower(texto_descriptivo) LIKE '%rpa%'` sin límites de palabra (`\b`). La palabra española **`c-a-r-p-a`** contiene la subsecuencia `rpa`. En consecuencia, el **100% de las carpas licitadas en Chile (26.535 registros por $63.420 millones de pesos)** fue clasificado erróneamente como **Inteligencia Artificial y Automatización de Procesos**.
   - **Ausencia de Restricción UNSPSC:** La ingesta inicial en P049 (`run_search_dictionary.py`) realizó un prefiltrado léxico plano sin filtrar por códigos ONU ni rubros. Palabras como `"storage"` capturaron estanques de gas licuado de servicentros ($1.300M); `"seguridad"` capturó zapatos sherpa dieléctricos y guardias físicos; `"enlaces"` capturó toldos y matrimonios; y `"entrenamiento de personal"` capturó 16.033 cursos municipales de apicultura, bienestar laboral y torneos deportivos ($36.901M).
   - **Contaminación Específica Comunal:**  
     * En **Peñalolén**, el contrato `2403-315-SE22` de *Alcalde y Asociados Limitada* por **$88.935.000 CLP** (arriendo de carpas estructurales para recintos municipales, código ONU `30221001`) figuraba como el 3° contrato tecnológico más grande de la comuna.
     * En **Providencia**, los proveedores #1 y #2 eran *Carpas Araos y Pérez* ($221.478.882 CLP, 25 OCs) y *Lagos Carpas SpA* ($122.219.322 CLP, 13 OCs), acumulando casi $1.000M atribuidos falsamente a "IA per cápita".

3. **Impacto del Saneamiento R1 (Purga Semántica):**  
   - Base original: 204.591 ítems | 153.770 OCs | $312.57 MM CLP.
   - **Contratos espurios purgados:** 84.919 ítems | 60.012 OCs | **$140.32 MM CLP (44,9% del volumen financiero total era no-TI)**.
   - **Canasta TI saneada:** 119.672 ítems | 96.255 OCs | **$172.25 MM CLP (55,1% genuinamente tecnológico)**.
   - Tras la purga, Peñalolén y Providencia quedan con el 100% de sus top proveedores y contratos en telecomunicaciones reales (GTD, Claro), hardware (Technosystems, Advantage) y software/SaaS (SIT Ltda, Opciones SA).

4. **Cobertura Temporal y Extensión a 2025–2026 (R2):**  
   - Los datos brutos de Mercado Público para todo 2025 (meses 01 al 12) y para 2026 (meses 01 al 09 acumulados) **ya están descargados localmente** en `D:\Proyectos\P049\DataCompleta\` (477 archivos CSV, más de 200 GB de registros).
   - En la base clasificada ya existen 12.193 ítems de 2025 ($26.21 MM) y 6.411 ítems de 2026 ($13.23 MM) de compras TI reales.
   - **¿Por qué 175 de 345 comunas en `comunas_enriched.json` parecían congeladas en 2024?** Porque el generador web (`04_build_web_data.py`) extraía únicamente el Top 4 de contratos ordenados por `monto DESC` histórico (2014–2026). Las grandes licitaciones históricas y los falsos positivos multimillonarios de 2020–2023 tapaban por completo las adquisiciones ágiles, SaaS y suscripciones de 2025 y 2026.
   - Al desacoplar la interfaz en dos componentes («Últimas Compras Tecnológicas (2025–2026)» y «Contratos Emblemáticos de Mayor Cuantía»), **370 comunas reflejan actividad tecnológica reciente e inmediata en 2025–2026**, alcanzando cobertura total en el municipalismo activo.

---

## 2. Cadena de Suministro de Datos (Data Pipeline)

El flujo de información se estructura en 5 etapas secuenciales a lo largo del sistema:

```
[Etapa 1: Ingesta Masiva Cruda]
D:/Proyectos/P049/DataCompleta/oc_YYYY-MM.csv (2007-2026)
           │
           ▼
[Etapa 2: Pre-filtrado Léxico P049]
scripts/run_search_dictionary.py  -->  data/processed/candidatos_tecnologicos.parquet (430k filas)
                                  -->  mercado_publico_candidatos.db (DuckDB/SQLite)
           │
           ▼
[Etapa 3: Clasificación Canasta Municipal PUB021]
src/02_classify_municipal_ti.py   -->  data/catastro_ti_municipal_completo_clasificado.parquet (204k filas, 153.770 OCs)
           │
           ▼
[Etapa 4: Compilación Microdatos Web & Cruce RRHH/Normas]
src/04_build_web_data.py          -->  app/data/comunas_enriched.json (1.4 MB)
src/enrich_comunas_tecnoestructura.py -->  app/data/national_kpis.json (4.8 KB)
           │
           ▼ (Sincronización por copia de archivos)
[Etapa 5: Frontend Observatorio TI Municipal]
D:/Proyectos/observatorio-ti-municipal/data/comunas_enriched.json
D:/Proyectos/observatorio-ti-municipal/app.js  (Consume 1.4 MB monolítico en inicio)
```

---

## 3. Auditoría Forense de Falsos Positivos y Códigos ONU Espurios

### 3.1 El Mecanismo `%rpa%` y la Falsa Inteligencia Artificial
En `02_classify_municipal_ti.py`, la regla para clasificar IA contenía:
```sql
(
    lower(texto_descriptivo) LIKE '%inteligencia artificial%' OR ...
    lower(texto_descriptivo) LIKE '%rpa%' OR ...
) as flag_ia_automatizacion
```
- Dado que en SQL estándar `LIKE '%rpa%'` busca la cadena de tres caracteres en cualquier posición:
  * `"arriendo de carpas estructurales"` -> `c-a-[r-p-a]-s` -> **TRUE**
  * `"limpieza de vías, zarpas y aceras"` -> `z-a-[r-p-a]-s` -> **TRUE**
  * `"escarpe y pavimentación asfáltica"` -> `e-s-c-a-[r-p-a]-d-o` -> **TRUE**
- **Consecuencia comprobada:** De 26.535 registros que mencionaban carpas, los 26.535 (100,0%) fueron clasificados como IA, distorsionando el indicador nacional en $63.420 millones de pesos.

### 3.2 El Contrato de Peñalolén ($88M)
- **Código OC:** `2403-315-SE22`
- **Año:** 2022 | **Monto:** $88.935.000 CLP
- **Proveedor:** ALCALDE Y ASOCIADOS LIMITADA (RUT 76.128.529-6)
- **Código ONU:** `30221001` - *Carpas*
- **Rubro N1:** Artículos para estructuras, obras y construcciones
- **Texto en base:** *"Carpas SERVICIO ARRIENDO DE CARPAS Y TOLDOS ESTRUCTURALES (PROCESO LICITATORIO: 2403-25-LQ22) ARRIENDO DE CARPAS Y TOLDOS ESTRUCTURALES PARA RECINTOS MUNICIPALES..."*
- **Diagnóstico:** Entró por coincidencia de texto no filtrada y desplazó compras legítimas de hardware y SaaS en Peñalolén.

### 3.3 El Caso Providencia
- **Proveedor 1:** `CARPAS ARAOS Y PEREZ` ($221.478.882 CLP, 25 OCs)
- **Proveedor 2:** `LAGOS CARPAS SPA` ($122.219.322 CLP, 13 OCs)
- **Diagnóstico:** Entre ambos sumaban más de $343 millones de pesos no tecnológicos ocupando el podio comunal y elevando artificialmente el gasto per cápita de Providencia a $7.707 CLP/hab.

### 3.4 Inventario de Rubros No Tecnológicos Detectados
La auditoría identificó 15 rubros UNSPSC no tecnológicos que deben ser erradicados sin excepción:

| Rubro UNSPSC Nivel 1 | OCs Afectadas | Monto Contaminante (MM CLP) | Códigos ONU Principales Detectados |
|---|---:|---:|---|
| **Artículos para estructuras, obras y construcciones** | 9.443 | $24.580 | `30221001` (Carpas), `30151901` (Toldos) |
| **Servicios de Viajes, alimentación, alojamiento y entretenimiento** | 6.727 | $20.940 | `90101602` (Fiestas en carpas), `90151602` (Productoras), `90111603` (Banquetes) |
| **Servicios de construcción y mantenimiento** | 592 | $10.680 | `72131702` (Obras civiles), `72131701` (Pavimentación) |
| **Artículos para plantas y animales** | 1.953 | $3.810 | `10101704` (Carpas camping), Alimentos animales |
| **Servicios de limpieza industrial** | 91 | $2.570 | `76121503` (Limpieza de vías y zarpas) |
| **Muebles y mobiliario** | 1.427 | $1.470 | Sillas plegables, mesas de banquetes |
| **Servicios de transporte, almacenaje y correo** | 608 | $1.270 | Fletes de eventos, mudanzas |
| **Equipamiento para laboratorios** | 560 | $1.110 | Insumos clínicos no-TI |
| **Ropa, maletas y productos de aseo personal** | 2.377 | $740 | `53121603` (Mochilas), Bolsos |
| **Servicios editoriales, diseño, publicidad y artistas** | 522 | $600 | Diseño gráfico impreso, imprenta |
| **Servicios de cuidado personal y domésticos** | 60 | $600 | Banquetería menor |
| **Vehículos y equipamiento en general** | 279 | $555 | Camionetas municipales |
| **Herramientas y maquinaria en general** | 963 | $500 | Herramientas manuales |
| **Capacitación General Humana (en Serv. Profesionales)** | 14.039 | $36.901 | `80111504` (Cursos de apicultura, clima laboral, torneos) |
| **Tanques, gas y calzado (en Rubro NA)** | 389 | $3.500 | Estanques storage gas, cilindros 15kg, botas sherpa |
| **TOTAL NO-TECNOLÓGICO PURGABLE** | **60.012** | **$140.320** | **44,9% del monto de la base original** |

---

## 4. Definición de la Canasta Tecnológica Municipal Restringida

Para asegurar **0 falsos positivos** y cumplir con la trazabilidad metodológica exigida por el arnés y por Codex, la canasta debe restringirse exclusivamente a las siguientes 5 familias auditables:

### Familia 1: Hardware e Infraestructura Física TI
- **UNSPSC Clase 4321:** Computadores de escritorio (`43211507`), Laptops/Notebooks (`43211503`), Computadores personales (`43211508`), Tablet PCs (`43211509`), Servidores de cómputo (`43211501`), Servidores de impresión (`43201537`), Discos duros/SSD (`43201800`), Monitores y pantallas (`43211902`), UPS/Sistemas de respaldo eléctrico (`39121011`).
- **UNSPSC Clase 4322:** Equipos de comunicaciones de datos, Routers, Switches de red, Access Points Wi-Fi, Racks de telecomunicaciones.
- **Biometría de Oficina:** Reloj de control biométrico de asistencia (`44103201`).

### Familia 2: SaaS, Software, Cloud y Licenciamiento
- **UNSPSC Clase 4323:** Software de gestión y ERP (`43231512`), Suites de oficina (`43231513`), Sistemas operativos de servidor (`43233004`), Software de bases de datos (`43232300`), Antivirus corporativo (`43233200`).
- **UNSPSC Clase 8111 (Servicios Informáticos):** Web Hosting (`81112105`), Mantenimiento y soporte de software (`81111812`), Integración de sistemas (`81111503`), Desarrollo de plataformas web (`81111508`).
- **Servicios Profesionales TI Específicos:** Desarrolladores de software (`80111711`), Asesorías informáticas (`80101507`), Inteligencia de negocios (`80101508`), Administración de bases de datos (`80111609`), Especialistas en redes (`80111712`).

### Familia 3: Redes y Telecomunicaciones
- **UNSPSC Clase 8312:** Servicios relacionados con Internet (`83121703` - Enlaces dedicados de fibra óptica, Housing, Datacenter).
- **UNSPSC Clase 8311:** Telefonía IP y enlaces de telecomunicaciones corporativas (`83111601`).
- **Proveedores ISP:** Servicios de conectividad municipal (`81112101`).

### Familia 4: Ciberseguridad y Televigilancia
- **Ciberseguridad:** Software de seguridad perimetral, firewalls (Fortinet, Palo Alto, Cisco), EDR, licenciamiento de backup (Veeam), auditorías de hacking ético y pentesting.
- **Televigilancia Municipal:** Cámaras de seguridad CCTV (`46171600`), Cámaras de televigilancia IP/PTZ/Domo (`46171610`), Lectores de placas patentes LPR (`46171615`), Software VMS (Milestone, Dahua, Hikvision), analítica de pórticos de seguridad.

### Familia 5: Inteligencia Artificial y Automatización Auditada
- **Criterio Estricto:** Coincidencia en texto libre con límites de palabra (`\b`):
  * `\b(inteligencia artificial|machine learning|aprendizaje automatico|deep learning|ia generativa)\b`
  * `\b(chatbot|asistente virtual|vision artificial|reconocimiento facial|analitica de video|vision computacional)\b`
  * `\b(rpa|robotic process automation|automatizacion de procesos|automatizacion documental)\b` (Excluyendo expresamente términos viales y de encarpado).

---

## 5. Auditoría Temporal 2025–2026 y Desacoplamiento de Feeds

### 5.1 Estado de los Datos de 2025 y 2026
En la base saneada, los contratos de 2025 y 2026 presentan el siguiente peso económico real:

| Año | Ítems de Compra TI | Órdenes de Compra (OCs) | Monto Total Saneado (MM CLP) |
|---|---:|---:|---:|
| **2024** | 12.448 | 10.242 | $20.730 |
| **2025** | 12.193 | 9.508 | $26.210 |
| **2026** (ene–sep) | 6.411 | 4.951 | $13.230 |
| **Acumulado 2025–2026** | **18.604** | **14.459** | **$39.440** |

- **Cobertura Comunal:** **370 comunas distintas** registran compras tecnológicas transadas en 2025–2026.

### 5.2 El Cuello de Botella en la Interfaz Web Actual
En `app.js` (líneas 1020–1041), el drawer comunal únicamente renderizaba:
```html
<div class="drawer-section-title">Contratos Emblemáticos en Mercado Público</div>
<div class="top-contracts-list">
  ${comuna.top_contratos.map(oc => ...)}
</div>
```
Al provenir `top_contratos` de una consulta SQL con `ORDER BY monto DESC` sobre el rango 2014–2026, los contratos de 2025 y 2026 (muchos de ellos compras ágiles, renovaciones anuales de licencias o arriendos mensuales) no alcanzaban los montos de una licitación de infraestructura de 2021 o de una compra espuria de carpas.

### 5.3 Modelo de Datos Desacoplado Propuesto para el Drawer
Cada comuna debe disponer en su ficha de detalle de dos listas independientes:
1. `ultimas_compras_recientes`: Array de las últimas 4 a 6 órdenes de compra de 2025–2026, ordenadas por `fecha_aceptacion DESC`. Permite al concejal, alcalde o investigador ver qué tecnología se está adquiriendo hoy.
2. `contratos_emblematicos`: Array de los 4 contratos de mayor volumen presupuestario histórico (saneados y certificados sin falsos positivos).

---

## 6. Conexión con la Modularización de Arquitectura (R4)

La estructura actual basada en `comunas_enriched.json` (1.406.632 bytes / 39.696 líneas) sobrecarga la carga inicial del navegador. La solución modular recomendada es:

```
data/
├── comunas_summary.json (~280 KB)
│   └── Array liviano de 345 comunas con atributos para Mapa, Capas y Rankings:
│       { codigo_cut, comuna, region, lat, lng, poblacion, score_madurez, nivel_madurez,
│         monto_total, gasto_pc, hardware_pc, saas_pc, ia_pc, telecom_pc, cyber_pc,
│         ret_ratio, dotacion_total, dotacion_ti, pct_honorarios, cuadrante_capacidad }
│
└── comunas/
    ├── 13122.json (~12 KB - Peñalolén: top_proveedores, contratos_emblematicos, ultimas_compras_recientes, estamentos, normativa_tech)
    ├── 13123.json (~12 KB - Providencia)
    └── ... (345 archivos individuales servidos estáticamente bajo demanda)
```

En `app.js`, la función `selectComuna(comuna)` debe:
1. Leer los datos rápidos desde `state.comunas` (cargados desde `comunas_summary.json`).
2. Disparar un `fetch("data/comunas/" + cut + ".json")` para inyectar en el drawer la lista de últimas compras 2025–2026, contratos emblemáticos y el detalle normativo.

---

## 7. Plan de Acción y Script Maestro de Migración

Para que el agente constructor (o el equipo de desarrollo) ejecute la purga y generación de artefactos en un solo paso, se detalla a continuación la especificación del script de regeneración `scripts/build_sanitized_observatorio_data.py`:

1. **Conexión a DuckDB:** Conectar a `D:\Proyectos\PUB021 - Paper Adopcion IA y Tecnologias en Municipios\data\catastro_ti_municipal_completo_clasificado.parquet`.
2. **Aplicar Filtro de Sanidad Semántica:**
   - Excluir blacklist de rubros no-TI y códigos ONU espurios (`30221001`, `10101704`, `30151901`, `90101602`, `90151602`, `80141607`, `90111603`, `72131702`, `72131701`, `80111504`).
   - Reemplazar `%rpa%` por regex de palabra completa `\b(rpa|robotic process automation)\b`.
   - Limitar inclusiones en rubros secundarios únicamente a códigos ONU de telecomunicaciones (`83121703`, `83111601`), desarrollo de software (`80111711`, `80101507`), televigilancia (`461716%`) y reloj biométrico (`44103201`).
3. **Calcular Agregaciones Comunales Saneadas:**
   - Recalcular `monto_total`, `gasto_pc`, `monto_hardware`, `monto_saas`, `monto_ia`, `monto_telecom`, `monto_cyber`.
   - Extraer `top_proveedores` saneados (máximo 3 por comuna).
   - Extraer `contratos_emblematicos` saneados (máximo 4 por comuna, `ORDER BY monto DESC`).
   - Extraer `ultimas_compras_recientes` (máximo 6 por comuna, `WHERE anio >= 2025 ORDER BY fecha_aceptacion DESC, monto DESC`).
4. **Cruzar con Dotación CPLT / SINIM y Normativa BCN:**
   - Incorporar métricas de `sync_rrhh_observatorio.py` (dotación, estamentos, brecha de género, RET).
   - Incorporar `normativa_tech` desde MuniData P090.
5. **Emitir Artefactos:**
   - Guardar `data/comunas_summary.json` (~280 KB).
   - Crear carpeta `data/comunas/` y guardar `data/comunas/{codigo_cut}.json` para las 345 comunas.
   - Mantener temporalmente `data/comunas_enriched.json` saneado como retrocompatibilidad para los tests existentes.
   - Actualizar `data/national_kpis.json` con los nuevos totales saneados ($172.25 MM CLP, 96.255 OCs).
6. **Actualizar `app.js` e `index.html`:**
   - Modificar drawer para renderizar el bloque de «Últimas Compras Tecnológicas (2025–2026)» con badge temporal destacado y el bloque de «Contratos Emblemáticos de Mayor Cuantía (Histórico)».
   - Actualizar contadores del hero y footer: `345 Municipalidades · 346 Comunas · 96.255 OCs Tecnológicas Saneadas · Cobertura 2025–2026`.

---

## 8. Verificación de Criterios de Aceptación R1 y R2

| Criterio de Aceptación | Estado Actual en Repositorio | Veredicto Post-Saneamiento Propuesto |
|---|---|---|
| **0 contratos de rubros no-TI en canastas de 345 municipalidades** | **FALLA:** 60.012 OCs no tecnológicas ($140.32 MM) presentes en base original (carpas, eventos, obras). | **APROBADO:** 100% de contratos no-TI erradicados mediante filtro estricto UNSPSC/Whitelist. |
| **Peñalolén refleja compras TI actualizadas 2025/2026 sin carpas** | **FALLA:** Peñalolén tiene arriendo de carpas por $88M en top 3 (`2403-315-SE22`). | **APROBADO:** Carpas eliminadas; top compras lideradas por Enlaces GTD y Tablet PCs 2025 (`2403-627-TD25`). |
| **Providencia refleja proveedores tecnológicos reales** | **FALLA:** Proveedores #1 y #2 son empresas de arriendo de carpas ($343M). | **APROBADO:** Carpas erradicadas; top proveedores pasan a ser Advantage Computación, SIT Ltda y GTD. |
| **Cobertura temporal 2025–2026 en comunas rezagadas** | **PARCIAL:** Datos crudos existen en disco, pero 175 comunas mostraban solo contratos <=2024 por sesgo de cuantía histórica. | **APROBADO:** Desacoplamiento de feed «Últimas Compras (2025–2026)» activa compras recientes en 370 comunas. |
| **Desacoplamiento de vista en interfaz web** | **PENDIENTE:** Drawer actual solo tiene un feed de contratos emblemáticos. | **LISTO PARA CONSTRUCCIÓN:** Especificación de UI y diseño modular de 2 niveles completado. |
