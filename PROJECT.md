# Project: Observatorio de Capacidades Tecnológicas Municipales de Chile

## Architecture
- **Ecosistema**: evegat.cl (`https://observatoriotimunicipal.evegat.cl`).
- **Arquitectura de Datos**:
  - `data/catastro_ti_municipal_completo_clasificado.parquet` / `build_sanitized_observatorio_data.py`: Pipeline saneado de compras públicas sin falsos positivos de carpas ni eventos (96.255 OCs puramente TI, 2014-2026).
  - `P166/data/personal_municipal.duckdb` / `portal_autonomo_harvester.py`: Ingesta nominal de 345 comunas con seudonimización HMAC-SHA256 Ley 21.719 (corte sept 2026).
  - `data/comunas_summary.json`: Payload inicial ultraliviano (~245-300 KB, 82% reducción) para mapa y rankings.
  - `data/comunas/{codigo_cut}.json`: 345 microarchivos JSON individuales (~3.6-12 KB) cargados bajo demanda al seleccionar comuna.
- **Frontend SPA**:
  - `index.html`: Marcado semántico, barra a11y, scrollytelling, mapa Leaflet, drawer híbrido, modal Glosario Metodológico (`#glosario-modal`), Termómetro de Madurez (0-100 pts), y Comparador Maipú vs Algarrobo.
  - `app.js`: Controlador unificado client-side con caché Map `state.comunaDetailsCache`, hash routing, dos feeds de compras (Recientes 2025-2026 vs Emblemáticos Históricos).
  - `style.css`: Tokens de diseño sobrio evegat.cl, soporte de temas claro, oscuro y alto contraste WCAG 2.1 AA.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Saneamiento Semántico de Compras (R1) | Purga de 60.012 contratos no-TI (carpas Peñalolén $88M, carpas Providencia $343M, gas, eventos). Canasta reducida a 96.255 OCs tecnológicas reales. | M1 | Survey Compras |
| 2 | Restricción Taxonómica Códigos ONU TI (R1) | Filtrado estricto por 5 familias tecnológicas auditables (Hardware, SaaS, Telecom, IA, Cyber) erradicando el falso positivo `%rpa%`. | M1 | Survey Compras |
| 3 | Cobertura Temporal 2025–2026 (R2) | Integración efectiva de 14.459 OCs de 2025 y 2026 (ene-sep) en las 370 entidades compradoras. | M1 | Survey Compras |
| 4 | Feed Cronológico Desacoplado 2025-2026 (R2) | Desacoplamiento en datos e interfaz: «Últimas Compras Tecnológicas (2025–2026)» vs «Contratos Emblemáticos de Mayor Cuantía (Histórico)». | M1 | Survey Compras |
| 5 | Ingesta de 27 Comunas a DuckDB (R3) | Extensión de `portal_autonomo_harvester.py` e ingesta de las 19 comunas autónomas (Las Condes, Recoleta, etc.) y 8 CPLT vacías a DuckDB. | M2 | Survey Nóminas |
| 6 | Erradicación de Ratios Teóricos (R3) | Eliminación de la estimación de 1.6% en `sync_rrhh_observatorio.py`; 100% de las 345 comunas con dotación observada real al corte sept 2026. | M2 | Survey Nóminas |
| 7 | Cumplimiento Ley N° 21.719 (R3) | Seudonimización estricta HMAC-SHA256 de 16 caracteres hexadecimales para todos los registros de dotación activa municipal. | M2 | Survey Nóminas |
| 8 | Desacoplamiento de Datos en 2 Niveles (R4) | Reemplazo del monolito de 1.4 MB por `data/comunas_summary.json` (<400 KB, ~245-307 KB) y `data/comunas/{codigo_cut}.json` bajo demanda (<150 ms). | M3 | Survey Web |
| 9 | Drawer Híbrido y Caché en Memoria (R4) | Despliegue instantáneo (0 ms) del drawer con datos del resumen y carga diferida no bloqueante de contratos y normativa con caché Map. | M3 | Survey Web |
| 10 | Glosario Metodológico Interactivo (R4) | Componente accesible en navbar y modal de bienvenida con las 5 secciones metodológicas explicativas. | M3 | Survey Web |
| 11 | Termómetro de Madurez 0–100 pts (R4) | Calibración en 5 dimensiones de 20 pts con indicador visual semi-donut SVG en la ficha comunal y drawer. | M3 | Survey Web |
| 12 | Paradoja de Escala Maipú vs Algarrobo (R4) | Callout analítico en el Comparador A vs B explicando por qué Algarrobo gasta 5.7x per cápita que Maipú teniendo 0 staff TI vs 9 en Maipú. | M3 | Survey Web |
| 13 | Auditoría Cruzada Ciega con Codex CLI (R5) | Verificación independiente de datos con `codex-cli 0.154.0` (`codex exec`) certificando consistencia, 0 NaNs y paridad CUT. | M4 | Survey Web |
| 14 | Regresión E2E y Gates MyWorld Harness (R5) | Suite completa de pruebas de regresión y pasaje de gates `preflight`, `quality` y `security` del arnés MyWorld. | M4 | Survey Web |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Saneamiento Semántico y Cobertura 2025-2026 de Compras Públicas | Purga de carpas/espurios, canasta ONU TI estricta, integración 2025-2026 y generación de feeds recientes vs históricos. | none | PLANNED |
| M2 | Ingesta de Nóminas de Portales Autónomos en DuckDB (Cero Estimaciones) | Extensión de `portal_autonomo_harvester.py`, ingesta de 27 comunas en DuckDB, actualización `sync_rrhh_observatorio.py` (0 ratios teóricos). | none | PLANNED |
| M3 | Modularización de Arquitectura Web y Nuevas Vistas | Generación de `comunas_summary.json` + `data/comunas/{cut}.json`, drawer bajo demanda, Glosario, Termómetro 0-100 y Maipú vs Algarrobo. | M1, M2 | PLANNED |
| M4 | Verificación Adversarial Cruzada con Codex CLI y Gates MyWorld | Auditoría ciega con Codex CLI, suite de regresión E2E (0 NaNs, latencia <150 ms, payload <400 KB) y gates del arnés. | M3 | PLANNED |

