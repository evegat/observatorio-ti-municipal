# Auditoría Integral y Diagnóstico Técnico: Ingesta de Nóminas Web Autónomas (Requerimiento R3)

**Fecha**: 2026-10-24  
**Agente**: `explorer_survey_r2_nominas`  
**Objetivo**: Diagnóstico integral de la infraestructura de datos de Recursos Humanos municipales, estado de las comunas autónomas sin CPLT, análisis de `portal_autonomo_harvester.py`, base DuckDB `personal_municipal.duckdb`, script `sync_rrhh_observatorio.py` y cumplimiento del estándar de privacidad Ley N° 21.719 con HMAC-SHA256 al corte de septiembre 2026.

---

## 1. Resumen Ejecutivo

1. **Estado Actual de Cobertura Observada**: De las 345 municipalidades del país (346 comunas), el dataset de producción `data/comunas_enriched.json` tiene actualmente **318 comunas (92.2%) con datos observados reales** provenientes de CPLT Transparencia Activa en DuckDB y **27 comunas (7.8%) con estimaciones sintéticas** derivadas de un modelo fallback sobre SUBDERE SINIM (año 2023).
2. **Erradicación de Ratios Teóricos**: El script `scripts/sync_rrhh_observatorio.py` contiene una estimación paramétrica en las líneas 169–175: `ti_tot = max(1, round(total * 0.016))`, que imputa un 1.6% de personal TI a todas las comunas sin registro en DuckDB. Cumplir con el criterio de aceptación de R3 (**"100% de las 345 comunas con datos observados de dotación activa, sin ratios teóricos"**) exige eliminar este fallback y cargar datos nominales reales en DuckDB para las 27 comunas rezagadas.
3. **Localización del Harvester**: `portal_autonomo_harvester.py` fue localizado en `D:/Proyectos/P166 - Personal Municipal de Chile/src/portal_autonomo_harvester.py`. Cuenta con un detector dinámico de encabezados de planillas (`encontrar_fila_header`), un parser de planillas Excel (`parsear_planilla_excel`) y un cargador idempotente hacia DuckDB (`insertar_registros_en_duckdb`). Sin embargo, carece de crawler web HTTP automatizado (requiere archivos locales `.xls`/`.xlsx`) y no tiene soporte para archivos delimitados `.csv`.
4. **Catastro de las 19 Comunas Autónomas**: En el directorio institucional `cplt_municipal_directory.json` existen **21 municipios fuera de la plataforma centralizada CPLT** (`ta_status != 'portal'`). De ellos, 2 ya cuentan con registros parciales en DuckDB (Providencia y Puente Alto, solo estamento Planta de sep-2026). Quedan exactamente **19 comunas autónomas sin datos observados** (Alto Hospicio, Ancud, Cabrero, Calama, Castro, Concón, Contulmo, Curacaví, Curepto, Hualañé, Longaví, Lota, Melipilla, Purén, Recoleta, San Pedro de Atacama, San Rafael, Temuco y Teodoro Schmidt).
5. **Hallazgo Crítico sobre Comunas con Falla CPLT**: Adicionalmente, existen **8 comunas** catalogadas formalmente como `ta_status: "portal"` en CPLT (entre ellas **Las Condes (MU135)**, Antofagasta, Copiapó, Chonchi, Colchane, Nueva Imperial, Quinta de Tilcoco y Rauco) que devuelven `total_records: 0` al ser consultadas vía CPLT Liferay/PrimeFaces, ya sea porque gestionan su propio portal externo (ej. Las Condes) o porque sus tablas en CPLT están vacías. Total de comunas a subsanar: 19 autónomas + 8 CPLT vacías = 27 comunas.
6. **Cumplimiento Ley N° 21.719**: El módulo `privacy_hasher.py` implementa seudonimización criptográfica unidireccional vía HMAC-SHA256 truncada a 16 caracteres hexadecimales (`hash_person_identifier` y `hash_run`), purgando nombres y RUN antes de la persistencia analítica.
7. **Corte Temporal Septiembre 2026**: En DuckDB, 260 comunas tienen registros al corte exacto de septiembre 2026 (`202609`), 37 comunas a agosto 2026 (`202608`) y 23 comunas en fechas previas.

