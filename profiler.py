import re

# --- Patrones para reconocer formatos comunes dentro de un texto ---
URL_RE   = re.compile(r"^https?://", re.IGNORECASE)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
UUID_RE  = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)
DATE_RE  = re.compile(r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}:\d{2})?")


def detect_type(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        if URL_RE.match(value):
            return "url"
        if EMAIL_RE.match(value):
            return "email"
        if UUID_RE.match(value):
            return "uuid"
        if DATE_RE.match(value):
            return "datetime"
        return "string"
    return "unknown"


def looks_numeric(text):
    """¿Este texto representa un número? Ej: '42' o '3.14' -> True"""
    try:
        float(text)
        return True
    except (ValueError, TypeError):
        return False


def annotate(value, raw_type, semantic_type):
    transformations = []
    validations = []
    enrichments = []

    # Transformaciones: cambios de tipo reales
    if raw_type == "str":
        if semantic_type == "datetime":
            transformations.append("Texto → fecha")
        elif looks_numeric(value):
            transformations.append("Texto → número")

    # Validaciones: calidad de datos
    if value is None or value == "":
        validations.append("Vacío: revisar completitud")

    # Enriquecimientos: derivar datos nuevos
    if semantic_type == "url":
        enrichments.append("Extraer dominio")
    elif semantic_type == "email":
        enrichments.append("Extraer dominio del email")
    elif semantic_type == "datetime":
        enrichments.append("Extraer año/mes/día")

    return {
        "transformations": transformations,
        "validations": validations,
        "enrichments": enrichments,
    }


def flatten(data, prefix=""):
    rows = []
    if data is None:
        rows.append({
            "path": prefix,
            "value": None,
            "type": "NoneType",
            "semanticType": "null",
            "annotations": {
                "transformations": [],
                "validations": ["Vacío: revisar completitud"],
                "enrichments": [],
            },
        })
    elif isinstance(data, dict):
        for key, value in data.items():
            new_prefix = f"{prefix}.{key}" if prefix else key
            rows.extend(flatten(value, new_prefix))
    elif isinstance(data, list):
        for index, item in enumerate(data):
            new_prefix = f"{prefix}[{index}]"
            rows.extend(flatten(item, new_prefix))
    else:
        raw_type = type(data).__name__
        semantic = detect_type(data)
        rows.append({
            "path": prefix,
            "value": data,
            "type": raw_type,
            "semanticType": semantic,
            "annotations": annotate(data, raw_type, semantic),
        })
    return rows


if __name__ == "__main__":
    import json
    ejemplo = {
        "web": "https://github.com",
        "correo": "daniel@correo.com",
        "fecha": "2017-02-10T19:23:51Z",
        "cantidad_texto": "42",
        "cantidad_real": 42,
        "vacio": "",
    }
    print(json.dumps(flatten(ejemplo), indent=2, ensure_ascii=False))