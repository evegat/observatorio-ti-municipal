# Handoff Report: Auditoría Forense y Saneamiento de Compras Públicas TI (R1 / R2)

**Agente:** `explorer_survey_r1_compras`  
**Tipo de Handoff:** Hard (Investigación completa)  
**Fecha:** 24 de Octubre de 2026  
**Destinatario:** Orquestador (`556b08c5-0b60-438b-8148-0f340527cb59`) y Agente Implementador  

---

## 1. Observation

1. **Ubicación canónica de la base de 153.770 órdenes de compra:**
   - Archivo: `D:/Proyectos/PUB021 - Paper Adopcion IA y Tecnologias en Municipios/data/catastro_ti_municipal_completo_clasificado.parquet`
   - DuckDB query:
     ```sql
     SELECT count(*), count(distinct codigo_orden), sum(monto_linea) 
     FROM read_parquet('D:/Proyectos/PUB021 - Paper Adopcion IA y Tecnologias en Municipios/data/catastro_ti_municipal_completo_clasificado.parquet')
     ```
   - Resultado empírico exacto: **204.591 ítems**, **153.770 órdenes de compra (OCs) únicas**, **$312.570.954.499 CLP** transados en 442 comunas/entidades compradoras.

2. **Detección del falso positivo emblemático en Peñalolén:**
   - En `data/catastro_ti_municipal_completo_clasificado.parquet`:
     ```sql
     SELECT codigo_orden, anio, nombre_proveedor, codigo_producto_onu, nombre_producto_generico, rubro_nivel1, monto_linea, texto_descriptivo
     FROM read_parquet(...)
     WHERE lower(comuna_comprador) LIKE '%peñalol%' AND monto_linea BETWEEN 80000000 AND 95000000
     ```
   - Registro observado:
     * `codigo_orden`: `"2403-315-SE22"`
     * `anio`: 2022
     * `monto_linea`: $88.935.000 CLP
     * `nombre_proveedor`: `"ALCALDE Y ASOCIADOS LIMITADA"`
     * `codigo_producto_onu`: `"30221001"` (*Carpas*)
     * `rubro_nivel1`: `"Artículos para estructuras, obras y construcciones"`
     * `texto_descriptivo`: *"Carpas SERVICIO ARRIENDO DE CARPAS Y TOLDOS ESTRUCTURALES (PROCESO LICITATORIO: 2403-25-LQ22) ARRIENDO DE CARPAS Y TOLDOS ESTRUCTURALES PARA RECINTOS MUNICIPALES..."*

3. **Detección de los falsos positivos en Providencia:**
   - En `data/comunas_enriched.json` (líneas 25931–25946):
     ```json
     "top_proveedores": [
       { "proveedor": "CARPAS ARAOS Y PEREZ", "monto": 221478882.0, "ocs": 25 },
       { "proveedor": "LAGOS CARPAS SPA", "monto": 122219322.0, "ocs": 13 },
       { "proveedor": "ADVANTAGE COMPUTACION SPA", "monto": 85736654.0, "ocs": 12 }
     ]
     ```
   - Total carpas en Providencia en los dos primeros puestos: $343.698.204 CLP en 38 órdenes de compra.

4. **Descubrimiento del mecanismo de falsa IA por substring `%rpa%`:**
   - En `D:/Proyectos/PUB021 - Paper Adopcion IA y Tecnologias en Municipios/src/02_classify_municipal_ti.py` (líneas 171–180):
     ```sql
     (
         lower(texto_descriptivo) LIKE '%inteligencia artificial%' OR ...
         lower(texto_descriptivo) LIKE '%rpa%' OR ...
     ) as flag_ia_automatizacion
     ```
   - Verificación empírica con script `test_rpa_carpas.py`:
     * Total registros con texto `'carpa'`: 26.535
     * Registros clasificados con `flag_ia_automatizacion = TRUE`: **26.535 (100,0%)**
     * Monto total de carpas asignado a IA: **$63.420.000.000 CLP**.
     * Causa: La palabra española `carpa` contiene la subsecuencia `r-p-a` (`c-a-[r-p-a]`). Lo mismo ocurre con `escarpe` (pavimentación) y `zarpas` (limpieza de cunetas).

