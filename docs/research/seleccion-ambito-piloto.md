# Selección del ámbito piloto para el primer hallazgo

**Fecha:** 2026-07-02 · **Ticket:** [#7](https://github.com/spulido99/anticorruption-ai/issues/7)
**Método:** agregaciones SoQL server-side sobre los datasets **completos** de SECOP II — contratos `jbjy-vk9h` (firmados desde 2022-01-01) y procesos `p6dx-8zbt` (publicados desde 2022-01-01) — sin muestreo. Indicadores del [catálogo de red flags](./red-flags-contratacion.md): RF-01 (single bidding, solo modalidades competitivas adjudicadas), RF-02 (% contratación directa), concentración de proveedores (proxy de RF-05/06 a nivel departamento) y componentes de opacidad (RF-19). Código y métricas crudas reproducibles en [`assets/seleccion-ambito-piloto/`](./assets/seleccion-ambito-piloto/).

## Recomendación

**Boyacá, con foco en su contratación municipal, y el single bidding (RF-01) como indicador ancla.** Es el departamento con la anomalía más fuerte, más robusta y con mejor textura narrativa del país, en un tamaño manejable para un piloto. Condicional: si el aliado ([#4](https://github.com/spulido99/anticorruption-ai/issues/4)) resulta tener agenda territorial propia, su región pesa más que este ranking — el análisis es reproducible para cualquier departamento cambiando un filtro.

## 1. Comparativo por departamento (contratos firmados / procesos publicados desde 2022)

Columnas: valor contratado (billones COP, con tope de sanidad de 5×10¹¹ por contrato — ver §4), % del valor por contratación directa, procesos competitivos adjudicados, % de ellos con un solo oferente (SB%).

| Departamento | Valor (bn) | % directa (valor) | Procesos comp. | SB% |
|---|---:|---:|---:|---:|
| Bogotá D.C. | 263,0 | 45,7 | 133.201 | 8,7 |
| Antioquia | 74,8 | 64,4 | 43.996 | 32,1 |
| Valle del Cauca | 34,7 | 52,3 | 26.107 | 35,2 |
| Atlántico | 21,0 | 51,4 | 7.291 | 28,8 |
| Cundinamarca | 19,7 | 44,1 | 24.029 | 39,3 |
| Santander | 17,5 | 31,2 | 18.819 | 29,3 |
| Bolívar | 16,8 | 35,0 | 8.274 | 25,0 |
| **Boyacá** | **14,1** | **34,7** | **19.736** | **54,7** |
| Meta | 10,2 | 29,0 | 10.061 | 48,0 |
| Magdalena | 9,9 | 28,8 | 3.114 | 34,7 |
| Norte de Santander | 9,0 | 36,7 | 8.254 | 51,2 |
| Cesar | 8,8 | 17,6 | 3.955 | 51,2 |
| La Guajira | 8,2 | 31,5 | 2.582 | 56,7 |
| Nariño | 5,7 | 41,2 | 14.651 | **9,4** |
| Casanare | 5,1 | 30,4 | 5.072 | 54,9 |
| Arauca | 2,4 | 20,9 | 3.293 | 66,7 |
| Caquetá | 2,5 | 33,1 | 4.376 | 56,5 |
| Putumayo | 2,2 | 32,8 | 3.206 | 58,2 |

SB% nacional agregado: ~27 %. Los departamentos con SB% > Boyacá (Arauca, Putumayo, La Guajira, Caquetá, Casanare) tienen 6–8× menos procesos y el falso positivo clásico de territorio remoto/conflicto ("no hay oferentes"). Boyacá tiene la señal alta **con** masa estadística (19.736 procesos, el 5.º departamento por procesos competitivos) y sin esa excusa: es central, denso (123 municipios) y comparable con Nariño — también rural y montañoso, con 14.651 procesos — que marca 9,4 %.

## 2. Por qué la señal de Boyacá es real y no un artefacto

**No es composición de modalidades.** Dentro de *cada* modalidad, Boyacá dobla o cuadruplica la tasa nacional:

| Modalidad | SB% nacional | SB% Boyacá |
|---|---:|---:|
| Licitación pública | 15,3 | **66,8** |
| Selección abreviada subasta inversa | 11,5 | **43,3** |
| Selección abreviada de menor cuantía | 41,6 | **72,8** |
| Concurso de méritos abierto | 26,8 | **56,4** |
| Mínima cuantía | 34,7 | **53,5** |
| Licitación pública de obra | 10,6 | **29,3** |

**No es un año raro — y está empeorando.** SB% de Boyacá por año: 33,5 (2022) → 48,2 (2023) → 55,3 (2024) → 61,0 (2025) → 63,7 (2026 parcial), siempre ~2× el nacional (21→36 en el mismo periodo, que además sube — señal nacional relevante en sí misma). El salto de 2024 coincide con la entrada de las administraciones municipales 2024–2027.

**No es solo menudeo.** En procesos con adjudicación > 500 M COP: Boyacá 47,1 % vs 21,8 % nacional.

**Tiene textura municipal para la historia.** Municipios con ≥ 80 procesos competitivos y SB% ≥ 75: Macanal (86), Somondoco (85), Santana (81), San Eduardo (80), Soatá (79), Garagoa (79), Coper (78), San Pablo de Borbur (77), Sotaquirá (77), Cómbita (76), Socotá (76), Sáchica (76), Tota (75), Cubará (85, con 422 procesos). En estos municipios "la licitación" es de facto un ritual de oferente único. Y la Gobernación de Boyacá aporta el ángulo complementario de RF-02: 72,6 % de su valor contratado desde 2022 fue por contratación directa (2,55 bn COP con tope de sanidad aplicado).

## 3. Alternativas consideradas

- **Antioquia** — 64,4 % del valor por directa (el más alto entre los grandes), Medellín D.E. con 74 % directa sobre 18,2 bn, y municipios de Urabá/Bajo Cauca con SB% 70–89 (Dabeiba 89,1). Historia enorme pero: mercado mediático ya cubierto, tamaño poco manejable para un piloto, y el falso positivo de seguridad/conflicto en Urabá exige controles que aún no tenemos. Buen **segundo** ámbito.
- **Magdalena** — Alcaldía de Santa Marta con SB 53,8 % y 58,1 % del valor por directa; Corpamag SB 47,5 %; mega-contratos de consorcios de 1 solo contrato (quinto centenario). Narrativa política jugosa pero base estadística chica (3.114 procesos en todo el departamento) — un hallazgo se sostendría en pocos casos, no en un patrón masivo.
- **La Guajira, Cesar, Casanare, Arauca, Caquetá, Putumayo** — SB% altos pero muestras chicas y el descargo de "territorio sin oferentes" es plausible; para señalar riesgo ahí primero hay que construir el control por mercado local (RF-04).
- **Corte por sector** (nacional, % directa en valor): agricultura 77 %, Hacienda 64 %, Trabajo 58 %. Señales reales pero difusas territorialmente — el campo `sector` es del lado entidad y demasiado grueso para anclar una primera historia. Sirve como corte *dentro* del piloto, no como piloto.

## 4. Hallazgos metodológicos (insumos para la ingesta y el modelo core)

1. **Errores de dígitos en `valor_del_contrato` distorsionan cualquier métrica de valor.** Verificado: una "mínima cuantía" de 2.115 bn COP (Personería de Viterbo, Caldas) y una subasta de 2.386 bn (Gobernación de Boyacá) — imposibles, un solo contrato ≈ 25 % del valor departamental. Sin tope, el "top proveedor" de Caldas y Boyacá era una persona natural con un contrato mal digitado. **Regla para `core`:** winsorizar/marcar valores > 5×10¹¹ COP y todo ranking por valor debe declararlo. (Refuerza RF-19: el error absurdo de valor es en sí una señal de opacidad.)
2. **La concentración real a nivel departamento es moderada** una vez capada (top-1 ≤ 5,4 %, top-5 ≤ 16 %): el winner share (RF-05) debe computarse a nivel **entidad**, como dice el catálogo — a nivel departamento se diluye.
3. **La opacidad (RF-19, componentes 'No Definido' y valor 0) no discrimina entre departamentos** en SECOP II 2022+ (0,2–1,6 % en todos): es un control por entidad, no un criterio de selección territorial.
4. **`proveedores_unicos_con` / `respuestas_al_procedimiento` discriminan bien** (Nariño 9,4 % vs Arauca 66,7 %) — la base del RF-01 es confiable como campo, aunque cada caso a publicar exige verificación contra expediente (regla del catálogo).

## 5. Qué NO cubre este análisis

- **SECOP I** (`f789-7hwg`): la ventana 2022+ es esencialmente SECOP II; entidades rezagadas en SECOP I quedan subrepresentadas (sesgo declarado, menor cada año).
- Ventana **preelectoral/Ley de Garantías** (RF-08), adiciones (RF-10/11) y winner share por entidad (RF-05): se computarán ya sobre el datastore, dentro del piloto.
- La **causa** del single bidding boyacense (pliegos a la medida, desierta reincidente, mercados capturados por municipio) — eso *es* la investigación del piloto, no este ranking.

## 6. Definición operativa del piloto propuesto

- **Ámbito:** Boyacá — 123 municipios + gobernación + descentralizadas; ventana 2022-01-01 en adelante (cubre el cierre de administraciones 2020–2023 y el arranque de 2024–2027).
- **Indicador ancla:** RF-01 single bidding (municipio, entidad y modalidad), con RF-02 (directa, gobernación y alcaldías grandes) y RF-04 (control por mercado local) como acompañantes; RF-19 como control de evaluabilidad por entidad.
- **Primera pregunta de investigación:** ¿qué explica que 2 de cada 3 licitaciones públicas en Boyacá reciban un solo oferente, y en qué municipios/mercados se concentra?
