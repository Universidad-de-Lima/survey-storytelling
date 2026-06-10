"""
SURVEY VALIDATION — Validador de contratos de datos para encuestas.

Inspecciona los archivos JSON generados para cada periodo y nivel, asegurando
que cumplan con los tipos, claves y restricciones de los contratos v2.0.
También valida que los index.html tengan las secciones cualitativas requeridas.
"""

import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Reutilizar I/O helper y configuraciones centrales
from lib.config import RESPUESTAS_TEXTO
from lib.io_helper import load_json

BASE_DIR: Path = Path(__file__).resolve().parent
ROOT_DIR: Path = BASE_DIR.parent / "students"

REQUIRED_PERIOD_FILES: Dict[str, Dict[str, any]] = {
    "dashboard_data.json": dict(type=dict, non_empty=True),
    "dimensiones.json": dict(type=list, non_empty=True),
    "ids.json": dict(type=list, non_empty=True),
    "nps_ciclo_carrera.json": dict(type=list, non_empty=True),
    "csat_ciclo_carrera.json": dict(type=list, non_empty=True),
    "filtros.json": dict(type=dict, non_empty=True),
    "sentimiento.json": dict(type=dict, non_empty=True),
}

# Archivos legacy: validados si existen, pero su ausencia no genera error
LEGACY_PERIOD_FILES: Dict[str, Dict[str, any]] = {
    "nps_carrera.json": dict(type=list, non_empty=True),
    "csat_carrera.json": dict(type=list, non_empty=True),
}

# Derivar llaves de respuestas del catálogo central
SAT_KEYS: Set[str] = set(RESPUESTAS_TEXTO[:5])
VISIBILITY_KEYS: Set[str] = set(RESPUESTAS_TEXTO[5:7])
REQUIRED_RESPONSE_KEYS: Set[str] = SAT_KEYS | VISIBILITY_KEYS

REQUIRED_DASHBOARD_KEYS: Set[str] = {"resumen", "hallazgos", "nps", "csat"}
REQUIRED_RESUMEN_KEYS: Set[str] = {"encuestas", "fecha_inicio", "fecha_fin", "nps", "csat"}
REQUIRED_SCORE_KEYS: Set[str] = {"score"}
REQUIRED_HALLAZGOS_KEYS: Set[str] = {
    "csat_pct", "nps_score", "nps_tipo", "nps_etapas", "tendencia", "delta",
}
REQUIRED_FILTROS_KEYS: Set[str] = {"has_ciclo", "facultades", "carreras", "ciclos", "facultad_carrera"}
REQUIRED_DIMENSION_KEYS: Set[str] = (
    {"facultad", "carrera", "ciclo", "categoria", "dimension", "t3b", "b2b", "total", "t3b_pct", "no_utilizo", "no_conozco"}
    | REQUIRED_RESPONSE_KEYS
)
REQUIRED_ID_KEYS: Set[str] = {"facultad", "carrera", "ciclo", "count"}
REQUIRED_CROSS_KEYS: Set[str] = {"facultad", "carrera", "ciclo"}
REQUIRED_SENTIMIENTO_KEYS: Set[str] = {"resumen", "topicos", "por_carrera", "por_ciclo"}
REQUIRED_SENTIMIENTO_RESUMEN_KEYS: Set[str] = {
    "total_con_comentario", "total_analizados", "pasivos", "detractores", "nota",
}
REQUIRED_TOPICO_KEYS: Set[str] = {
    "topico", "tipo", "icono", "total_comentarios", "por_facultad",
    "por_carrera", "por_ciclo", "frases_representativas",
}


def validate_shape(value: any, expected_type: type, non_empty: bool) -> None:
    """Verifica que un valor coincida con el tipo y restricción de vacío esperados."""
    if not isinstance(value, expected_type):
        raise ValueError(f"se esperaba {expected_type.__name__}, se encontró {type(value).__name__}")
    if non_empty and not value:
        raise ValueError("estructura vacía")


def require_keys(value: any, keys: Set[str], label: str) -> None:
    """Valida la presencia de un set de llaves requeridas dentro de un objeto/diccionario."""
    if not isinstance(value, dict):
        raise ValueError(f"{label} debe ser un objeto")
    missing = keys - value.keys()
    if missing:
        raise ValueError(f"{label} no contiene las llaves requeridas: {sorted(missing)}")