5. **Disponibilidad de datos 2025 y 2026 en disco:**
   - En `D:\Proyectos\P049 - Compras publicas tecnologicas e IA publica\DataCompleta`:
     * 2025: `oc_2025-01.csv` a `oc_2025-12.csv` (12 meses completos).
     * 2026: `oc_2026-01.csv` a `oc_2026-09.csv` (9 meses acumulados, con abril como `2026-4.csv`).
   - En `catastro_ti_municipal_completo_clasificado.parquet`:
     * 2025: 23.499 ítems (17.530 OCs), $48.005.598.430 CLP.
     * 2026: 13.511 ítems (9.758 OCs), $27.903.800.356 CLP.

6. **Diagnóstico del rezago temporal aparente en `comunas_enriched.json`:**
   - Verificación con `audit_temporal_enriched.py`:
     * 165 comunas tienen año máximo >= 2025.
     * **175 comunas** reflejan año máximo <= 2024 en `top_contratos`.
   - Causa en código: En `PUB021/src/04_build_web_data.py` (línea 195), `top_contratos` se extrae con `ROW_NUMBER() OVER(PARTITION BY comuna ORDER BY monto DESC)` sobre todo el histórico (2014–2026), provocando que contratos antiguos de gran cuantía (o contratos espurios de carpas) desplacen por completo las compras legítimas de 2025–2026.

---

## 2. Logic Chain

1. **Premisa A (Observaciones 1 y 4):** La base de datos original contiene 153.770 órdenes de compra seleccionadas inicialmente por coincidencia léxica abierta en P049 sin validación taxonómica UNSPSC.
2. **Premisa B (Observaciones 2, 3 y 4):** El uso de `%rpa%` y términos abiertos como `enlaces`, `storage` y `entrenamiento de personal` introdujo masivamente contratos de carpas, toldos, eventos, tanques de combustible y capacitaciones agrícolas/sociales. El 100% de las carpas fue categorizado erróneamente como IA y 44,9% del volumen financiero ($140.320M CLP) corresponde a rubros ajenos a TI.
3. **Premisa C (Observaciones 2 y 3):** Esto distorsionó severamente las métricas de comunas específicas: Peñalolén exhibe un contrato de carpas por $88M en su Top 3 y Providencia coloca dos empresas de carpas en los puestos #1 y #2 de sus proveedores comunales.
4. **Premisa D (Observación 5 y 6):** Los datos de compras de 2025 y 2026 están completamente descargados y clasificados localmente, pero no se visibilizan en 175 comunas porque la interfaz web solo muestra 4 contratos históricos ordenados por monto, sepultando las adquisiciones recientes.
5. **Deducción Lógica:** Erradicar los falsos positivos requiere un filtro de dos capas (Blacklist explícita de códigos ONU/rubros no-TI y Whitelist estricta de las 5 familias tecnológicas auditables). La solución al rezago temporal de 2025–2026 no requiere llamar a la API externa de ChileCompra, sino desacoplar en el pipeline de datos y en la interfaz dos listas: «Últimas Compras Tecnológicas (2025–2026)» y «Contratos Emblemáticos de Mayor Cuantía (Histórico)».

---

## 3. Caveats

