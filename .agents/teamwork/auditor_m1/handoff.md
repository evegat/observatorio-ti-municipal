# Forensic Audit Report: Milestone 1 (Compras Públicas TI Saneadas)

**Work Product**: Saneamiento Semántico y Cobertura Temporal de Compras Públicas TI (R1 / R2) por `worker_m1_compras`  
**Profile**: General Project (Development Mode)  
**Verdict**: **CLEAN**  

---

### Phase Results
- **Hardcoded test results detection**: PASS — Cero valores de prueba o bypasses fijos en el código.
- **Facade detection**: PASS — Implementación genuina con queries SQL completas, window functions y agregaciones reales en DuckDB.
- **Fabricated verification outputs**: PASS — Todos los artefactos fueron reproducidos empíricamente desde el dataset bruto.
- **Algorithmic filtering (Peñalolén / Providencia)**: PASS — Erradicación 100% algorítmica sin if-statements comunales ni overrides por ID de orden.
- **Build and test verification**: PASS — Suite `pytest tests/test_sanitized_purchases_m1.py` pasa 8/8; script maestro reproduce datos en <10s; gate de calidad MyWorld Harness pasa.

---

## 1. Observation

1. **Replicación empírica independiente de DuckDB:**
   - Dataset de entrada bruto: `D:/Proyectos/PUB021 - Paper Adopcion IA y Tecnologias en Municipios/data/catastro_ti_municipal_completo_clasificado.parquet`:
     * Total registros brutos: **204.591 ítems**, **153.770 órdenes de compra**, **$312.570.954.499 CLP**.
   - Ejecución independiente de la query de saneamiento de `scripts/build_sanitized_observatorio_data.py` (líneas 106–261):
     * Total registros saneados: **119.659 ítems**, **96.245 órdenes de compra únicas**, **$172.240.070.566 CLP**.
   - Comparación con `data/catastro_ti_saneado.parquet` entregado por el worker:
     * Ítems: 119.659 vs 119.659 (Coincidencia 100%).
     * OCs distintas: 96.245 vs 96.245 (Coincidencia 100%).
     * Monto total CLP: $172.240.070.566 vs $172.240.070.566 (Coincidencia exacta al peso).
   - Los números NO son estáticos ni fabricados; reflejan el resultado exacto del cómputo en DuckDB.

2. **Ausencia de mocks o overrides para Peñalolén y Providencia:**
   - Búsqueda en `scripts/build_sanitized_observatorio_data.py`:
     * "Peñalolén" y "Providencia" NO aparecen en ninguna cláusula `WHERE`, `IF` o función de procesamiento de datos. Aparecen exclusivamente en las aserciones de validación al final del archivo (`run_verification_suite`, líneas 818 y 833).
     * El contrato `2403-315-SE22` ($88.935.000 CLP de carpas en Peñalolén) NO aparece en la lógica de filtrado. Fue purgado porque en el catastro bruto posee `codigo_producto_onu = '30221001'` y `rubro_nivel1 = 'Artículos para estructuras, obras y construcciones'`, lo cual activa la Capa 1 (Blacklist de ONU `30221001` y texto `carpa`) y no cumple la Capa 2 (Whitelist UNSPSC de TI).
     * En Providencia, los proveedores `CARPAS ARAOS Y PEREZ` y `LAGOS CARPAS SPA` fueron eliminados por la regla general `prov LIKE '%carpa%'` y su rubro `Servicios de Viajes, alimentación, alojamiento y entretenimiento`. Con ello, `ADVANTAGE COMPUTACION SPA` ($85.736.654 CLP) asciende al 1° lugar de forma natural por volumen de compras de TI.

3. **Reparación del falso positivo `%rpa%` en IA:**
   - En el dataset original clasificado, la búsqueda por substring `%rpa%` capturaba palabras como `carpa`, `escarpe` y `zarpas`, inflando el gasto en IA en $63.420 millones de pesos (26.535 registros espurios).
   - En `scripts/build_sanitized_observatorio_data.py` (línea 185), se reemplazó por la expresión regular con delimitador de palabra `\b(rpa|robotic process automation|automatizacion de procesos|automatización de procesos|automatizacion documental|automatización documental)\b`.
   - Se verificó que el gasto de IA saneado nacional es de **$1.581.239.685 CLP** (0 carpas).

4. **Filtrado de términos no tecnológicos y códigos ONU:**
   - Se ejecutó auditoría sobre `data/catastro_ti_saneado.parquet` para términos espurios adicionales:
     * `toldo`: 0
     * `banquete`: 0
     * `fiesta`: 0
     * `curanto`: 0
     * `gas licuado`: 0
     * `zapato`: 0
     * `camioneta maxus`: 0
     * `obras civiles`: 0
     * `pavimentac`: 0
     * `apicol`: 0
     * `desratizac`: 0
     * Códigos ONU de la blacklist (`30221001`, `90101602`, `90151602`, etc.): 0 en toda la base saneada.

