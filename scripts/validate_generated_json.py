import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent / "zoho-survey" / "students"

REQUIRED_PERIOD_FILES = {
    "dashboard_data.json": dict(type=dict, non_empty=True),
    "dimensiones.json": dict(type=list, non_empty=True),
    "ids.json": dict(type=list, non_empty=True),
    "nps_ciclo_carrera.json": dict(type=list, non_empty=True),
    "csat_ciclo_carrera.json": dict(type=list, non_empty=True),
    "filtros.json": dict(type=dict, non_empty=True),
    "sentimiento.json": dict(type=dict, non_empty=True),
}

# Estos archivos se siguen permitiendo por compatibilidad historica, pero el
# frontend actual no debe depender de ellos como contrato obligatorio.
LEGACY_PERIOD_FILES = {
    "nps.json": dict(type=dict, non_empty=True),
    "csat.json": dict(type=dict, non_empty=True),
    "nps_carrera.json": dict(type=list, non_empty=True),
    "csat_carrera.json": dict(type=list, non_empty=True),
    "resumen.json": dict(type=dict, non_empty=True),
}

SAT_KEYS = {
    "Totalmente satisfecho",
    "Muy satisfecho",
    "Satisfecho",
    "Insatisfecho",
    "Totalmente insatisfecho",
}
VISIBILITY_KEYS = {"No utilizo", "No conozco"}
REQUIRED_RESPONSE_KEYS = SAT_KEYS | VISIBILITY_KEYS

REQUIRED_DASHBOARD_KEYS = {"resumen", "hallazgos", "nps", "csat"}
REQUIRED_RESUMEN_KEYS = {"encuestas", "fecha_inicio", "fecha_fin", "nps", "csat"}
REQUIRED_SCORE_KEYS = {"score"}
REQUIRED_HALLAZGOS_KEYS = {
    "csat_pct", "nps_score", "nps_tipo", "nps_etapas", "tendencia", "delta",
}
REQUIRED_FILTROS_KEYS = {"has_ciclo", "facultades", "carreras", "ciclos", "facultad_carrera"}
REQUIRED_DIMENSION_KEYS = {
    "facultad", "carrera", "ciclo", "categoria", "dimension",
    "t3b", "b2b", "total", "t3b_pct", "no_utilizo", "no_conozco",
} | REQUIRED_RESPONSE_KEYS
REQUIRED_ID_KEYS = {"facultad", "carrera", "ciclo", "count"}
REQUIRED_CROSS_KEYS = {"facultad", "carrera", "ciclo"}
REQUIRED_SENTIMIENTO_KEYS = {"resumen", "topicos", "por_carrera", "por_ciclo"}
REQUIRED_SENTIMIENTO_RESUMEN_KEYS = {
    "total_con_comentario", "total_analizados", "pasivos", "detractores", "nota",
}
REQUIRED_TOPICO_KEYS = {
    "topico", "tipo", "icono", "total_comentarios", "por_facultad",
    "por_carrera", "por_ciclo", "frases_representativas",
}


def load_json(path):
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise ValueError(f"no se pudo leer: {exc}") from exc

    if not text.strip():
        raise ValueError("archivo vacio")

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON invalido: {exc}") from exc


def validate_shape(value, expected_type, non_empty):
    if not isinstance(value, expected_type):
        raise ValueError(f"se esperaba {expected_type.__name__}, se encontro {type(value).__name__}")
    if non_empty and not value:
        raise ValueError("estructura vacia")


def require_keys(value, keys, label):
    if not isinstance(value, dict):
        raise ValueError(f"{label} debe ser objeto")
    missing = keys - value.keys()
    if missing:
        raise ValueError(f"{label} sin claves requeridas: {sorted(missing)}")


def require_numeric(value, keys, label):
    for key in keys:
        if not isinstance(value.get(key), (int, float)):
            raise ValueError(f"{label}.{key} debe ser numerico")


