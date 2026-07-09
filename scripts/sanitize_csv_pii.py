"""
SANITIZADOR DE PII — Redacta columnas de identificación directa en CSVs.

Columnas redactadas:
  - Dirección IP (columna 2 en todos los CSVs Zoho Survey)
  - Agente Usuario (columna 3)

Estas columnas contienen datos personales identificables (Ley 29733, GDPR).
Se reemplazan con string vacío para preservar estructura CSV sin datos sensibles.

Uso:
  python scripts/sanitize_csv_pii.py "data/ENCUESTA...csv"
  # Modifica el archivo in-place (sobreescribe con columnas redactadas)
"""

import csv
import sys
import os
from pathlib import Path


def sanitizar_csv(ruta_csv: str) -> bool:
    """Redacta columnas PII en un CSV, modificándolo in-place."""
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
    # Identificar índices de columnas PII por nombre
    col_ip = None
    col_ua = None
    for i, h in enumerate(headers):
        h_clean = h.strip().strip('"')
        if h_clean == "Dirección IP":
            col_ip = i
        elif h_clean == "Agente Usuario":
            col_ua = i

    if col_ip is None and col_ua is None:
        print(f"INFO: no se encontraron columnas PII en {ruta_csv}. Saltando.")
        return True  # No es error, el archivo ya está limpio

    cambios_ip = 0
    cambios_ua = 0
    for fila in filas[1:]:  # Saltar header
        if col_ip is not None and col_ip < len(fila) and fila[col_ip].strip():
            fila[col_ip] = ""
            cambios_ip += 1
        if col_ua is not None and col_ua < len(fila) and fila[col_ua].strip():
            fila[col_ua] = ""
            cambios_ua += 1

    # Escribir el CSV sanitizado (sobreescribe original)
    with open(ruta, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(filas)

    total_filas = len(filas) - 1  # Sin contar header
    print(f"✓ {ruta.name}: {total_filas} filas, {cambios_ip} IPs redactadas, {cambios_ua} UAs redactadas")
    return True


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/sanitize_csv_pii.py <ruta_csv1> [ruta_csv2 ...]")
        print("  O: python scripts/sanitize_csv_pii.py --all  (sanitiza todos los CSVs en data/)")
        sys.exit(1)

    if sys.argv[1] == "--all":
        data_dir = Path(__file__).resolve().parent.parent / "data"
        csvs = list(data_dir.glob("*.csv"))
        if not csvs:
            print(f"No se encontraron CSVs en {data_dir}")
            sys.exit(0)
        exitos = 0
        for csv_path in csvs:
            if sanitizar_csv(str(csv_path)):
                exitos += 1
        print(f"\nTotal: {exitos}/{len(csvs)} CSVs sanitizados")
    else:
        for ruta in sys.argv[1:]:
            sanitizar_csv(ruta)


if __name__ == "__main__":
    main()