---

## 2. Localización y Análisis de `portal_autonomo_harvester.py`

### 2.1. Ficha Técnica del Módulo
- **Ruta Absoluta**: `D:/Proyectos/P166 - Personal Municipal de Chile/src/portal_autonomo_harvester.py`
- **Líneas de Código**: 146 líneas.
- **Dependencias Principales**: `pandas`, `re`, `logging`, `pathlib`, `src.cplt_schema_normalizer.CanonicalPersonalRecord`, `src.privacy_hasher.hash_person_identifier`, `src.agent_ready_backend.AgentReadyBackend`.

### 2.2. Arquitectura Interna y Componentes
El script implementa tres funciones modulares:

1. **`encontrar_fila_header(df_raw: pd.DataFrame) -> Optional[int]`**:
   - Inspecciona las primeras 25 filas de un DataFrame sin encabezados.
   - Detecta la presencia de las cadenas clave `estamento` y (`cargo`, `nombre`, `año` o `ano`).
   - Resuelve el problema estructural de las planillas públicas chilenas (donde las primeras 5 a 9 filas contienen advertencias legales o notas metodológicas del CPLT).
2. **`parsear_planilla_excel(...) -> List[CanonicalPersonalRecord]`**:
   - Lee archivos vía `pd.read_excel(file_path, header=None)`.
   - Normaliza encabezados eliminando puntuación y acentos (`col_map`).
   - Extrae campos canónicos con tolerancia a múltiples alias:
     - Nombres y apellidos: `primerapellido`, `apellido1`, `paterno`, `segundoapellido`, `nombres`, `nombre`.
     - Cargo/Función: `cargoo`, `cargo`, `funcion`.
     - Profesión/Formación: `calificacion`, `profesion`, `titulo`.
     - Estamento: `estamento` (normalizado a mayúsculas).
     - Remuneración bruta: `remuneracionbruta`, `remunbruta`, `sueldobruto`, `honorariobruto`, `totalhaberes`.
     - Horas extras: `horasextra`, `horasextras`, `asignacionespeciales`, `bonos`.
     - Grado: extracción mediante regex `\d+`.
   - Seudonimización inmediata: Genera `id_persona_hash = hash_person_identifier(full_name, prefix=comuna_id)`.
3. **`insertar_registros_en_duckdb(records: List[CanonicalPersonalRecord], db_path: Path) -> int`**:
   - Instancia `AgentReadyBackend` e invoca `insert_canonical_records`.
   - Garantiza idempotencia: borra los registros previos de la comuna/año/mes/calidad antes de insertar el lote.

### 2.3. Brechas Técnicas Detectadas en `portal_autonomo_harvester.py`
Para cumplir plenamente el requerimiento R3, el harvester presenta las siguientes limitaciones que deben ser atendidas por el agente implementador:
1. **Ausencia de Crawler Web HTTP**: La función `parsear_planilla_excel` asume que el archivo ya existe localmente en el disco (`file_path.exists()`). No incluye cliente HTTP (`requests`/`httpx`) para navegar hacia los portales de los municipios y descargar automáticamente los archivos mensuales.
2. **Incompatibilidad con CSV**: Si un municipio autónomo publica su nómina en formato `.csv` o `.tsv` (común en portales de datos abiertos como CKAN), `pd.read_excel` lanza excepción. Se requiere bifurcar la lectura según extensión (`.csv` vs `.xlsx`/`.xls`).
3. **Filtro de Descarte de Totales**: La regla `if "total" in paterno.lower() or "total" in nombres.lower() or "total" in cargo.lower(): continue` es efectiva para filtrar filas resumen, pero podría descartar funcionarios cuyos cargos incluyan la palabra "total" (caso improbable pero a considerar).
4. **Remuneraciones en Cero**: En la prueba con Providencia, los registros quedaron con `remuneracion_bruta = 0.0` porque la planilla oficial de Providencia utiliza encabezados con nombres ligeramente distintos (ej. "Total Haberes" o estructura matricial).

