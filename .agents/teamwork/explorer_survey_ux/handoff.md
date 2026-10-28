# Informe de Auditoría UX/UI, Arquitectura de Información y Accesibilidad WCAG 2.1 AA
**Proyecto:** Observatorio de Capacidades Tecnológicas y RRHH en Municipios de Chile (2014–2026)  
**Investigador:** Survey Explorer 2 (UX/UI, Information Architecture & Accessibility)  
**Fecha de Emisión:** 2026-10-16T22:18:00Z  
**Ruta del Informe:** `D:\Proyectos\observatorio-ti-municipal\.agents\teamwork\explorer_survey_ux\handoff.md`  

---

## 1. Observation

### 1.1 Inventario de Archivos Inspeccionados y Métricas de Código
- **`index.html`**: 793 líneas, 49.506 bytes. 139 clases CSS declaradas, 75 atributos `id` únicos (cero IDs duplicados).
- **`style.css`**: 1.978 líneas, 40.086 bytes. Define variables temáticas (`:root`, `html[data-theme="dark"]`, `html[data-theme="contrast"]`), 86 declaraciones de `font-size` fijadas en `px` y 0 en `rem`.
- **`app.js`**: 1.922 líneas, 96.984 bytes. Sintaxis validada con `node -c app.js` (0 errores de parsing). Contiene 78 clases estáticas inyectadas por template literals.
- **`data/comunas_enriched.json`**: 346 registros comunales enriquecidos con 53 atributos por municipio.

---

### 1.2 Hallazgo Crítico 1: 48 Clases CSS Huérfanas (Sin Estilo en `style.css`)
Mediante script de auditoría automatizada (`audit_classes.py`) se contrastaron las 139 clases presentes en el marcado de `index.html` contra las reglas de `style.css`. Se constató que **48 clases (34,5% del total)** carecen totalmente de reglas CSS en la hoja de estilos:

```
Clases presentes en index.html pero ausentes en style.css:
- a11y-btn, a11y-container, a11y-controls, a11y-divider, a11y-eco-home, a11y-eco-link,
  a11y-ecosystem, a11y-group, a11y-hide-md, a11y-hide-sm, a11y-label
- btn-academic-action, secondary
- btn-export-csv, ranking-actions, ranking-header-row, filter-select
- btn-footer-cta, btn-footer-download, footer-bio, footer-bottom, footer-brand,
  footer-col, footer-cta-row, footer-grid, footer-heading, footer-legal-trigger,
  footer-links-row, site-footer
- btn-guia-detail, guia-banner, guia-banner-header, guia-banner-title,
  guia-step-card, guia-step-num, guia-steps-grid
- btn-hero-primary, btn-hero-secondary, btn-hero-share, hero-actions-bar,
  hero-share-group, hero-status-pill, hero-top-row, status-dot
- btn-intercept-download, btn-nav-link
- form-checkbox-row
- legal-block
```

#### Impacto Observable Directo:
1. **Barra Superior de Accesibilidad (`.a11y-topbar`, líneas 46–81 de `index.html`)**: Solo existe una regla de fondo en modo oscuro (`style.css:1935`). Carece de estilos base (`display: flex`, alineación, padding, estilo de botones `a11y-btn`, separadores `a11y-divider`). Los botones de TTS, tamaño de fuente y temas se renderizan como botones HTML nativos grises desalineados.
2. **Botones de Acción en Hero (`.hero-actions-bar`, líneas 125–144 de `index.html`)**: Los botones `#btn-hero-como-usar`, enlaces de exploración y botones de compartir en WhatsApp y LinkedIn no tienen estilos visuales.
3. **Banda de Orientación en 4 Pasos (`.guia-banner`, líneas 179–215 de `index.html`)**: Se renderiza sin grilla (`guia-steps-grid`), sin bordes ni padding de tarjetas (`guia-step-card`), quedando los textos colapsados verticalmente sin diseño de tarjetas editoriales.
4. **Pie de Página Institucional de 3 Columnas (`.site-footer`, líneas 504–562 de `index.html`)**: `style.css:1154` define un estilo arcaico para la etiqueta `footer` (`display: flex; justify-content: space-between;`), pero no existen reglas para `.footer-grid`, `.footer-col`, `.footer-brand`, ni los botones de descarga de microdatos.

---

### 1.3 Hallazgo Crítico 2: Auditoría Matemática de Contraste Cromático (WCAG AA)
Se calcularon las luminancias relativas y ratios de contraste matemático conforme a la fórmula estándar WCAG 2.1 AA ($L = 0.2126R + 0.7152G + 0.0722B$):

