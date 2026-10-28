# Adversarial Challenge Report — Milestone 1: Data Integrity, Temporal Coverage & Saneamiento Semántico (R1 & R2)

**Agente:** `challenger_m1_2`  
**Roles:** Critic, Specialist (Empirical Challenger)  
**Destinatario:** Orquestador (`556b08c5-0b60-438b-8148-0f340527cb59`)  
**Fecha:** 24 de Octubre de 2026  
**Veredicto Explícito:** **CHALLENGE**  
**Nivel de Riesgo Global:** **CRITICAL**

---

## Challenge Summary

El trabajo entregado por `worker_m1_compras` logró un avance valioso al erradicar las carpas (`%carpa%`) y el contrato espurio de Peñalolén (`2403-315-SE22`). Sin embargo, una auditoría empírica y adversarial profunda sobre los datos reales revela **dos fallas críticas y bloqueantes** que invalidan la integridad de la plataforma:

1. **Colisión de Diccionario y Destrucción Silenciosa de $13.645 Millones de Pesos en 68 Comunas:**
   En `scripts/build_sanitized_observatorio_data.py` (líneas 316–349 y 498–510), la agregación comunal agrupa por `comuna_comprador, region_comprador`. Debido a inconsistencias ortográficas de la región en Mercado Público ("Coquimbo" vs "Región de Coquimbo "), 68 comunas producen múltiples filas. Al poblar el diccionario en Python usando solo el nombre de la comuna, la última fila (generalmente un microfragmento residual) sobreescribe la fila principal. Esto causa que comunas de gran envergadura queden virtualmente en cero:
   - **Ovalle (111.000 hab):** Pasa de $2.763.061.287 CLP (783 OCs) a **$770 CLP (1 OC)** y gasto per cápita de **$0 CLP/hab**.
   - **Puerto Montt (245.000 hab, capital regional):** Pasa de $1.835.142.919 CLP (1.081 OCs) a **$2.649 CLP (2 OCs)** y gasto per cápita de **$0 CLP/hab**.
   - **Cañete (35.000 hab):** Pasa de $522.599.913 CLP (470 OCs) a **$537 CLP (1 OC)** y gasto per cápita de **$0 CLP/hab**.
   - **La Cisterna (90.000 hab):** Pasa de $504.363.346 CLP (374 OCs) a **$14.982 CLP (2 OCs)**.
   - En total, **$13.645.913.730 CLP y 9.083 órdenes de compra** desaparecen entre `national_kpis.json` ($172.240M) y `comunas_enriched.json` ($158.594M), contaminando además a `regiones_enriched.json` ($159.646M, brecha de $12.593M).

2. **Supervivencia de Falsos Positivos Automotrices y Mecánicos en Feeds y Catastro Saneado:**
   La whitelist basada en códigos ONU (`43211512` Servidores, `43211601` Switches, `43211508` Computadores, `43211503` Laptops) permitió la entrada de reparaciones mecánicas y repuestos de vehículos debido a que municipios compraron "computadores de camioneta" (ECUs de motor), aceite de motor y barras de dirección bajo códigos de computación:
   - **Paillaco (OC `3789-7023-SE25` en `top_contratos_recientes`):** "MANTENCION CAMIONETA NP300 PATENTE LHDH-76 DETECCION DE FALLA EN COMPUTADOR" por taller mecánico Neubacar Ltda.
   - **Nueva Imperial (OC `3485-378-AG26`):** "ADQUISICION DE COMPUTADOR PARA CAMIONETA TOYOTA HILUX 3.0" ($890.000 CLP) codificado como computador personal.
   - **Pedro Aguirre Cerda (OC `2393-1379-AG23`):** "1 computador (ecu) para camioneta changan" provisto por un lubricentro y taller mecánico.
   - **Los Lagos (OCs `1723-184-SE19` y `1723-596-SE20`):** "BARRA CENTRAL DIRECCION Camioneta Toyota" y "lts aceite 15W40 mobil para camioneta Toyota" clasificados como "Servidores centrales".

---

## 1. Observation

Evidencia directa, verbatim, de comandos ejecutados, archivos, líneas y consultas en DuckDB y JSON:

### 1.1 Inconsistencia Masiva entre Artefactos (Brecha de $13.645M CLP)
Ejecución del script adversarial `empirical_adversarial_test.py`:
```
parquet_total_rows: 119659
parquet_total_ocs: 96245
parquet_total_monto: $172,240,070,566 CLP
national_kpis.json total_ocs: 96245
national_kpis.json monto_total_clp: $172,240,070,566 CLP
Sum of monto_total in comunas_enriched.json: $158,594,156,836 CLP (87,162 OCs)
Sum of monto_total in regiones_enriched.json: $159,646,858,503 CLP (87,551 OCs)
Diferencia absoluta (Parquet/KPIs vs Comunas): $13,645,913,730 CLP y 9,083 OCs faltantes
```

### 1.2 Causa Raíz en `scripts/build_sanitized_observatorio_data.py`
1. **Líneas 316–349 (`compute_comuna_metrics`)**:
   ```python
   SELECT 
       comuna_comprador as comuna,
       region_comprador as region,
       count(distinct codigo_orden) as total_ocs,
       round(coalesce(sum(monto_linea), 0), 0) as monto_total,
       ...
   FROM catastro_ti_saneado
   ...
   GROUP BY comuna_comprador, region_comprador
   ```
2. **Líneas 499–510 (`merge_and_save_data`)**:
   ```python
   for _, row in comunas_df.iterrows():
       raw_name = str(row["comuna"]).strip()
       norm_name = normalize_text(raw_name)
       resolved = COMUNA_ALIASES.get(norm_name, norm_name)
       duck_metrics_by_norm[resolved] = {
           "row": row,
           "raw_name": raw_name
       }
   ```
   Al iterar `comunas_df`, si una comuna aparece en dos regiones por suciedad de texto en Mercado Público, la segunda fila sobreescribe a la primera en `duck_metrics_by_norm`.

### 1.3 Muestra Verbatim de Comunas Destruidas por la Sobreescritura
Consulta ejecutada sobre `catastro_ti_saneado.parquet` vs `comunas_enriched.json`:
- **Ovalle**:
  - En Parquet (Región de Coquimbo): 782 OCs, $2.763.060.517 CLP.
  - En Parquet (Coquimbo): 1 OC, $770 CLP.
  - En `comunas_enriched.json`: `total_ocs: 1`, `monto_total: 770.0`, `gasto_pc: 0.0`.
- **Puerto Montt**:
  - En Parquet (Región de los Lagos ): 1.079 OCs, $1.835.140.270 CLP.
  - En Parquet (Los Lagos): 2 OCs, $2.649 CLP.
  - En `comunas_enriched.json`: `total_ocs: 2`, `monto_total: 2649.0`, `gasto_pc: 0.0`.
- **Cañete**:
  - En Parquet: 470 OCs, $522.599.913 CLP.
  - En `comunas_enriched.json`: `total_ocs: 1`, `monto_total: 537.0`, `gasto_pc: 0.0`.
- **La Cisterna**:
  - En Parquet: 374 OCs, $504.363.346 CLP.
  - En `comunas_enriched.json`: `total_ocs: 2`, `monto_total: 14982.0`, `gasto_pc: 0.0`.
- **Chillán**: Perdió $1.086.967.012 CLP (figura con $57M en lugar de $1.144M).
- **San Carlos**: Perdió $749.632.237 CLP (figura con $45M en lugar de $795M).
- **Longaví**: Perdió $673.365.337 CLP.
- **Yungay**: Perdió $589.263.472 CLP.
- **El Carmen**: Perdió $493.277.382 CLP.
- **Penco**: Perdió $468.243.405 CLP.
- **Coihueco**: Perdió $397.692.481 CLP.
- **Quillón**: Perdió $391.711.917 CLP.
- **Los Muermos**: Perdió $275.554.586 CLP (figura con $9.080 CLP y 2 OCs).
- **Pelarco**: Perdió $217.192.864 CLP (figura con $9.735 CLP y 1 OC).
- **Pitrufquén**: Perdió $194.587.867 CLP (figura con $9.102 CLP y 2 OCs).
- **Corral**: Perdió $125.598.494 CLP (figura con $29.460 CLP y 1 OC).
- **Graneros**: Perdió $121.302.941 CLP (figura con $5.118 CLP y 4 OCs).

### 1.4 Muestra Verbatim de Falsos Positivos Automotrices en Feeds y Parquet
Consulta ejecutada sobre `catastro_ti_saneado.parquet` y feeds:
1. `Paillaco` (`top_contratos_recientes` en `comunas_enriched.json`):
   - OC: `3789-7023-SE25` (Fecha: 2025-12-18).
   - Proveedor: `IMPORTADORA Y COMERCIALIZADORA NEUBACAR LTDA.`
   - Monto: $59.900 CLP.
   - Glosa: `"Cajas de conmutación de computadores MANTENCION CAMIONETA NP300 PATENTE LHDH-76 DETECCION DE FALLA EN COMPUTADOR"`.
   - Código ONU: `43211601`.
