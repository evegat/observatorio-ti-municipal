# Handoff Report: Auditoría de Calidad y Revisión Adversarial de Saneamiento Semántico (M1: R1 / R2)

**Agente:** `reviewer_m1_1`  
**Roles:** Reviewer, Adversarial Critic  
**Tipo de Handoff:** Hard (Revisión y auditoría completada)  
**Fecha:** 24 de Octubre de 2026  
**Destinatario:** Orquestador (`556b08c5-0b60-438b-8148-0f340527cb59`)  
**Veredicto Explícito:** **APPROVE**  

---

## 1. Observation

Se realizaron observaciones directas, verificación empírica de código fuente, datasets estructurados y ejecución de pruebas sobre el trabajo entregado por `worker_m1_compras`:

### 1.1 Ejecución y Reproducibilidad del Pipeline
- Se ejecutó el pipeline completo de saneamiento de forma independiente:
  `python scripts/build_sanitized_observatorio_data.py`
  * Tiempo de ejecución observado: **9,88 segundos**.
  * Código de salida: `0` (limpio, sin excepciones).
  * Todos los artefactos fueron regenerados y sincronizados de forma determinista:
    - `data/catastro_ti_saneado.parquet` (31,6 MB)
    - `data/comunas_enriched.json` (3,3 MB)
    - `data/compras_saneadas_por_comuna.json` (2,1 MB)
    - `data/national_kpis.json` (4,8 KB)
    - `data/proveedores_ranking.json` (40 registros)
    - `data/regiones_enriched.json` (16 regiones)

### 1.2 Métricas Cuantitativas Verificadas Directamente en Parquet
Mediante conexión DuckDB directa e independiente sobre `catastro_ti_saneado.parquet`:
- **Total registros brutos evaluados:** 204.591 líneas (153.770 órdenes de compra, $312.570.954.499 CLP).
- **Total registros saneados:** **119.659 líneas**, **96.245 órdenes de compra únicas**, **$172.240.070.566 CLP**.
- **Volumen total purgado:** **84.932 líneas**, **57.525 OCs**, **$140.330.883.933 CLP** (reducción del 44,9% del volumen financiero total previo).
- **Contratos/proveedores de carpas en parquet saneado:** **0 (Cero absoluto)**.
- **Presencia de la OC espuria `2403-315-SE22` de Peñalolén ($88.935.000 CLP de Alcalde y Asociados):** **0 (Erradicado al 100%)**.

### 1.3 Verificación Adversarial del Bug `%rpa%` y Regex de Límites de Palabra
Se probó el motor regex de DuckDB frente a entradas maliciosas y colisiones ortográficas:
- Colisiones falsas probadas:
  * `"arriendo de carpas"` → `False`
  * `"escarpe vial terreno"` → `False`
  * `"zarpa de embarcacion"` → `False`
- Expresiones legítimas de RPA probadas:
  * `"solucion rpa para dclick"` → `True`
  * `"licenciamiento rpa"` → `True`
  * `"robotic process automation azure"` → `True`
  * `"rpa.bot"` → `True`
  * `"rpa, automatizacion"` → `True`
- En el dataset saneado `catastro_ti_saneado.parquet`, sobrevivieron **8 registros legítimos de software RPA municipal** (Rocketbot RPA, capacitación operador RPA en La Pintana, software RPA para verificación y reclamo DTE de facturas en Antofagasta, Insico SIRH-SP-RPA). Los demás registros con la sigla RPA en la base cruda correspondían a drones o seguros aeronáuticos (*Remotely Piloted Aircraft*), correctamente discriminados por la whitelist UNSPSC.
- Gasto en IA y automatización saneado verificado: **488 registros por $1.581.239.685 CLP** (frente a los $63.420M espurios previos causados por carpas).

### 1.4 Verificación de Casos Emblemáticos en JSONs Comunales
- **Peñalolén (`codigo_cut: 13122`):**
  * Monto saneado: **$2.060.203.387 CLP** (Gasto pc: $7.549 CLP/hab, 402 OCs).
  * Top proveedores: GTD TELESAT ($1.002M), GTD TELEDUCTOS ($152M), TECHNOSYSTEMS ($112M), IMPORTADORA HEVIA ($66M), STM Computación ($60M). Cero carpas ni productoras.
  * `top_contratos_recientes`: 6 compras vigentes de 2026 (Servidores GTD, Inversiones O&E, Mave Technology, etc.).
  * `top_contratos_historicos`: Fibra óptica GTD ($871M), Tablets Technosystems ($101M), GTD ($71M y $66M). 0 carpas.