| Combinación de Elemento | Color Texto | Color Fondo | Ratio Medido | Requisito WCAG AA | Estado |
|---|---|---|---|---|---|
| Texto normal `--muted` sobre `--paper` | `#6b777a` | `#faf8f5` | **4.36:1** | 4.5:1 | **FALLA** |
| Texto normal `--muted` sobre `--paper-soft` | `#6b777a` | `#f4efe6` | **4.03:1** | 4.5:1 | **FALLA** |
| Oro editorial `--gold` sobre `--paper` | `#b38209` | `#faf8f5` | **3.24:1** | 4.5:1 | **FALLA** |
| Oro editorial `--gold` sobre `--gold-bg` | `#b38209` | `#fbf4e4` | **3.13:1** | 4.5:1 | **FALLA** |
| Oro editorial `--gold` sobre `--paper-soft` | `#b38209` | `#f4efe6` | **3.00:1** | 4.5:1 | **FALLA** |
| Anillo de Foco Teclado (`:focus-visible`) | `#38bdf8` | `#faf8f5` | **2.02:1** | 3.0:1 (Non-text) | **FALLA** |
| Anillo de Foco Teclado (`:focus-visible`) | `#38bdf8` | `#ffffff` | **2.14:1** | 3.0:1 (Non-text) | **FALLA** |
| Foco de Inputs de Formulario (halo 15%) | `rgba(179,130,9,0.15)` | `#ffffff` | **1.12:1** | 3.0:1 (Non-text) | **FALLA** |
| Texto de Input Búsqueda en Modo Oscuro | `#f8fafc` (`var(--ink)`) | `#ffffff` (hardcoded) | **1.06:1** | 4.5:1 | **CRÍTICO: INVISIBLE** |
| Texto de Input Región en Modo Oscuro | `#f8fafc` (`var(--ink)`) | `#ffffff` (hardcoded) | **1.06:1** | 4.5:1 | **CRÍTICO: INVISIBLE** |
| Cabecera Tabla `<th>` en Modo Oscuro | `#38bdf8` (`var(--navy)`) | `#f7f4ee` (hardcoded) | **1.95:1** | 4.5:1 | **CRÍTICO: ILEGIBLE** |
| Fila de Tabla Hover en Modo Oscuro | `#cbd5e1` (`var(--ink-secondary)`) | `#faf8f3` (hardcoded) | **1.40:1** | 4.5:1 | **CRÍTICO: ILEGIBLE** |
| Número Central Termómetro SVG Modo Oscuro | `#14171a` (hardcoded) | `#0a2652` (`--paper-card`) | **1.21:1** | 4.5:1 / 3.0:1 | **CRÍTICO: INVISIBLE** |
| Número Central SVG Modo Alto Contraste | `#14171a` (hardcoded) | `#000000` (`--paper`) | **1.17:1** | 4.5:1 / 3.0:1 | **CRÍTICO: INVISIBLE** |
| Leyenda del Mapa en Modo Oscuro | `#f8fafc` (`var(--ink)`) | `rgba(255,255,255,0.95)` | **1.06:1** | 4.5:1 | **CRÍTICO: INVISIBLE** |
| Cabecera `<th>` en Modo Alto Contraste | `#ffff00` (`var(--navy)`) | `#f7f4ee` (hardcoded) | **1.02:1** | 4.5:1 | **CRÍTICO: INVISIBLE** |

---

### 1.4 Hallazgo Crítico 3: Alternancia de Temas y Capas Cartográficas Esri/Leaflet
1. **Parpadeo Blanco (Flicker) al cambiar a Modo Oscuro**:
   - `style.css:503`: `#chile-map` tiene hardcoded `background: #f4efe6;` (marfil claro).
   - En `app.js:379-388`, `updateMapTheme(theme)` remueve síncronamente `state.esriLightGroup` e inserta `state.esriDarkGroup`. Durante el lapso de descarga asíncrona de los tiles de ArcGIS Server, el contenedor expone el fondo `#f4efe6`, generando un destello blanco abrupto en medio de una interfaz oscura.
2. **Modo Alto Contraste (`data-theme="contrast"`) desincronizado con el mapa**:
   - `app.js:381`: La condición solo evalúa `if (theme === "dark")`. Ante `theme === "contrast"`, el `else` inyecta la capa cartográfica **clara** de Esri (`World_Light_Gray_Base`), mientras la página entera se tiñe de negro azabache (`#000000`), generando una disonancia cromática extrema.
