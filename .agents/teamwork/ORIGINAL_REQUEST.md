# Original User Request

## 2026-10-16T22:00:06Z

Auditoría integral de fondo y forma, ingeniería de software, arquitectura client-side, accesibilidad WCAG y experiencia de usuario (UX/UI) del Observatorio de Capacidades Tecnológicas Municipales de Chile, validada mediante una batería de simulación de 100 perfiles de usuarios reales y juzgada mediante la API evaluadora JEV.

Working directory: D:\Proyectos\observatorio-ti-municipal
Integrity mode: development

## Requirements

### R1. Auditoría de Ingeniería, Rendimiento y Resiliencia Client-Side
- Auditar la integridad técnica de index.html, app.js y style.css (cero errores en consola, manejo de excepciones, carga asíncrona de datos pesados, lazy loading de capas geoespaciales y fallbacks ante cortes de red).
- Validar el flujo completo de descarga de datos y persistencia en la API de registro (https://brujulaiaedusuperior.evegat.cl/api/register-download) asegurando validaciones y telemetría no bloqueante.

### R2. Auditoría UX/UI, Arquitectura de Información y Accesibilidad
- Evaluar jerarquía visual, contraste cromático, responsive design (mobile/tablet/desktop), legibilidad editorial y consistencia con el sistema de diseño de evegat.cl.
- Cumplimiento estricto de WCAG 2.1 AA (navegación por teclado, atributos ARIA en modales y tablas, roles semánticos y soporte TTS).

### R3. Panel de Simulación Adversarial de 100 Usuarios Finales
- Simular el recorrido y fricciones de 100 perfiles de usuarios categorizados en 5 estamentos reales:
  1. Funcionarios municipales (DAF/SECPLA/TI con poca conectividad o hardware antiguo).
  2. Concejales y alcaldes (búsqueda rápida de su comuna y contraste comunal A vs B).
  3. Investigadores y analistas de datos (filtrado, orden multidimensional y exportación CSV/JSON).
  4. Periodistas de investigación (detección rápida de concentración ERP y anomalías de gasto per cápita).
  5. Ciudadanos y dirigentes vecinales (comprensión inmediata del lenguaje sin tecnicismos excesivos).
- Registrar una matriz estructurada de hallazgos, bloqueos y oportunidades de fricción cero.

### R4. Veredicto y Evaluación JEV (Juez de Calidad y Estética)
- Someter las interfaces, narrativa y componentes al evaluador JEV (a través de la API/criterios de diseño del ecosistema) para calificar:
  - Sobriedad y rigor editorial.
  - Ausencia de sensacionalismo.
  - Usabilidad táctil y accesibilidad universal.

## Acceptance Criteria

### Integridad y Rendimiento
- [ ] 0 errores de consola al inicializar el mapa, alternar las 7 capas territoriales y abrir fichas de las 346 comunas.
- [ ] El mapa Leaflet carga sin solicitar API keys ni exhibir marcas de agua externas.
- [ ] El modal de registro intercepta las descargas, envía exitosamente el JSON a la API de Brújula IA y descarga el archivo sin trabas.

### Experiencia y Accesibilidad
- [ ] Calificación de contraste y navegación por teclado al 100% en modales, comparador y tablas.
- [ ] Selector de tema claro/oscuro sincronizado instantáneamente con las capas cartográficas de Esri.

### Simulación de Usuarios y Evaluación JEV
- [ ] Matriz de pruebas de 100 usuarios completada con tasa de éxito en tareas clave (encontrar comuna, comparar, registrarse y descargar) superior al 95%.
- [ ] Dictamen JEV aprobado con nota sobresaliente y plan de remediación inmediata de micro-detalles detectados.

## 2026-10-24T15:40:58Z

Plataforma Nacional de Adopción Tecnológica y RRHH en 345 Municipalidades de Chile (346 Comunas). Saneamiento integral de 153.770 órdenes de compra de Mercado Público, extracción de nóminas web observadas de 21 municipios autónomos y desacoplamiento de la arquitectura de datos web en capas livianas bajo demanda.

Working directory: D:/Proyectos/observatorio-ti-municipal  
Integrity mode: development

## Requirements

### R1. Saneamiento Semántico y Erradicación de Falsos Positivos en Compras Públicas
- Auditar y purgar la base de datos de compras públicas eliminando contratos espurios no tecnológicos (ej. arriendo de carpas en Peñalolén por $88M).
- Restringir la canasta a códigos ONU y rubros tecnológicos auditables (Hardware, SaaS, Telecomunicaciones, IA, Ciberseguridad).
- Garantizar que ninguna orden de compra no tecnológica contamine los indicadores comunales.

### R2. Cobertura Temporal y Extensión a 2025–2026
- Poner al día las compras públicas de todas las comunas rezagadas a 2024, integrando las órdenes de compra transadas en 2025 y lo acumulado de 2026.
- En la interfaz web, desacoplar la vista de adquisiciones: presentar un feed cronológico de «Últimas Compras Tecnológicas (2025–2026)» diferenciado de los «Contratos Emblemáticos de Mayor Cuantía (Histórico)».

### R3. Ingesta de Nóminas de Portales Web Autónomos (Cero Estimaciones)
- Completar la ingesta en DuckDB de las 19 comunas restantes con portales propios (Las Condes, Recoleta, Temuco, Calama, Concón, Melipilla, etc.) usando `portal_autonomo_harvester.py`.
- Consolidar la métrica de Dotación Activa (corte mensual septiembre 2026) bajo estándar Ley N° 21.719 con seudonimización HMAC-SHA256.

### R4. Modularización de la Arquitectura de Software Web
- Reemplazar el monolito `comunas_enriched.json` (1.5 MB) por una arquitectura desacoplada en dos niveles:
  1. `data/comunas_summary.json` (~280 KB) para carga inicial instantánea del mapa y rankings.
  2. `data/comunas/{codigo_cut}.json` (~15 KB) cargado bajo demanda al seleccionar una comuna en el mapa.
- Incorporar en el frontend el Glosario Metodológico, Termómetro de Madurez (0–100 pts) y la explicación analítica del efecto escala per cápita (Maipú vs Algarrobo).

### R5. Verificación Adversarial y Auditoría Cruzada con Codex CLI
- Utilizar Codex CLI para auditar de forma independiente la integridad de los datos, consistencia entre capas, ausencia de NaNs y coherencia demográfica.
- Ejecutar suite de pruebas de regresión y preflight del arnés MyWorld antes de cualquier commit o despliegue.

## Acceptance Criteria

### Calidad de Datos
- [ ] 0 contratos de rubros no-TI en las canastas funcionales de las 345 municipalidades.
- [ ] Peñalolén y demás comunas reflejan compras actualizadas con registros de 2025/2026.
- [ ] 100% de las 345 comunas con datos observados de dotación activa, sin ratios teóricos.

### Rendimiento y Arquitectura
- [ ] Payload inicial de datos reducido en al menos 70% (de 1.5 MB a <400 KB).
- [ ] Detalle comunal cargado bajo demanda con latencia menor a 150 ms.
- [ ] Glosario interactivo operativo desde el navbar y desde el modal de bienvenida.

### Calidad de Código y Gates
- [ ] Pasaje exitoso de gates `quality` y `security` del arnés MyWorld.
- [ ] Validación cruzada aprobada mediante auditoría con Codex CLI.


## 2026-10-28T02:14:52Z

Ingesta, saneamiento, auditoría forense y análisis exhaustivo del 100% de los datos de compras públicas tecnológicas (2014–2026) y dotación de personal municipal de Chile, incorporando la nueva capa integral de capacitaciones y desarrollo de habilidades digitales (ciberseguridad, sistemas/ERP, ofimática, IA y alfabetización comunitaria).

Working directory: D:\Proyectos\observatorio-ti-municipal
Supporting directories: D:\Proyectos\P166 - Personal Municipal de Chile, D:\Proyectos\P152 - Compras Municipales de Chile
Integrity mode: development

## Requirements

### R1. Auditoría Forense y Consolidación de Datos Base
- Auditar y consolidar el universo completo de adquisiciones TI municipales (2014–2026) y personal municipal (345 comunas).
- Garantizar datos 100% observados y trazables (fuentes oficiales CPLT y SUBDERE SINIM), con cero estimaciones paramétricas ficticias.

### R2. Construcción e Integración de la Capa de Capacitaciones Tecnológicas Dual
- Aislar, filtrar y clasificar todas las órdenes de compra de capacitación en tecnología de las municipalidades en dos dimensiones:
  1. Capacitación Interna Institucional (Funcionarios): Ciberseguridad y Protección de Datos (Ley N° 21.719), Sistemas de Gestión y ERP Municipal (CAS-CHILE, SIAPER, DocDigital), Ofimática y Productividad (Excel, Microsoft 365, Google Workspace), e Innovación/IA/BI.
  2. Alfabetización y Formación Digital Comunitaria (Ciudadanía): Cursos de computación básica, inclusión digital para personas mayores y talleres tecnológicos vecinales (DIDECO/OTEC).
- Aplicar blacklist estricta para eliminar gastos conexos espurios (catering, coffee breaks, colaciones, arriendo de salones).
- Incorporar en el Parquet flag_capacitacion_ti y subcategoria_capacitacion.
- Enriquecer data/comunas_enriched.json, data/national_kpis.json y data/regiones_enriched.json con:
  - monto_capacitacion_ti y ocs_capacitacion_ti.
  - capacitacion_pc (inversión en formación tecnológica por habitante).
  - Desglose por áreas formativas (interna_funcionarios vs comunitaria_vecinal).

### R3. Verificación Adversarial y Convergencia Matemática 100%
- Ejecutar verificación adversarial cruzada entre la capa transaccional (catastro_ti_saneado.parquet) y todos los artefactos de salida (comunas_enriched.json, national_kpis.json, regiones_enriched.json, proveedores_ranking.json).
- Asegurar convergencia matemática exacta al peso ($0 CLP de discrepancia) en compras totales, categorías y capacitaciones.
- Validar gates quality y security del arnés MyWorld.

## Acceptance Criteria
- [ ] 345 de 345 comunas de Chile integradas con datos de compras y dotación 100% observados y trazables.
- [ ] Capa de capacitaciones tecnológicas integrada con 100% de órdenes de compra clasificadas (interna vs comunitaria).
- [ ] Blacklist estricta aplicada a capacitaciones, garantizando cero pesos de catering o coffee break en la canasta formativa.
- [ ] Cero discrepancias matemáticas entre la suma de comunas, suma de regiones y totales nacionales en compras y capacitaciones.
- [ ] Suite de pruebas adversariales ejecutada con 100% de casos aprobados (0 fallos).
- [ ] Gates quality y security del arnés MyWorld validados en verde.
