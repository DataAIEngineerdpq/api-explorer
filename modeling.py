import ollama



def recommend_with_llm(fields, use_cloud=False):
    # 1. Generar las pistas heurísticas
    pistas = suggest_model(fields)

    # 2. Preparar la estructura COMPLETA (todos los campos, sin filtrar)
    estructura_completa = "\n".join(
        f"- {f['path']} (tipo: {f.get('semanticType', '?')})" for f in fields
    )

    # 3. Preparar las pistas como AYUDA adicional
    pistas_texto = "\n".join(
        f"- {h['path']} → sugerencia: {h['role']} ({h['reason']})"
        for h in pistas["hints"]
    )

    # 4. Armar el prompt: estructura completa + pistas
    prompt = f"""Eres un experto en modelado dimensional de datos (data warehousing).

A continuación tienes la ESTRUCTURA COMPLETA de una respuesta de API, y unas PISTAS
automáticas que pueden ayudarte (pero úsalas solo como apoyo; confía en tu criterio
sobre la estructura completa).

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
    respuesta = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])

    return {
        "recommendation": respuesta["message"]["content"],
        "hints": pistas["hints"],
        "summary": pistas["summary"],
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
    semantic = field.get("semanticType", "")

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
            "type": field.get("semanticType", ""),
            "role": clasificacion["role"],
            "reason": clasificacion["reason"],
        })

    # Resumen: contar cuántos de cada rol
    resumen = {"measure": 0, "key": 0, "dimension": 0}
    for h in hints:
        resumen[h["role"]] += 1

    return {"hints": hints, "summary": resumen}


if __name__ == "__main__":
    campos_prueba = [
        {"path": "id", "semanticType": "integer"},
        {"path": "name", "semanticType": "string"},
        {"path": "assignees.count", "semanticType": "integer"},
        {"path": "due_date", "semanticType": "datetime"},
        {"path": "status", "semanticType": "string"},
        {"path": "owner.id", "semanticType": "integer"},
        {"path": "owner.name", "semanticType": "string"},
    ]
    resultado = recommend_with_llm(campos_prueba)
    print("=== RECOMENDACIÓN DEL LLM ===")
    print(resultado["recommendation"])