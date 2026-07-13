import ollama
from profiler import to_schema


def recommend_with_llm(fields, use_cloud=False):
    # 1. Collapse the flattened rows into a unique schema (no truncation,
    #    only deduplication of repeated array items)
    schema = to_schema(fields)

    # 2. Heuristic hints, computed over the schema (not over every data row)
    pistas = suggest_model(schema)

    # 3. The full structure: every distinct field, its types, and an example
    estructura_completa = "\n".join(
        f"- {f['path']} (tipos: {', '.join(f['types'])}) ej: {f['example']!r}"
        for f in schema
    )

    # 4. Hints as supporting material
    pistas_texto = "\n".join(
        f"- {h['path']} → sugerencia: {h['role']} ({h['reason']})"
        for h in pistas["hints"]
    )

    prompt = f"""Eres un experto en modelado dimensional de datos (data warehousing).

A continuación tienes la ESTRUCTURA COMPLETA de una respuesta de API, y unas PISTAS
automáticas que pueden ayudarte (pero úsalas solo como apoyo; confía en tu criterio
sobre la estructura completa).

Los campos que provienen de listas se muestran con la notación `campo[]`, lo que
significa que el endpoint devuelve múltiples elementos con esa misma estructura.
Cuando un campo tiene varios tipos (ej. "datetime, null"), significa que puede venir
vacío.

--- ESTRUCTURA COMPLETA DE LA API ---
{estructura_completa}

--- PISTAS AUTOMÁTICAS (solo como ayuda, pueden estar incompletas) ---
{pistas_texto}

Basándote en TODA la estructura, propón un modelo dimensional (esquema estrella).
Responde en dos partes claramente separadas:

1. EXPLICACIÓN SENCILLA: en lenguaje simple, para alguien no técnico, qué tabla de
   hechos y qué dimensiones tendría y por qué.

2. EXPLICACIÓN TÉCNICA: la tabla de hechos (con sus medidas y claves foráneas) y las
   tablas de dimensión (con sus atributos), en términos de data warehousing.
"""

    model = "gemma4:cloud" if use_cloud else "qwen2.5-coder:7b"
    respuesta = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        options={"num_ctx": 8192},
    )

    return {
        "recommendation": respuesta["message"]["content"],
        "hints": pistas["hints"],
        "summary": pistas["summary"],
        "schema_size": len(schema),
        "rows_size": len(fields),
    }

# Palabras que sugieren una MEDIDA (algo cuantificable, va en la tabla de hechos)
MEASURE_HINTS = {"count", "total", "amount", "price", "cost", "duration",
                 "points", "size", "quantity", "sum", "avg", "number", "time_ms"}

# Palabras que sugieren una DIMENSIÓN (contexto descriptivo)
DIMENSION_HINTS = {"name", "status", "type", "category", "title", "label",
                   "email", "country", "city", "state", "color", "role"}


def classify_field(field):
    """Clasifica un campo como candidato a medida, clave o dimensión (una pista)."""
    path = field["path"].lower()
    last = path.split(".")[-1]          # el último tramo del path (ej. owner.id -> id)

    # El esquema trae una lista de tipos (un campo puede ser nullable).
    # Ignoramos "null": no compite con el tipo real, solo indica opcionalidad.
    types = [t for t in field.get("types", []) if t != "null"]
    semantic = types[0] if types else ""

    # --- ¿Es una CLAVE? ---
    if last == "id" or last.endswith("_id") or semantic == "uuid":
        return {"role": "key", "reason": "Identificador (conecta tablas)"}

    # --- ¿Es una MEDIDA? ---
    if semantic in ("integer", "float"):
        # numérico + nombre que suena a métrica = medida fuerte
        if any(h in last for h in MEASURE_HINTS):
            return {"role": "measure", "reason": "Numérico y nombre de métrica"}
        # numérico sin nombre de métrica = medida débil (podría serlo)
        return {"role": "measure", "reason": "Campo numérico (posible métrica)"}

    # --- ¿Es una DIMENSIÓN? ---
    if semantic == "datetime":
        return {"role": "dimension", "reason": "Fecha (dimensión temporal)"}
    if any(h in last for h in DIMENSION_HINTS):
        return {"role": "dimension", "reason": "Atributo descriptivo"}

    # Por defecto: dimensión (texto descriptivo genérico)
    return {"role": "dimension", "reason": "Texto descriptivo"}


def suggest_model(fields):
    """Genera pistas de modelado a partir de los campos del profiler."""
    hints = []
    for field in fields:
        clasificacion = classify_field(field)
        hints.append({
            "path": field["path"],
            "type": ", ".join(field.get("types", [])),
            "role": clasificacion["role"],
            "reason": clasificacion["reason"],
        })

    # Resumen: contar cuántos de cada rol
    resumen = {"measure": 0, "key": 0, "dimension": 0}
    for h in hints:
        resumen[h["role"]] += 1

    return {"hints": hints, "summary": resumen}


if __name__ == "__main__":
    from profiler import flatten

    ejemplo = {
        "tasks": [
            {"id": 1, "name": "Uno", "due_date": "2026-01-15", "points": 3,
             "assignee": {"id": 10, "username": "dc"}},
            {"id": 2, "name": "Dos", "due_date": None, "points": 5,
             "assignee": {"id": 11, "username": "ana"}},
            {"id": 3, "name": "Tres", "due_date": "2026-02-20", "points": 8,
             "assignee": {"id": 10, "username": "dc"}},
        ]
    }

    filas = flatten(ejemplo)
    resultado = recommend_with_llm(filas)

    print(f"flatten -> {resultado['rows_size']} filas")
    print(f"to_schema -> {resultado['schema_size']} campos\n")
    print("=== PISTAS ===")
    for h in resultado["hints"]:
        print(f"  {h['path']:<28} {h['role']:<10} ({h['reason']})")
    print(f"\nResumen: {resultado['summary']}\n")
    print("=== RECOMENDACIÓN DEL LLM ===")
    print(resultado["recommendation"])