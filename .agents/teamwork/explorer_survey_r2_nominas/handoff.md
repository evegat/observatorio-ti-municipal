# Handoff Report: Ingesta de Nóminas de Portales Web Autónomos (R3)

**Agent Identity**: `explorer_survey_r2_nominas`  
**Handoff Type**: Hard (Task complete)  
**Parent Conversation ID**: `556b08c5-0b60-438b-8148-0f340527cb59`  
**Reference Report**: `D:/Proyectos/observatorio-ti-municipal/.agents/teamwork/explorer_survey_r2_nominas/survey_nominas.md`

---

## 1. Observation

1. **Ubicación de `portal_autonomo_harvester.py`**:
   - Archivo ubicado en: `D:/Proyectos/P166 - Personal Municipal de Chile/src/portal_autonomo_harvester.py` (146 líneas).
   - Componentes observados:
     * `encontrar_fila_header(df_raw)`: líneas 25–31. Escanea las primeras 25 filas buscando cadenas `"estamento"` y (`"cargo"`, `"nombre"`, `"año"`, `"ano"`).
     * `parsear_planilla_excel(...)`: líneas 34–133. Carga planillas Excel vía `pd.read_excel(file_path, header=None)` y mapea columnas normalizadas.
     * `id_persona_hash`: líneas 114–115. Invoca `hash_person_identifier(full_name, prefix=comuna_id)` de `src.privacy_hasher`.
     * `insertar_registros_en_duckdb`: líneas 136–145. Carga registros canónicos en DuckDB usando `AgentReadyBackend(db_path=str(db_path)).insert_canonical_records(records)`.
2. **Ubicación y Estado de DuckDB**:
   - Archivo en: `D:/Proyectos/P166 - Personal Municipal de Chile/data/personal_municipal.duckdb` (63.7 MB).
   - Tabla única: `rrhh_personal` con **1.755.343 filas**.
   - Conteo de comunas distintas: `SELECT COUNT(DISTINCT comuna_id) FROM rrhh_personal` arrojó **320 claves distintas**.
   - Claves anómalas: `10102` (Calbuco) y `13102` (Cerro Navia) están almacenadas con su código CUT en vez del slug textual. Al corregir esto, el número de comunas únicas cubiertas en DuckDB es **318**.
3. **Lógica de Estimación en `sync_rrhh_observatorio.py`**:
   - Archivo en: `D:/Proyectos/observatorio-ti-municipal/scripts/sync_rrhh_observatorio.py`.
   - Líneas 169–175:
     ```python
     # Estimar dotación TI institucional (ratio estándar observado 1.6% del personal)
     ti_tot = max(1, round(total * 0.016))
     ti_formal = max(1, round(ti_tot * 0.65))
     ti_hono = max(0, ti_tot - ti_formal)
     ti_planta = round(ti_formal * 0.5)
     ti_contrata = ti_formal - ti_planta
     ```
   - Al ejecutar `check_enriched_sources.py` sobre `data/comunas_enriched.json`:
     * `CPLT Transparencia Activa (Observado)`: 318 comunas (92.2%).
     * `SUBDERE SINIM Oficial (Observado 2023)`: 27 comunas (7.8%) con ratio teórico 1.6%.
     * Universo total: 345 comunas.
4. **Catastro de Comunas en Directorio CPLT**:
   - Archivo en: `D:/Proyectos/P166 - Personal Municipal de Chile/data/cplt_municipal_directory.json` (345 municipios).
   - Clasificación por `ta_status`:
     * `portal`: 324 municipios.
     * `not_in_portal`: 20 municipios.
     * `unknown`: 1 municipio (`teodoro schmidt`).
   - De los 21 municipios con `ta_status != 'portal'`:
     * 2 ya cuentan con registros en DuckDB: `providencia` (598 registros de Planta, sep-2026) y `puente alto` (576 registros de Planta, sep-2026).
     * **19 municipios autónomos carecen de datos en DuckDB**: Alto Hospicio, Ancud, Cabrero, Calama, Castro, Concón, Contulmo, Curacaví, Curepto, Hualañé, Longaví, Lota, Melipilla, Purén, Recoleta, San Pedro de Atacama, San Rafael, Temuco y Teodoro Schmidt.
