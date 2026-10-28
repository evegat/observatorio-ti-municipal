# BRIEFING — 2026-10-24T16:00:00Z

## Mission
Investigar la ingesta de nóminas de portales web autónomos (R3), localización de DuckDB, scripts, estado de las 19 comunas restantes, y estándar Ley N° 21.719 con HMAC-SHA256.

## 🔒 My Identity
- Archetype: explorer
- Roles: investigation, synthesis
- Working directory: D:/Proyectos/observatorio-ti-municipal/.agents/teamwork/explorer_survey_r2_nominas
- Original parent: 556b08c5-0b60-438b-8148-0f340527cb59
- Milestone: survey_r2_nominas

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Ingesta de Nóminas de Portales Web Autónomos (Cero Estimaciones)
- Consolidar la métrica de Dotación Activa (corte mensual septiembre 2026) bajo estándar Ley N° 21.719 con seudonimización HMAC-SHA256
- Criterio: 100% de las 345 comunas con datos observados de dotación activa, sin ratios teóricos

## Current Parent
- Conversation ID: 556b08c5-0b60-438b-8148-0f340527cb59
- Updated: not yet

## Investigation State
- **Explored paths**:
  - `D:/Proyectos/P166 - Personal Municipal de Chile/src/portal_autonomo_harvester.py`
  - `D:/Proyectos/P166 - Personal Municipal de Chile/src/privacy_hasher.py`
  - `D:/Proyectos/P166 - Personal Municipal de Chile/src/cplt_schema_normalizer.py`
  - `D:/Proyectos/P166 - Personal Municipal de Chile/src/agent_ready_backend.py`
  - `D:/Proyectos/P166 - Personal Municipal de Chile/src/cplt_batch_harvester.py`
  - `D:/Proyectos/P166 - Personal Municipal de Chile/data/personal_municipal.duckdb`
  - `D:/Proyectos/P166 - Personal Municipal de Chile/data/cplt_municipal_directory.json`
  - `D:/Proyectos/P166 - Personal Municipal de Chile/data/maestro_comunas_chile.csv`
  - `D:/Proyectos/observatorio-ti-municipal/scripts/sync_rrhh_observatorio.py`
  - `D:/Proyectos/observatorio-ti-municipal/data/comunas_enriched.json`
- **Key findings**:
  1. `portal_autonomo_harvester.py` localizado en P166/src. Cuenta con detección dinámica de headers (`encontrar_fila_header`), parser robusto de planillas Excel (`parsear_planilla_excel`) y carga idempotente a DuckDB. Carece de crawler HTTP autónomo y soporte directo para .csv.
  2. DuckDB oficial: `D:/Proyectos/P166 - Personal Municipal de Chile/data/personal_municipal.duckdb` (63.7 MB, 1.755.343 registros en `rrhh_personal`).
  3. `sync_rrhh_observatorio.py` extrae el `latest_period` por comuna desde DuckDB. Al no hallar registros, cae al fallback de SUBDERE SINIM (`sinim_2019-2023.parquet`) aplicando ratio teórico de 1.6% para TI (`ti_tot = round(total * 0.016)`). Actualmente 27 comunas en `comunas_enriched.json` usan este ratio teórico.
  4. De las 27 comunas en SINIM, exactamente 19 son comunas autónomas sin datos en DuckDB (`not_in_portal` / `unknown`), 2 ya tenían registros en DuckDB (Providencia y Puente Alto, solo Planta sep-2026), y 8 comunas marcadas `portal` en CPLT (como Las Condes, Antofagasta, Copiapó) devuelven 0 registros vía CPLT Liferay porque publican en portales propios o tienen tablas vacías.
  5. Seudonimización Ley N° 21.719 opera vía HMAC-SHA256 truncado a 16 hex (`hash_person_identifier` y `hash_run`) con salt `MYWORLD_ANON_SALT`.
  6. Corte temporal septiembre 2026: 260 comunas ya tienen `202609`, 37 comunas tienen `202608`, 23 comunas tienen períodos anteriores y 25 no tienen ningún registro en DuckDB.
- **Unexplored areas**: Ninguna dentro del alcance de R3.

## Key Decisions Made
- Redactar `survey_nominas.md` y `handoff.md` consolidando el mapeo exhaustivo de las 19 comunas autónomas, los requisitos del harvester, y el plan de erradicación del ratio teórico de 1.6%.

## Artifact Index
- `D:/Proyectos/observatorio-ti-municipal/.agents/teamwork/explorer_survey_r2_nominas/survey_nominas.md` — Reporte exhaustivo de auditoría de nóminas
- `D:/Proyectos/observatorio-ti-municipal/.agents/teamwork/explorer_survey_r2_nominas/handoff.md` — Handoff estructurado en 5 componentes