---

## 3. Estado de DuckDB y Persistencia de RRHH

### 3.1. Base DuckDB Principal
- **Ruta**: `D:/Proyectos/P166 - Personal Municipal de Chile/data/personal_municipal.duckdb`
- **Tamaño en Disco**: 63.7 MB (63,713,280 bytes).
- **Volumen de Datos**: **1.755.343 registros** en la tabla canónica `rrhh_personal`.
- **Esquema de la Tabla**:
```sql
CREATE TABLE rrhh_personal (
    comuna_id VARCHAR,
    anio INTEGER,
    mes INTEGER,
    calidad_juridica VARCHAR,
    estamento VARCHAR,
    grado INTEGER,
    cargo_funcion VARCHAR,
    profesion VARCHAR,
    remuneracion_bruta DOUBLE,
    horas_extras_monto DOUBLE,
    id_persona_hash VARCHAR
);
CREATE INDEX idx_personal_comuna ON rrhh_personal(comuna_id, anio, mes);
```

### 3.2. Cobertura Comunal en DuckDB
- **Total de `comuna_id` distintos en DuckDB**: **320**.
- **Análisis de Discrepancia**:
  - De las 320 claves en DuckDB, 318 corresponden a slugs canónicos de comunas (ej. `algarrobo`, `santiago`, `providencia`, `puente alto`).
  - 2 claves corresponden a códigos CUT numéricos que no fueron convertidos a slugs (`13102` = Cerro Navia y `10102` = Calbuco).
  - Al normalizar y homologar estas 2 claves, DuckDB cubre **318 comunas únicas**.
- **Comunas Totales del País**: 345 municipios oficiales (en `cplt_municipal_directory.json` y `comunas_enriched.json`).
- **Brecha Exacta de Ingesta**: $345 - 318 = \mathbf{27}$ comunas sin registros en DuckDB.

---

## 4. Diagnóstico de `scripts/sync_rrhh_observatorio.py`

### 4.1. Lógica de Sincronización
El script `scripts/sync_rrhh_observatorio.py` (296 líneas) orquesta el traspaso de métricas de personal hacia `data/comunas_enriched.json`:
1. **Prioridad 1 (CPLT DuckDB)**:
   - Extrae el período más reciente observado (`MAX(anio * 100 + mes)`) para cada comuna.
   - Computa dotación total, desglose por calidad (Planta, Contrata, Honorarios), personal TI mediante filtros textuales sobre cargos y profesiones (`%informat%`, `%sistema%`, `%comput%`, `%software%`, `%redes%`, `%ciberseguridad%`, `%soporte tecnic%`), y medianas de remuneración bruta general y de TI.
   - Asigna `"fuente": "CPLT Transparencia Activa (Observado)"`.
2. **Prioridad 2 (SUBDERE SINIM Oficial - Parquet)**:
   - Para comunas no encontradas en DuckDB, consulta `D:/Proyectos/P166 - Personal Municipal de Chile/data/sinim_2019-2023.parquet`.
   - Extrae dotación observada institucional (Ley 20.922) a 2023.
   - **El Problema del Ratio Teórico (Líneas 169–175)**:
     ```python
     # Estimar dotación TI institucional (ratio estándar observado 1.6% del personal)
     ti_tot = max(1, round(total * 0.016))
     ti_formal = max(1, round(ti_tot * 0.65))
     ti_hono = max(0, ti_tot - ti_formal)
     ti_planta = round(ti_formal * 0.5)
     ti_contrata = ti_formal - ti_planta
     ```
     Este bloque asigna un ratio teórico del 1.6% para inventar dotación TI cuando no hay registros nominales. Esto viola directamente el criterio de aceptación R3: *"100% de las 345 comunas con datos observados de dotación activa, sin ratios teóricos"*.