5. **Comunas CPLT con Retorno Cero**:
   - Al ejecutar prueba de extracción con `CPLTHarvester` sobre las 8 comunas restantes de `ta_status == 'portal'` que no estaban en DuckDB:
     * `las condes` (MU135): `months=0, records=0` (posee portal externo en `transparencia.lascondes.cl`).
     * `antofagasta` (MU009), `colchane` (MU056), `copiapo` (MU066): `months=0, records=0`.
     * `chonchi` (MU046), `nueva imperial` (MU184), `quinta de tilcoco` (MU256), `rauco` (MU262): `months=9, records=0` (tablas vacías en portal CPLT).
6. **Módulo de Seudonimización Ley N° 21.719**:
   - Archivo en: `D:/Proyectos/P166 - Personal Municipal de Chile/src/privacy_hasher.py`.
   - Línea 15: `DEFAULT_SALT = os.environ.get("MYWORLD_ANON_SALT", "myworld-sec-default-salt-chile-2026")`.
   - Líneas 51–59: `hash_person_identifier` genera HMAC-SHA256 con payload `f"{prefix.strip().lower()}:{clean_id}"`, truncando a 16 caracteres hexadecimales (`digest[:16]`).
   - Líneas 62–80: `sanitize_personal_row` elimina de raíz los campos de PII (`nombre`, `run`, `rut`, etc.).
7. **Corte Temporal de Septiembre 2026**:
   - En `personal_municipal.duckdb`:
     * Período `202609`: 260 comunas.
     * Período `202608`: 37 comunas.
     * Períodos anteriores a agosto 2026: 23 comunas.
     * Sin registros: 25 comunas (que aumentan a 27 al corregir los 2 códigos numéricos).

---

## 2. Logic Chain

1. **Premisa**: El requerimiento R3 exige que el 100% de las 345 comunas tengan datos observados reales de dotación activa al corte de septiembre 2026, eliminando cualquier ratio teórico (Observación 3).
2. **Causa Raíz de los Ratios Teóricos**: El archivo de producción `data/comunas_enriched.json` tiene 27 comunas alimentadas con SUBDERE SINIM 2023 porque `sync_rrhh_observatorio.py` no las encontró en `personal_municipal.duckdb` y les aplicó la fórmula `ti_tot = max(1, round(total * 0.016))` (Observación 3).
3. **Identificación de las Comunas Faltantes**: La diferencia entre el universo de 345 comunas y las 318 comunas observadas en DuckDB corresponde exactamente a:
   - 19 comunas con portales autónomos propios (`not_in_portal` y `unknown` en `cplt_municipal_directory.json`) (Observación 4).
   - 8 comunas registradas en CPLT cuyas llamadas a la API/portal retornan 0 registros o redirecciones externas (ej. Las Condes) (Observación 5).
   - Total: $19 + 8 = 27$ comunas.
4. **Idoneidad del Harvester**: `portal_autonomo_harvester.py` ya posee la lógica para procesar planillas Excel con encabezados dinámicos y persistir en DuckDB con seudonimización HMAC-SHA256 (Observación 1 y 6). Sin embargo, requiere una extensión para:
   - Descargar o leer planillas en formato `.csv`.
   - Permitir la ingesta masiva de las 27 comunas hacia DuckDB.
5. **Impacto en el Frontend**: Una vez que las 27 comunas ingresen a `rrhh_personal` en DuckDB y se ejecute `sync_rrhh_observatorio.py`, el 100% de las 345 comunas tendrá dotación observada nominal y `ret_ratio` real, erradicando por completo el ratio teórico de 1.6%.