3. **Popups de Leaflet sin Adaptación de Tema**:
   - `leaflet.css` fija `.leaflet-popup-content-wrapper` en fondo blanco `#fff`. En modo oscuro, los textos inyectados en `app.js:457-465` usan `color: var(--navy)` (`#38bdf8`, contraste 2.14:1 contra blanco) y `color: var(--ink)` (`#f8fafc`, blanco sobre blanco, contraste 1.06:1).

---

### 1.5 Hallazgo Crítico 4: Capas Cartográficas Faltantes en `app.js` (`ret` y `rrhh`)
- En `index.html:254-255`, existen los botones:
  - `<button class="layer-btn" data-layer="ret">🏛️ Capacidad Estatal (RET)</button>`
  - `<button class="layer-btn" data-layer="rrhh">👥 RRHH & Honorarios</button>`
- En `app.js:390-435` (`getMarkerStyle(comuna)`):
  - Existen bloques para `madurez`, `gasto_pc`, `lockin`, `foss`, e `infra`.
  - **No existe ningún bloque para `ret` ni `rrhh`**.
  - Al pulsar cualquiera de estas dos dimensiones, la función retorna el valor por defecto inmutable (`color = "#146e66"`, `radius = 6`), renderizando las 346 comunas con idéntico círculo verde azulado sin diferenciación territorial.
- En `app.js:479-528` (`updateLegend()`):
  - **No existe bloque para `ret` ni `rrhh`**. La leyenda no se actualiza y preserva el texto de la capa anterior.

---

### 1.6 Hallazgo Crítico 5: Cumplimiento WCAG 2.1 AA y Navegación por Teclado
1. **Ausencia de Enlace de Salto (`skip-link`)**:
   - `index.html` no incluye un enlace `<a href="#main-content" class="skip-link">Saltar al contenido principal</a>`.
   - Un usuario de teclado o lector de pantalla debe ejecutar **18 tabulaciones obligatorias** (ecosistema, TTS, escala tipográfica, temas, enlaces del topbar) antes de acceder al contenido principal del Hero.
2. **Modales sin Trampa de Foco (`Focus Trap`) ni Retorno de Foco**:
   - En `app.js:1485-1500` (`openModal`, `closeModal`):
     - `openModal` añade `.active` y cambia `aria-hidden="false"`, pero **no transfiere el foco (`element.focus()`) al modal** ni al botón de cierre.
     - No existe trampa de tabulación: el usuario puede seguir tabulando libremente por los elementos de la página subyacente detrás del backdrop.
     - `closeModal` remueve `.active` y cambia `aria-hidden="true"`, pero **no devuelve el foco al botón disparador**, provocando la pérdida de posición del usuario (el foco se reinicia en el `<body>`).
3. **Inaccesibilidad de Cabeceras y Filas de Tablas por Teclado**:
   - `index.html:403-416`: Las cabeceras `<th>` tienen atributo `data-sort`, pero en `app.js:1138-1150` solo se les asocia un listener de evento `click`. No poseen `tabindex="0"`, ni rol semántico interactivo, ni escuchan `keydown` (`Enter` o `Space`). Un usuario que no usa ratón **no puede ordenar la tabla**.
   - `index.html:418`: Las filas `<tr>` del cuerpo de la tabla son clickeables con el ratón (`app.js:1215-1224`), pero carecen de `tabindex="0"`, rol `button` y control por teclado para seleccionar la comuna.
   - Las cabeceras no comunican el estado de ordenación mediante `aria-sort="ascending"` o `aria-sort="descending"`.
4. **Marcadores del Mapa Leaflet no Accesibles por Teclado**:
   - `app.js:447`: Los marcadores se crean con `L.circleMarker()`, que genera nodos vectoriales SVG `<path>` en el panel de Leaflet sin `tabindex="0"`, sin roles de botón accesible y sin listeners de teclado. Un usuario con discapacidad motriz no puede inspeccionar comunas directamente sobre el mapa sin recurrir a la tabla.
5. **Formulario de Descarga sin Gestión Accesible de Errores**:
   - `index.html:710-778`: Los campos obligatorios tienen `required`, pero carecen de `aria-required="true"`.
   - Ante error de validación en `app.js:1573`, solo se ejecuta `errorMsg.style.display = "block"`. No se asigna `aria-invalid="true"` a los inputs deficientes, el mensaje `#reg-error-msg` carece de `role="alert"` o `aria-live="assertive"`, y el foco no es redirigido al primer campo con error.