def validate_dashboard(value):
    require_keys(value, REQUIRED_DASHBOARD_KEYS, "dashboard_data.json")
    resumen = value.get("resumen") or {}
    hallazgos = value.get("hallazgos") or {}

    require_keys(resumen, REQUIRED_RESUMEN_KEYS, "dashboard_data.resumen")
    if "año" not in resumen and "ano" not in resumen:
        raise ValueError("dashboard_data.resumen sin clave requerida: año")
    require_keys(hallazgos, REQUIRED_HALLAZGOS_KEYS, "dashboard_data.hallazgos")
    require_keys(resumen.get("nps") or {}, REQUIRED_SCORE_KEYS, "dashboard_data.resumen.nps")
    require_keys(resumen.get("csat") or {}, REQUIRED_SCORE_KEYS, "dashboard_data.resumen.csat")
    require_numeric(resumen, {"encuestas"}, "dashboard_data.resumen")
    require_numeric(resumen["nps"], {"score"}, "dashboard_data.resumen.nps")
    require_numeric(resumen["csat"], {"score"}, "dashboard_data.resumen.csat")
    require_numeric(hallazgos, {"csat_pct", "nps_score", "delta"}, "dashboard_data.hallazgos")

    for key in ("Promotores", "Pasivos", "Detractores"):
        if key not in value["nps"]:
            raise ValueError(f"dashboard_data.nps sin clave requerida: {key}")
    missing_csat = SAT_KEYS - value["csat"].keys()
    if missing_csat:
        raise ValueError(f"dashboard_data.csat sin claves requeridas: {sorted(missing_csat)}")


def validate_filtros(value):
    require_keys(value, REQUIRED_FILTROS_KEYS, "filtros.json")
    has_ciclo = value.get("has_ciclo", True)

    for key in ("facultades", "carreras"):
        if not isinstance(value.get(key), list) or not value[key]:
            raise ValueError(f"filtros.{key} debe ser una lista no vacia")
        if not all(isinstance(item, str) and item.strip() for item in value[key]):
            raise ValueError(f"filtros.{key} debe contener textos no vacios")

    # Ciclo es opcional: si has_ciclo=false, puede estar vacio
    if not isinstance(value.get("ciclos"), list):
        raise ValueError("filtros.ciclos debe ser una lista")
    if has_ciclo and not value["ciclos"]:
        raise ValueError("filtros.ciclos debe ser una lista no vacia cuando has_ciclo=true")
    if value["ciclos"] and not all(isinstance(item, str) and item.strip() for item in value["ciclos"]):
        raise ValueError("filtros.ciclos debe contener textos no vacios")

    facultad_carrera = value.get("facultad_carrera")
    if not isinstance(facultad_carrera, dict) or not facultad_carrera:
        raise ValueError("filtros.facultad_carrera debe ser un objeto no vacio")
    for facultad in value["facultades"]:
        if facultad not in facultad_carrera:
            raise ValueError(f"filtros.facultad_carrera no incluye facultad: {facultad}")
        if not isinstance(facultad_carrera[facultad], list):
            raise ValueError(f"filtros.facultad_carrera.{facultad} debe ser lista")


def validate_dimensiones(value):
    rows_with_data = 0
    for index, row in enumerate(value):
        if not isinstance(row, dict):
            raise ValueError(f"dimensiones[{index}] debe ser objeto")
        require_keys(row, REQUIRED_DIMENSION_KEYS, f"dimensiones[{index}]")
        require_numeric(row, {"t3b", "b2b", "total", "t3b_pct", "no_utilizo", "no_conozco"}, f"dimensiones[{index}]")
        require_numeric(row, REQUIRED_RESPONSE_KEYS, f"dimensiones[{index}]")
        if row.get("total", 0) > 0:
            rows_with_data += 1

    if not rows_with_data:
        raise ValueError("dimensiones.json no contiene filas con total > 0")


def validate_id_rows(value, filename):
    total = 0
    for index, row in enumerate(value):
        if not isinstance(row, dict):
            raise ValueError(f"{filename}[{index}] debe ser objeto")
        require_keys(row, REQUIRED_ID_KEYS, f"{filename}[{index}]")
        require_numeric(row, {"count"}, f"{filename}[{index}]")
        total += row.get("count", 0)
    if total <= 0:
        raise ValueError(f"{filename} no contiene conteos positivos")


