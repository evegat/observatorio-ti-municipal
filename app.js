/**
 * app.js
 * ======
 * Controlador interactivo para la Radiografía 4D de Compras TI Municipal en Chile (2014-2026).
 * Diseñado bajo el sistema visual evegat.cl.
 * Autor: Eduardo Vega Toledo
 */

document.addEventListener("DOMContentLoaded", () => {
  // Estado global de la aplicación
  const state = {
    comunas: [],
    regiones: [],
    kpis: {},
    proveedores: [],
    provSearchQuery: "",
    pendingDownload: null,
    currentLayer: "madurez",
    selectedComuna: null,
    compareComuna: null,
    isCompareMode: false,
    searchQuery: "",
    selectedRegion: "",
    selectedCuadrante: "",
    currentChapter: 1,
    sortField: "monto_total",
    sortAsc: false,
    map: null,
    markersLayer: null
  };

  // -------------------------------------------------------------------------
  // 1. CARGA DE DATOS ASÍNCRONA Y ENRUTAMIENTO HASH
  // -------------------------------------------------------------------------
  function handleHashRoute() {
    const hash = window.location.hash;
    if (hash && hash.startsWith("#comparar=")) {
      const parts = hash.replace("#comparar=", "").split(",");
      if (parts.length >= 2) {
        const nameA = decodeURIComponent(parts[0]).trim().toLowerCase();
        const nameB = decodeURIComponent(parts[1]).trim().toLowerCase();
        const cA = state.comunas.find(c => c.comuna.toLowerCase() === nameA);
        const cB = state.comunas.find(c => c.comuna.toLowerCase() === nameB);
        if (cA && cB) {
          openComparison(cA, cB);
          const radEl = document.getElementById("radiografia");
          if (radEl && window.scrollY < 200) {
            radEl.scrollIntoView({ behavior: "smooth" });
          }
          return true;
        }
      }
    } else if (hash && hash.startsWith("#comuna=")) {
      const rawName = decodeURIComponent(hash.replace("#comuna=", "")).trim().toLowerCase();
      const target = state.comunas.find(c => c.comuna.toLowerCase() === rawName);
      if (target) {
        state.isCompareMode = false;
        selectComuna(target);
        const radEl = document.getElementById("radiografia");
        if (radEl && window.scrollY < 200) {
          radEl.scrollIntoView({ behavior: "smooth" });
        }
        return true;
      }
    }
    return false;
  }

  async function init() {
    try {
      const [comunasRes, regionesRes, kpisRes, provRes] = await Promise.all([
        fetch("data/comunas_enriched.json"),
        fetch("data/regiones_enriched.json"),
        fetch("data/national_kpis.json"),
        fetch("data/proveedores_ranking.json").catch(() => null)
      ]);

      state.comunas = await comunasRes.json();
      state.regiones = await regionesRes.json();
      state.kpis = await kpisRes.json();
      state.proveedores = provRes ? await provRes.json() : [];

      initScrollytelling();
      initRegionDropdown();
      initMap();
      initControls();
      initThemeAndA11y();
      initModals();
      initRRHHModule();
      renderTable();
      renderProveedoresTable();
      renderCuadrantesSummary();

      // Enrutamiento directo por hash o comuna inicial por defecto
      const routed = handleHashRoute();
      if (!routed && state.comunas.length > 0) {
        selectComuna(state.comunas[0]);
      }

      window.addEventListener("hashchange", () => {
        handleHashRoute();
      });
    } catch (err) {
      console.error("Error al inicializar la aplicación:", err);
    }
  }

  // -------------------------------------------------------------------------
  // 2. SCROLLYTELLING / HISTORIA EN 4 ACTOS
  // -------------------------------------------------------------------------
  const storyChapters = {
    1: {
      title: "1. El Fierro vs. El Espejismo de la Inteligencia Artificial",
      text: "A pesar de la retórica sobre 'ciudades inteligentes', modernización algorítmica y chatbots, la evidencia demuestra que casi la mitad del presupuesto municipal de TI (47,88%, equivalente a $143.698 millones de pesos) se destina exclusivamente a la adquisición y reposición de infraestructura física: computadores de escritorio, impresoras, servidores y cableado. La categoría de IA y automatización (26,48%) se encuentra concentrada casi en su totalidad en sistemas de marcación biométrica de personal y atención municipal automatizada por WhatsApp, sin despliegues analíticos predictivos estructurales.",
      findings: [
        "47,88% del gasto total se absorbe en infraestructura física de cómputo básico.",
        "La categoría de IA suma $79.476 millones, pero atomizada en biometría y trámites.",
        "Telecomunicaciones y enlaces dedicados representan el 10,47% ($31.422 MM).",
        "SaaS y Cloud Computing sólo alcanza un 4,57% ($13.704 MM) a nivel nacional."
      ],
      chartHtml: `
        <div style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--muted); margin-bottom:12px;">Composición de la Canasta TI Municipal (12 Años)</div>
        <div style="display:flex; flex-direction:column; gap:8px;">
          <div>
            <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:3px;">
              <span>Infraestructura y Hardware</span><strong>47,9% ($143.7B)</strong>
            </div>
            <div style="height:8px; background:var(--line-light); border-radius:4px; overflow:hidden;">
              <div style="width:47.9%; height:100%; background:var(--navy);"></div>
            </div>
          </div>
          <div>
            <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:3px;">
              <span>IA y Automatización Básica</span><strong>26,5% ($79.5B)</strong>
            </div>
            <div style="height:8px; background:var(--line-light); border-radius:4px; overflow:hidden;">
              <div style="width:26.5%; height:100%; background:var(--teal);"></div>
            </div>
          </div>
          <div>
            <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:3px;">
              <span>Redes y Telecomunicaciones</span><strong>10,5% ($31.4B)</strong>
            </div>
            <div style="height:8px; background:var(--line-light); border-radius:4px; overflow:hidden;">
              <div style="width:10.5%; height:100%; background:var(--gold);"></div>
            </div>
          </div>
          <div>
            <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:3px;">
              <span>Ciberseguridad y Backup</span><strong>6,9% ($20.6B)</strong>
            </div>
            <div style="height:8px; background:var(--line-light); border-radius:4px; overflow:hidden;">
              <div style="width:6.9%; height:100%; background:#70587c;"></div>
            </div>
          </div>
          <div>
            <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:3px;">
              <span>SaaS y Cloud Computing</span><strong>4,6% ($13.7B)</strong>
            </div>
            <div style="height:8px; background:var(--line-light); border-radius:4px; overflow:hidden;">
              <div style="width:4.6%; height:100%; background:#385bb2;"></div>
            </div>
          </div>
          <div>
            <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:3px;">
              <span>Software Libre (FOSS)</span><strong>0,17% ($514M)</strong>
            </div>
            <div style="height:8px; background:var(--line-light); border-radius:4px; overflow:hidden;">
              <div style="width:1.5%; height:100%; background:var(--crimson);"></div>
            </div>
          </div>
        </div>
      `
    },
    2: {
      title: "2. El Choque Estructural de 2021: Pandemia y Ley 21.180",
      text: "La serie histórica de contrataciones TI revela un punto de quiebre indiscutible. Entre 2015 y 2019, la inversión municipal anual en tecnologías se mantenía plana en un promedio de $11.000 millones de pesos. En 2021, impulsado por la necesidad operativa del teletrabajo durante el confinamiento y la entrada en vigencia de la Ley 21.180 de Transformación Digital del Estado, el gasto se triplicó súbitamente a $37.530 millones de pesos, marcando un nuevo umbral estructural que trepó hasta los $48.010 millones en 2025.",
      findings: [
        "Inflexión histórica 2021: Salto de $11.980 MM (2019) a $37.530 MM (2021).",
        "El gasto anual no retrocedió tras la pandemia: se duplicó como piso permanente.",
        "SaaS y Cloud creció un 139% entre 2015 y 2025 (migración a M365 y Azure).",
        "Pico histórico en 2025 con $48.010 millones de pesos transados en 17.530 órdenes."
      ],
      chartHtml: `
        <div style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--muted); margin-bottom:12px;">Evolución Anual del Gasto TI Municipal (MM CLP)</div>
        <div style="display:flex; align-items:flex-end; gap:6px; height:180px; padding-top:20px; border-bottom:1px solid var(--line); position:relative;">
          <div style="flex:1; display:flex; flex-direction:column; align-items:center; height:100%;">
            <div style="margin-top:auto; width:100%; height:24%; background:#c7d1cc; border-radius:2px;"></div>
            <span style="font-size:9px; margin-top:4px; color:var(--muted);">'15</span>
          </div>
          <div style="flex:1; display:flex; flex-direction:column; align-items:center; height:100%;">
            <div style="margin-top:auto; width:100%; height:25%; background:#c7d1cc; border-radius:2px;"></div>
            <span style="font-size:9px; margin-top:4px; color:var(--muted);">'17</span>
          </div>
          <div style="flex:1; display:flex; flex-direction:column; align-items:center; height:100%;">
            <div style="margin-top:auto; width:100%; height:25%; background:#c7d1cc; border-radius:2px;"></div>
            <span style="font-size:9px; margin-top:4px; color:var(--muted);">'19</span>
          </div>
          <div style="flex:1; display:flex; flex-direction:column; align-items:center; height:100%;">
            <div style="margin-top:auto; width:100%; height:36%; background:#a0b8af; border-radius:2px;"></div>
            <span style="font-size:9px; margin-top:4px; color:var(--muted);">'20</span>
          </div>
          <div style="flex:1; display:flex; flex-direction:column; align-items:center; height:100%;">
            <div style="margin-top:auto; width:100%; height:78%; background:var(--gold); border-radius:2px; box-shadow:0 0 8px rgba(179,130,9,0.3);"></div>
            <span style="font-size:9px; margin-top:4px; font-weight:700; color:var(--gold);">'21</span>
          </div>
          <div style="flex:1; display:flex; flex-direction:column; align-items:center; height:100%;">
            <div style="margin-top:auto; width:100%; height:83%; background:var(--teal); border-radius:2px;"></div>
            <span style="font-size:9px; margin-top:4px; color:var(--muted);">'23</span>
          </div>
          <div style="flex:1; display:flex; flex-direction:column; align-items:center; height:100%;">
            <div style="margin-top:auto; width:100%; height:100%; background:var(--navy); border-radius:2px;"></div>
            <span style="font-size:9px; margin-top:4px; font-weight:700; color:var(--navy);">'25</span>
          </div>
        </div>
        <div style="font-size:10px; color:var(--muted); margin-top:8px; text-align:center;">Salto estructural 2021: El presupuesto anual se triplicó en 12 meses.</div>
      `
    },
    3: {
      title: "3. Concentración en Software de Gestión y Ecosistema de Proveedores",
      text: "El análisis de libre competencia y estructura de mercado revela una altísima concentración en los Sistemas de Información y Gestión Municipal (ERPs de rentas, patentes, finanzas y personal). El Índice Herfindahl-Hirschman (HHI) para este segmento alcanza 7.607 puntos (un mercado sobre 2.500 ya es considerado de alta concentración por las autoridades antimonopolio). Los proveedores tradicionales e históricos concentran más del 87% del volumen transado en este rubro, generando elevados costos de cambio (switching costs) y barreras técnicas de interoperabilidad para las alcaldías. En contraste, el Software Libre (FOSS) y estándares abiertos han recibido apenas el 0,17% del gasto total ($514 millones en 12 años).",
      findings: [
        "HHI de 7.607 en ERPs de gestión: Alta concentración de mercado a nivel nacional.",
        "El segmento ERP municipal concentra el 87,2% del gasto en proveedores históricos especializados.",
        "Elevados costos de cambio (switching costs) e inercias técnicas para migrar bases de datos.",
        "El Software Libre (FOSS) y estándares abiertos representan solo el 0,17% del gasto de modernización."
      ],
      chartHtml: `
        <div style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--muted); margin-bottom:12px;">Concentración del Mercado de Software Municipal (HHI)</div>
        <div style="background:var(--paper-soft); border:1px solid var(--gold-border); border-radius:6px; padding:16px; margin-bottom:14px;">
          <div style="font-size:28px; font-family:var(--font-serif); font-weight:700; color:var(--navy); line-height:1;">HHI: 7.607,1</div>
          <div style="font-size:11px; font-weight:700; text-transform:uppercase; color:var(--gold); margin-top:4px;">Alta Concentración de Mercado (Umbral HHI &gt; 2.500)</div>
          <div style="font-size:12px; color:var(--ink-secondary); margin-top:6px;">Proveedores tradicionales concentran más del 87% del volumen transado en software ERP local.</div>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:11px; color:var(--muted); border-top:1px solid var(--line); padding-top:10px;">
          <span>SaaS / Cloud: <strong>HHI 950</strong> (Moderado)</span>
          <span>Hardware: <strong>HHI 107</strong> (Competitivo y Atomizado)</span>
        </div>
      `
    },
    4: {
      title: "4. La Fractura Territorial del Gasto Per Cápita",
      text: "El análisis per cápita ($ invertido por cada habitante comunal) desnuda la profunda desigualdad territorial en la capacidad de los gobiernos locales de Chile. Municipios con alta recaudación propia o capitales regionales (como Valdivia con $36.789 CLP/hab o Ovalle con $39.404 CLP/hab) despliegan infraestructuras robustas de ciberseguridad, centros de monitoreo y servicios en la nube. En contraste, más de 120 municipios semi-urbanos y rurales de los grupos FIGEM 4 y 5 gastan menos de $1.500 CLP por habitante, condenando a su ciudadanía a brechas críticas de acceso y seguridad digital.",
      findings: [
        "Brecha de hasta 30x entre comunas de alta inversión per cápita y comunas rezagadas.",
        "Puente Alto (667k hab) invierte $6.986 CLP/hab, frente a Valdivia con $36.789 CLP/hab.",
        "La Región Metropolitana absorbe el 23,75% del gasto nacional ($71.290 MM).",
        "Regiones extremas (Aysén, Arica, Magallanes) no superan el 1,5% de participación cada una."
      ],
      chartHtml: `
        <div style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--muted); margin-bottom:12px;">Disparidad de Inversión Per Cápita Acumulada (CLP / Habitante)</div>
        <div style="display:flex; flex-direction:column; gap:10px;">
          <div>
            <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:3px;">
              <span>Ovalle (Región de Coquimbo)</span><strong>$39.404 / hab</strong>
            </div>
            <div style="height:8px; background:var(--line-light); border-radius:4px; overflow:hidden;">
              <div style="width:100%; height:100%; background:var(--teal);"></div>
            </div>
          </div>
          <div>
            <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:3px;">
              <span>Valdivia (Región de Los Ríos)</span><strong>$36.789 / hab</strong>
            </div>
            <div style="height:8px; background:var(--line-light); border-radius:4px; overflow:hidden;">
              <div style="width:93%; height:100%; background:var(--teal);"></div>
            </div>
          </div>
          <div>
            <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:3px;">
              <span>Temuco (Región de La Araucanía)</span><strong>$14.280 / hab</strong>
            </div>
            <div style="height:8px; background:var(--line-light); border-radius:4px; overflow:hidden;">
              <div style="width:36%; height:100%; background:var(--navy);"></div>
            </div>
          </div>
          <div>
            <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:3px;">
              <span>Puente Alto (Región Metropolitana)</span><strong>$6.986 / hab</strong>
            </div>
            <div style="height:8px; background:var(--line-light); border-radius:4px; overflow:hidden;">
              <div style="width:17%; height:100%; background:var(--gold);"></div>
            </div>
          </div>
          <div>
            <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:3px;">
              <span>Comuna Rural Promedio (Grupo FIGEM 5)</span><strong>$1.150 / hab</strong>
            </div>
            <div style="height:8px; background:var(--line-light); border-radius:4px; overflow:hidden;">
              <div style="width:3%; height:100%; background:var(--crimson);"></div>
            </div>
          </div>
        </div>
      `
    }
  };

  function initScrollytelling() {
    renderChapter(1);
    const tabBtns = document.querySelectorAll(".story-tab-btn");
    tabBtns.forEach(btn => {
      btn.addEventListener("click", () => {
        tabBtns.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        const chap = parseInt(btn.dataset.chapter, 10);
        renderChapter(chap);
      });
    });
  }

  function renderChapter(chapNum) {
    const data = storyChapters[chapNum];
    if (!data) return;
    const stage = document.getElementById("story-stage");
    stage.innerHTML = `
      <div class="story-content">
        <h3>${data.title}</h3>
        <p>${data.text}</p>
        <ul class="story-key-findings">
          ${data.findings.map(f => `<li><span class="story-bullet">✦</span><span>${f}</span></li>`).join("")}
        </ul>
      </div>
      <div class="story-chart">
        ${data.chartHtml}
      </div>
    `;
  }

  // -------------------------------------------------------------------------
  // 3. MAPA INTERACTIVO Y CAPAS (LEAFLET)
  // -------------------------------------------------------------------------
  function initMap() {
    // Centro geográfico aproximado de Chile continental
    const map = L.map("chile-map", {
      zoomControl: true,
      minZoom: 4,
      maxZoom: 12,
      scrollWheelZoom: false
    }).setView([-35.6751, -71.5430], 5);

    // Habilitar zoom por scrollwheel tras interactuar para evitar trampa de scroll en lectura
    map.on("click", () => { map.scrollWheelZoom.enable(); });
    map.on("focus", () => { map.scrollWheelZoom.enable(); });

    // Fondo cartográfico sobrio de alta resolución sin API key ni marcas de agua (Esri World Gray Canvas)
    const esriLightBase = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}", {
      attribution: 'Esri, HERE, Garmin, &copy; OpenStreetMap contributors | Observatorio TI',
      maxZoom: 16
    });
    const esriLightLabels = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}", {
      maxZoom: 16
    });

    const esriDarkBase = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}", {
      attribution: 'Esri, HERE, Garmin, &copy; OpenStreetMap contributors | Observatorio TI',
      maxZoom: 16
    });
    const esriDarkLabels = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}", {
      maxZoom: 16
    });

    state.esriLightGroup = L.layerGroup([esriLightBase, esriLightLabels]);
    state.esriDarkGroup = L.layerGroup([esriDarkBase, esriDarkLabels]);

    const initialTheme = document.documentElement.getAttribute("data-theme") || "light";
    if (initialTheme === "dark") {
      state.esriDarkGroup.addTo(map);
    } else {
      state.esriLightGroup.addTo(map);
    }

    state.map = map;
    state.markersLayer = L.layerGroup().addTo(map);

    renderMapMarkers();
    updateLegend();
  }

  function updateMapTheme(theme) {
    if (!state.map || !state.esriLightGroup || !state.esriDarkGroup) return;
    if (theme === "dark") {
      if (state.map.hasLayer(state.esriLightGroup)) state.map.removeLayer(state.esriLightGroup);
      if (!state.map.hasLayer(state.esriDarkGroup)) state.map.addLayer(state.esriDarkGroup);
    } else {
      if (state.map.hasLayer(state.esriDarkGroup)) state.map.removeLayer(state.esriDarkGroup);
      if (!state.map.hasLayer(state.esriLightGroup)) state.map.addLayer(state.esriLightGroup);
    }
  }

  function getMarkerStyle(comuna) {
    let color = "#146e66";
    let radius = 6;

    if (state.currentLayer === "madurez") {
      const score = comuna.score_madurez;
      if (score >= 80) color = "#146e66"; // Avanzada (Teal)
      else if (score >= 60) color = "#2b5c8f"; // Intermedia (Steel Blue)
      else if (score >= 40) color = "#b38209"; // Inicial (Gold)
      else color = "#a3492e"; // Rezago (Terracotta)
      radius = Math.max(5, Math.min(13, (score / 100) * 12));
    } else if (state.currentLayer === "gasto_pc") {
      const pc = comuna.gasto_pc || 0;
      if (pc > 30000) color = "#002b49";
      else if (pc > 15000) color = "#146e66";
      else if (pc > 5000) color = "#b38209";
      else color = "#dcd7cc";
      radius = Math.max(4, Math.min(15, Math.sqrt(pc / 200)));
    } else if (state.currentLayer === "lockin") {
      if (comuna.tiene_lockin_legado) {
        color = "#9b2226"; // Lockin detectado (Crimson)
        radius = 8;
      } else {
        color = "#e5eee9";
        radius = 4;
      }
    } else if (state.currentLayer === "foss") {
      if (comuna.tiene_foss) {
        color = "#2d6a4f"; // Usa Open Source
        radius = 9;
      } else {
        color = "#ded8cb";
        radius = 4;
      }
    } else if (state.currentLayer === "infra") {
      if (comuna.tiene_infra_propia) {
        color = "#002b49";
        radius = 8;
      } else {
        color = "#ded8cb";
        radius = 4;
      }
    }

    return { color, radius };
  }

  function renderMapMarkers() {
    if (!state.map || !state.markersLayer) return;
    state.markersLayer.clearLayers();

    const filtered = getFilteredComunas();

    filtered.forEach(c => {
      if (c.lat && c.lng) {
        const { color, radius } = getMarkerStyle(c);

        const marker = L.circleMarker([c.lat, c.lng], {
          radius: radius,
          fillColor: color,
          color: "#ffffff",
          weight: 1.5,
          opacity: 0.9,
          fillOpacity: 0.85
        });

        const popupContent = `
          <div style="font-family:var(--font-sans); min-width:180px;">
            <div style="font-size:10px; font-weight:700; color:var(--muted); text-transform:uppercase;">${c.region}</div>
            <strong style="font-family:var(--font-serif); font-size:16px; color:var(--navy); display:block; margin:2px 0 6px;">${c.comuna}</strong>
            <div style="font-size:12px; margin-bottom:2px;">Inversión TI Total: <strong>$${formatCLP(c.monto_total)}</strong></div>
            <div style="font-size:12px; margin-bottom:2px;">Inversión Per Cápita: <strong>$${formatCLP(c.gasto_pc)} / hab</strong></div>
            <div style="font-size:12px; margin-bottom:6px;">Madurez Tecnológica: <strong>${c.score_madurez}/100</strong> (${c.nivel_madurez})</div>
            <div style="font-size:11px; color:var(--gold); font-weight:600;">Haz click para abrir Ficha de Capacidades ↗</div>
          </div>
        `;

        marker.bindTooltip(`<strong>${c.comuna}</strong>: ${c.score_madurez}/100`, { direction: "top", offset: [0, -6] });
        marker.bindPopup(popupContent);

        marker.on("click", () => {
          selectComuna(c);
        });

        state.markersLayer.addLayer(marker);
      }
    });
  }

  function updateLegend() {
    const legendEl = document.getElementById("map-legend");
    if (!legendEl) return;

    if (state.currentLayer === "madurez") {
      legendEl.innerHTML = `
        <div class="map-legend-title">Termómetro de Madurez TI (0 a 100)</div>
        <div class="map-legend-items">
          <div class="map-legend-item"><span class="legend-color-box" style="background:#146e66;"></span><span>Avanzada (80 - 100 pts)</span></div>
          <div class="map-legend-item"><span class="legend-color-box" style="background:#2b5c8f;"></span><span>Intermedia (60 - 79 pts)</span></div>
          <div class="map-legend-item"><span class="legend-color-box" style="background:#b38209;"></span><span>Inicial (40 - 59 pts)</span></div>
          <div class="map-legend-item"><span class="legend-color-box" style="background:#a3492e;"></span><span>Rezago Crítico (&lt; 40 pts)</span></div>
        </div>
      `;
    } else if (state.currentLayer === "gasto_pc") {
      legendEl.innerHTML = `
        <div class="map-legend-title">Gasto TI Per Cápita Acumulado</div>
        <div class="map-legend-items">
          <div class="map-legend-item"><span class="legend-color-box" style="background:#002b49;"></span><span>&gt; $30.000 CLP / habitante</span></div>
          <div class="map-legend-item"><span class="legend-color-box" style="background:#146e66;"></span><span>$15.000 - $30.000 CLP / hab</span></div>
          <div class="map-legend-item"><span class="legend-color-box" style="background:#b38209;"></span><span>$5.000 - $15.000 CLP / hab</span></div>
          <div class="map-legend-item"><span class="legend-color-box" style="background:#dcd7cc;"></span><span>&lt; $5.000 CLP / hab (Rezago)</span></div>
        </div>
      `;
    } else if (state.currentLayer === "lockin") {
      legendEl.innerHTML = `
        <div class="map-legend-title">Nivel de Dependencia ERP / Vendor Lock-in</div>
        <div class="map-legend-items">
          <div class="map-legend-item"><span class="legend-color-box" style="background:#9b2226;"></span><span>Alta Dependencia ERP / Lock-in Legado</span></div>
          <div class="map-legend-item"><span class="legend-color-box" style="background:#e5eee9;"></span><span>Ecosistema Diversificado / Abierto</span></div>
        </div>
      `;
    } else if (state.currentLayer === "foss") {
      legendEl.innerHTML = `
        <div class="map-legend-title">Presencia de Software Libre (FOSS)</div>
        <div class="map-legend-items">
          <div class="map-legend-item"><span class="legend-color-box" style="background:#2d6a4f;"></span><span>Registra compras / soporte Open Source</span></div>
          <div class="map-legend-item"><span class="legend-color-box" style="background:#ded8cb;"></span><span>Cero inversión en FOSS</span></div>
        </div>
      `;
    } else if (state.currentLayer === "infra") {
      legendEl.innerHTML = `
        <div class="map-legend-title">Capacidad de Infraestructura TI Física</div>
        <div class="map-legend-items">
          <div class="map-legend-item"><span class="legend-color-box" style="background:#002b49;"></span><span>Infraestructura propia recurrente</span></div>
          <div class="map-legend-item"><span class="legend-color-box" style="background:#ded8cb;"></span><span>Sin parque de servidores propio</span></div>
        </div>
      `;
    }
  }

  // -------------------------------------------------------------------------
  // 4. RADIOGRAFÍA 4D: FICHA DETALLADA (DRAWER)
  // -------------------------------------------------------------------------
  function renderGaugeSvg(score) {
    const clamped = Math.max(0, Math.min(100, score || 0));
    // Ángulo en radianes: 0 pts = PI (180°), 100 pts = 0 (0°)
    const rad = Math.PI * (1 - clamped / 100);
    const needleLen = 38;
    const nx = (60 + needleLen * Math.cos(rad)).toFixed(1);
    const ny = (60 - needleLen * Math.sin(rad)).toFixed(1);

    return `
      <svg class="gauge-svg" viewBox="0 0 120 72" role="img" aria-label="Termómetro de madurez: ${clamped}/100">
        <!-- Arco Cuadrante 1: Rezago 0-39 (Terracotta) -->
        <path d="M 14 60 A 46 46 0 0 1 45.8 16.3" fill="none" stroke="#a3492e" stroke-width="8" stroke-linecap="butt" />
        <!-- Arco Cuadrante 2: Inicial 40-59 (Gold) -->
        <path d="M 45.8 16.3 A 46 46 0 0 1 74.2 16.3" fill="none" stroke="#b38209" stroke-width="8" stroke-linecap="butt" />
        <!-- Arco Cuadrante 3: Intermedia 60-79 (Steel Blue) -->
        <path d="M 74.2 16.3 A 46 46 0 0 1 97.2 33.0" fill="none" stroke="#2b5c8f" stroke-width="8" stroke-linecap="butt" />
        <!-- Arco Cuadrante 4: Avanzada 80-100 (Teal) -->
        <path d="M 97.2 33.0 A 46 46 0 0 1 106 60" fill="none" stroke="#146e66" stroke-width="8" stroke-linecap="butt" />

        <!-- Aguja indicadora -->
        <line x1="60" y1="60" x2="${nx}" y2="${ny}" stroke="#14171a" stroke-width="2.5" stroke-linecap="round" />
        <circle cx="60" cy="60" r="4.5" fill="#14171a" />
        <circle cx="60" cy="60" r="1.8" fill="#faf8f5" />

        <!-- Marcadores numéricos de soporte -->
        <text x="60" y="52" text-anchor="middle" font-family="var(--font-serif)" font-size="18" font-weight="700" fill="#14171a">${clamped}</text>
        <text x="60" y="68" text-anchor="middle" font-family="var(--font-sans)" font-size="8.5" font-weight="600" fill="var(--muted)">pts / 100</text>
        <text x="14" y="69" text-anchor="start" font-family="var(--font-sans)" font-size="7.5" fill="var(--muted)">0</text>
        <text x="106" y="69" text-anchor="end" font-family="var(--font-sans)" font-size="7.5" fill="var(--muted)">100</text>
      </svg>
    `;
  }

  function selectComuna(comuna) {
    state.selectedComuna = comuna;
    const drawer = document.getElementById("comuna-drawer");
    if (!drawer) return;

    // Actualizar hash deeplinking en la URL sin forzar reload
    if (window.history && window.history.replaceState) {
      window.history.replaceState(null, null, "#comuna=" + encodeURIComponent(comuna.comuna));
    }

    const score = comuna.score_madurez;
    const mTotal = Math.max(1, comuna.monto_total);
    const pob = Math.max(1, comuna.poblacion || 0);
    const pPct = (amt) => Math.min(100, Math.round((amt / mTotal) * 100));
    const pPc = (amt) => comuna.poblacion ? `<span class="cat-pc-badge">$${formatCLP(Math.round(amt / pob))} / hab</span> · ` : "";

    drawer.innerHTML = `
      <div class="drawer-header">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:12px;">
          <div>
            <div class="drawer-region-name">${comuna.region} · CUT ${comuna.codigo_cut || "—"}</div>
            <h3 class="drawer-comuna-name">${comuna.comuna}</h3>
            <div style="font-size:12px; color:var(--ink-secondary);">
              Población Oficial INE: <strong>${(comuna.poblacion || 0).toLocaleString("es-CL")} habitantes</strong>
            </div>
          </div>
          <button id="btn-share-comuna" class="btn-share" title="Copiar enlace directo a esta comuna">
            <span>🔗</span><span id="btn-share-text">Compartir</span>
          </button>
        </div>
      </div>

      <button id="btn-start-compare" class="btn-compare" title="Comparar ${comuna.comuna} con otro municipio de Chile">
        <span>⚖️</span><span>Comparar ${comuna.comuna} con otra comuna</span>
      </button>

      <!-- Thermometer Gauge Box -->
      <div class="drawer-thermometer-box">
        ${renderGaugeSvg(score)}
        <div class="thermometer-info">
          <h4>${comuna.nivel_madurez}</h4>
          <p>Termómetro dimensional basado en balance de infraestructura física, nube, ciberseguridad, automatización y servicios locales.</p>
        </div>
      </div>

      <!-- Financial Cards -->
      <div class="financial-strip">
        <div class="f-card">
          <div class="f-card-label">Gasto Histórico Total</div>
          <div class="f-card-val">$${formatCLP(comuna.monto_total)}</div>
          <div style="font-size:10px; color:var(--muted); margin-top:2px;">${comuna.total_ocs} órdenes de compra</div>
        </div>
        <div class="f-card">
          <div class="f-card-label">Gasto Per Cápita</div>
          <div class="f-card-val">$${formatCLP(comuna.gasto_pc)}</div>
          <div style="font-size:10px; color:var(--muted); margin-top:2px;">Pesos por habitante</div>
        </div>
      </div>

      <!-- Diagnostic Badges -->
      <div class="drawer-section-title">Banderas de Diagnóstico Institucional</div>
      <div class="diagnostic-badges">
        ${comuna.cuadrante_capacidad
          ? `<span class="diag-badge ${comuna.cuadrante_capacidad === 'Estado Soberano' ? 'good' : (comuna.cuadrante_capacidad === 'Estado Cautivo' ? 'danger' : 'warning')}">🏛️ ${comuna.cuadrante_capacidad}</span>`
          : ''}
        ${comuna.tiene_lockin_legado
          ? `<span class="diag-badge danger">⚠️ Alta Dependencia ERP / Lock-in</span>`
          : `<span class="diag-badge good">✓ Ecosistema Diversificado / Abierto</span>`}
        ${comuna.tiene_foss
          ? `<span class="diag-badge good">🐧 Usa Software Libre (FOSS)</span>`
          : `<span class="diag-badge neutral">✕ Sin Adopción FOSS</span>`}
        ${comuna.tiene_infra_propia
          ? `<span class="diag-badge good">🖥️ Infraestructura TI Propia</span>`
          : `<span class="diag-badge warning">⚡ Dependencia de Terceros</span>`}
      </div>

      <!-- Tecnoestructura y RRHH Propio -->
      <div class="drawer-section-title">Tecnoestructura & Músculo Propio (MuniData RRHH)</div>
      <div class="financial-strip">
        <div class="f-card">
          <div class="f-card-label">Dotación TI Interna</div>
          <div class="f-card-val">${comuna.dotacion_ti || 0} profesionales</div>
          <div style="font-size:10px; color:var(--muted); margin-top:2px;">Planta y contrata de informática</div>
        </div>
        <div class="f-card">
          <div class="f-card-label">Ratio Externalización (RET)</div>
          <div class="f-card-val">${comuna.ret_ratio !== undefined ? comuna.ret_ratio : "—"}</div>
          <div style="font-size:10px; color:var(--muted); margin-top:2px;">Gasto compras vs masa TI propia</div>
        </div>
      </div>

      <!-- Category Breakdown -->
      <div class="drawer-section-title">Desglose de la Canasta Tecnológica</div>
      <div class="category-breakdown-list">
        <div class="cat-item">
          <div class="cat-item-header">
            <span class="cat-name">Infraestructura y Hardware</span>
            <span class="cat-amount">${pPc(comuna.monto_hardware)}$${formatCLP(comuna.monto_hardware)} (${pPct(comuna.monto_hardware)}%)</span>
          </div>
          <div class="cat-bar-bg"><div class="cat-bar-fill" style="width:${pPct(comuna.monto_hardware)}%; background:var(--navy);"></div></div>
        </div>

        <div class="cat-item">
          <div class="cat-item-header">
            <span class="cat-name">IA y Automatización Básica</span>
            <span class="cat-amount">${pPc(comuna.monto_ia)}$${formatCLP(comuna.monto_ia)} (${pPct(comuna.monto_ia)}%)</span>
          </div>
          <div class="cat-bar-bg"><div class="cat-bar-fill" style="width:${pPct(comuna.monto_ia)}%; background:var(--teal);"></div></div>
        </div>

        <div class="cat-item">
          <div class="cat-item-header">
            <span class="cat-name">Redes y Telecomunicaciones</span>
            <span class="cat-amount">${pPc(comuna.monto_telecom)}$${formatCLP(comuna.monto_telecom)} (${pPct(comuna.monto_telecom)}%)</span>
          </div>
          <div class="cat-bar-bg"><div class="cat-bar-fill" style="width:${pPct(comuna.monto_telecom)}%; background:var(--gold);"></div></div>
        </div>

        <div class="cat-item">
          <div class="cat-item-header">
            <span class="cat-name">Ciberseguridad y Respaldo</span>
            <span class="cat-amount">${pPc(comuna.monto_cyber)}$${formatCLP(comuna.monto_cyber)} (${pPct(comuna.monto_cyber)}%)</span>
          </div>
          <div class="cat-bar-bg"><div class="cat-bar-fill" style="width:${pPct(comuna.monto_cyber)}%; background:#70587c;"></div></div>
        </div>

        <div class="cat-item">
          <div class="cat-item-header">
            <span class="cat-name">SaaS y Cloud Computing</span>
            <span class="cat-amount">${pPc(comuna.monto_saas)}$${formatCLP(comuna.monto_saas)} (${pPct(comuna.monto_saas)}%)</span>
          </div>
          <div class="cat-bar-bg"><div class="cat-bar-fill" style="width:${pPct(comuna.monto_saas)}%; background:#385bb2;"></div></div>
        </div>

        <div class="cat-item">
          <div class="cat-item-header">
            <span class="cat-name">Sistemas ERP de Gestión (Legados)</span>
            <span class="cat-amount">${pPc(comuna.monto_legado)}$${formatCLP(comuna.monto_legado)} (${pPct(comuna.monto_legado)}%)</span>
          </div>
          <div class="cat-bar-bg"><div class="cat-bar-fill" style="width:${pPct(comuna.monto_legado)}%; background:var(--crimson);"></div></div>
        </div>

        <div class="cat-item">
          <div class="cat-item-header">
            <span class="cat-name">Software Libre (FOSS)</span>
            <span class="cat-amount">${pPc(comuna.monto_foss)}$${formatCLP(comuna.monto_foss)} (${pPct(comuna.monto_foss)}%)</span>
          </div>
          <div class="cat-bar-bg"><div class="cat-bar-fill" style="width:${pPct(comuna.monto_foss)}%; background:var(--forest);"></div></div>
        </div>
      </div>

      <!-- Contratos Emblemáticos Mercado Público -->
      <div class="drawer-section-title">Contratos Emblemáticos en Mercado Público</div>
      <div class="top-contracts-list">
        ${(comuna.top_contratos && comuna.top_contratos.length > 0)
          ? comuna.top_contratos.map(oc => `
            <div class="contract-card">
              <div class="contract-card-header">
                <span class="contract-code">${oc.codigo_oc}</span>
                <span class="contract-amount">$${formatCLP(oc.monto)}</span>
              </div>
              <div class="contract-prov">${oc.proveedor} (${oc.anio})</div>
              <div class="contract-desc">${oc.descripcion}</div>
              <a href="${oc.url_mercadopublico}" target="_blank" rel="noopener noreferrer" class="contract-link">
                Auditar en MercadoPúblico ↗
              </a>
            </div>
          `).join("")
          : `<div style="font-size:12px; color:var(--muted);">Sin detalle de contratos individuales disponible.</div>`
        }
      </div>

      <!-- Top Suppliers -->
      <div class="drawer-section-title">Principales Proveedores Contratados</div>
      <div class="top-suppliers-list">
        ${(comuna.top_proveedores && comuna.top_proveedores.length > 0)
          ? comuna.top_proveedores.map(p => `
            <div class="supplier-item">
              <span class="supplier-name" title="${p.proveedor}">${p.proveedor}</span>
              <span class="supplier-amount">$${formatCLP(p.monto)}</span>
            </div>
          `).join("")
          : `<div style="font-size:12px; color:var(--muted);">Sin detalle de proveedores disponible.</div>`
        }
      </div>
    `;

    // Conectar botón de compartir con portapapeles
    const btnShare = document.getElementById("btn-share-comuna");
    if (btnShare) {
      btnShare.addEventListener("click", () => {
        const url = window.location.origin + window.location.pathname + "#comuna=" + encodeURIComponent(comuna.comuna);
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(url).then(() => {
            const txt = document.getElementById("btn-share-text");
            if (txt) {
              txt.textContent = "¡Copiado!";
              setTimeout(() => { txt.textContent = "Compartir"; }, 2000);
            }
          }).catch(() => {
            prompt("Copia este enlace directo:", url);
          });
        } else {
          prompt("Copia este enlace directo:", url);
        }
      });
    }

    // Conectar botón de comparar
    const btnCompare = document.getElementById("btn-start-compare");
    if (btnCompare) {
      btnCompare.addEventListener("click", () => {
        let other = state.comunas.find(c => c.comuna !== comuna.comuna && c.region === comuna.region);
        if (!other) {
          other = state.comunas.find(c => c.comuna !== comuna.comuna);
        }
        if (other) {
          openComparison(comuna, other);
        }
      });
    }

    // Centrar mapa si tiene coordenadas
    if (state.map && comuna.lat && comuna.lng) {
      state.map.setView([comuna.lat, comuna.lng], 9, { animate: true });
    }
  }

  // -------------------------------------------------------------------------
  // 4.1 COMPARADOR COMUNAL A VS B
  // -------------------------------------------------------------------------
  function openComparison(comunaA, comunaB) {
    state.selectedComuna = comunaA;
    state.compareComuna = comunaB;
    state.isCompareMode = true;

    if (window.history && window.history.replaceState) {
      window.history.replaceState(null, null, "#comparar=" + encodeURIComponent(comunaA.comuna) + "," + encodeURIComponent(comunaB.comuna));
    }

    renderComparisonView();
  }

  function renderComparisonView() {
    const drawer = document.getElementById("comuna-drawer");
    if (!drawer || !state.selectedComuna || !state.compareComuna) return;

    const cA = state.selectedComuna;
    const cB = state.compareComuna;

    const pobA = Math.max(1, cA.poblacion || 0);
    const pobB = Math.max(1, cB.poblacion || 0);

    const pcDiff = cA.gasto_pc - cB.gasto_pc;
    const pcPctDiff = cB.gasto_pc > 0 ? Math.round(((cA.gasto_pc - cB.gasto_pc) / cB.gasto_pc) * 100) : 0;

    const otherComunas = state.comunas.slice().sort((a, b) => a.comuna.localeCompare(b.comuna));

    drawer.innerHTML = `
      <div class="compare-view">
        <div class="compare-top-nav">
          <button id="btn-back-to-single" class="btn-back">
            <span>←</span><span>Volver a ${cA.comuna}</span>
          </button>
          <button id="btn-share-compare" class="btn-share" title="Copiar enlace a esta comparación">
            <span>🔗</span><span id="btn-share-compare-text">Compartir vs</span>
          </button>
        </div>

        <div class="compare-selector-box">
          <label for="compare-select-b">Comparar ${cA.comuna} con:</label>
          <select id="compare-select-b" class="compare-select">
            ${otherComunas.map(c => `
              <option value="${c.comuna}" ${c.comuna === cB.comuna ? 'selected' : ''}>
                ${c.comuna} (${c.region})
              </option>
            `).join("")}
          </select>
        </div>

        <!-- Encabezados de Comunas -->
        <div class="compare-grid">
          <div class="compare-col highlight-a">
            <div style="font-size:10px; font-weight:700; color:var(--muted); text-transform:uppercase;">${cA.region}</div>
            <h3 class="compare-comuna-title">${cA.comuna}</h3>
            <div style="font-size:11px; color:var(--ink-secondary);">${(cA.poblacion || 0).toLocaleString("es-CL")} hab.</div>
          </div>
          <div class="compare-col highlight-b">
            <div style="font-size:10px; font-weight:700; color:var(--muted); text-transform:uppercase;">${cB.region}</div>
            <h3 class="compare-comuna-title">${cB.comuna}</h3>
            <div style="font-size:11px; color:var(--ink-secondary);">${(cB.poblacion || 0).toLocaleString("es-CL")} hab.</div>
          </div>
        </div>

        <!-- Termómetro Madurez TI -->
        <div class="drawer-section-title" style="margin-top:8px;">Madurez Tecnológica (0-100)</div>
        <div class="compare-grid">
          <div class="compare-col">
            <div style="font-size:24px; font-family:var(--font-serif); font-weight:700; color:var(--navy); line-height:1;">${cA.score_madurez} <span style="font-size:12px; font-weight:400; color:var(--muted);">/100</span></div>
            <div style="font-size:11px; font-weight:600; color:var(--teal);">${cA.nivel_madurez}</div>
          </div>
          <div class="compare-col">
            <div style="font-size:24px; font-family:var(--font-serif); font-weight:700; color:var(--teal); line-height:1;">${cB.score_madurez} <span style="font-size:12px; font-weight:400; color:var(--muted);">/100</span></div>
            <div style="font-size:11px; font-weight:600; color:var(--teal);">${cB.nivel_madurez}</div>
          </div>
        </div>

        <!-- Inversión Per Cápita -->
        <div class="drawer-section-title" style="margin-top:8px;">Inversión Per Cápita Acumulada</div>
        <div class="compare-grid">
          <div class="compare-col">
            <div class="compare-row-metric">
              <div class="lbl">Gasto / Habitante</div>
              <div class="val" style="color:var(--navy);">$${formatCLP(cA.gasto_pc)}</div>
            </div>
            <div class="compare-row-metric">
              <div class="lbl">Gasto Histórico Total</div>
              <div class="val" style="font-size:12px;">$${formatCLP(cA.monto_total)}</div>
            </div>
          </div>
          <div class="compare-col">
            <div class="compare-row-metric">
              <div class="lbl">Gasto / Habitante</div>
              <div class="val" style="color:var(--teal);">$${formatCLP(cB.gasto_pc)}</div>
            </div>
            <div class="compare-row-metric">
              <div class="lbl">Gasto Histórico Total</div>
              <div class="val" style="font-size:12px;">$${formatCLP(cB.monto_total)}</div>
            </div>
          </div>
        </div>
        <div style="background:var(--paper-soft); border:1px solid var(--line-light); border-radius:6px; padding:10px 12px; font-size:12px; text-align:center;">
          ${pcDiff > 0
            ? `<strong>${cA.comuna}</strong> invierte <strong>$${formatCLP(Math.abs(pcDiff))} CLP más por habitante (+${Math.abs(pcPctDiff)}%)</strong> que ${cB.comuna}.`
            : pcDiff < 0
            ? `<strong>${cB.comuna}</strong> invierte <strong>$${formatCLP(Math.abs(pcDiff))} CLP más por habitante</strong> que ${cA.comuna}.`
            : `Ambos municipios tienen una inversión per cápita idéntica.`
          }
        </div>

        <!-- Comparativa de Categorías Clave ($ / hab) -->
        <div class="drawer-section-title" style="margin-top:8px;">Inversión por Habitante en Canastas Clave</div>
        <div style="display:flex; flex-direction:column; gap:8px;">
          <div style="background:var(--paper); border:1px solid var(--line-light); border-radius:4px; padding:8px 10px;">
            <div style="font-size:11px; font-weight:700; color:var(--navy); margin-bottom:4px;">Infraestructura y Hardware</div>
            <div style="display:flex; justify-content:space-between; font-size:12px; font-family:var(--font-mono);">
              <span>${cA.comuna}: <strong>$${formatCLP(Math.round(cA.monto_hardware / pobA))}</strong></span>
              <span>${cB.comuna}: <strong>$${formatCLP(Math.round(cB.monto_hardware / pobB))}</strong></span>
            </div>
          </div>
          <div style="background:var(--paper); border:1px solid var(--line-light); border-radius:4px; padding:8px 10px;">
            <div style="font-size:11px; font-weight:700; color:var(--teal); margin-bottom:4px;">IA y Automatización Básica</div>
            <div style="display:flex; justify-content:space-between; font-size:12px; font-family:var(--font-mono);">
              <span>${cA.comuna}: <strong>$${formatCLP(Math.round(cA.monto_ia / pobA))}</strong></span>
              <span>${cB.comuna}: <strong>$${formatCLP(Math.round(cB.monto_ia / pobB))}</strong></span>
            </div>
          </div>
          <div style="background:var(--paper); border:1px solid var(--line-light); border-radius:4px; padding:8px 10px;">
            <div style="font-size:11px; font-weight:700; color:#385bb2; margin-bottom:4px;">SaaS y Cloud Computing</div>
            <div style="display:flex; justify-content:space-between; font-size:12px; font-family:var(--font-mono);">
              <span>${cA.comuna}: <strong>$${formatCLP(Math.round(cA.monto_saas / pobA))}</strong></span>
              <span>${cB.comuna}: <strong>$${formatCLP(Math.round(cB.monto_saas / pobB))}</strong></span>
            </div>
          </div>
          <div style="background:var(--paper); border:1px solid var(--line-light); border-radius:4px; padding:8px 10px;">
            <div style="font-size:11px; font-weight:700; color:#70587c; margin-bottom:4px;">Ciberseguridad y Respaldo</div>
            <div style="display:flex; justify-content:space-between; font-size:12px; font-family:var(--font-mono);">
              <span>${cA.comuna}: <strong>$${formatCLP(Math.round(cA.monto_cyber / pobA))}</strong></span>
              <span>${cB.comuna}: <strong>$${formatCLP(Math.round(cB.monto_cyber / pobB))}</strong></span>
            </div>
          </div>
        </div>

        <!-- Banderas de Diagnóstico -->
        <div class="drawer-section-title" style="margin-top:8px;">Diagnóstico Institucional</div>
        <div class="compare-grid">
          <div class="compare-col" style="font-size:11px;">
            <div>${cA.tiene_lockin_legado ? '⚠️ <span style="color:var(--crimson); font-weight:700;">Alta Dependencia ERP</span>' : '✓ Ecosistema Diversificado'}</div>
            <div>${cA.tiene_foss ? '🐧 <span style="color:var(--forest); font-weight:700;">Usa Software Libre</span>' : '✕ Sin FOSS'}</div>
            <div>${cA.tiene_infra_propia ? '🖥️ <span style="color:var(--navy); font-weight:700;">Infra TI Propia</span>' : '⚡ Tercerizado'}</div>
          </div>
          <div class="compare-col" style="font-size:11px;">
            <div>${cB.tiene_lockin_legado ? '⚠️ <span style="color:var(--crimson); font-weight:700;">Alta Dependencia ERP</span>' : '✓ Ecosistema Diversificado'}</div>
            <div>${cB.tiene_foss ? '🐧 <span style="color:var(--forest); font-weight:700;">Usa Software Libre</span>' : '✕ Sin FOSS'}</div>
            <div>${cB.tiene_infra_propia ? '🖥️ <span style="color:var(--navy); font-weight:700;">Infra TI Propia</span>' : '⚡ Tercerizado'}</div>
          </div>
        </div>
      </div>
    `;

    // Eventos de la vista comparativa
    const btnBack = document.getElementById("btn-back-to-single");
    if (btnBack) {
      btnBack.addEventListener("click", () => {
        state.isCompareMode = false;
        selectComuna(state.selectedComuna);
      });
    }

    const selectB = document.getElementById("compare-select-b");
    if (selectB) {
      selectB.addEventListener("change", (e) => {
        const targetB = state.comunas.find(c => c.comuna === e.target.value);
        if (targetB) {
          openComparison(state.selectedComuna, targetB);
        }
      });
    }

    const btnShareComp = document.getElementById("btn-share-compare");
    if (btnShareComp) {
      btnShareComp.addEventListener("click", () => {
        const url = window.location.origin + window.location.pathname + "#comparar=" + encodeURIComponent(cA.comuna) + "," + encodeURIComponent(cB.comuna);
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(url).then(() => {
            const txt = document.getElementById("btn-share-compare-text");
            if (txt) {
              txt.textContent = "¡Copiado!";
              setTimeout(() => { txt.textContent = "Compartir vs"; }, 2000);
            }
          }).catch(() => {
            prompt("Copia este enlace de comparación:", url);
          });
        } else {
          prompt("Copia este enlace de comparación:", url);
        }
      });
    }
  }

  // -------------------------------------------------------------------------
  // 5. FILTROS, BÚSQUEDA Y CONTROLES
  // -------------------------------------------------------------------------
  function initRegionDropdown() {
    const select = document.getElementById("region-filter");
    if (!select) return;

    // Obtener regiones únicas
    const regionNames = [...new Set(state.comunas.map(c => c.region))].filter(Boolean).sort();
    regionNames.forEach(r => {
      const opt = document.createElement("option");
      opt.value = r;
      opt.textContent = r;
      select.appendChild(opt);
    });
  }

  function initControls() {
    // Botones de capas
    const layerBtns = document.querySelectorAll(".layer-btn[data-layer]");
    layerBtns.forEach(btn => {
      btn.addEventListener("click", () => {
        layerBtns.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        state.currentLayer = btn.dataset.layer;
        renderMapMarkers();
        updateLegend();
      });
    });

    // Búsqueda instantánea
    const searchInput = document.getElementById("comuna-search");
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        state.searchQuery = e.target.value.toLowerCase().trim();
        renderMapMarkers();
        renderTable();
      });
    }

    // Filtro por Región
    const regionSelect = document.getElementById("region-filter");
    if (regionSelect) {
      regionSelect.addEventListener("change", (e) => {
        state.selectedRegion = e.target.value;
        renderMapMarkers();
        renderTable();

        // Ajustar zoom a la región
        if (state.selectedRegion && state.map) {
          const matchComunas = state.comunas.filter(c => c.region === state.selectedRegion && c.lat && c.lng);
          if (matchComunas.length > 0) {
            const bounds = L.latLngBounds(matchComunas.map(c => [c.lat, c.lng]));
            state.map.fitBounds(bounds, { padding: [50, 50], maxZoom: 8 });
          }
        }
      });
    }

    // Filtro por Cuadrante de Capacidad Estatal
    const cuadranteSelect = document.getElementById("cuadrante-filter");
    if (cuadranteSelect) {
      cuadranteSelect.addEventListener("change", (e) => {
        state.selectedCuadrante = e.target.value;
        renderMapMarkers();
        renderTable();
      });
    }

    // Reset Map
    const btnReset = document.getElementById("btn-reset-map");
    if (btnReset) {
      btnReset.addEventListener("click", () => {
        state.searchQuery = "";
        state.selectedRegion = "";
        state.selectedCuadrante = "";
        if (searchInput) searchInput.value = "";
        if (regionSelect) regionSelect.value = "";
        if (cuadranteSelect) cuadranteSelect.value = "";
        if (state.map) state.map.setView([-35.6751, -71.5430], 5);
        renderMapMarkers();
        renderTable();
      });
    }

    // Exportar CSV Comunal
    const btnExport = document.getElementById("btn-export-csv");
    if (btnExport) {
      btnExport.addEventListener("click", () => {
        // Interceptado por initModals
      });
    }

    // Exportar CSV Proveedores
    const btnExportProv = document.getElementById("btn-export-prov-csv");
    if (btnExportProv) {
      btnExportProv.addEventListener("click", () => {
        // Interceptado por initModals
      });
    }

    // Buscador de Proveedores
    const provSearchInput = document.getElementById("prov-search");
    if (provSearchInput) {
      provSearchInput.addEventListener("input", (e) => {
        state.provSearchQuery = e.target.value.toLowerCase().trim();
        renderProveedoresTable();
      });
    }

    // Pestañas del Centro de Rankings
    const rankTabs = document.querySelectorAll(".rank-tab-btn[data-rank-pane]");
    rankTabs.forEach(btn => {
      btn.addEventListener("click", () => {
        rankTabs.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        const paneId = btn.dataset.rankPane;
        document.querySelectorAll(".rank-pane").forEach(pane => {
          pane.classList.remove("active");
        });
        const targetPane = document.getElementById(paneId);
        if (targetPane) targetPane.classList.add("active");
        if (paneId === "pane-proveedores") renderProveedoresTable();
        if (paneId === "pane-cuadrantes") renderCuadrantesSummary();
      });
    });

    // Clicks en comunas de los Podios
    document.querySelectorAll(".rank-podium-item .comuna-name").forEach(span => {
      span.addEventListener("click", () => {
        const cName = span.dataset.comuna;
        if (!cName) return;
        const target = state.comunas.find(c => c.comuna.toLowerCase() === cName.toLowerCase());
        if (target) {
          selectComuna(target);
          const radEl = document.getElementById("radiografia");
          if (radEl) radEl.scrollIntoView({ behavior: "smooth" });
        }
      });
    });

    // Table sorting headers
    const ths = document.querySelectorAll("#ranking-table th[data-sort]");
    ths.forEach(th => {
      th.addEventListener("click", () => {
        const field = th.dataset.sort;
        if (state.sortField === field) {
          state.sortAsc = !state.sortAsc;
        } else {
          state.sortField = field;
          state.sortAsc = false; // Descendente por defecto para métricas
        }
        renderTable();
      });
    });
  }

  function getFilteredComunas() {
    return state.comunas.filter(c => {
      const matchSearch = !state.searchQuery || 
        c.comuna.toLowerCase().includes(state.searchQuery) || 
        c.region.toLowerCase().includes(state.searchQuery);
      const matchRegion = !state.selectedRegion || c.region === state.selectedRegion;
      const matchCuadrante = !state.selectedCuadrante || c.cuadrante_capacidad === state.selectedCuadrante;
      return matchSearch && matchRegion && matchCuadrante;
    });
  }

  // -------------------------------------------------------------------------
  // 6. RANKING & TABLA DE DATOS
  // -------------------------------------------------------------------------
  function renderTable() {
    const tbody = document.getElementById("ranking-tbody");
    if (!tbody) return;

    let filtered = getFilteredComunas();

    // Ordenar
    filtered.sort((a, b) => {
      let va = a[state.sortField];
      let vb = b[state.sortField];
      if (typeof va === "string") {
        va = va.toLowerCase();
        vb = (vb || "").toLowerCase();
      }
      if (va < vb) return state.sortAsc ? -1 : 1;
      if (va > vb) return state.sortAsc ? 1 : -1;
      return 0;
    });

    tbody.innerHTML = filtered.slice(0, 100).map((c, idx) => `
      <tr data-comuna-name="${c.comuna}">
        <td style="font-weight:700; color:var(--muted);">${idx + 1}</td>
        <td style="font-weight:600; color:var(--navy);">${c.comuna}</td>
        <td style="font-size:12px; color:var(--muted);">${c.region}</td>
        <td>${(c.poblacion || 0).toLocaleString("es-CL")}</td>
        <td style="font-family:var(--font-mono); font-weight:600;">$${formatCLP(c.monto_total)}</td>
        <td style="font-family:var(--font-mono); color:var(--teal); font-weight:600;">$${formatCLP(c.gasto_pc)}</td>
        <td>
          <span class="badge-pill" style="background:${c.score_madurez >= 80 ? 'var(--teal-bg)' : c.score_madurez >= 60 ? '#eaf0f8' : c.score_madurez >= 40 ? 'var(--gold-bg)' : 'var(--crimson-bg)'}; color:${c.score_madurez >= 80 ? 'var(--teal)' : c.score_madurez >= 60 ? '#2b5c8f' : c.score_madurez >= 40 ? 'var(--gold)' : 'var(--crimson)'};">
            ${c.score_madurez}/100
          </span>
        </td>
        <td>${(c.dotacion_total || 0).toLocaleString("es-CL")}</td>
        <td style="font-family:var(--font-mono);">${c.pct_honorarios !== undefined ? c.pct_honorarios + '%' : '—'}</td>
        <td style="font-family:var(--font-mono); font-weight:700; color:var(--teal);">${c.dotacion_ti || 0}</td>
        <td style="font-family:var(--font-mono); font-weight:600;">${c.ret_ratio !== undefined ? c.ret_ratio + 'x' : '—'}</td>
        <td>
          ${c.cuadrante_capacidad ? `
            <span class="diag-badge ${c.cuadrante_capacidad === 'Estado Soberano' ? 'good' : (c.cuadrante_capacidad === 'Estado Cautivo' ? 'danger' : (c.cuadrante_capacidad === 'Estado Híbrido Dependiente' ? 'warning' : 'neutral'))}" style="font-size:10px; padding:2px 6px;">
              ${c.cuadrante_capacidad.replace('Estado ', '')}
            </span>
          ` : '—'}
        </td>
        <td>${c.tiene_lockin_legado ? '<span style="color:var(--crimson); font-weight:700;">⚠️ Lock-in</span>' : '<span style="color:var(--forest);">✓ Limpio</span>'}</td>
      </tr>
    `).join("");

    // Click en fila selecciona comuna y hace scroll al mapa
    tbody.querySelectorAll("tr").forEach(tr => {
      tr.addEventListener("click", () => {
        const cName = tr.dataset.comunaName;
        const target = state.comunas.find(c => c.comuna === cName);
        if (target) {
          selectComuna(target);
          document.getElementById("radiografia").scrollIntoView({ behavior: "smooth" });
        }
      });
    });
  }

  function exportTableToCSV() {
    const filtered = getFilteredComunas();
    const headers = [
      "Ranking", "Comuna", "Region", "Poblacion", "Gasto_Total_CLP", 
      "Gasto_Per_Capita_CLP", "Madurez_TI", "Dotacion_RRHH_Total", 
      "Pct_Honorarios", "Dotacion_TI", "Ratio_RET", "Cuadrante_Capacidad", "Lockin_Legado"
    ];
    const rows = filtered.map((c, idx) => [
      idx + 1,
      `"${c.comuna}"`,
      `"${c.region}"`,
      c.poblacion || 0,
      c.monto_total || 0,
      c.gasto_pc || 0,
      c.score_madurez || 0,
      c.dotacion_total || 0,
      c.pct_honorarios !== undefined ? c.pct_honorarios : "",
      c.dotacion_ti || 0,
      c.ret_ratio !== undefined ? c.ret_ratio : "",
      `"${c.cuadrante_capacidad || ''}"`,
      c.tiene_lockin_legado ? "Lock-in" : "Limpio"
    ]);

    const csvContent = "\uFEFF" + [headers.join(";")].concat(rows.map(e => e.join(";"))).join("\r\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `ranking_ti_rrhh_municipal_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  function renderProveedoresTable() {
    const tbody = document.getElementById("prov-tbody");
    if (!tbody || !state.proveedores) return;

    let filtered = state.proveedores.filter(p => {
      if (!state.provSearchQuery) return true;
      return (
        (p.proveedor && p.proveedor.toLowerCase().includes(state.provSearchQuery)) ||
        (p.rut && p.rut.toLowerCase().includes(state.provSearchQuery)) ||
        (p.rubro_principal && p.rubro_principal.toLowerCase().includes(state.provSearchQuery))
      );
    });

    tbody.innerHTML = filtered.map((p, idx) => {
      let badgeClass = "general";
      const rubro = p.rubro_principal || "";
      if (rubro.includes("ERP") || rubro.includes("Gestión")) badgeClass = "erp";
      else if (rubro.includes("Telecom")) badgeClass = "telecom";
      else if (rubro.includes("Hardware")) badgeClass = "hardware";
      else if (rubro.includes("Cloud") || rubro.includes("Software")) badgeClass = "cloud";
      else if (rubro.includes("Seguridad")) badgeClass = "seguridad";
      else if (rubro.includes("Consultoría")) badgeClass = "consultoria";

      return `
        <tr>
          <td style="font-weight:700; color:var(--muted);">${idx + 1}</td>
          <td style="font-weight:600; color:var(--navy);">${p.proveedor}</td>
          <td style="font-family:var(--font-mono); font-size:11px; color:var(--muted);">${p.rut || "—"}</td>
          <td><span class="prov-badge ${badgeClass}">${rubro}</span></td>
          <td style="font-family:var(--font-mono); text-align:center;">${p.total_munis} comunas</td>
          <td style="font-family:var(--font-mono); text-align:center;">${(p.total_ocs || 0).toLocaleString("es-CL")}</td>
          <td style="font-family:var(--font-mono); font-weight:700; color:var(--navy);">$${formatCLP(p.monto_total_clp)}</td>
          <td style="font-family:var(--font-mono); font-weight:700; color:var(--gold);">${p.cuota_mercado_pct}%</td>
        </tr>
      `;
    }).join("");
  }

  function exportProveedoresToCSV() {
    if (!state.proveedores || state.proveedores.length === 0) return;
    const headers = [
      "Ranking", "Proveedor", "RUT", "Rubro_Principal", 
      "Municipios_Clientes", "Total_OCs", "Monto_Total_CLP", "Cuota_Mercado_Pct"
    ];
    const rows = state.proveedores.map((p, idx) => [
      idx + 1,
      `"${p.proveedor}"`,
      `"${p.rut || ''}"`,
      `"${p.rubro_principal || ''}"`,
      p.total_munis || 0,
      p.total_ocs || 0,
      p.monto_total_clp || 0,
      p.cuota_mercado_pct || 0
    ]);
    const csvContent = "\uFEFF" + [headers.join(";")].concat(rows.map(e => e.join(";"))).join("\r\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `proveedores_ti_municipal_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  function renderCuadrantesSummary() {
    const container = document.getElementById("rank-cuadrantes-summary");
    if (!container) return;
    const dist = (state.kpis && state.kpis.rrhh_nacional && state.kpis.rrhh_nacional.cuadrantes_distribucion) || {
      "Estado Soberano": 198,
      "Estado Híbrido Dependiente": 5,
      "Estado Artesanal": 99,
      "Estado Cautivo": 46,
      "Estado Desconectado": 49
    };

    container.innerHTML = `
      <div class="quadrant-card soberano" style="cursor:pointer;" data-filter-quadrant="Estado Soberano">
        <div class="quadrant-header">
          <span class="quadrant-title">🏛️ Estado Soberano</span>
          <span class="quadrant-count">${dist["Estado Soberano"] || 198} comunas</span>
        </div>
        <p class="quadrant-desc">
          Gobiernos locales con equipo TI propio robusto (&ge; 5 profesionales) y un gasto externo equilibrado (RET &le; 1,8x). Mantienen autonomía técnica sobre sus datos y plataformas.
        </p>
        <div style="font-size:11px; font-weight:700; color:var(--forest);">Click para filtrar ranking por este cuadrante →</div>
      </div>

      <div class="quadrant-card hibrido" style="cursor:pointer;" data-filter-quadrant="Estado Híbrido Dependiente">
        <div class="quadrant-header">
          <span class="quadrant-title">⚡ Estado Híbrido Dependiente</span>
          <span class="quadrant-count">${dist["Estado Híbrido Dependiente"] || 5} comunas</span>
        </div>
        <p class="quadrant-desc">
          Municipios con alta capacidad técnica interna pero con un gasto masivo en consultoras y proveedores externos (RET &gt; 1,8x). Riesgo de duplicidad presupuestaria.
        </p>
        <div style="font-size:11px; font-weight:700; color:var(--teal);">Click para filtrar ranking por este cuadrante →</div>
      </div>

      <div class="quadrant-card artesanal" style="cursor:pointer;" data-filter-quadrant="Estado Artesanal">
        <div class="quadrant-header">
          <span class="quadrant-title">🛠️ Estado Artesanal</span>
          <span class="quadrant-count">${dist["Estado Artesanal"] || 99} comunas</span>
        </div>
        <p class="quadrant-desc">
          Baja dotación informática (&lt; 5 profesionales) y bajo gasto externo. Operación austera o manual con baja penetración de sistemas digitales avanzados.
        </p>
        <div style="font-size:11px; font-weight:700; color:var(--gold);">Click para filtrar ranking por este cuadrante →</div>
      </div>

      <div class="quadrant-card cautivo" style="cursor:pointer;" data-filter-quadrant="Estado Cautivo">
        <div class="quadrant-header">
          <span class="quadrant-title">⚠️ Estado Cautivo</span>
          <span class="quadrant-count">${dist["Estado Cautivo"] || 46} comunas</span>
        </div>
        <p class="quadrant-desc">
          Escaso personal informático interno (&lt; 5 profesionales) y alta dependencia financiera de proveedores y ERPs externos (RET &gt; 1,8x). Máximo riesgo de vendor lock-in.
        </p>
        <div style="font-size:11px; font-weight:700; color:var(--crimson);">Click para filtrar ranking por este cuadrante →</div>
      </div>
    `;

    container.querySelectorAll(".quadrant-card[data-filter-quadrant]").forEach(card => {
      card.addEventListener("click", () => {
        const qName = card.dataset.filterQuadrant;
        const cuadranteSelect = document.getElementById("cuadrante-filter");
        if (cuadranteSelect) {
          cuadranteSelect.value = qName;
          state.selectedCuadrante = qName;
          renderTable();
        }
        // Cambiar a la pestaña de comunas
        const btnComunasTab = document.querySelector(".rank-tab-btn[data-rank-pane='pane-comunas']");
        if (btnComunasTab) btnComunasTab.click();
        const tableEl = document.getElementById("ranking-table");
        if (tableEl) tableEl.scrollIntoView({ behavior: "smooth" });
      });
    });
  }

  // -------------------------------------------------------------------------
  // 7. GESTIÓN DE TEMA Y ACCESIBILIDAD (A11Y)
  // -------------------------------------------------------------------------
  function initThemeAndA11y() {
    // Botones de tema
    document.querySelectorAll("[data-theme-btn]").forEach(btn => {
      btn.addEventListener("click", () => {
        const theme = btn.dataset.themeBtn;
        document.documentElement.setAttribute("data-theme", theme);
        try { localStorage.setItem("evegat_theme", theme); } catch (e) {}
        updateMapTheme(theme);
      });
    });

    // Control de tipografía
    let currentFontSize = 16;
    try {
      const savedFont = localStorage.getItem("evegat_fontsize");
      if (savedFont) currentFontSize = parseInt(savedFont, 10);
    } catch (e) {}

    const updateFont = (sz) => {
      currentFontSize = Math.min(22, Math.max(13, sz));
      document.documentElement.style.fontSize = currentFontSize + "px";
      try { localStorage.setItem("evegat_fontsize", currentFontSize); } catch (e) {}
    };

    const btnDec = document.getElementById("btn-font-dec");
    const btnReset = document.getElementById("btn-font-reset");
    const btnInc = document.getElementById("btn-font-inc");

    if (btnDec) btnDec.addEventListener("click", () => updateFont(currentFontSize - 1));
    if (btnReset) btnReset.addEventListener("click", () => updateFont(16));
    if (btnInc) btnInc.addEventListener("click", () => updateFont(currentFontSize + 1));

    // Lector de voz TTS
    const btnTts = document.getElementById("btn-tts");
    if (btnTts && "speechSynthesis" in window) {
      let isSpeaking = false;
      btnTts.addEventListener("click", () => {
        if (isSpeaking) {
          window.speechSynthesis.cancel();
          isSpeaking = false;
          const textEl = document.getElementById("tts-text");
          if (textEl) textEl.textContent = "Escuchar";
          return;
        }

        let narrative = "";
        if (state.selectedComuna) {
          const c = state.selectedComuna;
          narrative = `Resumen de capacidades tecnológicas para la comuna de ${c.comuna}, región de ${c.region}. Población: ${(c.poblacion || 0).toLocaleString("es-CL")} habitantes. Inversión histórica en contratos tecnológicos: ${formatCLP(c.monto_total)} pesos chilenos, equivalente a ${formatCLP(c.gasto_pc)} pesos por habitante. Índice de madurez tecnológica: ${c.score_madurez} sobre 100, clasificado como ${c.nivel_madurez}. Diagnóstico de capacidad estatal: ${c.cuadrante_capacidad || "En evaluación"}. Tecnoestructura municipal: ${c.dotacion_ti || 0} profesionales TI contratados. Ratio de externalización tecnológica: ${c.ret_ratio || "No determinado"}.`;
        } else {
          narrative = `Observatorio de Capacidades Tecnológicas y Capacidad Estatal en los 346 municipios de Chile. Se analizaron más de 312 mil millones de pesos transados en 153 mil contratos en Mercado Público durante 12 años, cruzados con la dotación funcionaria y tecnoestructura de Transparencia Activa.`;
        }

        const utter = new SpeechSynthesisUtterance(narrative);
        utter.lang = "es-CL";
        utter.rate = 1.0;
        utter.onend = () => {
          isSpeaking = false;
          const textEl = document.getElementById("tts-text");
          if (textEl) textEl.textContent = "Escuchar";
        };
        isSpeaking = true;
        const textEl = document.getElementById("tts-text");
        if (textEl) textEl.textContent = "Detener";
        window.speechSynthesis.speak(utter);
      });
    }
  }

  // -------------------------------------------------------------------------
  // 8. GESTIÓN DE MODALES ("CÓMO USAR" Y "AVISO LEGAL / LEY 21.719")
  // -------------------------------------------------------------------------
  function initModals() {
    const comoUsarModal = document.getElementById("como-usar-modal");
    const legalModal = document.getElementById("legal-modal");
    const registroModal = document.getElementById("registro-descarga-modal");
    const formRegistro = document.getElementById("form-registro-descarga");
    const errorMsg = document.getElementById("reg-error-msg");
    const filenameLabel = document.getElementById("descarga-filename-label");
    const chkNoAutoShow = document.getElementById("chk-no-auto-show");

    function openModal(modal) {
      if (!modal) return;
      modal.classList.add("active");
      modal.setAttribute("aria-hidden", "false");
      document.body.style.overflow = "hidden";
    }

    function closeModal(modal) {
      if (!modal) return;
      modal.classList.remove("active");
      modal.setAttribute("aria-hidden", "true");
      document.body.style.overflow = "";
      if (modal === comoUsarModal && chkNoAutoShow && chkNoAutoShow.checked) {
        try { localStorage.setItem("evegat_seen_guide_v3", "1"); } catch (e) {}
      }
    }

    // Auto-apertura de la guía de uso en primera visita
    try {
      const seenGuide = localStorage.getItem("evegat_seen_guide_v3");
      if (!seenGuide) {
        setTimeout(() => {
          openModal(comoUsarModal);
        }, 1200);
      }
    } catch (e) {}

    // Botones para abrir "Cómo usar"
    ["btn-open-guia", "btn-open-guia-band", "btn-hero-como-usar", "btn-banner-open-modal", "btn-floating-guia"].forEach(id => {
      const btn = document.getElementById(id);
      if (btn) btn.addEventListener("click", () => openModal(comoUsarModal));
    });

    // Botones para abrir "Aviso Legal"
    ["btn-open-legal-top", "btn-open-legal-band", "btn-open-legal-footer"].forEach(id => {
      const btn = document.getElementById(id);
      if (btn) btn.addEventListener("click", () => openModal(legalModal));
    });

    // Interceptor para todas las descargas de datos (exige registro previo)
    document.querySelectorAll(".btn-intercept-download").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        const file = btn.dataset.file || "comunas_enriched.json";
        const label = btn.dataset.label || file;
        state.pendingDownload = { file, label };

        if (filenameLabel) filenameLabel.textContent = label;

        // Pre-cargar datos del usuario si ya se registró previamente
        try {
          const rawLead = localStorage.getItem("evegat_registered_lead");
          if (rawLead) {
            const lead = JSON.parse(rawLead);
            const inNombre = document.getElementById("reg-nombre");
            const inEmail = document.getElementById("reg-email");
            const inInst = document.getElementById("reg-institucion");
            const inPerfil = document.getElementById("reg-perfil");
            const inProp = document.getElementById("reg-proposito");
            const inProy = document.getElementById("reg-proyecto");

            if (inNombre && lead.nombre) inNombre.value = lead.nombre;
            if (inEmail && lead.email) inEmail.value = lead.email;
            if (inInst && lead.institucion) inInst.value = lead.institucion;
            if (inPerfil && lead.perfil) inPerfil.value = lead.perfil;
            if (inProp && lead.proposito) inProp.value = lead.proposito;
            if (inProy && lead.proyecto) inProy.value = lead.proyecto;
          }
        } catch (e) {}

        if (errorMsg) errorMsg.style.display = "none";
        openModal(registroModal);
      });
    });

    // Envío del formulario de registro y disparo de descarga
    if (formRegistro) {
      formRegistro.addEventListener("submit", (e) => {
        e.preventDefault();
        const nombre = (document.getElementById("reg-nombre")?.value || "").trim();
        const email = (document.getElementById("reg-email")?.value || "").trim();
        const institucion = (document.getElementById("reg-institucion")?.value || "").trim();
        const perfil = (document.getElementById("reg-perfil")?.value || "").trim();
        const proposito = (document.getElementById("reg-proposito")?.value || "").trim();
        const proyecto = (document.getElementById("reg-proyecto")?.value || "").trim();
        const contacto = document.getElementById("reg-contacto")?.checked !== false;

        // Validación básica
        if (!nombre || !email || !institucion || !perfil || !proposito || !email.includes("@")) {
          if (errorMsg) errorMsg.style.display = "block";
          return;
        }

        if (errorMsg) errorMsg.style.display = "none";

        // Persistir lead
        const leadData = {
          nombre,
          email,
          institucion,
          perfil,
          proposito,
          proyecto,
          contacto,
          fecha: new Date().toISOString()
        };
        try {
          localStorage.setItem("evegat_registered_lead", JSON.stringify(leadData));
        } catch (err) {}

        // Ejecutar descarga
        const targetFile = state.pendingDownload ? state.pendingDownload.file : "comunas_enriched.json";
        if (targetFile === "ranking_comunal.csv") {
          exportTableToCSV();
        } else if (targetFile === "proveedores_tecnologicos.csv") {
          exportProveedoresToCSV();
        } else {
          const a = document.createElement("a");
          a.href = "data/" + targetFile;
          a.download = targetFile;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
        }

        closeModal(registroModal);
        showToast("✓ ¡Registro completado! Tu descarga ha comenzado.");
      });
    }

    // Cerrar modales mediante atributos data-close-modal
    document.querySelectorAll("[data-close-modal]").forEach(btn => {
      btn.addEventListener("click", () => {
        const modalId = btn.dataset.closeModal;
        const targetModal = document.getElementById(modalId);
        if (targetModal) closeModal(targetModal);
      });
    });

    // Cerrar al clickear el backdrop
    [comoUsarModal, legalModal, registroModal].forEach(m => {
      if (!m) return;
      m.addEventListener("click", (e) => {
        if (e.target === m) closeModal(m);
      });
    });

    // Cerrar con Escape
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        closeModal(comoUsarModal);
        closeModal(legalModal);
        closeModal(registroModal);
      }
    });

    // Botones de salto rápido dentro del modal "Cómo usar"
    document.querySelectorAll(".btn-modal-jump[data-jump-target]").forEach(btn => {
      btn.addEventListener("click", () => {
        closeModal(comoUsarModal);
        const targetId = btn.dataset.jumpTarget;
        const el = document.querySelector(targetId);
        if (el) el.scrollIntoView({ behavior: "smooth" });
      });
    });

    // Demo compare: Maipú vs Algarrobo
    const btnDemoCompare = document.getElementById("btn-demo-compare");
    if (btnDemoCompare) {
      btnDemoCompare.addEventListener("click", () => {
        closeModal(comoUsarModal);
        const maipu = state.comunas.find(c => c.comuna.toLowerCase() === "maipú" || c.comuna.toLowerCase() === "maipu");
        const algarrobo = state.comunas.find(c => c.comuna.toLowerCase() === "algarrobo");
        if (maipu && algarrobo) {
          openComparison(maipu, algarrobo);
          const radEl = document.getElementById("radiografia");
          if (radEl) radEl.scrollIntoView({ behavior: "smooth" });
        }
      });
    }
  }

  function showToast(msg) {
    let toast = document.getElementById("obs-toast-el");
    if (!toast) {
      toast = document.createElement("div");
      toast.id = "obs-toast-el";
      toast.className = "obs-toast";
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => {
      toast.classList.remove("show");
    }, 3500);
  }

  // -------------------------------------------------------------------------
  // 9. MÓDULO RRHH MUNICIPAL Y CAPACIDAD ESTATAL (P166)
  // -------------------------------------------------------------------------
  function initRRHHModule() {
    const kpisGrid = document.getElementById("rrhh-kpis-grid");
    const tabsContainer = document.getElementById("rrhh-tabs");
    const stage = document.getElementById("rrhh-stage");
    if (!kpisGrid || !stage) return;

    // Métricas nacionales calculadas dinámicamente desde el catastro
    const totalDotacion = state.comunas.reduce((acc, c) => acc + (c.dotacion_total || 0), 0) || 151342;
    const totalTI = state.comunas.reduce((acc, c) => acc + (c.dotacion_ti || 0), 0) || 3647;
    const pctTI = ((totalTI / totalDotacion) * 100).toFixed(2);
    const comunasConHon = state.comunas.filter(c => c.pct_honorarios !== undefined && c.pct_honorarios > 0);
    const avgHonorarios = comunasConHon.length > 0 
      ? (comunasConHon.reduce((acc, c) => acc + c.pct_honorarios, 0) / comunasConHon.length).toFixed(1)
      : 42.8;
    const comunasConRET = state.comunas.filter(c => c.ret_ratio !== undefined && c.ret_ratio > 0);
    const avgRET = comunasConRET.length > 0
      ? (comunasConRET.reduce((acc, c) => acc + c.ret_ratio, 0) / comunasConRET.length).toFixed(2)
      : 2.42;

    kpisGrid.innerHTML = `
      <div class="rrhh-kpi-card">
        <div class="rrhh-kpi-label">Dotación Total Municipal</div>
        <div class="rrhh-kpi-val">${totalDotacion.toLocaleString("es-CL")}</div>
        <div class="rrhh-kpi-desc">Funcionarios analizados en 346 comunas (Planta, Contrata y Honorarios)</div>
      </div>
      <div class="rrhh-kpi-card">
        <div class="rrhh-kpi-label">Músculo Propio TI</div>
        <div class="rrhh-kpi-val" style="color:var(--teal);">${totalTI.toLocaleString("es-CL")}</div>
        <div class="rrhh-kpi-desc">Apenas el <strong>${pctTI}%</strong> de la dotación municipal total corresponde a informáticos</div>
      </div>
      <div class="rrhh-kpi-card">
        <div class="rrhh-kpi-label">Tasa de Precarización</div>
        <div class="rrhh-kpi-val" style="color:var(--crimson);">${avgHonorarios}%</div>
        <div class="rrhh-kpi-desc">Personal contratado a honorarios, sin estabilidad ni carrera funcionaria</div>
      </div>
      <div class="rrhh-kpi-card">
        <div class="rrhh-kpi-label">Ratio RET Promedio</div>
        <div class="rrhh-kpi-val" style="color:var(--gold);">${avgRET}x</div>
        <div class="rrhh-kpi-desc">Por cada $1 peso invertido en tecnoestructura interna se gastan $2,42 en compras externas</div>
      </div>
    `;

    // Conteo de comunas por cuadrante
    const cuadrantesCount = {
      "Estado Soberano": state.comunas.filter(c => c.cuadrante_capacidad === "Estado Soberano").length,
      "Estado Híbrido Dependiente": state.comunas.filter(c => c.cuadrante_capacidad === "Estado Híbrido Dependiente").length,
      "Estado Cautivo": state.comunas.filter(c => c.cuadrante_capacidad === "Estado Cautivo").length,
      "Estado Artesanal": state.comunas.filter(c => c.cuadrante_capacidad === "Estado Artesanal").length,
    };

    function renderRRHHTab(tabKey) {
      if (tabKey === "capacidad") {
        stage.innerHTML = `
          <div style="margin-bottom:20px;">
            <h3 style="font-family:var(--font-serif); font-size:22px; color:var(--navy); margin-bottom:8px;">
              Matriz de Capacidad Estatal y Soberanía Tecnológica (Ratio RET)
            </h3>
            <p style="font-size:13px; color:var(--ink-secondary); line-height:1.6;">
              El <strong>Ratio de Externalización de la Tecnoestructura (RET)</strong> evalúa la relación entre las compras de tecnología a proveedores privados y la capacidad técnica instalada propia del gobierno local. Permite clasificar a las 346 municipalidades de Chile en cuatro cuadrantes operativos:
            </p>
          </div>

          <div class="quadrant-grid">
            <div class="quadrant-card soberano">
              <div class="quadrant-header">
                <span class="quadrant-title">🏛️ Estado Soberano</span>
                <span class="quadrant-count">${cuadrantesCount["Estado Soberano"]} comunas</span>
              </div>
              <p class="quadrant-desc">
                Dotación informática interna robusta (&ge; 5 profesionales) y un ratio de compras externas balanceado (RET &le; 1,8x). Capacidad instalada para gobernar contratos, auditar código y mantener autonomía de datos públicos.
              </p>
              <div class="quadrant-examples">
                <strong>Referentes:</strong> Santiago, Providencia, Las Condes, Maipú, Peñalolén.
              </div>
            </div>

            <div class="quadrant-card hibrido">
              <div class="quadrant-header">
                <span class="quadrant-title">⚡ Estado Híbrido Dependiente</span>
                <span class="quadrant-count">${cuadrantesCount["Estado Híbrido Dependiente"]} comunas</span>
              </div>
              <p class="quadrant-desc">
                Dispone de equipo técnico calificado pero realiza un gasto intensivo en consultorías externas y licitaciones de gran envergadura (RET &gt; 1,8x). Fuerte capacidad de contraparte técnica pero alta absorción de presupuesto por terceros.
              </p>
              <div class="quadrant-examples">
                <strong>Referentes:</strong> Viña del Mar, Antofagasta, Temuco, Puerto Montt.
              </div>
            </div>

            <div class="quadrant-card cautivo">
              <div class="quadrant-header">
                <span class="quadrant-title">⚠️ Estado Cautivo</span>
                <span class="quadrant-count">${cuadrantesCount["Estado Cautivo"]} comunas</span>
              </div>
              <p class="quadrant-desc">
                Dotación técnica informática reducida (&lt; 5 profesionales) combinada con alta tercerización tecnológica y captura por proveedores monopólicos (vendor lock-in en ERPs legados). Riesgo crítico de asimetría de información y vulnerabilidad.
              </p>
              <div class="quadrant-examples">
                <strong>Referentes:</strong> Calama, Quillota, Algarrobo, Melipilla, San Bernardo.
              </div>
            </div>

            <div class="quadrant-card artesanal">
              <div class="quadrant-header">
                <span class="quadrant-title">🛠️ Estado Artesanal / Desconectado</span>
                <span class="quadrant-count">${cuadrantesCount["Estado Artesanal"]} comunas</span>
              </div>
              <p class="quadrant-desc">
                Baja inversión financiera externa y casi nulo personal de informática interno. Los trámites operan con planillas desconectadas, carpetas compartidas y soporte ad-hoc. Severo rezago frente a las exigencias de la Ley de Transformación Digital.
              </p>
              <div class="quadrant-examples">
                <strong>Referentes:</strong> Alhué, Alto Biobío, Putre, Timaukel, Ollagüe.
              </div>
            </div>
          </div>
        `;
      } else if (tabKey === "dotacion") {
        stage.innerHTML = `
          <div>
            <h3 style="font-family:var(--font-serif); font-size:22px; color:var(--navy); margin-bottom:8px;">
              Composición Jurídica del Personal y la Tecnoestructura Municipal
            </h3>
            <p style="font-size:13px; color:var(--ink-secondary); line-height:1.6; margin-bottom:20px;">
              El análisis longitudinal del proyecto <strong>P166</strong> revela que la transformación digital municipal en Chile se sostiene sobre una base de alta fragilidad contractual. Mientras las plantas funcionarias permanecen congeladas desde hace décadas, los puestos de soporte computacional, ciberseguridad y desarrollo web se cubren masivamente bajo honorarios a suma alzada:
            </p>

            <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:18px;">
              <div style="background:var(--paper); border:1px solid var(--line); border-radius:8px; padding:18px;">
                <h4 style="font-size:14px; font-weight:700; color:var(--navy); margin-bottom:6px;">Planta Municipal (31,4%)</h4>
                <p style="font-size:12px; color:var(--ink-secondary); line-height:1.5;">Máxima estabilidad laboral bajo el Estatuto Administrativo Municipal. Sin embargo, menos del <strong>0,3%</strong> de los cargos de planta corresponden a profesionales con título en Informática, Ciencia de la Computación o Telecomunicaciones.</p>
              </div>
              <div style="background:var(--paper); border:1px solid var(--line); border-radius:8px; padding:18px;">
                <h4 style="font-size:14px; font-weight:700; color:var(--navy); margin-bottom:6px;">Contrata Anual (25,8%)</h4>
                <p style="font-size:12px; color:var(--ink-secondary); line-height:1.5;">Contratos renovables anualmente sujetos al tope presupuestario legal del 40% del gasto en personal. Concentra la mayor parte de las jefaturas operativas de informática en municipios medianos y grandes.</p>
              </div>
              <div style="background:var(--paper); border:1px solid var(--line); border-radius:8px; padding:18px;">
                <h4 style="font-size:14px; font-weight:700; color:var(--crimson); margin-bottom:6px;">Honorarios a Suma Alzada (42,8%)</h4>
                <p style="font-size:12px; color:var(--ink-secondary); line-height:1.5;">Relación contractual civil sin fuero ni derechos estatutarios. En las áreas digitales y de soporte ciudadano, el <strong>68%</strong> de los desarrolladores y técnicos TI municipales prestan servicios bajo esta modalidad precaria.</p>
              </div>
            </div>
          </div>
        `;
      } else if (tabKey === "genero") {
        stage.innerHTML = `
          <div>
            <h3 style="font-family:var(--font-serif); font-size:22px; color:var(--navy); margin-bottom:8px;">
              Estabilidad Funcionaria, Remuneraciones y Brecha en Tecnología
            </h3>
            <p style="font-size:13px; color:var(--ink-secondary); line-height:1.6; margin-bottom:20px;">
              El cruce entre los salarios brutos informados en Transparencia Activa y las trayectorias individuales del motor P166 evidencia tres hallazgos estructurales:
            </p>

            <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:18px;">
              <div style="background:var(--paper); border:1px solid var(--line); border-radius:8px; padding:18px;">
                <div style="font-size:11px; font-weight:700; color:var(--gold); text-transform:uppercase;">Permanencia Media</div>
                <div style="font-size:26px; font-family:var(--font-serif); color:var(--navy); font-weight:700; margin:4px 0;">14 Meses</div>
                <p style="font-size:12px; color:var(--ink-secondary);">La rotación promedio del personal TI a honorarios es de solo 14 meses, lo que genera pérdida crítica de conocimiento institucional y dependencia de consultores externos.</p>
              </div>
              <div style="background:var(--paper); border:1px solid var(--line); border-radius:8px; padding:18px;">
                <div style="font-size:11px; font-weight:700; color:var(--teal); text-transform:uppercase;">Brecha Salarial Comunal</div>
                <div style="font-size:26px; font-family:var(--font-serif); color:var(--navy); font-weight:700; margin:4px 0;">3,8x</div>
                <p style="font-size:12px; color:var(--ink-secondary);">Un profesional informático en comunas del cono oriente de Santiago percibe en promedio $3,2M brutos, frente a $850.000 en municipios rurales de la macrozona sur.</p>
              </div>
              <div style="background:var(--paper); border:1px solid var(--line); border-radius:8px; padding:18px;">
                <div style="font-size:11px; font-weight:700; color:var(--crimson); text-transform:uppercase;">Participación Femenina TI</div>
                <div style="font-size:26px; font-family:var(--font-serif); color:var(--navy); font-weight:700; margin:4px 0;">18,4%</div>
                <p style="font-size:12px; color:var(--ink-secondary);">Menos de 1 de cada 5 funcionarios dedicados a funciones técnicas de tecnología, redes o infraestructura en municipios chilenos son mujeres.</p>
              </div>
            </div>
          </div>
        `;
      }
    }

    // Inicializar pestaña por defecto
    renderRRHHTab("capacidad");

    // Eventos de pestañas
    if (tabsContainer) {
      tabsContainer.querySelectorAll(".rrhh-tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
          tabsContainer.querySelectorAll(".rrhh-tab-btn").forEach(b => b.classList.remove("active"));
          btn.classList.add("active");
          renderRRHHTab(btn.dataset.rrhhTab);
        });
      });
    }
  }

  // -------------------------------------------------------------------------
  // UTILIDADES
  // -------------------------------------------------------------------------
  function formatCLP(val) {
    if (!val || isNaN(val)) return "0";
    return Math.round(val).toLocaleString("es-CL");
  }

  // Iniciar ejecución
  init();
});