5. **Cobertura temporal 2025–2026 y desacoplamiento de feeds:**
   - Conteo en `data/catastro_ti_saneado.parquet`:
     * Año 2025: 12.188 ítems, 9.505 OCs, $26.202.908.483 CLP.
     * Año 2026: 6.411 ítems, 4.951 OCs, $13.234.510.420 CLP.
   - En `data/comunas_enriched.json` (345 comunas):
     * 344 comunas tienen registros en `top_contratos_recientes` (compras 2025–2026).
     * 344 comunas tienen registros en `top_contratos_historicos`.
     * `top_contratos` es 100% idéntico a `top_contratos_historicos` en las 345 comunas, preservando retrocompatibilidad total con el frontend y tests preexistentes.
   - Combarbalá tiene 0 compras en el parquet bruto de Mercado Público; su tratamiento como comuna sin OCs es fiel a la fuente original y no una omisión del código.

6. **Integridad de datos JSON y atributos preexistentes:**
   - 0 valores `NaN`, `null` o corrupciones en las métricas financieras de las 345 comunas en `comunas_enriched.json` y `compras_saneadas_por_comuna.json`.
   - 100% de las comunas preservan sus coordenadas geográficas (`lat`, `lng`), población y métricas de dotación de personal municipal y RRHH previas.

7. **Ejecución de suites de prueba y arnés:**
   - `pytest tests/test_sanitized_purchases_m1.py -v`: 8 passed en 0.29s.
   - `scripts/build_sanitized_observatorio_data.py`: Ejecución limpia end-to-end con 7/7 aserciones empíricas aprobadas en 9.6s.
   - MyWorld Harness: `.myworld-harness/harness.ps1 quality` pasa (`node -c app.js` exit=0).

---

## 2. Logic Chain

1. **Premisa 1 (Verificación del Cómputo):** Si los datos de `catastro_ti_saneado.parquet`, `national_kpis.json` y `comunas_enriched.json` fuesen estáticos o fabricados, re-ejecutar independientemente el script maestro o la query DuckDB desde el archivo de origen `catastro_ti_municipal_completo_clasificado.parquet` produciría discrepancias numéricas. La coincidencia es del 100,000% al peso ($172.240.070.566 CLP en 96.245 OCs).
2. **Premisa 2 (Verificación de Imparcialidad Algorítmica):** Si Peñalolén o Providencia hubiesen sido limpiadas mediante parches especiales orientados a pasar los tests, existirían condicionales específicos por nombre de comuna o código de orden en la lógica de saneamiento. La inspección del código fuente y el rastreo de ejecución demuestran que su saneamiento es consecuencia pura del filtro taxonómico de dos capas (códigos ONU UNSPSC y familias de rubros TI) y la corrección de regex para `%rpa%`.
3. **Premisa 3 (Verificación de Requerimientos R1 y R2):** El saneamiento erradicó el 100% de las carpas y contratos espurios de la canasta, integró 14.456 OCs de 2025–2026 en 344 comunas y desacopló los feeds recientes vs históricos sin regresión en la retrocompatibilidad del frontend.
4. **Deducción:** El trabajo entregado por `worker_m1_compras` cumple con todos los criterios de integridad, rigor metodológico y calidad requeridos, sin patrones prohibidos ni trampas de implementación.

---

## 3. Caveats

- **Combarbalá:** Es la única comuna sin órdenes de compra en Mercado Público en el periodo 2015–2026 en la fuente original. Se verificó contra el dataset bruto que efectivamente cuenta con 0 compras, por lo que su estado de 0 OCs es fáctico y legítimo.
- **Frontend SPA:** Siguiendo la delimitación de responsabilidades de los hitos, los archivos `index.html` y `app.js` no sufrieron mutaciones en M1; los nuevos campos desacoplados (`top_contratos_recientes` y `top_contratos_historicos`) quedan disponibles en los datos para su explotación en la interfaz durante el hito correspondiente.

---

## 4. Conclusion

**Veredicto Final: CLEAN (APROBADO).**

El trabajo de `worker_m1_compras` en el Hito M1 es íntegro, auditable, genuino y reproducible. No se detectó ninguna violación de integridad:
- Cero resultados de prueba hardcodeados.
- Cero implementaciones fachada.
- Cero falsos positivos de carpas o eventos en las 345 comunas.
- Cobertura temporal contemporánea (2025–2026) plenamente integrada.

---

## 5. Verification Method

Para verificar independientemente este veredicto:

1. **Re-ejecutar la suite de pruebas unitarias:**
   ```powershell
   pytest tests/test_sanitized_purchases_m1.py -v
   ```
   *Resultado esperado:* 8 passed en < 1 segundo.

2. **Re-ejecutar el script forense independiente de auditoría:**
   ```powershell
   python .agents/teamwork/auditor_m1/forensic_check.py
   ```
   *Resultado esperado:* Mensaje `-> MATCH 100% IDENTICAL: The parquet file was genuinely generated from DuckDB query!` y 0 NaNs en JSON.

3. **Verificar que no existen menciones a Peñalolén o Providencia en la lógica de filtrado:**
   ```powershell
   python -c "with open('scripts/build_sanitized_observatorio_data.py', encoding='utf-8') as f: lines = f.readlines()[:788]; assert not any('penalol' in l.lower() or 'providencia' in l.lower() for l in lines); print('Lógica de saneamiento libre de overrides comunales')"
   ```
   *Resultado esperado:* `Lógica de saneamiento libre de overrides comunales`.

4. **Verificar el gate de calidad del arnés MyWorld:**
   ```powershell
   powershell -ExecutionPolicy Bypass -File .myworld-harness/harness.ps1 quality
   ```
   *Resultado esperado:* `[PASS] quality.command.1: exit=0: node -c app.js`.
