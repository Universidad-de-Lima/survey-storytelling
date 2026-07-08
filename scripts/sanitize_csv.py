#!/usr/bin/env python3
"""
CC-04: Script de sanitización de CSVs fuente para eliminar PII.

El repositorio es público, por lo que los CSVs exportados desde Zoho Survey
deben sanitizarse antes de commitearse para eliminar información de identificación
personal (PII):

Columnas eliminadas:
  - Dirección IP
  - Agente Usuario
  - URL de la encuesta a la que accede el encuestado
  - Recopilador

Columnas anonimizadas:
  - Start time (truncar a fecha sin hora)
  - Hora de finalización (truncar a fecha sin hora)

Uso:
  python scripts/sanitize_csv.py <csv_crudo> <csv_sanitizado>

  python scripts/sanitize_csv.py "data/raw/ENCUESTA 2026-1.csv" "data/ENCUESTA 2026-1.csv"

Flujo de trabajo recomendado:
  1. Colocar CSV crudo (con PII) en data/raw/ (gitignored)
  2. Ejecutar este script para generar CSV sanitizado en data/
  3. Commitear solo el CSV sanitizado
  4. El CSV crudo nunca entra al repositorio

Compatibilidad:
  - El ETL (build_json.py) funciona sin las columnas eliminadas (ya maneja
    columnas faltantes con fallbacks).
  - Las fechas truncadas permiten calcular dias_recoleccion sin exponer
    el momento exacto de respuesta.
"""
import sys
import csv
from pathlib import Path


# Columnas PII a eliminar completamente
PII_COLUMNS_TO_REMOVE = [
    "Dirección IP",
    "Agente Usuario",
    "URL de la encuesta a la que accede el encuestado",
    "Recopilador",
]

# Columnas de fecha a anonimizar (truncar a solo fecha, sin hora)
DATE_COLUMNS_TO_ANONYMIZE = [
    "Start time",
    "Hora de finalización",
]


def sanitize_csv(input_path: str, output_path: str) -> None:
    """Lee un CSV crudo, elimina PII y escribe CSV sanitizado.

    Args:
        input_path: Ruta al CSV crudo con PII.
        output_path: Ruta donde escribir el CSV sanitizado.

    Raises:
        FileNotFoundError: Si input_path no existe.
        ValueError: Si no se puede leer el CSV.
    """
    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        raise FileNotFoundError(f"CSV crudo no encontrado: {input_path}")

    # Detectar encoding (probar UTF-8 con BOM, luego UTF-8, luego latin-1)
    encoding = None
    for enc in ["utf-8-sig", "utf-8", "latin-1"]:
        try:
            with open(input_file, encoding=enc) as f:
                f.read(1024)
            encoding = enc
            break
        except (UnicodeDecodeError, UnicodeError):
            continue

    if encoding is None:
        raise ValueError(f"No se pudo detectar encoding del CSV: {input_path}")

    print(f"Sanitizando: {input_path}")
    print(f"  Encoding detectado: {encoding}")

    with open(input_file, encoding=encoding, newline="") as fin:
        reader = csv.reader(fin)
        headers = next(reader)
        rows = list(reader)

    print(f"  Filas: {len(rows)}")
    print(f"  Columnas originales: {len(headers)}")

    # Identificar índices de columnas a eliminar y a anonimizar
    indices_to_remove = set()
    for i, h in enumerate(headers):
        if h in PII_COLUMNS_TO_REMOVE:
            indices_to_remove.add(i)
            print(f"  Eliminando columna PII: {i} '{h}'")

    indices_to_anonymize = set()
    for i, h in enumerate(headers):
        if h in DATE_COLUMNS_TO_ANONYMIZE:
            indices_to_anonymize.add(i)
            print(f"  Anonimizando fecha: {i} '{h}'")

    # Construir nuevos headers (sin columnas PII)
    new_headers = [h for i, h in enumerate(headers) if i not in indices_to_remove]

    # Construir nuevas filas
    new_rows = []
    for row in rows:
        new_row = []
        for i, val in enumerate(row):
            if i in indices_to_remove:
                continue
            if i in indices_to_anonymize:
                # Truncar a fecha: tomar solo los primeros 10 caracteres (YYYY-MM-DD)
                # o el formato de fecha que esté antes de cualquier separador de hora
                date_only = val.strip().split(" ")[0].split("T")[0]
                new_row.append(date_only)
            else:
                new_row.append(val)
        new_rows.append(new_row)

    print(f"  Columnas sanitizadas: {len(new_headers)}")

    # Escribir CSV sanitizado (UTF-8 con BOM para compatibilidad con Excel)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8-sig", newline="") as fout:
        writer = csv.writer(fout)
        writer.writerow(new_headers)
        writer.writerows(new_rows)

    print(f"  ✓ CSV sanitizado escrito en: {output_path}")

    # Verificación: grep de patrones PII en el output
    with open(output_file, encoding="utf-8-sig") as f:
        content = f.read()
        import re
        ip_pattern = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
        ip_matches = ip_pattern.findall(content)
        if ip_matches:
            print(f"  ⚠ ADVERTENCIA: Se encontraron {len(ip_matches)} posibles IPs en el CSV sanitizado")
        else:
            print(f"  ✓ Verificación: sin IPs detectadas en CSV sanitizado")


def main():
    if len(sys.argv) != 3:
        print("Uso: python scripts/sanitize_csv.py <csv_crudo> <csv_sanitizado>")
        print()
        print("Ejemplo:")
        print('  python scripts/sanitize_csv.py "data/raw/ENCUESTA 2026-1.csv" "data/ENCUESTA 2026-1.csv"')
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    sanitize_csv(input_path, output_path)


if __name__ == "__main__":
    main()