### 4.2. Estado Actual de `comunas_enriched.json`
Al auditar `data/comunas_enriched.json`:
- **Comunas con fuente observada real CPLT**: 318 comunas (92.2%).
- **Comunas con fuente estimada SINIM (Ratio 1.6%)**: 27 comunas (7.8%).
- **Comunas sin fuente / vacías**: 0.

Las 27 comunas actualmente contaminadas con el ratio teórico son:
`Alto Hospicio`, `Ancud`, `Antofagasta`, `Cabrero`, `Calama`, `Castro`, `Chonchi`, `Colchane`, `Concón`, `Contulmo`, `Copiapó`, `Curacaví`, `Curepto`, `Hualañé`, `Las Condes`, `Longaví`, `Lota`, `Melipilla`, `Nueva Imperial`, `Purén`, `Quinta de Tilcoco`, `Rauco`, `Recoleta`, `San Pedro de Atacama`, `San Rafael`, `Temuco`, `Teodoro Schmidt`.

---

## 5. Catastro Detallado: Las 19 Comunas Autónomas y las 8 Comunas CPLT Fallidas

La investigación desglosa con absoluta claridad por qué faltan exactamente 27 comunas:
- **19 comunas** corresponden a municipios autónomos que no usan la plataforma CPLT (`ta_status: "not_in_portal"` o `"unknown"`).
- **8 comunas** corresponden a municipios registrados en CPLT (`ta_status: "portal"`) cuyas tablas retornan 0 registros al intentar cosecharlas.

### 5.1. Matriz de las 19 Comunas Autónomas (Sin Portal CPLT)

| N° | Comuna | Código CPLT | Código CUT | Estado TA | Web Municipal Oficial / Portal Transparencia |
|:---|:---|:---:|:---:|:---:|:---|
| 1 | **Alto Hospicio** | MU005 | 01107 | `not_in_portal` | `https://www.maho.cl` / `https://transparencia.maho.cl` |
| 2 | **Ancud** | MU006 | 10202 | `not_in_portal` | `https://www.muniancud.cl` / `https://transparencia.muniancud.cl` |
| 3 | **Cabrero** | MU018 | 08303 | `not_in_portal` | `https://www.cabrero.cl` / Transparencia Activa Cabrero |
| 4 | **Calama** | MU019 | 02201 | `not_in_portal` | `http://www.municipalidadcalama.cl` / Portal Transparencia Calama |
| 5 | **Castro** | MU031 | 10201 | `not_in_portal` | `https://www.castromunicipio.cl` / Transparencia Castro |
| 6 | **Concón** | MU063 | 05103 | `not_in_portal` | `https://www.concon.cl` / Transparencia Activa Concón |
| 7 | **Contulmo** | MU065 | 08203 | `not_in_portal` | `https://www.contulmo.cl` / Transparencia Contulmo |
| 8 | **Curacaví** | MU073 | 13503 | `not_in_portal` | `https://www.curacavi.cl` / Transparencia Curacaví |
| 9 | **Curepto** | MU077 | 07103 | `not_in_portal` | `https://www.curepto.cl` / Transparencia Curepto |
| 10 | **Hualañé** | MU104 | 07502 | `not_in_portal` | `https://www.hualane.cl` / Transparencia Hualañé |
| 11 | **Longaví** | MU149 | 07304 | `not_in_portal` | `https://www.delongavi.cl` / Transparencia Longaví |
| 12 | **Lota** | MU158 | 08106 | `not_in_portal` | `https://www.munilota.cl` / Transparencia Lota |
| 13 | **Melipilla** | MU173 | 13501 | `not_in_portal` | `https://www.melipilla.cl` / Transparencia Activa Melipilla |
| 14 | **Purén** | MU241 | 09208 | `not_in_portal` | `https://www.mupuren.cl` / Transparencia Purén |
| 15 | **Recoleta** | MU263 | 13127 | `not_in_portal` | `https://www.recoleta.cl` / `https://recoletatransparente.cl` |
| 16 | **San Pedro de Atacama**| MU298 | 02203 | `not_in_portal` | `https://www.munispa.cl` / Transparencia San Pedro |
| 17 | **San Rafael** | MU300 | 07108 | `not_in_portal` | `https://www.munisanrafael.cl` / Transparencia San Rafael |
| 18 | **Temuco** | MU315 | 09101 | `not_in_portal` | `https://www.temuco.cl` / `https://transparencia.temuco.cl` |
| 19 | **Teodoro Schmidt** | MU317 | 09117 | `unknown` | `https://www.muniteodoro.cl` / Transparencia Teodoro Schmidt |

