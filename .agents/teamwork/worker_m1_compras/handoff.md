# Handoff Report: Saneamiento Semántico y Cobertura Temporal de Compras Públicas TI (M1: R1 / R2)

**Agente:** `worker_m1_compras`  
**Rol:** Implementer / QA / Specialist  
**Tipo de Handoff:** Hard (Tarea completada)  
**Fecha:** 24 de Octubre de 2026  
**Destinatario:** Orquestador (`556b08c5-0b60-438b-8148-0f340527cb59`) y Auditor de Previas  

---

## 1. Observation

1. **Estado Inicial del Catastro y Presencia de Falsos Positivos:**
   - En `D:/Proyectos/PUB021 - Paper Adopcion IA y Tecnologias en Municipios/data/catastro_ti_municipal_completo_clasificado.parquet`:
     * Total registros brutos: **204.591 ítems**, **153.770 órdenes de compra (OCs)**, **$312.570.954.499 CLP**.
     * Registros clasificados falsamente como IA por coincidencia de substring `%rpa%`: **26.535 registros** ($63.420 millones de pesos), correspondientes a carpas (`c-a-[r-p-a]`), escarpe vial y zarpas de limpieza.
     * En Peñalolén: Orden de compra `2403-315-SE22` (año 2022) por **$88.935.000 CLP** a nombre de *ALCALDE Y ASOCIADOS LIMITADA* (código ONU `30221001` - Carpas) figuraba como 3° contrato tecnológico más relevante de la comuna.
     * En Providencia: Proveedores #1 y #2 eran *CARPAS ARAOS Y PEREZ* ($221.478.882 CLP, 25 OCs) y *LAGOS CARPAS SPA* ($122.219.322 CLP, 13 OCs), acumulando $343.698.204 CLP espurios.

2. **Implementación del Pipeline de Saneamiento:**
   - Archivo implementado: `scripts/build_sanitized_observatorio_data.py`.
   - Se aplicó el filtro de dos capas auditables:
     * **Capa 1 (Blacklist):** Exclusión de códigos ONU no-TI (`30221001`, `10101704`, `30151901`, `90101602`, `90151602`, `80141607`, `90111603`, `72131702`, `72131701`, `90151803`, `80141611`, `80141609`, `80141605`, `80141620`, `76121503`, `53121603`, `80111504`) y glosas/proveedores espurios (carpas, toldos, eventos, banquetes, escenarios, gas licuado, zapatos de seguridad, obras civiles, pavimentación, cursos de apicultura, torneos, etc.).
     * **Capa 2 (Whitelist Taxonómica UNSPSC):** Admisión exclusiva de las 5 familias tecnológicas auditables (Hardware e Infraestructura, SaaS y Cloud, Redes y Telecomunicaciones, Ciberseguridad, Televigilancia y Reloj Biométrico).
     * **Corrección de IA:** Reemplazo de `%rpa%` por expresiones regulares con límites de palabra (`\b(rpa|robotic process automation)\b`), reduciendo el gasto de IA de $63.420M espurios a **$1.581.239.685 CLP** de IA/automatización genuina.

3. **Métricas Empíricas Post-Saneamiento Observadas:**
   - Ejecución de `python scripts/build_sanitized_observatorio_data.py`:
     * Total registros saneados: **119.659 ítems**, **96.245 órdenes de compra únicas**, **$172.240.070.566 CLP**.
     * Total espurio purgado: **84.932 ítems**, **57.525 OCs**, **$140.330.883.933 CLP** (44,9% del volumen financiero total eliminado).
     * Menciones de carpas en toda la base saneada: **0 (Cero absoluto)**.
     * Presencia de OC `2403-315-SE22` de Peñalolén: **0 (Erradicado al 100%)**.

