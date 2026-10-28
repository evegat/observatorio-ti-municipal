# Scope: Observatorio de Capacidades Tecnológicas Municipales de Chile (PUB021)

## Architecture
- Static client-side vanilla JS architecture, modular event-driven, zero build step.
- Primary components: `index.html`, `app.js`, `style.css`, `data/` JSON catalogs.

## Feature Inventory
| # | Feature | Description | Milestone | Status |
|---|---------|-------------|-----------|--------|
| 1 | 7 Capas Territoriales en Mapa | Estilos y leyendas dinámicas para 7 dimensiones. | M1 | DONE |
| 2 | Deduplicación de Microdatos | 346 comunas únicas a partir de 397 registros. | M1 | DONE |
| 3 | Búsqueda NFD y Alias | Tolerancia a tildes y nombres alternativos. | M1 | DONE |
| 4 | Sugerencia Proveedor-Comuna | Detección de ERP (CAS-CHILE, Opciones). | M1 | DONE |
| 5 | Flujo de Descarga Brújula IA | Modal, validaciones, keepalive, consentimiento. | M1 | DONE |
| 6 | Resiliencia de Carga Inicial | Manejo de excepciones y banner accesible. | M1 | DONE |
| 7 | 140 Clases CSS | Completitud de clases en `style.css`. | M2 | DONE |
| 8 | Contraste Cromático WCAG AA | 66/66 pares pasan (botones en oscuro/contraste >= 4.5:1). | M2 | DONE |
| 9 | Sincronización de Temas | Esri basemap y estilos adaptados a temas. | M2 | DONE |
| 10 | Accesibilidad Teclado | Skip-link, focus trap, retorno de foco, sortable tables. | M2 | DONE |
| 11 | Termómetro SVG | fill="currentColor" dinámico. | M2 | DONE |
| 12 | Simulación 100 Usuarios | 5 estamentos, tasa de éxito 97.0% (>95%), matriz de hallazgos. | M3 | DONE |
| 13 | Veredicto JEV y Cero AI-Slop | 12/12 secciones PASS, rigor editorial republicano. | M3 | DONE |
| 14 | Verificación E2E y Victoria | Gates MyWorld Harness (`preflight`, `quality`, `security`), auditoría final y cierre. | M4 | DONE |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Ingeniería Client-Side & Resiliencia | Capas `ret`/`rrhh`, deduplicación 346 comunas, NFD, alias, API Brújula IA. | none | DONE (Gate PASS) |
| M2 | UX/UI, Accesibilidad WCAG & Temas | 140 clases CSS, 66 contrastes WCAG AA, responsive 360px-1400px 0px overflow, focus trap. | M1 | DONE (Gate PASS) |
| M3 | Simulación de 100 Usuarios & JEV | Ejecución de `simulate_100_users.py` (97% éxito >95%), matriz de hallazgos, evaluación JEV. | M2 | DONE (Gate PASS) |
| M4 | Verificación E2E, Auditoría & Cierre | Gates de arnés (`harness.ps1 quality`, `security`), auditoría forense final y reclamo de victoria. | M3 | DONE (Gate PASS) |
