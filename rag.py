import ollama
from database import search_similar

LOCAL_MODEL = "qwen2.5-coder:7b"
CLOUD_MODEL = "gemma4:cloud"


def answer_question(question, use_cloud=False):
    # --- 1. RETRIEVAL: recuperar los contextos más relevantes ---
    resultados = search_similar(question, limit=3)

    if not resultados:
        return {
            "answer": "No hay APIs exploradas todavía para responder.",
            "sources": [],
        }

    # --- 2. AUGMENTED: construir el prompt con los contextos ---
    contexto = ""
    for r in resultados:
        contexto += f"Fuente: {r['source_url']}\nContenido: {r['content'][:500]}\n\n"

    prompt = f"""Eres un asistente que responde preguntas sobre APIs que el usuario ha explorado.
Usa ÚNICAMENTE la información proporcionada abajo para responder.
Si la información no es suficiente, dilo honestamente en vez de inventar.

--- INFORMACIÓN DISPONIBLE ---
{contexto}--- FIN DE LA INFORMACIÓN ---

Pregunta del usuario: {question}

Respuesta:"""

    # --- 3. GENERATION: pedirle al LLM que redacte la respuesta ---
    model = CLOUD_MODEL if use_cloud else LOCAL_MODEL
    respuesta = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    answer = respuesta["message"]["content"]

    # Devolver la respuesta y las fuentes usadas (para transparencia)
    return {
        "answer": answer,
        "sources": [r["source_url"] for r in resultados],
    }



if __name__ == "__main__":
    pregunta = "¿Qué APIs tienen datos de personas o usuarios?"
    print(f"Pregunta: {pregunta}\n")
    resultado = answer_question(pregunta)
    print("Respuesta:")
    print(resultado["answer"])
    print("\nFuentes:", resultado["sources"])