def require_numeric(value: dict, keys: Set[str], label: str) -> None:
    """Valida que los campos declarados dentro de un diccionario sean valores numéricos."""
    for key in keys:
        if not isinstance(value.get(key), (int, float)):
            raise ValueError(f"{label}.{key} debe ser numérico")


def validate_dashboard(value: dict) -> None:
    """Valida la estructura interna de dashboard_data.json."""
    require_keys(value, REQUIRED_DASHBOARD_KEYS, "dashboard_data.json")
    resumen = value.get("resumen") or {}
    hallazgos = value.get("hallazgos") or {}

    require_keys(resumen, REQUIRED_RESUMEN_KEYS, "dashboard_data.resumen")
    if "año" not in resumen and "ano" not in resumen:
        raise ValueError("dashboard_data.resumen no contiene la llave año")
        
    require_keys(hallazgos, REQUIRED_HALLAZGOS_KEYS, "dashboard_data.hallazgos")
    require_keys(resumen.get("nps") or {}, REQUIRED_SCORE_KEYS, "dashboard_data.resumen.nps")
    require_keys(resumen.get("csat") or {}, REQUIRED_SCORE_KEYS, "dashboard_data.resumen.csat")
    
    require_numeric(resumen, {"encuestas"}, "dashboard_data.resumen")
    require_numeric(resumen["nps"], {"score"}, "dashboard_data.resumen.nps")
    require_numeric(resumen["csat"], {"score"}, "dashboard_data.resumen.csat")
    require_numeric(hallazgos, {"csat_pct", "nps_score", "delta"}, "dashboard_data.hallazgos")

    for key in ("Promotores", "Pasivos", "Detractores"):
        if key not in value["nps"]:
            raise ValueError(f"dashboard_data.nps no contiene la llave requerida: {key}")
            
    missing_csat = SAT_KEYS - value["csat"].keys()
    if missing_csat:
        raise ValueError(f"dashboard_data.csat no contiene las llaves requeridas: {sorted(missing_csat)}")


def validate_filtros(value: dict) -> None:
    """Valida el contenido y coherencia del archivo filtros.json."""
    require_keys(value, REQUIRED_FILTROS_KEYS, "filtros.json")
    has_ciclo = value.get("has_ciclo", True)

    for key in ("facultades", "carreras"):
        if not isinstance(value.get(key), list) or not value[key]:
            raise ValueError(f"filtros.{key} debe ser una lista no vacía")
        if not all(isinstance(item, str) and item.strip() for item in value[key]):
            raise ValueError(f"filtros.{key} debe contener únicamente textos no vacíos")

    if not isinstance(value.get("ciclos"), list):
        raise ValueError("filtros.ciclos debe ser una lista")
    if has_ciclo and not value["ciclos"]:
        raise ValueError("filtros.ciclos debe ser una lista no vacía cuando has_ciclo=true")
    if value["ciclos"] and not all(isinstance(item, str) and item.strip() for item in value["ciclos"]):
        raise ValueError("filtros.ciclos debe contener únicamente textos no vacíos")

    facultad_carrera = value.get("facultad_carrera")
    if not isinstance(facultad_carrera, dict) or not facultad_carrera:
        raise ValueError("filtros.facultad_carrera debe ser un objeto no vacío")
        
    for facultad in value["facultades"]:
        if facultad not in facultad_carrera:
            raise ValueError(f"filtros.facultad_carrera no mapea la facultad: {facultad}")
        if not isinstance(facultad_carrera[facultad], list):
            raise ValueError(f"filtros.facultad_carrera.{facultad} debe ser una lista")


def validate_dimensiones(value: List[dict]) -> None:
    """Valida los agregados de dimensiones.json."""
    rows_with_data = 0
    for index, row in enumerate(value):
        if not isinstance(row, dict):
            raise ValueError(f"dimensiones[{index}] debe ser un objeto")
        require_keys(row, REQUIRED_DIMENSION_KEYS, f"dimensiones[{index}]")
        require_numeric(row, {"t3b", "b2b", "total", "t3b_pct", "no_utilizo", "no_conozco"}, f"dimensiones[{index}]")
        require_numeric(row, REQUIRED_RESPONSE_KEYS, f"dimensiones[{index}]")
        if row.get("total", 0) > 0:
            rows_with_data += 1

    if not rows_with_data:
        raise ValueError("dimensiones.json no contiene filas válidas con total > 0")