6. **Efecto Placebo en Escalado de Tipografía (`A-`, `A`, `A+`)**:
   - `app.js:1422-1426` altera `document.documentElement.style.fontSize`.
   - Sin embargo, en `style.css` hay **86 reglas con `font-size` hardcodeado en `px`** (y 0 en `rem`). Como consecuencia, el 90% de los textos (títulos, tarjetas de métricas, celdas de tabla, fichas comunales) mantienen su tamaño inmutable, haciendo que los botones de accesibilidad sean inoperantes sobre el grueso de la interfaz.

---

## 2. Logic Chain

1. **De la Observación 1.2 a la Conclusión de Desbalance Visual y Falta de Estilos**:
   - Dado que 48 clases presentes en `index.html` no tienen ninguna correspondencia en `style.css`,
   - y dado que estas clases abarcan componentes visuales principales (la barra de accesibilidad, los botones del hero, la guía de orientación rápida, el formulario modal y el footer institucional),
   - se infiere que la interfaz actual en producción exhibe fallas estéticas severas: elementos sin márgenes, botones nativos de navegador desalineados, texto colapsado y ausencia de la jerarquía visual característica del sistema de diseño `evegat.cl`.

2. **De la Observación 1.3 a la Conclusión de Violación de Criterios WCAG 2.1 AA**:
   - El estándar WCAG 2.1 AA exige un contraste mínimo de **4.5:1** para texto normal y de **3.0:1** para elementos de interfaz y estados de foco (Criterios 1.4.3 y 1.4.11).
   - El color corporativo secundario `--muted: #6b777a` genera un ratio de **4.36:1** sobre `#faf8f5` y **4.03:1** sobre `#f4efe6`, incumpliendo la norma.
   - El color de acento `--gold: #b38209` genera un ratio de **3.24:1** cuando se usa como texto sobre marfil, incumpliendo el umbral para texto normal.
   - El anillo de foco general `#38bdf8` sobre el fondo claro de la página obtiene un ratio de **2.02:1**, violando el criterio de contraste de indicadores visuales de foco (mínimo 3.0:1).
   - En modos oscuro y de alto contraste, los inputs (`#fff`) y las cabeceras/filas de tabla (`#f7f4ee`, `#faf8f3`) retienen fondos claros con textos claros, produciendo ratios entre **1.02:1 y 1.95:1**, lo que torna la plataforma completamente ilegible e inutilizable en dichos modos.

3. **De la Observación 1.4 a la Conclusión de Inestabilidad en la Cartografía**:
   - Leaflet requiere sincronizar el cambio de capas base respetando la asincronía de la red.
   - Al remover la capa clara antes de que la capa oscura esté renderizada, sumado a que `#chile-map` posee un color de fondo claro rígido (`#f4efe6`), se induce un destello blanco ("flash") que rompe la continuidad visual y fatiga a usuarios fotosensibles.
   - En el modo de alto contraste (`contrast`), al cargarse la cartografía clara de Esri sobre un fondo de página completamente negro, se desvirtúa el propósito del modo accesible.

4. **De la Observación 1.5 a la Conclusión de Inconsistencia Funcional en Capas**:
   - La interfaz propone al usuario 7 dimensiones territoriales; sin embargo, el motor de estilos cartográficos solo implementa 5.
   - Al seleccionar `ret` o `rrhh`, el usuario experimenta una respuesta nula: los marcadores no reflejan los datos de la comuna y la leyenda permanece estática o errónea, degradando la usabilidad exploratoria.

5. **De la Observación 1.6 a la Conclusión de Exclusión de Usuarios con Tecnologías de Asistencia**:
   - Sin `skip-link`, sin foco gestionado en modales y sin navegación por teclado en cabeceras de tablas ni marcadores, un usuario dependiente exclusivamente de teclado o lector de pantalla queda atrapado o desorientado en la navegación.
   - La falta de unidades relativas `rem` anula el beneficio de los controles de incremento de tipografía (`A+`), impidiendo la adecuación visual para usuarios con baja visión.

---

## 3. Caveats

1. **Alcance de Solo Lectura**: Como agente de investigación, no se aplicaron modificaciones sobre los archivos fuentes del proyecto (`index.html`, `style.css`, `app.js`). Todos los análisis se fundamentan en pruebas estáticas, cómputos cromáticos y ejecución de scripts locales de diagnóstico.
2. **Dependencia de Red para Tiles de Esri**: El comportamiento del parpadeo de capas cartográficas depende de la latencia hacia `server.arcgisonline.com`. En conexiones de alta velocidad el destello dura fracciones de segundo, pero en conexiones móviles o de baja calidad puede prolongarse por más de 1,5 segundos.
3. **Soporte de `speechSynthesis` en Navegadores**: El comportamiento del sintetizador TTS varía según el motor de voz nativo instalado en el sistema operativo del usuario final (e.g. voz de Google en Chrome vs. voz de Microsoft en Edge).