## Interface Contracts
### Comunas Summary (`data/comunas_summary.json`)
- Lista de 345 objetos comunales con 27 campos agregados:
  `["codigo_cut", "comuna", "comuna_raw", "region", "poblacion", "total_ocs", "monto_total", "gasto_pc", "score_madurez", "nivel_madurez", "lat", "lng", "dotacion_total", "pct_honorarios", "dotacion_ti", "ret_ratio", "cuadrante_capacidad", "tiene_lockin_legado", "tiene_foss", "tiene_infra_propia", "monto_hardware", "monto_saas", "monto_ia", "monto_telecom", "monto_cyber", "monto_legado", "monto_foss"]`
- Tamaño: $\le 350$ KB (minificado <250 KB).

### Comuna Detail (`data/comunas/{codigo_cut}.json`)
- Objeto individual con detalle profundo:
  - `codigo_cut`: string de 5 dígitos (ej. `"13101"`).
  - `comuna`: nombre oficial.
  - `resumen`: objeto con indicadores agregados.
  - `top_contratos_recientes`: lista de órdenes de compra 2025-2026 ordenadas cronológicamente por fecha/año.
  - `top_contratos_historicos`: lista de contratos emblemáticos de mayor cuantía (2014-2026) ordenados por monto DESC.
  - `top_proveedores`: lista de proveedores tecnológicos líderes.
  - `normativa_tech`: detalle de ordenanzas, convenios e iniciativas IA/datos.
  - `estamentos_pct`: desglose de planta, contrata y honorarios.

### DuckDB ↔ Observatorio Sync
- `personal_municipal.duckdb` tabla `rrhh_personal`:
  - `id_persona_hash`: string de 16 caracteres hexadecimales (HMAC-SHA256).
  - `comuna_id`: slug normalizado de comuna.
  - `periodo`: integer `YYYYMM` (corte sept 2026: `202609` o `202608`).
  - `estamento`: `"PLANTA"`, `"CONTRATA"`, `"HONORARIOS"`, `"CODIGO DEL TRABAJO"`.
  - `es_ti`: boolean / integer flag determinado por keywords de cargo/función.

## Code Layout
- `scripts/build_sanitized_observatorio_data.py`: Pipeline de saneamiento de compras públicas (M1).
- `D:/Proyectos/P166 - Personal Municipal de Chile/src/portal_autonomo_harvester.py`: Cosechador de nóminas autónomas (M2).
- `scripts/sync_rrhh_observatorio.py`: Sincronizador DuckDB -> observatorio (M2).
- `scripts/split_comunas_architecture.py`: Generador de `comunas_summary.json` y `data/comunas/{cut}.json` (M3).
- `app.js`: Controlador client-side, modularización on-demand, glosario, termómetro (M3).
- `index.html`: Estructura HTML5, navbar, modales, drawer (M3).
- `style.css`: Estilos visuales, termómetro SVG, callout comparativo (M3).
- `scripts/verify_data_integrity.py`: Script de verificación determinista de integridad de datos (M4).
- `tests/`: Batería de pruebas de regresión unitaria y E2E (M4).