def validate_id_rows(value: List[dict], filename: str) -> None:
    """Valida que los registros de conteo contengan valores positivos sumados."""
    total = 0
    for index, row in enumerate(value):
        if not isinstance(row, dict):
            raise ValueError(f"{filename}[{index}] debe ser un objeto")
        require_keys(row, REQUIRED_ID_KEYS, f"{filename}[{index}]")
        require_numeric(row, {"count"}, f"{filename}[{index}]")
        total += row.get("count", 0)
    if total <= 0:
        raise ValueError(f"{filename} no contiene conteos acumulados positivos")


def validate_cross_rows(value: List[dict], filename: str, response_keys: Set[str]) -> None:
    """Valida la integridad de las llaves cruzadas en los archivos combinados de ciclo y carrera."""
    required_keys = REQUIRED_CROSS_KEYS | response_keys
    for index, row in enumerate(value):
        if not isinstance(row, dict):
            raise ValueError(f"{filename}[{index}] debe ser un objeto")
        require_keys(row, required_keys, f"{filename}[{index}]")
        require_numeric(row, response_keys, f"{filename}[{index}]")


def validate_sentimiento(value: dict) -> None:
    """Valida la estructura de tópicos del archivo sentimiento.json."""
    require_keys(value, REQUIRED_SENTIMIENTO_KEYS, "sentimiento.json")
    require_keys(value.get("resumen") or {}, REQUIRED_SENTIMIENTO_RESUMEN_KEYS, "sentimiento.resumen")
    require_numeric(value["resumen"], {"total_con_comentario", "total_analizados", "pasivos", "detractores"}, "sentimiento.resumen")

    for key in ("topicos", "por_carrera", "por_ciclo"):
        if not isinstance(value.get(key), list):
            raise ValueError(f"sentimiento.{key} debe ser una lista")

    for index, topico in enumerate(value["topicos"]):
        if not isinstance(topico, dict):
            raise ValueError(f"sentimiento.topicos[{index}] debe ser un objeto")
        require_keys(topico, REQUIRED_TOPICO_KEYS, f"sentimiento.topicos[{index}]")
        if topico.get("tipo") not in {"negativo", "mejora", "positivo"}:
            raise ValueError(f"sentimiento.topicos[{index}].tipo tiene un valor inválido: {topico.get('tipo')}")
        require_numeric(topico, {"total_comentarios"}, f"sentimiento.topicos[{index}]")
        for map_key in ("por_facultad", "por_carrera", "por_ciclo"):
            if not isinstance(topico.get(map_key), dict):
                raise ValueError(f"sentimiento.topicos[{index}].{map_key} debe ser un objeto")


def validate_period_html(period_dir: Path) -> List[str]:
    """Verifica que el index.html del periodo contenga los enlaces y contenedores del módulo cualitativo."""
    path = period_dir / "index.html"
    if not path.exists():
        return [f"{path}: archivo index.html requerido ausente"]
    try:
        html = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{path}: no se pudo leer el archivo: {exc}"]

    required_fragments = [
        '<a href="#cualitativo">Cualitativo</a>',
        'ANALISIS CUALITATIVO',
        'id="cualitativo"',
        'id="cualitativo-heading"',
    ]
    normalized = (
        html.replace("Á", "A")
            .replace("É", "E")
            .replace("Í", "I")
            .replace("Ó", "O")
            .replace("Ú", "U")
    )
    errors = []
    for fragment in required_fragments:
        if fragment not in normalized and fragment not in html:
            errors.append(f"{path}: no contiene fragmento requerido: {fragment}")
    return errors


