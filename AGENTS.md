# Reglas Para Agentes IA

Este archivo define reglas operativas obligatorias para agentes que inspeccionan o modifican el repositorio.

## Fuentes Canonicas

- `README.md`: entrada general y mapa documental.
- `ARCHITECTURE.md`: arquitectura tecnica, capas, modulos y deuda vigente.
- `CONTRACTS.md`: contratos CSV/JSON e invariantes de datos.
- `docs/developer-guide.md`: guia operativa corta para cambios comunes.
- `tests/README.md`: ejecucion y extension de tests.

No duplicar estas fuentes en nuevos documentos.

## Principios Del Proyecto

Priorizar:

- delegacion de eventos
- reutilizacion de componentes
- separacion entre datos y renderizado
- separacion entre configuracion y logica
- cambios incrementales y verificables

Evitar:

- reescrituras completas sin necesidad critica
- breaking changes innecesarios
- abstracciones prematuras
- sobreingenieria
- documentos nuevos si uno existente puede actualizarse

## Reglas JSON

Los JSON generados deben:

- permanecer compactos
- minimizar redundancia
- evitar anidamientos innecesarios
- mantener compatibilidad backward
- mantener contratos consistentes
- estar desacoplados del layout visual

Nunca:

- modificar manualmente JSON generados
- generar payloads innecesariamente grandes
- duplicar metadata repetitiva
- acoplar JSON a implementaciones visuales especificas

## Reglas ETL

`zoho-survey/scripts/build_json.py` es la unica fuente oficial de transformacion.

Debe:

- permanecer idempotente
- validar columnas esperadas
- fallar explicitamente ante CSV invalidos
- minimizar procesamiento redundante
- generar estructuras consistentes con `CONTRACTS.md`

## Reglas Frontend

- Mantener Vanilla JS e IIFE con APIs `window.Survey*`.
- No introducir frameworks frontend ni dependencias runtime sin decision explicita.
- Sanitizar contenido externo antes de usar `innerHTML`.
- Mantener compatibilidad con GitHub Pages y navegadores modernos.

## Reglas GitHub Actions

Los workflows deben:

- minimizar commits innecesarios
- evitar loops automaticos
- evitar regeneraciones redundantes
- validar paths antes de commit
- minimizar tiempo de ejecucion y uso de runners

## Respuestas Tecnicas

Antes de recomendar cambios, inspeccionar el repositorio cuando sea posible.

Toda respuesta tecnica debe incluir, cuando aplique:

- diagnostico
- causa raiz
- impacto tecnico
- riesgos
- archivos afectados
- compatibilidad backward
- solucion concreta
- rutas reales