2. `Nueva Imperial` (en `catastro_ti_saneado.parquet`):
   - OC: `3485-378-AG26` (Fecha: 2026-05-22).
   - Monto: $890.000 CLP.
   - Glosa: `"ADQUISICION DE COMPUTADOR PARA CAMIONETA TOYOTA HILUX 3.0 AÑO 2013 PATENTE FJWV-23.- (SP 570) COMPUTADOR PARA CAMIONETA TOYOTA HILUZ 3.0"`.
   - Código ONU: `43211508` (Computadores personales).
3. `Pedro Aguirre Cerda` (en `catastro_ti_saneado.parquet`):
   - OC: `2393-1379-AG23` (Fecha: 2023-11-05).
   - Proveedor: `LUBRICENTRO Y TALLER MECANICO GUILLERMO ENRIQUE SALINAS DONOSO E.I.R.L`.
   - Glosa: `"1 computador (ecu) para camioneta changan ppu GJFB-15"`.
   - Código ONU: `43211503` (Laptops).
4. `Los Lagos` (en `catastro_ti_saneado.parquet`):
   - OC: `1723-596-SE20`: `"camioneta Toyota 7306 lts aceite 15W40 mobil"`, clasificado como `43211512` ("Servidores centrales").
   - OC: `1723-184-SE19`: `"BARRA CENTRAL DIRECCION Camioneta Municipal Patente TR-7306"`, clasificado como `43211512` ("Servidores centrales").

---

## 2. Logic Chain

1. **Premisa 1 (Observación 1.2 y 1.3):** El pipeline agrupa en DuckDB por `(comuna_comprador, region_comprador)`. Al haber variaciones de texto en la región para 68 comunas, se generan múltiples registros por comuna. Al insertarse en un diccionario indexado únicamente por nombre de comuna, cada registro posterior pisa al anterior.
2. **Premisa 2 (Observación 1.1):** Esta sobreescritura elimina del agregado comunal $13.645.913.730 CLP y 9.083 OCs, reduciendo a comunas como Ovalle, Puerto Montt y Cañete a montos menores a $3.000 CLP y 1 a 2 órdenes de compra.
3. **Premisa 3 (Observación 1.3):** En la interfaz web, cuando un usuario selecciona Puerto Montt o Ovalle, la ficha comunal muestra gasto per cápita de $0 CLP y 1 OC, mientras que el drawer de contratos muestra compras por decenas o cientos de millones de pesos, generando una contradicción inmediata e inaceptable para investigadores, concejales y ciudadanos.
4. **Premisa 4 (Observación 1.4):** La taxonomía UNSPSC aplicada en `scripts/build_sanitized_observatorio_data.py` confió ciegamente en códigos ONU de computadores y servidores sin filtrar términos automotrices. Funcionarios municipales usaron esos códigos para comprar mantenciones de camionetas, aceites y computadores de inyección vehicular (ECUs), contaminando el feed de compras recientes (`top_contratos_recientes`) y violando el criterio de aceptación de 0 contratos no-TI.
5. **Deducción:** El artefacto entregado por `worker_m1_compras` tiene fallas estructurales graves de integridad de datos y no cumple con los criterios de aceptación R1 y R2 de ORIGINAL_REQUEST.md. Se emite veredicto **CHALLENGE**.

---

## 3. Adversarial Challenges & Stress Test Results

### [Critical] Challenge 1: Colisión de Diccionario en Multi-Región Mutila 68 Comunas
- **Supuesto desafiado:** Se asumió que `GROUP BY comuna_comprador, region_comprador` producía una fila por comuna o que las comunas tenían regiones unívocas en Mercado Público.
- **Escenario de ataque:** Comunas con compras históricas registradas bajo "Región de Coquimbo " y compras aisladas bajo "Coquimbo" generan dos filas en DuckDB. La fila pequeña sobreescribe la fila grande en el diccionario de Python.
- **Blast Radius:** Destrucción de $13.645.913.730 CLP en 68 comunas; gasto per cápita en $0 CLP para capitales provinciales y regionales; inconsistencia total entre `national_kpis.json`, `regiones_enriched.json` y `comunas_enriched.json`.
- **Mitigación obligatoria:**
  En `scripts/build_sanitized_observatorio_data.py`, agrupar exclusivamente por `comuna_comprador`:
  ```sql
  SELECT 
      comuna_comprador as comuna,
      count(distinct codigo_orden) as total_ocs,
      round(coalesce(sum(monto_linea), 0), 0) as monto_total,
      ...
  FROM catastro_ti_saneado
  WHERE comuna_comprador IS NOT NULL 
    AND comuna_comprador NOT IN ('Sin comuna', 'NA', 'Extranjero', '*')
    AND NOT regexp_matches(comuna_comprador, '^[0-9 *]+$')
  GROUP BY comuna_comprador
  ```
  La prueba empírica simulada (`simulate_fix.py`) demuestra que agrupar por `comuna_comprador` restituye inmediatamente las 345 comunas, recuperando $2.763M en Ovalle, $1.835M en Puerto Montt y $170.980M a nivel comunal agregado.