- **Providencia (`codigo_cut: 13123`):**
  * Monto saneado: **$347.105.845 CLP** (Gasto pc: $2.116 CLP/hab, 226 OCs). Corregido desde los $7.707 inflados.
  * Top proveedores: ADVANTAGE COMPUTACION SPA ($85M), SIT LTDA ($67M), GTD INTESIS ($48M), STM Computacion ($29M), Servacom ($15M). *Carpas Araos y Pérez* ($221M) y *Lagos Carpas SpA* ($122M) erradicados al 100%.

### 1.5 Batería de Pruebas Automatizadas
- `pytest tests/test_sanitized_purchases_m1.py -v`:
  * 8 passed en 0,29 segundos.
  * Valida existencia de parquet, 0 carpas, erradicación Peñalolén, depuración Providencia, 0 carpas en 345 comunas, cobertura 2025–2026 desacoplada, ausencia de NaNs y consistencia nacional.
- Calidad de sintaxis frontend: `node -c app.js` retornó código `0`.

---

## 2. Logic Chain

1. **Premisa 1 (Integridad sin Atajos ni Fachadas):** Se auditó `scripts/build_sanitized_observatorio_data.py` línea por línea. El script contiene transformaciones DuckDB reales, funciones de ventana deterministas y algoritmos de toponimia. No existen diccionarios que "quemen" o hardcodeen resultados artificiales para Peñalolén o Providencia; la depuración de ambas comunas se deriva orgánicamente del filtro de 2 capas.
2. **Premisa 2 (Eficacia del Filtro Taxonómico de 2 Capas):** La Capa 1 veta explícitamente códigos ONU espurios (`30221001` y 16 adicionales) y palabras clave no-TI. La Capa 2 restringe a 6 familias tecnológicas UNSPSC. Esto garantiza que la erradicación de los $140.330 millones espurios sea sistémica y no un parche cosmético local.
3. **Premisa 3 (Resolución del Bug `%rpa%`):** La utilización de `\b(rpa|robotic process automation)\b` resuelve el falso positivo ortográfico donde `carpa` contenía la subcadena `rpa`. Se confirmó que la expresión regular mantiene límites de palabra con puntuación, respetando herramientas genuinas de automatización como Rocketbot sin reincorporar toldos o escarpes.
4. **Premisa 4 (Cobertura Temporal y Retrocompatibilidad):** La separación de `top_contratos_recientes` (2025–2026) y `top_contratos_historicos` satisface el requisito R2 de visibilizar la actividad contemporánea en 344 de 345 comunas. La inclusión de `top_contratos` como alias idéntico asegura que ningún componente legacy del frontend colapse.
5. **Deducción:** El trabajo entregado por `worker_m1_compras` cumple a cabalidad con los requerimientos R1 y R2 de ORIGINAL_REQUEST.md, demostrando solidez técnica, fidelidad empírica y ausencia de violaciones de integridad.

---

## 3. Review Findings & Adversarial Challenges

### Findings de Calidad

- **[Buenas Prácticas Observadas]:**
  - Manejo de tipos nativos en DuckDB y exportación directa a Parquet columnar comprimido.
  - Generación de espejo en `compras_saneadas_por_comuna.json` desacoplado para uso del frontend M3 sin romper `comunas_enriched.json`.
  - Recalibración completa de todos los artefactos satélite (`national_kpis.json`, `proveedores_ranking.json`, `regiones_enriched.json`).

### Desafíos Adversariales y Casos de Borde Analizados

#### Desafío 1: Registros con Municipio Comprador Nulo en Fuente Cruda (55 líneas)
- **Supuesto puesto a prueba:** Integridad de datos en la ingesta cruda de Mercado Público.
- **Hallazgo adversarial:** Existen 55 líneas en el catastro crudo de Mercado Público donde `comuna_comprador IS NULL` (pese a que la glosa indica compras de Punta Arenas, Curanilahue, etc.).
- **Comportamiento observado:** `compute_comuna_metrics` descarta oportunamente estos registros en la agregación comunal mediante `WHERE comuna_comprador IS NOT NULL`, evitando que ingresen comunas corruptas o nulas a los archivos JSON.
- **Riesgo:** Bajo / Mitigado. En los JSON comunales generados, las 345 comunas presentan 100% de consistencia, cero campos NaN y cero valores nulos.

