# Handoff Report: Adversarial Stress-Testing of M1 Sanitized Datasets (R1 / R2)

**Agente:** `challenger_m1_1`  
**Rol:** Empirical Challenger / Critic / Specialist  
**Tipo de Handoff:** Hard (Evaluación adversarial completa)  
**Fecha:** 24 de Octubre de 2026  
**Destinatario:** Orquestador (`556b08c5-0b60-438b-8148-0f340527cb59`)  
**Veredicto Explícito:** **CHALLENGE (RECHAZO CON BLOQUEO HASTA SUBSANACIÓN)**

---

## 1. Observation

A través de la suite adversarial automatizada `tests/test_adversarial_m1.py` y consultas SQL empíricas directas en DuckDB sobre `data/catastro_ti_saneado.parquet` y `data/comunas_enriched.json`, se observaron **9 fallas críticas de integridad y filtrado**:

### Hallazgo 1: Contaminación masiva por rubro de ingeniería sin filtro ONU (Caso Olmué)
- **Ubicación:** `scripts/build_sanitized_observatorio_data.py`, líneas 156-157:
  ```sql
  -- 2. Rubro Servicios TI e Ingeniería
  OR rubro = 'Servicios basados en ingeniería, ciencias sociales y tecnología de la información'
  ```
- **Evidencia Empírica:** En ChileCompra, el segmento 81 no es exclusivamente TI. La regla anterior admitió sin filtro códigos ONU no tecnológicos:
  * `81141806` (Inspección de instalaciones eléctricas): 6 contratos por **$98.086.177 CLP**.
  * `81141807` (Gasfitería y alcantarillado): 11 contratos por **$10.436.160 CLP** (incluye limpieza de fosas sépticas en Chillán Viejo `3673-85-SE19`, reparación de matriz de agua potable en Quintero `1202333-36-SE24`, y plantas de aguas servidas en Calle Larga `4105-16-SE22`).
  * `81151604` / `81151603` (Topografía y Fotogrametría): 14 contratos por **$71.110.380 CLP**.
  * `8110xxxx` (Ingeniería civil y mecánica): 14 contratos por **$18.764.380 CLP**.
- **Impacto directo en `comunas_enriched.json` (Olmué):**
  * Proveedor #1 de TI en Olmué: `MANTENIMIENTO MAURICIO ESTEBAN GUERRA CONTARDO EMPRESA INDIVIDUAL DE R` con **$97.941.177 CLP** (4 OCs), representando el **27,4% de todo el presupuesto TI comunal**.
  * Contratos históricos #1 y #2 de Olmué:
    - OC `3333-24-SE21` ($31.764.706 CLP): *"Inspección de instalaciones eléctricas MEJ. INSTALACIONES ELECTRICAS ESCUELA Q. ALVARADO"*.
    - OC `3333-224-SE21` ($25.714.286 CLP): *"Inspección de instalaciones eléctricas MEJ. INST. ELECTRICAS Y SALA DE ENLACES GRANIZO"*.

### Hallazgo 2: Presencia de palabras clave no-TI explícitas (`guitarra`)
- **Ubicación:** `data/catastro_ti_saneado.parquet`.
- **Evidencia Empírica:**
  * OC `2408-419-SE17` (Los Ángeles): Proveedor *SOC TECNOLOGICA Y SERVICIOS EXPRESS LIMITADA*, $197.479 CLP. Glosa: *"TABLET, PENDRIVE, GUITARRAS Y OTROS, PREMIOS CONC. TALENTOS PROGR. REC. BARRIOS"*.
  * OC `4079-584-AG20` (Cabrero): Proveedor *rodrigo andre*, $49.160 CLP. Glosa: *"GUITARRA, KARAOKE Y TABLET ODP NOTA DE PEDIDO N°26726 DIDECO"*.
- **Causa raíz:** En `build_sanitized_observatorio_data.py`, línea 123, la blacklist filtró `carpa`, `toldo`, etc., pero omitió `guitarra`, requerida explícitamente en el prompt de despacho.

### Hallazgo 3: Mantención vehicular en contratos recientes (Paillaco)
- **Ubicación:** `data/comunas_enriched.json` (Paillaco -> `top_contratos_recientes`).
- **Evidencia Empírica:**
  * OC `3789-7023-SE25` (Paillaco, año 2025): Proveedor *IMPORTADORA Y COMERCIALIZADORA NEUBACAR LTDA.*, $59.900 CLP.
  * Glosa en feed reciente: *"cajas de conmutación de computadores mantencion camioneta np300 patente lhdh-76 dete..."*. Corresponde a servicio mecánico y escaneo automotriz para una camioneta municipal Nissan NP300.