4. **Desacoplamiento de Feeds y Cobertura Temporal 2025–2026:**
   - Se crearon dos estructuras desacopladas en cada comuna:
     * `top_contratos_recientes`: Feed cronológico ordenado por `fecha_aceptacion DESC, monto DESC` restringido a compras de 2025 y 2026.
     * `top_contratos_historicos`: Contratos emblemáticos históricos ordenados por `monto DESC` (2014–2026).
     * `top_contratos`: Mantenido como alias idéntico a `top_contratos_historicos` para preservar retrocompatibilidad total con el frontend y suites de prueba.
   - Cobertura temporal verificada: **344 de 345 comunas** reflejan compras tecnológicas activas en 2025 y 2026 (la única comuna sin registros de compras en Mercado Público es Combarbalá, que se preserva con valores neutrales seguros).
   - Volumen de compras 2025–2026 incorporado:
     * 2025: 9.505 OCs transadas por **$26.202.908.483 CLP**.
     * 2026 (ene–sep): 4.951 OCs transadas por **$13.234.510.420 CLP**.
     * Total compras recientes activas: **14.456 OCs por $39.437.418.903 CLP**.

5. **Casos Clave Verificados en JSON:**
   - **Peñalolén (`comunas_enriched.json`):**
     * Monto total saneado: $2.060.203.387 CLP (Gasto pc: $7.549 CLP/hab).
     * Top Proveedores: GTD TELESAT ($1.002M), GTD TELEDUCTOS ($152M), TECHNOSYSTEMS ($112M), IMPORTADORA HEVIA ($66M), STM Computación ($60M). 0 carpas, 0 productoras de eventos.
     * Contratos Recientes 2025–2026 (6): Servidores centrales GTD (2026-09), All in One Lenovo (2026-08), Tablets Mave Technology (2026-08), Asus Vivobook (2026-08), HP ProBook (2026-08).
     * Contratos Emblemáticos: GTD Telesat ($871M enlaces fibra óptica), Technosystems ($101M tablets 2025), GTD Telesat ($71M), GTD Teleductos ($66M). 0 carpas.
   - **Providencia (`comunas_enriched.json`):**
     * Monto total saneado: $347.105.845 CLP (Gasto pc: $2.116 CLP/hab, corregido desde los $7.707 inflados).
     * Top Proveedores: ADVANTAGE COMPUTACION SPA ($85M), SIT LTDA ($67M), GTD INTESIS ($48M), STM Computación ($29M), Servacom ($15M). Carpas Araos y Lagos Carpas 100% eliminadas.

6. **Artefactos Emitidos y Sincronizados:**
   - `data/catastro_ti_saneado.parquet` (119.659 filas, 96.245 OCs).
   - `data/compras_saneadas_por_comuna.json` (345 comunas con indicadores y feeds desacoplados).
   - `data/comunas_enriched.json` (actualizado con métricas saneadas y feeds desacoplados, manteniendo íntegra toda la estructura de RRHH y normativa).
   - `data/national_kpis.json` (actualizado a 96.245 OCs, $172.240.070.566 CLP y serie anual saneada).
   - `data/proveedores_ranking.json` (ranking nacional saneado de 40 empresas TI).
   - `data/regiones_enriched.json` (agregaciones regionales saneadas).

7. **Pruebas Automatizadas:**
   - Se implementó `tests/test_sanitized_purchases_m1.py` con 8 tests:
     * `test_parquet_file_exists_and_valid`: PASSED.
     * `test_zero_carpas_in_parquet`: PASSED.
     * `test_penalolen_spurious_contract_eradicated`: PASSED.
     * `test_providencia_top_vendors_free_of_carpas`: PASSED.
     * `test_zero_carpas_in_all_345_comunas`: PASSED.
     * `test_temporal_coverage_and_decoupled_feeds`: PASSED.
     * `test_no_nans_in_financial_metrics`: PASSED.
     * `test_national_kpis_consistency`: PASSED.
   - Harness test (`node -c app.js`): PASSED.

---

## 2. Logic Chain

1. **Premisa 1 (Observación 1):** La base previa contenía 26.535 contratos de carpas y toldos que se clasificaron como IA debido a que el substring `%rpa%` coincide con `c-a-r-p-a`. Asimismo, licitaciones de producción de eventos, banquetes y obras civiles contaminaban el gasto per cápita comunal (Peñalolén y Providencia presentaban empresas de carpas en su podio).
2. **Premisa 2 (Observación 2 y 3):** La aplicación del filtro de 2 capas elimina en su totalidad los rubros y códigos ONU ajenos a TI y fuerza coincidencia por palabra completa `\b(rpa|robotic process automation)\b`.
3. **Premisa 3 (Observación 4 y 5):** Los contratos de compras de 2025 y 2026 ya estaban transados en las fuentes pero quedaban invisibilizados si solo se mostraban los 4 contratos históricos más cuantiosos. Al separar en la estructura de datos `top_contratos_recientes` (2025–2026 cronológico) y `top_contratos_historicos` (saneados por cuantía), se garantiza cobertura en 344 de 345 comunas y trazabilidad contemporánea.
4. **Deducción:** Todos los requisitos R1 y R2 están completados de manera genuina, verificable y sin regresión de código ni contaminación en los datos.