def validate_json_file(json_dir: Path, filename: str, spec: Dict[str, any]) -> any:
    """Carga y valida un archivo JSON individual según las especificaciones de su contrato."""
    path = json_dir / filename
    if not path.exists():
        raise ValueError("archivo requerido ausente")
    value = load_json(path)
    validate_shape(value, spec["type"], spec["non_empty"])

    if filename == "dashboard_data.json":
        validate_dashboard(value)
    elif filename == "filtros.json":
        validate_filtros(value)
    elif filename == "dimensiones.json":
        validate_dimensiones(value)
    elif filename == "ids.json":
        validate_id_rows(value, filename)
    elif filename == "nps_ciclo_carrera.json":
        validate_cross_rows(value, filename, {"Promotores", "Pasivos", "Detractores"})
    elif filename == "csat_ciclo_carrera.json":
        validate_cross_rows(value, filename, SAT_KEYS)
    elif filename == "sentimiento.json":
        validate_sentimiento(value)

    return value


def validate_period(period_dir: Path) -> Tuple[List[str], List[str]]:
    """Valida por completo un directorio de periodo (JSONs y index.html)."""
    errors = []
    warnings = []
    json_dir = period_dir / "json"
    if not json_dir.is_dir():
        return [f"{period_dir}: no existe carpeta json"], warnings

    errors.extend(validate_period_html(period_dir))

    # Descubrir has_ciclo leyendo filtros.json primero
    has_ciclo = True
    filtros_path = json_dir / "filtros.json"
    if filtros_path.exists():
        try:
            filtros_val = load_json(filtros_path)
            has_ciclo = filtros_val.get("has_ciclo", True)
        except Exception:
            pass

    required = dict(REQUIRED_PERIOD_FILES)
    if not has_ciclo:
        # Si no hay ciclos escolares, estos archivos pueden estar vacíos
        required["nps_ciclo_carrera.json"] = dict(type=list, non_empty=False)
        required["csat_ciclo_carrera.json"] = dict(type=list, non_empty=False)

    for filename, spec in required.items():
        path = json_dir / filename
        try:
            validate_json_file(json_dir, filename, spec)
        except ValueError as exc:
            errors.append(f"{path}: {exc}")

    for filename, spec in LEGACY_PERIOD_FILES.items():
        path = json_dir / filename
        if not path.exists():
            continue
        try:
            value = load_json(path)
            validate_shape(value, spec["type"], spec["non_empty"])
        except ValueError as exc:
            errors.append(f"{path}: archivo legado inválido: {exc}")
        else:
            warnings.append(f"{path}: archivo legado/deprecado; no debe ser contrato obligatorio")

    return errors, warnings


def read_periods(level_dir: Path) -> List[str]:
    """Lee y valida el catálogo periodos.json de un nivel académico."""
    periodos_path = level_dir / "periodos.json"
    periodos = load_json(periodos_path)
    if not isinstance(periodos, list) or not periodos:
        raise ValueError(f"{periodos_path}: debe ser una lista no vacía")

    ids = []
    seen = set()
    new_count = 0
    for item in periodos:
        if not isinstance(item, dict) or not item.get("id"):
            raise ValueError(f"{periodos_path}: cada periodo debe tener la llave id")
        period_id = str(item["id"])
        if period_id in seen:
            raise ValueError(f"{periodos_path}: periodo duplicado detectado: {period_id}")
        seen.add(period_id)
        ids.append(period_id)
        if item.get("isNew") is True:
            new_count += 1

    if new_count != 1:
        raise ValueError(f"{periodos_path}: debe existir exactamente un periodo con la propiedad isNew=true")

    return ids


def main() -> int:
    levels = sys.argv[1:] or ["undergraduate", "graduate"]
    all_errors = []
    all_warnings = []

    for level in levels:
        level_dir = ROOT_DIR / level
        if not level_dir.is_dir():
            all_errors.append(f"{level_dir}: nivel académico inexistente")
            continue

        try:
            period_ids = read_periods(level_dir)
        except ValueError as exc:
            all_errors.append(str(exc))
            continue

        for period_id in period_ids:
            errors, warnings = validate_period(level_dir / period_id)
            all_errors.extend(errors)
            all_warnings.extend(warnings)

    if all_warnings:
        print("Advertencias de contrato JSON:")
        for warning in all_warnings:
            print(f"- {warning}")

    if all_errors:
        print("Errores de contrato JSON:")
        for err in all_errors:
            print(f"- {err}")
        return 1

    print("Contratos JSON válidos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
