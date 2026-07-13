"""
SANITIZADOR DE PII — Redacta columnas de identificación directa en CSVs.

Columnas redactadas:
  - Dirección IP
  - Agente Usuario
  - URL de la encuesta a la que accede el encuestado

Estas columnas contienen datos personales identificables (Ley 29733, GDPR).
Se reemplazan con string vacío para preservar estructura CSV sin datos sensibles.

Uso:
  python zoho-survey/scripts/sanitize_csv_pii.py "data/ENCUESTA...csv"
  python zoho-survey/scripts/sanitize_csv_pii.py --all
  # Modifica el archivo in-place (sobreescribe con columnas redactadas)

Modo --check (FM-003 — gate pre-push):
  python zoho-survey/scripts/sanitize_csv_pii.py --check --all
  python zoho-survey/scripts/sanitize_csv_pii.py --check "data/ENCUESTA...csv"
  # Detecta PII sin modificar archivos. Retorna exit code 1 si detecta PII,
  # exit code 0 si todos los CSVs están sanitizados. Pensado para usarse como
  # gate en CI (tests.yml) antes del build del ETL. El gate CI propiamente dicho
  # se activa en una fase posterior (los workflows .github/workflows/*.yml están
  # en zona de exclusión de la Fase 1.7).

Idempotencia:
  Si las columnas PII ya están vacías (CSV previamente sanitizado),
  el script no realiza cambios y retorna exitosamente.
"""

import argparse
import csv
import sys
from pathlib import Path


# Columnas PII a redactar (búsqueda por nombre exacto, case-sensitive).
# Los nombres deben coincidir con los headers exportados por Zoho Survey.
COLUMNAS_PII = [
    "Dirección IP",
    "Agente Usuario",
    "URL de la encuesta a la que accede el encuestado",
]


def _find_pii_columns(headers):
    """Retorna {indice: nombre_columna} para las columnas PII presentes en headers."""
    indices_pii = {}
    for i, h in enumerate(headers):
        h_clean = h.strip().strip('"')
        if h_clean in COLUMNAS_PII:
            indices_pii[i] = h_clean
    return indices_pii