1. **Subcontrataciones dentro de Licitaciones Globales:** Licitaciones municipales complejas rotuladas como "Producción de Eventos" que hayan incluido arriendo de pantallas LED o sonido no pueden disgregarse a nivel de factura individual si la orden de compra en Mercado Público fue emitida bajo un único código ONU de eventos (`80141607`). La regla de saneamiento adoptada prioriza el rigor metodológico: ante la duda de si es show artístico o tecnología, se purga para erradicar cualquier contaminación no-TI.
2. **Códigos ONU en Rubro `NA`:** Existen 35.242 registros en Mercado Público donde el clasificador de ChileCompra dejó el rubro como `NA` o el código como `0`. De estos, se rescatan únicamente aquellos que contengan en su glosa técnica términos de hardware, software, hosting o enlaces unívocos; el resto (gas licuado, camionetas, calzado) queda purgado.
3. **No se modificó código productivo en este turno:** Siguiendo el protocolo estricto de Explorer (read-only), todos los scripts ejecutados residen exclusivamente en `.agents/teamwork/explorer_survey_r1_compras/`.

---

## 4. Conclusion

1. **Factibilidad Total de R1:** La purga semántica reduce la base a **96.255 órdenes de compra puramente tecnológicas** transadas por **$172.250 millones de pesos** (eliminando 60.012 OCs espurias por $140.320 millones). El contrato de carpas de Peñalolén ($88M) y las dos empresas de carpas de Providencia ($343M) quedan 100% erradicados.
2. **Factibilidad Total de R2:** La información 2025–2026 ya está disponible localmente con 14.459 órdenes de compra tecnológicas saneadas que abarcan **370 comunas**.
3. **Camino Crítico de Implementación:**
   - **Paso 1:** Ejecutar el pipeline de saneamiento en DuckDB (`build_sanitized_observatorio_data.py`).
   - **Paso 2:** Generar la arquitectura desacoplada de R4 (`comunas_summary.json` ~280 KB y `data/comunas/{codigo_cut}.json` ~12 KB por comuna con los dos feeds: recientes 2025–2026 y emblemáticos históricos).
   - **Paso 3:** Actualizar `app.js` e `index.html` para renderizar el feed cronológico y actualizar los indicadores del banner principal.

---

## 5. Verification Method

Para verificar independientemente este diagnóstico y los resultados numéricos:

1. **Verificar el contrato de carpas en Peñalolén ($88M):**
   ```powershell
   python -c "import duckdb; con=duckdb.connect(); print(con.execute(\"SELECT codigo_orden, monto_linea, texto_descriptivo FROM read_parquet('D:/Proyectos/PUB021 - Paper Adopcion IA y Tecnologias en Municipios/data/catastro_ti_municipal_completo_clasificado.parquet') WHERE codigo_orden = '2403-315-SE22'\").df())"
   ```
   *Condición de fallo:* Si el código `2403-315-SE22` no existe o no corresponde a arriendo de carpas por $88.935.000 CLP.

2. **Verificar el bug de `%rpa%` sobre carpas:**
   ```powershell
   python .agents/teamwork/explorer_survey_r1_compras/test_rpa_carpas.py
   ```
   *Salida esperada:* `Total registros con carpa: 26,535 | Registros con carpa clasificados como IA: 26,535 (100.0%) | Monto: $63.42 MM CLP`.

3. **Verificar la simulación de la canasta saneada:**
   ```powershell
   python .agents/teamwork/explorer_survey_r1_compras/simulate_sanitized_basket.py
   ```
   *Salida esperada:*
   - Base original: 153.770 OCs ($312.57 MM CLP).
   - Espurio purgado: 60.012 OCs ($140.32 MM CLP).
   - TI Saneado: 96.255 OCs ($172.25 MM CLP).
   - Peñalolén top 1: GTD Telesat ($871M, enlaces internet), top 2: Technosystems ($101M, tablet PCs 2025). Carpas erradicadas al 100%.
   - Providencia top 1: Advantage Computación ($85M). Carpas erradicadas al 100%.

4. **Verificar cobertura 2025–2026 en la base saneada:**
   ```powershell
   python .agents/teamwork/explorer_survey_r1_compras/audit_sanitized_temporal.py
   ```
   *Salida esperada:* 370 comunas con compras tecnológicas activas en 2025–2026.