---

## 4. Conclusion

El Observatorio de Capacidades Tecnológicas Municipales posee una arquitectura de información sólida y una propuesta editorial de alto valor académico. No obstante, **presenta 5 categorías de fallas críticas** que comprometen severamente la experiencia de usuario y vulneran los estándares internacionales de accesibilidad WCAG 2.1 AA:

1. **34,5% de clases CSS sin implementar**: Barra superior de accesibilidad, botones del hero, banner de 4 pasos y pie institucional se encuentran desprovistos de estilos.
2. **Deficiencias de Contraste Severas**: Infracción de WCAG AA en texto secundario (`#6b777a`), dorado textual (`#b38209`), indicador de foco teclado (`#38bdf8`), y colapso total (texto blanco sobre fondo blanco) en inputs, tablas y números del termómetro SVG durante el modo oscuro y alto contraste.
3. **Ruptura de Sincronización Cartográfica**: Parpadeo blanco al pasar a modo oscuro e inyección de cartografía errónea (clara) en modo alto contraste.
4. **Incompletitud Funcional en Mapas**: Capas `ret` (Capacidad Estatal) y `rrhh` (Dotación & Honorarios) no cuentan con implementación en `getMarkerStyle` ni en `updateLegend`.
5. **Barreras de Navegación Universal**: Ausencia de skip-link, modales sin `focus trap` ni restauración de foco, tablas y marcadores no operables por teclado, y escalado tipográfico inoperante por empleo de `px` rígidos.

### Propuestas Concretas de Remediación

#### Propuesta A: Bloque de Estilos Faltantes para `style.css`
Añadir a `style.css` las reglas canónicas para las 48 clases huérfanas:

