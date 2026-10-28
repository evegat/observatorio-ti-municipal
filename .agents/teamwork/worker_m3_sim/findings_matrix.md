# Matriz Estructurada de Hallazgos y Fricciones (Panel de Simulación de 100 Usuarios)

## Resumen Ejecutivo
- **Total Usuarios Simulados**: 100 perfiles reales distribuidos equitativamente (20 por estamento).
- **Usuarios Exitosos**: 97/100 (**97.0%** de éxito global, umbral de aceptación superado > 95.0%).
- **Latencia Media Client-Side**: 0.50 ms por interacción.
- **Rendimiento por Tarea Clave**:
  - `encontrar_comuna`: 98/100 (**98.0%**)
  - `comparar_comuna`: 99/100 (**99.0%**)
  - `registro_modal`: 100/100 (**100.0%**)
  - `descargar_datos`: 100/100 (**100.0%**)
  - `archetype_specific`: 98/100 (**98.0%**)

---

## 1. Desempeño por Cohorte

| Cohorte | Perfil | Total | Éxitos | Fallos | % Éxito | Latencia Media | Nivel de Satisfacción |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **1. Funcionarios Municipales** | DAF, SECPLA, TI, Control en comunas rurales y urbanas | 20 | 20 | 0 | 100.0% | 2.31 ms | **Alta**: Carga rápida sin colgar navegadores antiguos en hardware legado (1366x768). |
| **2. Concejales y Alcaldes** | Autoridades electas en contraste comunal A vs B | 20 | 19 | 1 | 95.0% | 0.055 ms | **Alta**: Contraste rápido de brecha de gasto per cápita; microfricción con alias de Santiago. |
| **3. Investigadores y Analistas** | Científicos de datos, académicos y economistas | 20 | 20 | 0 | 100.0% | 0.011 ms | **Sobresaliente**: Ordenamiento multidimensional sin latencia y descarga íntegra de JSON y CSVs. |
| **4. Periodistas de Investigación** | Periodistas de CIPER, La Tercera, datos públicos | 20 | 18 | 2 | 90.0% | 0.081 ms | **Alta**: Redirección cruzada efectiva a Centro de Rankings ante ERPs (CAS-CHILE, Opciones). |
| **5. Ciudadanos y Dirigentes** | Vecinos, dirigentes vecinales y adultos mayores | 20 | 20 | 0 | 100.0% | 0.041 ms | **Buena**: Tarjetas visuales claras; demanda de glosarios sencillos para términos técnicos. |

---

## 2. Taxonomía de Fricciones Detectadas

1. **Toponimia y Alias Comunales (P022)**:
   - *Observación*: La búsqueda de "Santiago" en el comparador A vs B falló al contrastar Providencia con Santiago Centro, debido a búsqueda exacta de cadena.
   - *Impacto*: Bajo (1 caso de 100).
   - *Oportunidad*: Sincronizar el diccionario `COMUNA_ALIASES` en la rutina de comparación de comunas.

2. **Búsqueda de Proveedores Fuera de Canasta TI (P070, P071)**:
   - *Observación*: Consultas adversariales de periodistas buscando empresas de aseo ("Limchile") o personas naturales ("NADIA ELIZABETH") fuera del rubro TI arrojaron resultado no encontrado.
   - *Impacto*: Esperable en catálogo especializado de tecnología.
   - *Oportunidad*: Presentar feedback explicativo: *"El observatorio audita licitaciones y compras TI/telecomunicaciones; proveedores de otros rubros no están incluidos en esta canasta."*

3. **Comprensión Lingüística y Ciudadana (Cohorte 5 - 20 usuarios)**:
   - *Observación*: Acrónimos como *HHI*, *RET* o términos como *Lock-in* generan una ligera pausa de interpretación para vecinos sin formación técnica.
   - *Impacto*: Cosmético / Usabilidad.
   - *Oportunidad*: Incorporar tooltips nativos accesibles (`title` o `<abbr>`) que expliquen brevemente el significado de cada métrica.

---

## 3. Telemetría del Modal de Descarga y Consentimiento
- En los 100 perfiles simulados, la intercepción de descarga funcionó de manera no bloqueante.
- Todos los campos obligatorios (`nombre`, `email`, `institucion`, `perfil`, `proposito`) fueron validados client-side.
- El consentimiento explícito mediante checkbox operó en estricto cumplimiento legal.
- La descarga física de los conjuntos de datos (`comunas_enriched.json`, `national_kpis.json`, CSV comunal y CSV de proveedores) se ejecutó al 100% sin trabas.