### Hallazgo 4: Agroveterinaria en contratos TI (Lumaco)
- **Ubicación:** `data/comunas_enriched.json` (Lumaco -> `top_contratos_historicos`).
- **Evidencia Empírica:**
  * OC `4406-952-AG25`: Proveedor *AGROVETERINARIA SANTA LUCIA SPA*, $5.664.391 CLP, admitido bajo el código ONU `80101508` (*"Asesorías en inteligencia de negocios"*).

### Hallazgo 5: Fuga de consultorías de arquitectura, urbanismo y marketing
- **Ubicación:** `data/catastro_ti_saneado.parquet` (ONU `80101508` y `80141600`).
- **Evidencia Empírica:**
  * En Las Condes: OC `2345-1469-SE22` ($11,1M) y `2345-1473-SE22` ($11,1M) a nombre de arquitectos y ex decanos de arquitectura (Pedro Bannen Lanata y José Rosas Vera), sumando $22,2M no-TI.
  * En Bulnes: OC `3902-27-SE20` ($5,57M): *"Diseño Rutas acces Veredas, centro Urbano"*.
  * En Lo Espejo: OC `750998-95-SE23`: *"GESTIÓN Y RECUPERACIÓN DE FONDOS LICENCIAS MÉDICAS"*.
  * En Chillán: OC `2471-368-CM17` (Agencia Lunetas, $1,49M, ONU `80141600`): *"ESTRATEGIA COMUNICACIONAL - MODELO Proyecto Difusión y Captación de matriculas"*.

### Hallazgo 6: 22.895 valores NaN/NULL en `monto_linea` en el Parquet saneado
- **Ubicación:** `data/catastro_ti_saneado.parquet`.
- **Evidencia Empírica:**
  ```sql
  SELECT count(*) FROM read_parquet('data/catastro_ti_saneado.parquet') 
  WHERE monto_linea IS NULL OR isnan(monto_linea);
  -- Resultado: 22.895 filas (19,1% del total de 119.659 filas)
  ```
- **Impacto:** Si un analista o el frontend calcula agregaciones directas desde el parquet sin `coalesce`, los cálculos devuelven `NaN` o distorsionan la suma. La aserción del worker `test_no_nans_in_financial_metrics` solo revisó los JSON comunales pero ignoró el archivo Parquet.

### Hallazgo 7: 1.175 filas con comuna ausente o inválida en Parquet
- **Ubicación:** `data/catastro_ti_saneado.parquet`.
- **Evidencia Empírica:**
  * 55 filas con `comuna_comprador` vacía / blank (`''`).
  * 208 filas con `comuna_comprador = 'NA'`.
  * 912 filas con códigos numéricos o caracteres de placeholder (`'58'`, `'*'`, `'Sin comuna'`).
- **Causa raíz:** En `build_sanitized_observatorio_data.py`, el filtro `WHERE comuna_comprador NOT IN ('Sin comuna', 'NA', 'Extranjero', '*')` se aplicó en `compute_comuna_metrics`, pero **no** se incluyó en `CREATE TABLE catastro_ti_saneado AS SELECT ...`.

---

## 2. Logic Chain

1. **Premisa 1 (Requerimiento R1):** El contrato original exige: *"0 contratos de rubros no-TI en las canastas funcionales de las 345 municipalidades"* y *"Restringir la canasta a códigos ONU y rubros tecnológicos auditables"*.
2. **Premisa 2 (Observación 1, 3 y 4):** Olmué tiene a un contratista de mantenimiento eléctrico como su proveedor tecnológico #1 ($97.9M), Paillaco tiene un servicio mecánico automotriz en sus compras recientes, y Lumaco tiene una agroveterinaria en sus contratos históricos.
3. **Premisa 3 (Observación 1 y 5):** La causa de esta contaminación es la cláusula abierta `OR rubro = 'Servicios basados en ingeniería, ciencias sociales y tecnología de la información'`, que no filtra por la familia TI `8111`, admitiendo gasfitería, fosas sépticas, instalaciones eléctricas y topografía; y la admisión indiscriminada de `80101508` y `80141600`.
4. **Premisa 4 (Observación 2, 6 y 7):** El archivo granular `catastro_ti_saneado.parquet` contiene guitarras, 22.895 registros con monto `NaN` y 1.175 registros sin comuna válida.
5. **Deducción Ineludible:** Los datasets generados para el Hito M1 violan los criterios de aceptación de Calidad de Datos del Requerimiento R1 y R5. Se debe emitir veredicto **CHALLENGE** para que el implementador subsane las reglas de filtrado y regenere los artefactos.

---

## 3. Caveats

- **No son malas intenciones del implementador:** El implementador logró una reducción masiva muy valiosa (purgó 84.932 registros y erradicó 100% de las carpas y el contrato emblemático de Peñalolén).
- **Alcance acotado de la falla:** Las fallas se concentran en 4 líneas específicas del script SQL (`scripts/build_sanitized_observatorio_data.py`), por lo que su remediación es rápida, determinista y de bajo riesgo.
- **Sin afectación en M2 (Accesibilidad/UX):** Esta observación es de integridad de datos y no invalida el trabajo de interfaz o diseño.