*Nota sobre Providencia (MU228) y Puente Alto (MU232)*: Pertenecen formalmente al grupo de 21 portales no CPLT, pero ya cuentan con 598 y 576 registros en DuckDB respectivamente (ingesta de prueba de Planta sep-2026). Requieren completar sus estamentos de Contrata y Honorarios.

### 5.2. Matriz de las 8 Comunas CPLT Fallidas (Retornan 0 Registros)

Al ejecutar la suite de cosecha controlada con `CPLTHarvester` sobre las 8 comunas restantes, se obtuvieron los siguientes resultados empíricos:

| N° | Comuna | Código CPLT | Código CUT | Meses Detectados | Registros Extraídos | Diagnóstico Técnico |
|:---|:---|:---:|:---:|:---:|:---:|:---|
| 1 | **Las Condes** | MU135 | 13114 | 0 | 0 | **Portal Autónomo Externo**: No publica en Liferay CPLT; aloja sus nóminas en `https://transparencia.lascondes.cl` y `https://datos.lascondes.cl`. |
| 2 | **Antofagasta** | MU009 | 02101 | 0 | 0 | **Iframe Vacío / Portal Propio**: CPLT redirige a portal municipal propio (`https://municipalidadantofagasta.cl`). |
| 3 | **Copiapó** | MU066 | 03101 | 0 | 0 | **Iframe Vacío**: CPLT no contiene data tabular en su portlet PrimeFaces. |
| 4 | **Chonchi** | MU046 | 10203 | 9 | 0 | **Tablas Vacías**: El portlet responde pero los meses contienen 0 filas. |
| 5 | **Colchane** | MU056 | 01403 | 0 | 0 | **Conexión CPLT Fallida**: No expone endpoint Liferay operativo. |
| 6 | **Nueva Imperial** | MU184 | 09111 | 9 | 0 | **Tablas Vacías**: Meses reportados sin personal indexado. |
| 7 | **Quinta de Tilcoco** | MU256 | 06114 | 9 | 0 | **Tablas Vacías**: El portal CPLT no tiene filas publicadas. |
| 8 | **Rauco** | MU262 | 07504 | 9 | 0 | **Tablas Vacías**: Meses reportados sin personal indexado. |

---

## 6. Verificación de Privacidad: Ley N° 21.719 y HMAC-SHA256

Se verificó exhaustivamente la implementación en `src/privacy_hasher.py` y `src/cplt_schema_normalizer.py`:
1. **Algoritmo Criptográfico**:
   - Función `hash_person_identifier(identifier: str | None, salt: str | None = None, prefix: str = "") -> str`:
     ```python
     clean_id = normalize_person_name(identifier)
     payload = f"{prefix.strip().lower()}:{clean_id}" if prefix else clean_id
     use_salt = (salt or DEFAULT_SALT).encode("utf-8")
     digest = hmac.new(use_salt, payload.encode("utf-8"), hashlib.sha256).hexdigest()
     return digest[:16]
     ```
   - Cumple con:
     - Unidireccionalidad irreversible (HMAC con clave secreta `MYWORLD_ANON_SALT`).
     - Aislamiento por comuna gracias al prefijo `comuna_id` (evita ataques de diccionario cruzados entre comunas).
     - Truncado a 16 caracteres hexadecimales (espacio de colisión suficiente para nóminas comunales preservando bajo consumo de almacenamiento).