def detect_pii_in_csv(ruta_csv):
    """Detecta PII no redactada en un CSV sin modificar el archivo.

    Retorna una lista de tuplas (columna_pii, fila_numero) para cada celda
    con PII no redactada. Lista vacía si el CSV no tiene PII o ya está sanitizado.
    Retorna None si el archivo no existe o está vacío (error).
    """
    ruta = Path(ruta_csv)
    if not ruta.exists():
        print(f"ERROR: archivo no encontrado: {ruta_csv}", file=sys.stderr)
        return None

    with open(ruta, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        filas = list(reader)

    if not filas:
        print(f"ERROR: archivo vacío: {ruta_csv}", file=sys.stderr)
        return None

    headers = filas[0]
    indices_pii = _find_pii_columns(headers)

    if not indices_pii:
        # No hay columnas PII en este CSV — no es error, no hay PII que detectar.
        return []

    hallazgos = []
    for num_fila, fila in enumerate(filas[1:], start=2):  # fila 1 = header
        for idx, nombre in indices_pii.items():
            if idx < len(fila) and fila[idx].strip():
                hallazgos.append((nombre, num_fila))
    return hallazgos


def sanitizar_csv(ruta_csv: str) -> bool:
    """Redacta columnas PII en un CSV, modificándolo in-place.

    Retorna True si el archivo fue procesado (o ya estaba limpio).
    Retorna False si el archivo no existe o está vacío.
    """
    ruta = Path(ruta_csv)
    if not ruta.exists():
        print(f"ERROR: archivo no encontrado: {ruta_csv}")
        return False

    # Leer todo el CSV en memoria
    with open(ruta, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        filas = list(reader)

    if not filas:
        print(f"ERROR: archivo vacío: {ruta_csv}")
        return False

    headers = filas[0]

    # Identificar índices de columnas PII por nombre exacto
    indices_pii = _find_pii_columns(headers)

    if not indices_pii:
        print(f"INFO: no se encontraron columnas PII en {ruta_csv}. Saltando.")
        return True  # No es error, el archivo ya está limpio

    # Contar redacciones por columna
    cambios_por_col = {nombre: 0 for nombre in indices_pii.values()}

    for fila in filas[1:]:  # Saltar header
        for idx, nombre in indices_pii.items():
            if idx < len(fila) and fila[idx].strip():
                fila[idx] = ""
                cambios_por_col[nombre] += 1

    # Escribir el CSV sanitizado (sobreescribe original)
    with open(ruta, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(filas)

    total_filas = len(filas) - 1  # Sin contar header
    detalle = ", ".join(f"{v} {k}" for k, v in cambios_por_col.items() if v > 0)
    if detalle:
        print(f"✓ {ruta.name}: {total_filas} filas, {detalle} redactadas")
    else:
        print(f"✓ {ruta.name}: {total_filas} filas, ya sanitizado (sin cambios)")
    return True


def _list_data_csvs():
    """Lista CSVs en data/ (3 niveles arriba de este script: scripts -> zoho-survey -> raiz_repo)."""
    data_dir = Path(__file__).resolve().parent.parent.parent / "data"
    return list(data_dir.glob("*.csv")), data_dir


def main():
    parser = argparse.ArgumentParser(
        description="Sanitizador de PII en CSVs de Zoho Survey.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Modo --check (FM-003): detecta PII sin modificar archivos. "
            "Exit code 1 si detecta PII, 0 si todos los CSVs están sanitizados."
        ),
    )
    parser.add_argument(
        "csvs",
        nargs="*",
        help="Rutas a CSVs a procesar (modo redacción por defecto).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Procesar todos los CSVs en data/.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Modo detección (FM-003): no modifica archivos. "
            "Retorna exit code 1 si detecta PII no redactada."
        ),
    )
    args = parser.parse_args()

    # Resolver lista de CSVs a procesar
    if args.all:
        csvs, data_dir = _list_data_csvs()
        if not csvs:
            if args.check:
                print(f"No se encontraron CSVs en {data_dir} — nada que verificar.")
                sys.exit(0)
            print(f"No se encontraron CSVs en {data_dir}")
            sys.exit(0)
    elif args.csvs:
        csvs = [Path(p) for p in args.csvs]
    else:
        parser.print_help()
        sys.exit(1)

    # Modo --check: detect-only, exit 1 si hay PII
    if args.check:
        total_pii = 0
        for csv_path in csvs:
            hallazgos = detect_pii_in_csv(str(csv_path))
            if hallazgos is None:
                # Error de lectura (archivo no existe o vacío) — contar como fallo.
                total_pii += 1
                continue
            if hallazgos:
                total_pii += len(hallazgos)
                por_col = {}
                for col, _fila in hallazgos:
                    por_col[col] = por_col.get(col, 0) + 1
                detalle = ", ".join(f"{v} celdas en '{k}'" for k, v in por_col.items())
                print(f"✗ {csv_path.name}: PII no redactada detectada — {detalle}", file=sys.stderr)
            else:
                print(f"✓ {csv_path.name}: sin PII detectada (limpio)")
        if total_pii > 0:
            print(
                f"\nFM-003 gate pre-push: PII detectada en {total_pii} celda(s). "
                "Ejecutar `python zoho-survey/scripts/sanitize_csv_pii.py --all` para redactar.",
                file=sys.stderr,
            )
            sys.exit(1)
        print(f"\nFM-003 gate pre-push: {len(csvs)} CSV(s) verificados, 0 PII detectada.")
        sys.exit(0)

    # Modo redacción (default): modifica in-place
    exitos = 0
    for csv_path in csvs:
        if sanitizar_csv(str(csv_path)):
            exitos += 1
    if args.all:
        print(f"\nTotal: {exitos}/{len(csvs)} CSVs sanitizados")
    sys.exit(0 if exitos == len(csvs) else 1)


if __name__ == "__main__":
    main()