```css
/* ==========================================================================
   BARRA SUPERIOR DE ACCESIBILIDAD Y ECOSISTEMA (BASE)
   ========================================================================== */
.a11y-topbar {
  background: var(--paper-soft);
  border-bottom: 1px solid var(--line);
  font-size: 11px;
  padding: 6px 5%;
}

.a11y-container {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.a11y-ecosystem {
  display: flex;
  align-items: center;
  gap: 10px;
}

.a11y-eco-home, .a11y-eco-link {
  color: var(--ink-secondary);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.15s;
}

.a11y-eco-home:hover, .a11y-eco-link:hover {
  color: var(--navy);
  text-decoration: underline;
}

.a11y-divider {
  color: var(--line);
}

.a11y-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.a11y-label {
  color: var(--muted);
  font-weight: 600;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.a11y-btn {
  background: var(--paper-card);
  border: 1px solid var(--line);
  color: var(--ink);
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: all 0.15s;
}

.a11y-btn:hover {
  background: var(--paper);
  border-color: var(--navy);
}

.a11y-group {
  display: inline-flex;
  gap: 2px;
}

@media (max-width: 640px) {
  .a11y-hide-sm { display: none !important; }
}

@media (max-width: 860px) {
  .a11y-hide-md { display: none !important; }
}

/* ==========================================================================
   ENLACE DE SALTO (SKIP-LINK WCAG 2.1 AA)
   ========================================================================== */
.skip-link {
  position: absolute;
  top: -100px;
  left: 20px;
  background: var(--navy);
  color: #fff !important;
  padding: 10px 16px;
  border-radius: 4px;
  font-weight: 700;
  font-size: 13px;
  z-index: 10002;
  text-decoration: none;
  transition: top 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 4px 14px rgba(0,0,0,0.25);
}

.skip-link:focus {
  top: 15px;
  outline: 3px solid var(--gold) !important;
}

/* ==========================================================================
   HERO ACTIONS & STATUS PILL
   ========================================================================== */
.hero-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 12px;
}

.hero-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--paper-card);
  border: 1px solid var(--line);
  border-radius: 20px;
  padding: 4px 12px;
  font-size: 11px;
  font-weight: 600;
  color: var(--ink-secondary);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--teal);
  box-shadow: 0 0 0 2px var(--teal-bg);
}

.hero-actions-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin: 28px 0 36px;
}

.btn-hero-primary {
  background: var(--gold);
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 11px 20px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.15s;
  box-shadow: 0 2px 8px rgba(179, 130, 9, 0.25);
}

.btn-hero-primary:hover {
  background: #875f00;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(179, 130, 9, 0.35);
}

.btn-hero-secondary {
  background: var(--paper-card);
  color: var(--navy);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 10px 18px;
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.15s;
}

.btn-hero-secondary:hover {
  background: var(--paper-soft);
  border-color: var(--navy);
}

.hero-share-group {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.btn-hero-share {
  background: var(--paper-soft);
  border: 1px solid var(--line);
  color: var(--ink-secondary);
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  transition: all 0.15s;
}

.btn-hero-share:hover {
  background: #fff;
  color: var(--navy);
  border-color: var(--muted);
}

/* ==========================================================================
   GUÍA RÁPIDA 4 PASOS
   ========================================================================== */
.guia-banner {
  background: var(--paper-card);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 28px;
  margin-top: 36px;
  box-shadow: 0 4px 14px rgba(0, 43, 73, 0.03);
}

.guia-banner-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 22px;
  gap: 16px;
}

.guia-banner-title {
  font-family: var(--font-serif);
  font-size: 24px;
  color: var(--navy);
  font-weight: 600;
  margin-top: 4px;
}

.btn-guia-detail {
  background: var(--paper-soft);
  border: 1px solid var(--line);
  color: var(--navy);
  border-radius: 6px;
  padding: 8px 14px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s;
}

.btn-guia-detail:hover {
  background: var(--navy);
  color: #fff;
  border-color: var(--navy);
}

.guia-steps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}

.guia-step-card {
  background: var(--paper);
  border: 1px solid var(--line-light);
  border-radius: 8px;
  padding: 18px;
  text-decoration: none;
  display: flex;
  flex-direction: column;
  transition: all 0.2s;
}

.guia-step-card:hover {
  transform: translateY(-2px);
  border-color: var(--gold-border);
  box-shadow: 0 4px 12px rgba(179, 130, 9, 0.08);
}

.guia-step-num {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 700;
  color: var(--gold);
  letter-spacing: 0.08em;
  margin-bottom: 6px;
}

.guia-step-card h3 {
  font-family: var(--font-sans);
  font-size: 14px;
  font-weight: 700;
  color: var(--navy);
  margin-bottom: 8px;
}

.guia-step-card p {
  font-size: 12px;
  color: var(--ink-secondary);
  line-height: 1.5;
  margin: 0;
}

/* ==========================================================================
   PIE INSTITUCIONAL 3 COLUMNAS (LOOK & FEEL EVEGAT.CL)
   ========================================================================== */
.site-footer {
  background: var(--paper);
  border-top: 1px solid var(--line);
  padding: 50px 5% 30px;
}

.footer-grid {
  max-width: 1400px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1.4fr 1.2fr 1.2fr;
  gap: 40px;
  margin-bottom: 40px;
}

@media (max-width: 900px) {
  .footer-grid {
    grid-template-columns: 1fr;
    gap: 30px;
  }
}

.footer-col {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.footer-brand strong {
  display: block;
  font-size: 14px;
  color: var(--navy);
}

.footer-brand span {
  font-size: 11px;
  color: var(--muted);
}

.footer-heading {
  font-family: var(--font-serif);
  font-size: 16px;
  color: var(--navy);
  font-weight: 600;
  line-height: 1.3;
}

.footer-bio {
  font-size: 12px;
  color: var(--ink-secondary);
  line-height: 1.6;
}

.footer-links-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 4px;
}

.footer-links-row a {
  font-size: 12px;
  color: var(--navy);
  text-decoration: none;
  font-weight: 600;
}

.footer-links-row a:hover {
  text-decoration: underline;
}

.footer-cta-row {
  margin-top: 6px;
}

.btn-footer-cta {
  background: var(--navy);
  color: #fff;
  border-radius: 6px;
  padding: 9px 16px;
  font-size: 12px;
  font-weight: 600;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: background 0.15s;
}

.btn-footer-cta:hover {
  background: var(--navy-soft);
}

.btn-footer-download {
  background: var(--paper-soft);
  border: 1px solid var(--line);
  color: var(--navy);
  border-radius: 4px;
  padding: 6px 10px;
  font-size: 11px;
  font-family: var(--font-mono);
  font-weight: 600;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s;
  display: block;
  width: 100%;
}

.btn-footer-download:hover {
  background: var(--navy);
  color: #fff;
  border-color: var(--navy);
}

.footer-downloads {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.footer-legal-trigger {
  background: transparent;
  border: none;
  color: var(--muted);
  font-size: 11px;
  cursor: pointer;
  text-decoration: underline;
  padding: 0;
}

.footer-legal-trigger:hover {
  color: var(--navy);
}

.footer-bottom {
  max-width: 1400px;
  margin: 0 auto;
  border-top: 1px solid var(--line-light);
  padding-top: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 11px;
  color: var(--muted);
}
```