2. **Purga de Datos Personales (PII)**:
   - La función `sanitize_personal_row` remueve explícitamente `run`, `rut`, `rut_funcionario`, `nombre`, `nombre_completo`, `nombres`, `apellidos`, `paterno`, `materno`.
   - En la tabla DuckDB `rrhh_personal` únicamente se almacena `id_persona_hash`, garantizando cumplimiento de la Ley N° 21.719 sobre Protección de Datos Personales.

---

## 7. Auditoría de Cobertura Temporal (Corte Septiembre 2026)

Distribución exacta de los 1.755.343 registros de `rrhh_personal` según el último período registrado por comuna:

| Período Más Reciente | Cantidad de Comunas | Porcentaje | Comentario |
|:---|:---:|:---:|:---|
| **2026-09 (Septiembre 2026)** | **260** | 81.3% | Corte estándar meta plenamente cumplido |
| 2026-08 (Agosto 2026) | 37 | 11.6% | Publicación desfasada en 1 mes por CPLT |
| 2026-06 / 2026-07 | 4 | 1.3% | Rezagadas leves (ej. Los Ángeles) |
| 2026-01 / 2026-03 | 2 | 0.6% | Rezagadas semestrales (ej. Osorno) |
| 2025-12 | 8 | 2.5% | Rezagadas anuales (ej. Alto del Carmen, Santa Bárbara) |
| 2024-10 / 2024-12 | 7 | 2.2% | Rezagadas a 2024 |
| 2026-10 / 2026-12 | 2 | 0.6% | Comunas con reportes futuros/anómalos (100 registros) |
| **Sin Registros en DuckDB** | **25** | 7.8% | Rezagadas totales (caen a SINIM) |
| **TOTAL** | **345** | **100.0%** | Universo de municipalidades de Chile |

---

## 8. Recomendaciones Técnicas para la Implementación (Agente Constructor)

Para que el agente de implementación logre el 100% de comunas con datos observados sin ratios teóricos, se recomienda la siguiente hoja de ruta técnica:

1. **Evolucionar `portal_autonomo_harvester.py`**:
   - Añadir soporte para lectura de `.csv` delimitado por punto y coma (`;`) o comas (`,`) con detección automática de codificación (`utf-8` vs `latin1`/`cp1252`).
   - Implementar un runner por lotes `harvest_autonomas.py` que reciba una carpeta de planillas locales `data/raw_autonomas/{comuna_id}/` o un catálogo de URLs directas.
2. **Plan de Descarga para las 27 Comunas**:
   - Para comunas grandes (Las Condes, Recoleta, Temuco, Calama, Concón, Melipilla): descargar las planillas oficiales de septiembre 2026 directamente desde sus portales de Transparencia Activa (sección Personal y Remuneraciones, ítems Planta, Contrata y Honorarios).
   - Para las comunas de menor conectividad que no tengan planilla web descargable en sep-2026: utilizar la nómina oficial observada más reciente (o reportes de personal del portal de datos abiertos) e ingerirla en DuckDB con su fecha respectiva, garantizando que **todas** provengan de un registro nominal individual con `id_persona_hash` y cargo real.
3. **Modificación de `sync_rrhh_observatorio.py`**:
   - Eliminar el bloque de estimación teórica de TI (`ti_tot = max(1, round(total * 0.016))`).
   - Reemplazar por una aserción estricta: si una comuna no tiene datos observados en DuckDB, levantar advertencia y no inventar dotación TI sintética.
   - Corregir el mapeo de alias para las 2 comunas con CUT numérico (`13102` y `10102`) para que sincronicen automáticamente sin perderse.
4. **Validación de Cierre**:
   - Ejecutar `python scripts/sync_rrhh_observatorio.py`.
   - Verificar que el reporte final indique:
     `Comunas con modelo complementario: 0` y `TOTAL COBERTURA OBSERVADA REAL: 345/345 (100.0%)`.
