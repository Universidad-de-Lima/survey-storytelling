# Logica de filtros del dashboard

Este documento captura la logica de filtros cascada en `shared/js/dashboard.js` alineada con la matriz FACULTAD / CARRERA / CICLO del negocio.

## Grupos de filtros

El HTML usa grupos identificados por sufijo:

| Sufijo        | Seccion                  | Elementos esperados             |
| ------------- | ------------------------ | ------------------------------- |
| `top3`        | Operativo - barras Top 3 | facultad, carrera, ciclo, reset |
| `radar`       | Operativo - radar        | facultad, carrera, ciclo, reset |
| `preguntas`   | Detallado - preguntas    | facultad, carrera, ciclo, reset |
| `detalle`     | Detallado - carrera      | facultad, ciclo, reset          |
| `visibilidad` | Detallado - visibilidad  | facultad, carrera, ciclo, reset |
| `sent`        | Cualitativo              | facultad, carrera, ciclo, reset |

La convencion de IDs es:

- `filter-facultad-<sufijo>`
- `filter-carrera-<sufijo>`
- `filter-ciclo-<sufijo>`
- `reset-<sufijo>`

## Matriz de combinaciones validas

Los tres filtros son independientes en el sentido de que cualquier combinacion de "Todas/Todos" o valor especifico es valida:

| FACULTAD                       | CARRERA                   | CICLO              |
| ------------------------------ | ------------------------- | ------------------ |
| Todas                          | Todas                     | Todos              |
| Todas                          | Todas                     | (ciclo especifico) |
| Todas                          | (carrera especifica)      | Todos              |
| Todas                          | (carrera especifica)      | (ciclo especifico) |
| (facultad especifica)          | Todas                     | Todos              |
| (facultad especifica)          | Todas                     | (ciclo especifico) |
| (facultad especifica)          | (carrera de esa facultad) | Todos              |
| (facultad especifica)          | (carrera de esa facultad) | (ciclo especifico) |
| Programa de Estudios Generales | Todas                     | Todos              |

El filtrado de datos (`filtrarDatos`) aplica AND entre los criterios activos (valor no vacio).

## Cascada de listas desplegables

1. **Facultad** se llena desde `filtros.facultades` mas `Programa de Estudios Generales` (siempre primero en UI).
2. **Carrera**:
   - Sin facultad o con Estudios Generales: lista global `filtros.carreras`.
   - Con otra facultad: solo carreras de `filtros.facultad_carrera[facultad]`.
3. **Ciclo** (opciones del selector, no el filtro aplicado):
   - Sin facultad ni carrera: todos los ciclos de `filtros.ciclos`.
   - Con seleccion: `getCiclosForFiltro(facultad, carrera)` segun consideraciones.
4. Cualquier cambio en facultad, carrera o ciclo dispara `updateCascade` (repobla listas y re-renderiza la seccion).

## CONSIDERACIONES (rango de ciclos en el selector)

| Condicion                                                        | Ciclos en lista |
| ---------------------------------------------------------------- | --------------- |
| Facultad = Programa de Estudios Generales                        | 1° y 2°         |
| Carrera = Derecho o Psicologia, o facultad de Derecho/Psicologia | 1° al 12°       |
| Otras carreras / facultades                                      | 1° al 10°       |

Al filtrar datos con Estudios Generales seleccionado, solo se incluyen filas con ciclo 1° o 2° aunque el usuario no elija ciclo.

## Cualitativo (limitacion)

`sentimiento.json` expone conteos por facultad, carrera y ciclo por separado. La seccion cualitativa prioriza carrera > facultad > ciclo (no interseccion exacta fila a fila). Estudios Generales usa la suma de ciclos 1° y 2° en `por_ciclo`.

## Riesgo de rendimiento

Las secciones `top3`, `radar`, `preguntas` y `visibilidad` filtran `dimensiones.json` en runtime. Roadmap: precalcular agregados en ETL y mover reglas de ciclo a `filtros.json`.

## Invariantes que no deben romperse

- Los IDs HTML son contrato publico para `dashboard.js`.
- `#sentimiento` se conserva como ID tecnico aunque la etiqueta visible sea `Cualitativo`.
- Los filtros deben poder inicializarse aunque una seccion no tenga selector de carrera.
- `periodos.json` debe tener exactamente un periodo con `isNew: true`.