def validate_cross_rows(value, filename, response_keys):
    required_keys = REQUIRED_CROSS_KEYS | set(response_keys)
    for index, row in enumerate(value):
        if not isinstance(row, dict):
            raise ValueError(f"{filename}[{index}] debe ser objeto")
        require_keys(row, required_keys, f"{filename}[{index}]")
        require_numeric(row, response_keys, f"{filename}[{index}]")


def validate_sentimiento(value):
    require_keys(value, REQUIRED_SENTIMIENTO_KEYS, "sentimiento.json")
    require_keys(value.get("resumen") or {}, REQUIRED_SENTIMIENTO_RESUMEN_KEYS, "sentimiento.resumen")
    require_numeric(value["resumen"], {"total_con_comentario", "total_analizados", "pasivos", "detractores"}, "sentimiento.resumen")

    for key in ("topicos", "por_carrera", "por_ciclo"):
        if not isinstance(value.get(key), list):
            raise ValueError(f"sentimiento.{key} debe ser lista")

    for index, topico in enumerate(value["topicos"]):
        if not isinstance(topico, dict):
            raise ValueError(f"sentimiento.topicos[{index}] debe ser objeto")
        require_keys(topico, REQUIRED_TOPICO_KEYS, f"sentimiento.topicos[{index}]")
        if topico.get("tipo") not in {"negativo", "mejora", "positivo"}:
            raise ValueError(f"sentimiento.topicos[{index}].tipo invalido")
        require_numeric(topico, {"total_comentarios"}, f"sentimiento.topicos[{index}]")
        for map_key in ("por_facultad", "por_carrera", "por_ciclo"):
            if not isinstance(topico.get(map_key), dict):
                raise ValueError(f"sentimiento.topicos[{index}].{map_key} debe ser objeto")


def validate_period_html(period_dir):
    path = period_dir / "index.html"
    if not path.exists():
        return [f"{path}: archivo requerido ausente"]
    try:
        html = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{path}: no se pudo leer: {exc}"]

    required_fragments = [
        '<a href="#sentimiento">Cualitativo</a>',
        'ANALISIS CUALITATIVO',
        'id="sentimiento"',
        'id="sentimiento-heading"',
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


def validate_json_file(json_dir, filename, spec):
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


def validate_period(period_dir):
    errors = []
    warnings = []
    json_dir = period_dir / "json"
    if not json_dir.is_dir():
        return [f"{period_dir}: no existe carpeta json"], warnings

    errors.extend(validate_period_html(period_dir))

    # Leer filtros.json primero para conocer has_ciclo
    has_ciclo = True
    filtros_path = json_dir / "filtros.json"
    if filtros_path.exists():
        try:
            filtros_val = load_json(filtros_path)
            has_ciclo = filtros_val.get("has_ciclo", True)
        except Exception:
            pass

    required = dict(REQUIRED_PERIOD_FILES)
    # Si no hay ciclo, nps_ciclo_carrera y csat_ciclo_carrera pueden estar vacios
    if not has_ciclo:
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
            errors.append(f"{path}: archivo legado invalido: {exc}")
        else:
            warnings.append(f"{path}: archivo legado/deprecado; no debe ser contrato obligatorio")

    return errors, warnings


def read_periods(level_dir):
    periodos_path = level_dir / "periodos.json"
    periodos = load_json(periodos_path)
    if not isinstance(periodos, list) or not periodos:
        raise ValueError(f"{periodos_path}: debe ser una lista no vacia")

    ids = []
    seen = set()
    new_count = 0
    for item in periodos:
        if not isinstance(item, dict) or not item.get("id"):
            raise ValueError(f"{periodos_path}: cada periodo debe tener id")
        period_id = str(item["id"])
        if period_id in seen:
            raise ValueError(f"{periodos_path}: periodo duplicado: {period_id}")
        seen.add(period_id)
        ids.append(period_id)
        if item.get("isNew") is True:
            new_count += 1

    if new_count != 1:
        raise ValueError(f"{periodos_path}: debe existir exactamente un periodo con isNew=true")

    return ids


def main():
    levels = sys.argv[1:] or ["undergraduate"]
    all_errors = []
    all_warnings = []

    for level in levels:
        level_dir = ROOT_DIR / level
        if not level_dir.is_dir():
            all_errors.append(f"{level_dir}: nivel inexistente")
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

    print("Contratos JSON validos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