### [High] Challenge 2: Falsos Positivos Automotrices (ECU Camionetas, Aceite, Talleres Mecánicos)
- **Supuesto desafiado:** Se asumió que el código ONU garantiza por sí solo que un ítem es computacional.
- **Escenario de ataque:** Compra de mantención de camionetas, repuestos mecánicos y computadores de motor registrados en Mercado Público bajo ONU `43211601` (Switches) o `43211508` (Computadores personales).
- **Blast Radius:** Contaminación visible de feeds (`Paillaco`, `Nueva Imperial`, `Pedro Aguirre Cerda`, `Los Lagos`). Violación directa de R1 ("0 contratos de rubros no-TI").
- **Mitigación obligatoria:**
  En `scripts/build_sanitized_observatorio_data.py`, ampliar la Capa 1 (Blacklist) con exclusiones léxicas automotrices estrictas:
  ```sql
  (
      txt LIKE '%camioneta%' OR txt LIKE '%taller mecanico%' OR txt LIKE '%taller mecánico%' OR
      txt LIKE '%lubricentro%' OR prov LIKE '%taller mecanico%' OR prov LIKE '%lubricentro%' OR
      txt LIKE '%aceite%mobil%' OR txt LIKE '%barra central direccion%' OR
      txt LIKE '%computador para camioneta%' OR txt LIKE '%computador (ecu)%' OR
      txt LIKE '%falla en computador%' OR prov LIKE '%neubacar%' OR
      (lower(texto_descriptivo) LIKE '%vehiculo%' AND lower(texto_descriptivo) NOT LIKE '%gps%')
  ) as es_espurio_obvio
  ```

---

## 4. Stress Test Results

| Test ID | Dimensión Evaluada | Comportamiento Esperado | Comportamiento Observado | Resultado |
|---|---|---|---|---|
| **ST-01** | Feed Reciente: Año &ge; 2025 | 100% de registros con `anio >= 2025` | 100% de registros con año 2025 o 2026 | **PASS** |
| **ST-02** | Feed Reciente: Orden Cronológico | `ORDER BY fecha_aceptacion DESC, monto DESC` | 0 inversiones de fecha o monto detectadas | **PASS** |
| **ST-03** | Feed Histórico: Orden Cuantía | `ORDER BY monto DESC` | 0 inversiones de monto detectadas | **PASS** |
| **ST-04** | Erradicación de Carpas | 0 menciones de carpas en parquet y JSONs | 0 carpas encontradas en todo el corpus | **PASS** |
| **ST-05** | Cobertura Comunas Remotas | 28 comunas extremas con datos íntegros | Comunas presentes, pero Corral y Los Muermos clobberizadas | **FAIL (CRITICAL)** |
| **ST-06** | Consistencia Cruzada de Cifras | Total Parquet / KPIs == Suma Comunas | Brecha de $13.645.913.730 CLP y 9.083 OCs faltantes | **FAIL (CRITICAL)** |
| **ST-07** | Integridad Comunal Ovalle/P.Montt | Cifras reflejan compras reales (&gt;$1.800M) | Ovalle: $770 CLP (1 OC); P.Montt: $2.649 CLP (2 OCs) | **FAIL (CRITICAL)** |
| **ST-08** | Canasta 100% Libre de No-TI | Cero contratos mecánicos o vehiculares | Camionetas, ECUs de motor y aceite en Paillaco, N.Imperial | **FAIL (HIGH)** |

---

## 5. Caveats

