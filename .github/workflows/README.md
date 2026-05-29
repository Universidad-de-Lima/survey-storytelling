# .github/workflows

Pipeline de CI/CD para el módulo de encuestas estudiantiles. Contiene dos workflows de GitHub Actions que automatizan la generación de datos y la validación de contratos.

## Workflows

### `build_students.yml` — Auto-build Survey JSON

**Trigger**: Push a `zoho-survey/students/data/**` o `zoho-survey/students/scripts/**`. También `workflow_dispatch`.

**Job**: `build` on `ubuntu-latest`

**Steps**:
1. Checkout repository
2. Setup Python 3.11
3. Install `pandas`
4. Run `build_json.py`
5. Commit and push generated JSON files

**Risk**: El workflow hace commit automático sin revisión. Si `build_json.py` falla silenciosamente, se commitearían datos corruptos. No hay validación post-build antes del commit.

### `validate-survey-json.yml` — Validate Survey JSON

**Trigger**: Pull request a `zoho-survey/students/**` o `.github/workflows/validate-survey-json.yml`. Push a `main` con cambios en esas rutas.

**Job**: `validate-json` on `ubuntu-latest`

**Steps**:
1. Checkout
2. Setup Python 3.11
3. Run `validate_generated_json.py undergraduate`

**Nota**: Solo valida `undergraduate`. No hay validación para `postgraduate`.

## Technical Debt

- **Solo undergraduate validado**: `validate-survey-json.yml` solo corre validación para pregrado. Posgrado no está cubierto.
- **Sin validación post-build**: `build_students.yml` no ejecuta el validador después de generar JSON, solo hace commit.
- **Commit sin control**: El bot `survey-bot` commitea cambios sin PR ni revisión. Puede introducir cambios no deseados.
- **Sin notificación de fallos**: No hay configuración de alertas si el build o validación fallan.
- **Sin cache de pip**: Cada ejecución reinstala pandas, aumentando el tiempo de ejecución.

## AI Agent Notes

- Ambos workflows usan `ubuntu-latest` y Python 3.11.
- El build workflow usa `git add .` desde `zoho-survey/students`, lo que incluye cualquier cambio no deseado en el directorio.
- El patrón de paths en `on.push.paths` debe actualizarse si se modifican las rutas de los scripts o datos.
- Para debuggear: `workflow_dispatch` permite ejecutar `build_students.yml` manualmente desde la UI de GitHub.