#### Desafío 2: Glosas Mixtas en Compras Escolares ("Guitarras y Tablets")
- **Supuesto puesto a prueba:** Ausencia total de cualquier término ajeno en descripciones.
- **Hallazgo adversarial:** Se detectaron 2 compras (años 2017 y 2020) por montos menores ($197k y $49k CLP) donde un municipio adquirió premios escolares categorizados bajo código ONU `43211509` (Tablet PC) cuya glosa menciona "Tablet, pendrive, guitarras y otros".
- **Comportamiento observado:** Debido a que el código ONU y el rubro principal son Tecnologías de la Información (Tablets), el filtro conservó la línea.
- **Riesgo:** Despreciable. Su impacto financiero es inferior al 0,0001% del presupuesto y no distorsiona ningún ranking de proveedores ni métrica comunal.

---

## 4. Caveats

1. **Combarbalá (CUT 4302):** Es la única comuna que no registra compras TI transadas bajo su RUT institucional en Mercado Público (gestionadas comúnmente a nivel de asociación provincial o corporativa). Se mantiene con `total_ocs: 0` y montos en `0`, garantizando que el mapa y los rankings conserven la totalidad de las 345 comunas sin generar datos artificiales.
2. **Consumo en Frontend (M3):** La exposición de los feeds desacoplados (`top_contratos_recientes` vs `top_contratos_historicos`) en el Drawer del mapa y modales corresponde a la implementación de interfaz asignada a M3; los datos están 100% disponibles y validados en el backend JSON.

---

## 5. Conclusion

**Veredicto:** **APPROVE**

1. **Requerimiento R1 (Saneamiento Semántico):** Aprobado con distinción. Erradicación al 100% del arriendo de carpas en Peñalolén (`2403-315-SE22`), eliminación de proveedores espurios en Providencia (*Carpas Araos*, *Lagos Carpas*) y purga auditada de $140.330 millones de pesos no tecnológicos en todo el país.
2. **Requerimiento R2 (Cobertura 2025–2026 y Desacoplamiento):** Aprobado. 344 comunas reflejan compras activas de 2025 y 2026, con feeds desacoplados y alias retrocompatible.
3. **Integridad y Antifraude:** Cero infracciones de integridad. Implementación genuina en DuckDB, sin resultados quemados en código, reproducible de principio a fin en menos de 10 segundos y con 8 de 8 pruebas unitarias pasando.

---

## 6. Verification Method

Para verificar independientemente este veredicto desde la raíz `D:/Proyectos/observatorio-ti-municipal`:

1. **Ejecutar la suite de pruebas unitarias de M1:**
   ```powershell
   pytest tests/test_sanitized_purchases_m1.py -v
   ```
   *Salida esperada:* `8 passed in 0.29s` (100% éxito).

2. **Re-ejecutar el pipeline completo de saneamiento:**
   ```powershell
   python scripts/build_sanitized_observatorio_data.py
   ```
   *Salida esperada:* Conclusión en < 15s con `=== TODAS LAS ASERCIONES DE INTEGRIDAD PASARON EXITOSAMENTE ===`.

3. **Verificar ausencia de carpas y contrato espurio en DuckDB:**
   ```powershell
   python -c "import duckdb; con=duckdb.connect(); print('Carpas:', con.execute(\"SELECT count(*) FROM read_parquet('data/catastro_ti_saneado.parquet') WHERE lower(texto_descriptivo) LIKE '%carpa%' OR lower(nombre_proveedor) LIKE '%carpa%'\").fetchone()[0]); print('Contrato 2403-315-SE22:', con.execute(\"SELECT count(*) FROM read_parquet('data/catastro_ti_saneado.parquet') WHERE codigo_orden = '2403-315-SE22'\").fetchone()[0])"
   ```
   *Salida esperada:* `Carpas: 0`, `Contrato 2403-315-SE22: 0`.

4. **Verificar verificación de sintaxis del frontend:**
   ```powershell
   node -c app.js
   ```
   *Salida esperada:* Exit code 0.