#### Propuesta B: Corrección de Contraste y Adaptabilidad Temática
1. **Ajuste de Paleta Base en `:root`**:
   - Cambiar `--muted` de `#6b777a` a **`#556265`** (ratio 5.96:1 sobre `#faf8f5`, pasa WCAG AA).
   - Introducir `--gold-text: #875f00;` para textos dorados (ratio 5.40:1 sobre `#faf8f5`, pasa WCAG AA).
2. **Corrección de Inputs, Tablas y SVG en Modo Oscuro (`html[data-theme="dark"]`)**:
   ```css
   html[data-theme="dark"] .search-input,
   html[data-theme="dark"] .region-select,
   html[data-theme="dark"] .compare-select {
     background: #071f43;
     color: #f8fafc;
     border-color: #1f5091;
   }

   html[data-theme="dark"] .map-legend-overlay {
     background: rgba(7, 31, 67, 0.95);
     border-color: #1f5091;
     color: #f8fafc;
   }

   html[data-theme="dark"] .data-table th {
     background: #071f43;
     color: #38bdf8;
     border-bottom-color: #153b70;
   }

   html[data-theme="dark"] .data-table tr:hover td {
     background: #0d3166;
     color: #f8fafc;
   }

   html[data-theme="dark"] #chile-map {
     background: #04142b;
   }

   /* Leaflet popups en modo oscuro */
   html[data-theme="dark"] .leaflet-popup-content-wrapper,
   html[data-theme="dark"] .leaflet-popup-tip {
     background: #071f43;
     color: #f8fafc;
     border: 1px solid #1f5091;
   }
   ```
3. **Indicador de Foco Accesible**:
   ```css
   :root {
     --focus-outline-color: #002b49;
   }
   html[data-theme="dark"] {
     --focus-outline-color: #38bdf8;
   }
   html[data-theme="contrast"] {
     --focus-outline-color: #ffff00;
   }

   a:focus-visible, button:focus-visible, input:focus-visible, select:focus-visible {
     outline: 3px solid var(--focus-outline-color) !important;
     outline-offset: 2px !important;
   }
   ```
4. **SVG Gauge Dinámico (`renderGaugeSvg` en `app.js`)**:
   - Reemplazar `fill="#14171a"` por `fill="currentColor"` o `fill="var(--ink)"` para que el dígito central se pinte blanco en modo oscuro y amarillo en modo alto contraste.

#### Propuesta C: Implementación de Capas Faltantes en `app.js` (`ret` y `rrhh`)
1. **Extender `getMarkerStyle`**:
   ```javascript
   } else if (state.currentLayer === "ret") {
     const ret = comuna.ret_ratio || 0;
     if (ret <= 1.0) color = "#2d6a4f";      // Soberano alto
     else if (ret <= 1.8) color = "#146e66"; // Equilibrado
     else if (ret <= 3.0) color = "#b38209"; // Dependiente moderado
     else color = "#9b2226";                 // Cautivo severo
     radius = Math.max(5, Math.min(14, Math.sqrt(ret) * 4.5));
   } else if (state.currentLayer === "rrhh") {
     const pctHon = comuna.pct_honorarios || 0;
     if (pctHon > 55) color = "#9b2226";     // Precarización crítica
     else if (pctHon > 40) color = "#b38209"; // Alerta media
     else color = "#146e66";                 // Dotación formalizada
     radius = Math.max(5, Math.min(14, (pctHon / 100) * 15));
   }
   ```
2. **Extender `updateLegend`**:
   ```javascript
   } else if (state.currentLayer === "ret") {
     legendEl.innerHTML = `
       <div class="map-legend-title">Ratio de Externalización TI (RET)</div>
       <div class="map-legend-items">
         <div class="map-legend-item"><span class="legend-color-box" style="background:#2d6a4f;"></span><span>Soberanía Fuerte (RET &le; 1,0x)</span></div>
         <div class="map-legend-item"><span class="legend-color-box" style="background:#146e66;"></span><span>Equilibrado (1,0x - 1,8x)</span></div>
         <div class="map-legend-item"><span class="legend-color-box" style="background:#b38209;"></span><span>Dependencia Media (1,8x - 3,0x)</span></div>
         <div class="map-legend-item"><span class="legend-color-box" style="background:#9b2226;"></span><span>Estado Cautivo (&gt; 3,0x)</span></div>
       </div>
     `;
   } else if (state.currentLayer === "rrhh") {
     legendEl.innerHTML = `
       <div class="map-legend-title">Precarización Laboral (% Honorarios)</div>
       <div class="map-legend-items">
         <div class="map-legend-item"><span class="legend-color-box" style="background:#9b2226;"></span><span>Crítica (&gt; 55% de personal a honorarios)</span></div>
         <div class="map-legend-item"><span class="legend-color-box" style="background:#b38209;"></span><span>Alerta Media (40% - 55%)</span></div>
         <div class="map-legend-item"><span class="legend-color-box" style="background:#146e66;"></span><span>Planta / Contrata Dominante (&lt; 40%)</span></div>
       </div>
     `;
   }
   ```

