import pandas as pd
from pathlib import Path

EXPORT_DIR = Path("exports")


def export_fields(fields, fmt="csv"):
    # Aseguramos que exista la carpeta de salida
    EXPORT_DIR.mkdir(exist_ok=True)

    # 1. Convertir las filas (lista de diccionarios) en un DataFrame
    df = pd.DataFrame(fields)

    # 'value' puede mezclar tipos (texto, números, booleanos);
    # la pasamos a texto para que Parquet acepte una columna consistente
    if "value" in df.columns:
        df["value"] = df["value"].astype(str)

    # 2. Elegir formato y escribir
    if fmt == "parquet":
        path = EXPORT_DIR / "export.parquet"
        df.to_parquet(path, index=False)
    else:
        path = EXPORT_DIR / "export.csv"
        df.to_csv(path, index=False, encoding="utf-8")

    return str(path)


if __name__ == "__main__":
    datos_prueba = [
        {"path": "name", "value": "cpython", "type": "str"},
        {"path": "stars", "value": 73315, "type": "int"},
    ]
    print("CSV:", export_fields(datos_prueba, "csv"))
    print("Parquet:", export_fields(datos_prueba, "parquet"))