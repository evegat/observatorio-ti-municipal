# Project: Observatorio de Capacidades Tecnológicas Municipales de Chile

## Architecture
- **Ecosistema**: evegat.cl (`https://observatoriotimunicipal.evegat.cl`).
- **Arquitectura**: Sitio estático client-side vanilla JavaScript modular orientado a eventos, sin build step ni empaquetadores pesados.
- **Componentes**:
  - `index.html`: Marcado semántico HTML5, barra de accesibilidad, hero, scrollytelling, visor cartográfico Leaflet, drawer de ficha comunal, módulo RRHH/RET, centro de rankings y 3 modales accesibles (guía, marco legal, registro de descarga).
  - `app.js`: Controlador unificado client-side (estado global `state`, carga asíncrona de datos, capas de Leaflet, hash routing `#comuna=`, comparador A vs B, filtros, ordenamiento, intercepción de descargas y telemetría).
  - `style.css`: Sistema de diseño editorial inspirado en la sobriedad republicana y tipográfica de `evegat.cl`, con soporte de temas claro, oscuro y alto contraste mediante variables CSS.
  - `data/`: Microdatos consolidados (`comunas_enriched.json`, `national_kpis.json`, `regiones_enriched.json`, `proveedores_ranking.json`).

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | 7 Capas Territoriales en Mapa | Soporte de estilos dinámicos y leyendas para las 7 dimensiones: `madurez`, `gasto_pc`, `ret`, `rrhh`, `lockin`, `foss`, `infra`. | M1 | Survey (Eng/UX/Sim) |
| 2 | Deduplicación de Microdatos Comunales | Consolidación client-side de las 346 comunas únicas a partir de los 397 registros brutos de Mercado Público/SINIM. | M1 | Survey (Eng/Sim) |
| 3 | Búsqueda Tolerante a Acentos y Alias | Normalización NFD y diccionario de alias toponímicos chilenos (Coyhaique, Marchigüe, Navarino, Santiago Centro). | M1 | Survey (Sim) |
| 4 | Sugerencia Cruzada Proveedor-Comuna | Detección de búsquedas de proveedores ERP (CAS-CHILE, Opciones) en input comunal con redirección guiada. | M1 | Survey (Sim) |
| 5 | Flujo de Descarga y Telemetría Brújula IA | Intercepción modal, validación de campos, persistencia en API con `keepalive: true` y sincronización de checkbox de consentimiento. | M1 | Survey (Eng) |
| 6 | Resiliencia de Carga Inicial | Manejo de excepciones y banner accesible de reintento si la carga de datos locales sufre interrupciones. | M1 | Survey (Eng) |
| 7 | Sistema de Estilos Faltantes (48 clases) | Implementación de las 48 clases CSS huérfanas en `style.css` (a11y-topbar, hero-actions, guia-banner, site-footer). | M2 | Survey (UX) |
| 8 | Contraste Cromático WCAG 2.1 AA | Calibración de luminancia para `--muted` (#556265 >= 4.5:1), `--gold-text` (#875f00 >= 4.5:1) y anillo de foco accesible. | M2 | Survey (UX) |
| 9 | Sincronización de Temas y Leaflet | Adaptación de inputs, tablas, leyendas y popups en modo oscuro/contraste; eliminación del parpadeo del contenedor de mapa. | M2 | Survey (UX) |
| 10 | Accesibilidad Teclado y Modales | Implementación de skip-link, trampa de foco (`focus trap`) y retorno de foco en modales, navegación por teclado en tablas (`<th>`, `<tr>`). | M2 | Survey (UX) |
| 11 | Termómetro SVG Dinámico | Uso de `fill="currentColor"` en dígito central de termómetro SVG para legibilidad en todos los temas. | M2 | Survey (UX) |
| 12 | Panel de Simulación 100 Usuarios | Ejecución empírica del runner automatizado en los 5 estamentos con tasa de éxito >95%. | M3 | Survey (Sim) |
| 13 | Veredicto JEV y Cero AI-Slop | Certificación de rigor editorial, ausencia de sensacionalismo y estado PASS en todos los componentes. | M3 | Survey (Sim/JEV) |
| 14 | Verificación E2E y Reclamo de Victoria | Ejecución de gates de calidad de MyWorld Harness, validación de criterios de aceptación y reporte al Sentinel. | M4 | Project Pattern |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Ingeniería Client-Side & Resiliencia | Capas `ret`/`rrhh`, deduplicación de 346 comunas, normalización NFD, alias, sugerencia de proveedores y fix de consentimiento. | none | DONE (Audit Clean, 320+2513 checks passed) |
| M2 | UX/UI, Accesibilidad WCAG & Temas | 48 clases CSS, ratios de contraste WCAG AA, modo oscuro/contraste completo, focus trap en modales, skip-link, tablas navegables. | M1 | PLANNED |
| M3 | Simulación de 100 Usuarios & JEV | Ejecución de `simulate_100_users.py` (>95% éxito), auditoría JEV de componentes, matrices de evidencia y remediación de micro-detalles. | M2 | PLANNED |
| M4 | Verificación E2E, Auditoría & Cierre | Gates de arnés (`node -c`, `harness.ps1 quality`), auditoría forense de integridad (`teamwork_preview_auditor`) y reclamo de victoria. | M3 | PLANNED |

## Interface Contracts
### Datos Comunales ↔ Leaflet & Renderizador
- `comuna`: `{ comuna, region, codigo_cut, lat, lng, monto_total, gasto_pc, ret_ratio, pct_honorarios, cuadrante_capacidad, ... }`
- Cada registro en `state.comunas` debe tener `lat` y `lng` válidos (no nulos) y representar un municipio único (346 en total).
- Las funciones `getMarkerStyle(comuna)` y `updateLegend()` deben soportar exactamente las 7 claves de capa:
  `["madurez", "gasto_pc", "ret", "rrhh", "lockin", "foss", "infra"]`.

### Modal de Registro ↔ API Brújula IA
- Endpoint: `https://brujulaiaedusuperior.evegat.cl/api/register-download`
- Payload: `{ nombre, email, institucion, perfil, proposito, consentimiento: boolean, source: "observatorio-ti-municipal", ts: ISOString }`
- Telemetría no bloqueante: Fallback local garantizado incluso ante falla HTTP o bloqueo de CORS.

### Accesibilidad Teclado ↔ Modales
- Al abrir modal: foco transferido al primer elemento interactivo o botón de cierre.
- Durante modal abierto: `Tab` y `Shift+Tab` confinados estrictamente al interior del modal. `Escape` cierra y retorna foco al disparador.

## Code Layout
- `index.html`: Estructura semántica, accesibilidad, modales. Owned by Worker M1 / M2.
- `app.js`: Lógica client-side, mapa, datos, búsqueda, filtros. Owned by Worker M1.
- `style.css`: Estilos, tokens, media queries, temas claro/oscuro/contraste. Owned by Worker M2.
- `.agents/teamwork/`: Metadatos de orquestación, bitácoras, evidencias de auditoría.
