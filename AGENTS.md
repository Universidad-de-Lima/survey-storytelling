# Proyecto
Priorizar:
- delegación de eventos
- reutilización de componentes
- separación entre datos y renderizado
- separación entre configuración y lógica

---

# Reglas JSON

Los JSON deben:
- permanecer compactos
- minimizar redundancia
- evitar anidamientos innecesarios
- mantener compatibilidad backward
- mantener contratos consistentes
- estar desacoplados del layout visual

Nunca:
- generar payloads innecesariamente grandes
- duplicar metadata repetitiva
- acoplar JSON a implementaciones visuales específicas

---

# Reglas ETL

build_json.py:
- es la única fuente oficial de transformación
- debe permanecer idempotente
- debe validar columnas esperadas
- debe fallar explícitamente ante CSV inválidos
- debe minimizar procesamiento redundante
- debe generar estructuras consistentes

Nunca modificar manualmente JSON generados.

---

# Reglas GitHub Actions

Los workflows deben:
- minimizar commits innecesarios
- evitar loops automáticos
- evitar regeneraciones redundantes
- validar paths antes de commit
- minimizar tiempo de ejecución
- minimizar uso innecesario de runners

---

# Estrategia de refactor

No realizar reescrituras completas salvo necesidad crítica.

Priorizar:
- refactors incrementales
- modularización progresiva
- extracción de utilidades compartidas
- reducción de duplicación
- estabilización de contratos
- desacoplamiento progresivo

Evitar:
- breaking changes innecesarios
- abstracciones prematuras
- sobreingeniería
- cambios masivos innecesarios

---

# Estándares de respuesta

Toda respuesta técnica debe incluir:
- diagnóstico
- causa raíz
- impacto técnico
- riesgos
- archivos afectados
- compatibilidad backward
- solución concreta
- rutas reales

Nunca responder con recomendaciones genéricas si el repositorio puede inspeccionarse primero.