1. **Cobertura de Combarbalá:** Se confirmó que Combarbalá no registra compras electrónicas directas en Mercado Público (0 OCs, $0 CLP); esta omisión es inherente a la fuente oficial y no un defecto del sistema.
2. **Antártica (CUT 12202):** No figura en el dataset de Mercado Público pero es inyectada correctamente en tiempo de ejecución por `app.js` (`deduplicateComunas`) para alcanzar el estándar territorial chileno de 346 comunas.
3. **Brecha Residual No Asignable ($1.259M CLP):** Del total de $172.240M en el catastro saneado, $1.259M CLP corresponden a compras con `comuna_comprador` etiquetada como `* `, `NA`, `None` o códigos numéricos huérfanos en Mercado Público. Estas no pueden asignarse a una comuna sin un proceso de conciliación por RUT comprador.

---

## 6. Conclusion & Verdict

**Veredicto Oficial:** **CHALLENGE**

El pipeline de M1 no puede ser aprobado en su estado actual. Aunque erradicó con éxito las carpas y el contrato de Peñalolén, introdujo un defecto crítico de agregación que deja a 68 municipalidades de Chile mutiladas (Ovalle con $770 CLP, Puerto Montt con $2.649 CLP) y filtró contratos mecánicos automotrices a los feeds de compras recientes.

### Acciones Requeridas para Levantar el Bloqueo:
1. **Reescribir `compute_comuna_metrics`** en `scripts/build_sanitized_observatorio_data.py` agrupando estrictamente por `comuna_comprador` (sin `region_comprador`).
2. **Ampliar la Capa 1 (Blacklist)** para erradicar compras automotrices (camionetas, ECUs de motor, lubricentros, aceites y talleres mecánicos).
3. **Re-ejecutar el pipeline completo** para sincronizar `catastro_ti_saneado.parquet`, `comunas_enriched.json`, `compras_saneadas_por_comuna.json`, `national_kpis.json` y `regiones_enriched.json`.
4. **Verificar que la suma de `monto_total` en `comunas_enriched.json` ascienda a ~$170.980M CLP** y que Ovalle y Puerto Montt reflejen sus compras genuinas (&gt;$1.800M).

---

## 7. Verification Method

Para reproducir empíricamente estos hallazgos desde `D:\Proyectos\observatorio-ti-municipal`:

1. **Reproducir la brecha de $13.645M CLP entre Parquet/KPIs y comunas_enriched:**
   ```powershell
   python -c "import json, duckdb; con=duckdb.connect(); p_monto=con.execute(\"SELECT round(sum(monto_linea),0) FROM read_parquet('data/catastro_ti_saneado.parquet')\").fetchone()[0]; d=json.load(open('data/comunas_enriched.json', encoding='utf-8')); c_monto=sum(c['monto_total'] for c in d); print(f'Parquet: {p_monto:,.0f} | Comunas: {c_monto:,.0f} | Gap: {p_monto - c_monto:,.0f} CLP')"
   ```
   *Salida observada:* `Parquet: 172,240,070,566 | Comunas: 158,594,156,836 | Gap: 13,645,913,730 CLP`.

2. **Verificar mutilación de Ovalle y Puerto Montt en comunas_enriched:**
   ```powershell
   python -c "import json; d=json.load(open('data/comunas_enriched.json', encoding='utf-8')); ov=next(c for c in d if c['comuna']=='Ovalle'); pm=next(c for c in d if c['comuna']=='Puerto Montt'); print(f'Ovalle: {ov[\"total_ocs\"]} OCs, ${ov[\"monto_total\"]:,.0f} CLP | Puerto Montt: {pm[\"total_ocs\"]} OCs, ${pm[\"monto_total\"]:,.0f} CLP')"
   ```
   *Salida observada:* `Ovalle: 1 OCs, $770 CLP | Puerto Montt: 2 OCs, $2,649 CLP`.

3. **Verificar mantención de camioneta en top_contratos_recientes de Paillaco:**
   ```powershell
   python -c "import json; d=json.load(open('data/comunas_enriched.json', encoding='utf-8')); pai=next(c for c in d if c['comuna']=='Paillaco'); print(pai['top_contratos_recientes'][0])"
   ```
   *Salida observada:* Contrato `3789-7023-SE25` con descripción `"MANTENCION CAMIONETA NP300 PATENTE LHDH-76"`.

4. **Condiciones de invalidación del veredicto CHALLENGE:**
   - Que `sum(c['monto_total'] for c in comunas_enriched) >= 170000000000`.
   - Que Ovalle registre `monto_total > 2000000000` y más de 700 OCs.
   - Que Puerto Montt registre `monto_total > 1500000000` y más de 1.000 OCs.
   - Que ninguna orden con glosa de mantención de vehículos o camionetas figure en los feeds de compras.