#### Propuesta D: Remediación de Accesibilidad Teclado y Modales
1. **Gestión de Foco en Modales**:
   - Guardar el elemento previamente enfocado (`lastFocusedElement = document.activeElement;`).
   - Al abrir el modal, ejecutar `focus()` sobre el botón de cierre o primer input.
   - Interceptar evento `keydown` (Tab / Shift+Tab) para atrapar el ciclo de tabulación exclusivamente dentro del contenedor `.obs-modal-card`.
   - Al cerrar, ejecutar `lastFocusedElement.focus();`.
2. **Navegación por Teclado en Tablas**:
   - Asignar `tabindex="0"`, `role="button"`, y listener de `keydown` (`Enter`/`Space`) a las cabeceras `<th>` y actualizar dinámicamente `aria-sort`.
   - Asignar `tabindex="0"` a cada fila `<tr>` del ranking para permitir selección de comuna con tecla `Enter`.

---

## 5. Verification Method

Para verificar independientemente cada uno de los hallazgos y validar futuras remediaciones:

1. **Auditoría de Clases CSS Ausentes**:
   ```powershell
   python "D:\Proyectos\observatorio-ti-municipal\.agents\teamwork\explorer_survey_ux\audit_classes.py"
   ```
   *Criterio de validación:* El número de clases faltantes debe reducirse de 48 a 0.

2. **Verificación Sintáctica y Linter de JavaScript**:
   ```powershell
   node -c "D:\Proyectos\observatorio-ti-municipal\app.js"
   ```
   *Criterio de validación:* Debe retornar exit code 0 sin advertencias ni errores.

3. **Cálculo de Ratios de Contraste WCAG**:
   ```powershell
   python -c "
   def lum(r, g, b):
       c = [x / 255.0 for x in (r, g, b)]
       c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
       return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
   def ratio(h1, h2):
       c1 = tuple(int(h1.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
       c2 = tuple(int(h2.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
       l1, l2 = lum(*c1), lum(*c2)
       return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)
   print('Muted ajustado (#556265 sobre #faf8f5):', ratio('#556265', '#faf8f5'))
   print('Gold ajustado (#875f00 sobre #faf8f5):', ratio('#875f00', '#faf8f5'))
   "
   ```
   *Criterio de validación:* Todo ratio para texto normal debe ser $\ge 4.5:1$ y para indicadores de foco $\ge 3.0:1$.

4. **Verificación de Capas Cartográficas**:
   Inspeccionar que `getMarkerStyle` y `updateLegend` en `app.js` contengan las ramas para `"ret"` y `"rrhh"`.
   *Criterio de invalidación:* Al hacer click en los botones `🏛️ Capacidad Estatal (RET)` y `👥 RRHH & Honorarios`, los colores de los círculos deben diversificarse territorialmente y la leyenda debe mostrar los tramos de RET y porcentaje de honorarios correspondientes.

5. **Verificación Visual de Temas**:
   Alternar en la barra superior entre `Claro`, `Oscuro` y `Accesible`.
   *Criterio de validación:*
   - En Modo Oscuro, el input de búsqueda comunal debe mostrar fondo azul marino oscuro (`#071f43`) con texto claro legible, las cabeceras de tabla deben mantener contraste $> 4.5:1$, el valor central del termómetro SVG debe ser claramente visible, y el mapa no debe emitir destello blanco.
   - En Modo Alto Contraste, el mapa debe permanecer en tonalidad oscura/negra armonizada con el fondo.

6. **Inspección de Foco por Teclado**:
   Navegar la página usando exclusivamente `Tab`, `Shift+Tab`, `Enter`, `Space` y `Escape`.
   *Criterio de validación:*
   - El enlace de salto debe aparecer en la esquina superior izquierda al primer `Tab`.
   - Al abrir un modal, el foco debe quedar restringido a su interior. Al presionar `Escape`, el modal debe cerrarse y el foco debe regresar exactamente al botón que lo abrió.
   - Las cabeceras de la tabla deben recibir foco y ordenar la columna al pulsar `Enter`.