---

## 4. Conclusion

**Veredicto Oficial:** **CHALLENGE** (Rechazo formal con bloqueo de entrega hasta remediación).

**Calificación de Riesgo:** **CRÍTICO** para la credibilidad metodológica del Observatorio. Publicar una plataforma donde la Municipalidad de Olmué figura gastando el 27% de su presupuesto TI en un contratista de reparaciones eléctricas escolares, o donde figuran servicios de fosas sépticas y mantención de camionetas, destruiría la confianza institucional del estudio.

### Matriz de Remediación Concreta para el Implementador:

1. **En `scripts/build_sanitized_observatorio_data.py` (Capa 1 Blacklist):**
   Agregar al filtro de exclusión:
   ```sql
   txt LIKE '%guitarra%' OR prov LIKE '%guitarra%' OR
   txt LIKE '%fosa%septica%' OR txt LIKE '%fosa%séptica%' OR
   txt LIKE '%gasfiter%' OR txt LIKE '%alcantarillado%' OR
   txt LIKE '%camioneta%' OR txt LIKE '%vehiculo%' OR txt LIKE '%vehículo%' OR
   txt LIKE '%agroveterinaria%' OR txt LIKE '%veterinaria%' OR
   onu IN ('81141806', '81141807', '81151604', '81151603', '81141602', '80141600')
   ```

2. **En `scripts/build_sanitized_observatorio_data.py` (Capa 2 Whitelist):**
   Modificar la regla 2 del rubro de ingeniería para restringir estrictamente a la familia TI `8111`:
   ```sql
   -- 2. Rubro Servicios TI e Ingeniería: SOLO familia 8111 (Servicios informáticos)
   OR (rubro = 'Servicios basados en ingeniería, ciencias sociales y tecnología de la información' AND onu LIKE '8111%')
   ```
   En la regla 4 (Servicios profesionales), eliminar `80101508` si no viene acompañado de palabras TI (`inteligencia artificial`, `software`, `datos`, `bi`).

3. **En la exportación de `catastro_ti_saneado.parquet`:**
   Filtrar filas con comunas inválidas y montos nulos:
   ```sql
   WHERE comuna_comprador IS NOT NULL 
     AND comuna_comprador NOT IN ('Sin comuna', 'NA', 'Extranjero', '*')
     AND NOT regexp_matches(comuna_comprador, '^[0-9 *]+$')
     AND monto_linea IS NOT NULL 
     AND NOT isnan(monto_linea)
     AND monto_linea > 0
   ```

4. **Regenerar artefactos:**
   Ejecutar `python scripts/build_sanitized_observatorio_data.py` y verificar con `pytest tests/test_adversarial_m1.py -v`.

---

## 5. Verification Method

Para reproducir independientemente todas las observaciones y fallas reportadas:

1. **Ejecutar la suite de pruebas adversariales:**
   ```powershell
   pytest tests/test_adversarial_m1.py -v
   ```
   *Resultado observable:* **9 tests fallados** (`FAILED`) y 47 tests aprobados.

2. **Comprobar la anomalía de Olmué (Mantenimiento Eléctrico como #1 TI):**
   ```powershell
   python -c "import json; d=json.load(open('data/comunas_enriched.json', encoding='utf-8')); olm=next(c for c in d if c['comuna']=='Olmué'); print('Top 1 Olmué:', olm['top_proveedores'][0])"
   ```
   *Salida observada:* `Top 1 Olmué: {'proveedor': 'MANTENIMIENTO MAURICIO ESTEBAN GUERRA CONTARDO...', 'monto': 97941177.0, 'ocs': 4}`.

3. **Comprobar contratos de gasfitería, fosas sépticas y alcantarillado en Parquet:**
   ```powershell
   python -c "import duckdb; con=duckdb.connect(); print('Contratos gasfitería/alcantarillado:', con.execute(\"SELECT count(*) FROM read_parquet('data/catastro_ti_saneado.parquet') WHERE codigo_producto_onu = '81141807'\").fetchone()[0])"
   ```
   *Salida observada:* `Contratos gasfitería/alcantarillado: 11`.

4. **Comprobar los 22.895 NaNs en `monto_linea` en Parquet:**
   ```powershell
   python -c "import duckdb; con=duckdb.connect(); print('NaNs en monto_linea:', con.execute(\"SELECT count(*) FROM read_parquet('data/catastro_ti_saneado.parquet') WHERE monto_linea IS NULL OR isnan(monto_linea)\").fetchone()[0])"
   ```
   *Salida observada:* `NaNs en monto_linea: 22895`.