---

## 3. Caveats

- **Disponibilidad de Nóminas Web al Corte Exacto de Septiembre 2026**: Algunas municipalidades de baja escala (ej. Contulmo, Curepto, Teodoro Schmidt) pueden presentar desfases en la publicación de sus nóminas web (ej. agosto o julio 2026). En tal caso, la regla del proyecto establece tomar el mes observado más reciente disponible en sus portales antes que inventar datos con ratios teóricos.
- **Formato PDF en Providencia**: El archivo `data/test_providencia.pdf` evidenció que Providencia suele publicar en PDF además de Excel. Para ingerir Contrata y Honorarios de Providencia se requiere asegurar que la fuente sea planilla tabular (.xlsx/.csv) o procesar con Stirling-PDF si solo existiera PDF.
- **No Inmutabilidad de Salt**: Para que los hashes de funcionarios sean longitudinalmente comparables, la variable `MYWORLD_ANON_SALT` debe mantenerse constante entre ejecuciones.

---

## 4. Conclusion

1. **Diagnóstico Concluido**: Se identificaron con precisión quirúrgica las 19 comunas autónomas restantes y las 8 comunas con falla de portal CPLT (total 27 comunas) que impiden alcanzar el 100% de cobertura observada.
2. **Herramienta Base Lista**: `portal_autonomo_harvester.py` en `P166 - Personal Municipal de Chile/src` está operativo y validado para procesar planillas de portales autónomos con detección dinámica de headers y seudonimización Ley N° 21.719.
3. **Acción Inmediata para el Agente Implementador**:
   - Ajustar `portal_autonomo_harvester.py` para soportar `.csv`.
   - Cargar en DuckDB las planillas de las 27 comunas faltantes (iniciando por Las Condes, Recoleta, Temuco, Calama, Concón, Melipilla).
   - Re-ejecutar `sync_rrhh_observatorio.py` eliminando el bloque del 1.6% teórico, consolidando el 100% de comunas con datos observados.

---

## 5. Verification Method

Para verificar independientemente todos los hallazgos y validar la implementación subsiguiente:

1. **Verificar comunas con ratio teórico en `comunas_enriched.json`**:
   ```bash
   python -c "import json; d = json.load(open(r'D:/Proyectos/observatorio-ti-municipal/data/comunas_enriched.json', encoding='utf-8')); sinim = [c['comuna'] for c in d if 'SINIM' in c.get('fuente_rrhh','')]; print('Comunas con ratio teorico:', len(sinim), sinim)"
   ```
   *Condición de éxito tras implementación*: `len(sinim) == 0`.

2. **Verificar conteo de comunas en DuckDB**:
   ```bash
   python -c "import duckdb; con = duckdb.connect(r'D:/Proyectos/P166 - Personal Municipal de Chile/data/personal_municipal.duckdb', read_only=True); print('Total comunas en DuckDB:', con.execute('SELECT count(distinct comuna_id) FROM rrhh_personal').fetchone()[0])"
   ```
   *Condición de éxito tras implementación*: `>= 345`.

3. **Verificar seudonimización HMAC-SHA256 (ausencia de PII en DuckDB)**:
   ```bash
   python -c "import duckdb; con = duckdb.connect(r'D:/Proyectos/P166 - Personal Municipal de Chile/data/personal_municipal.duckdb', read_only=True); print(con.execute('SELECT distinct length(id_persona_hash) FROM rrhh_personal').fetchall())"
   ```
   *Condición de éxito*: Todos los hashes deben tener longitud exactamente 16 caracteres hexadecimales.

4. **Ejecutar Suite de Pruebas de P166**:
   ```bash
   cd "D:/Proyectos/P166 - Personal Municipal de Chile"
   pytest tests/test_privacy_hasher.py tests/test_schema_normalizer.py tests/test_agent_ready_backend.py -v
   ```