---

## 3. Caveats

- **Combarbalá:** Es la única comuna del territorio nacional que no registra órdenes de compra electrónicas de TI emitidas bajo su RUT en Mercado Público en el periodo 2015–2026 (o gestiona sus adquisiciones mediante convenios de asociación provincial). Se preserva con 0 OCs y listas vacías para garantizar la existencia de las 345 comunas sin generar registros artificiales.
- **Frontend SPA (M3):** Siguiendo las instrucciones de asignación exclusiva, no se modificaron `app.js` ni `index.html` en este turno, garantizando que el agente de M3 pueda realizar el desacoplamiento en interfaz y drawer bajo demanda. Los datos en `data/comunas_enriched.json` y `data/compras_saneadas_por_comuna.json` ya exponen ambos feeds listos para consumo directo.

---

## 4. Conclusion

1. **Requerimiento R1 Completado:** La base de datos de compras públicas quedó 100% saneada, purgando 57.525 órdenes de compra espurias ($140.330 millones de pesos) y dejando una canasta limpia de 96.245 órdenes de compra tecnológicas ($172.240 millones de pesos). 0 carpas en todas las comunas; Peñalolén y Providencia regularizadas con proveedores tecnológicos genuinos.
2. **Requerimiento R2 Completado:** Cobertura temporal extendida a 2025 y 2026 (ene–sep) con 14.456 OCs recientes integradas en 344 comunas y estructura desacoplada de feeds recientes vs históricos.
3. **Cero regresiones:** Todas las pruebas pasan (8/8 unitarias, harness `node -c app.js` limpio, compatibilidad con RRHH intacta).

---

## 5. Verification Method

Para verificar independientemente este trabajo, ejecutar los siguientes comandos en PowerShell desde `D:/Proyectos/observatorio-ti-municipal`:

1. **Ejecutar la suite de pruebas automatizadas de M1:**
   ```powershell
   pytest tests/test_sanitized_purchases_m1.py -v
   ```
   *Salida esperada:* 8 passed en ~0.3s.

2. **Verificar ausencia absoluta de carpas en el parquet saneado:**
   ```powershell
   python -c "import duckdb; con=duckdb.connect(); print('Carpas encontradas:', con.execute(\"SELECT count(*) FROM read_parquet('data/catastro_ti_saneado.parquet') WHERE lower(texto_descriptivo) LIKE '%carpa%' OR lower(nombre_proveedor) LIKE '%carpa%'\").fetchone()[0])"
   ```
   *Salida esperada:* `Carpas encontradas: 0`.

3. **Verificar que el contrato espurio 2403-315-SE22 de Peñalolén está erradicado:**
   ```powershell
   python -c "import duckdb; con=duckdb.connect(); print('Contrato 2403-315-SE22:', con.execute(\"SELECT count(*) FROM read_parquet('data/catastro_ti_saneado.parquet') WHERE codigo_orden = '2403-315-SE22'\").fetchone()[0])"
   ```
   *Salida esperada:* `Contrato 2403-315-SE22: 0`.

4. **Verificar top proveedores de Providencia en comunas_enriched.json:**
   ```powershell
   python -c "import json; d=json.load(open('data/comunas_enriched.json', encoding='utf-8')); provi=next(c for c in d if c['comuna']=='Providencia'); print('Providencia top 1:', provi['top_proveedores'][0]['proveedor'])"
   ```
   *Salida esperada:* `Providencia top 1: ADVANTAGE COMPUTACION SPA`.

5. **Verificar sintaxis del arnés MyWorld:**
   ```powershell
   node -c app.js
   ```
   *Salida esperada:* Código de salida 0 sin errores.
