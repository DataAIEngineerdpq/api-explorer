import httpx
import json
import ollama

SYSTEM_PROMPT = """Eres un agente que explora APIs para responder preguntas.

Tienes UNA herramienta disponible:
- explore_api(url): hace una petición GET a la URL y devuelve el resultado.

Para responder, sigues un ciclo. En CADA turno respondes con UNA de estas dos opciones, en formato JSON:

1. Si necesitas explorar una API para obtener información:
{"action": "explore_api", "url": "https://la-url-que-decidas.com/..."}

2. Si ya tienes suficiente información para responder:
{"action": "final_answer", "answer": "tu respuesta aquí"}

Reglas:
- Responde SIEMPRE con un único objeto JSON válido, nada más.
- Piensa qué URL explorar según la pregunta del usuario.
- Si la observación no basta, puedes explorar otra URL.
- Cuando tengas la respuesta, usa final_answer.
"""

async def run_agent(question: str, use_cloud: bool = False, headers: dict = None, max_steps: int = 5):
    model = "gemma4:cloud" if use_cloud else "qwen2.5-coder:7b"

    # El historial de la conversación con el LLM
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    # Aquí registramos cada paso, para el panel del frontend
    steps = []

    for step_num in range(max_steps):
        # --- RAZONAR: el LLM decide qué hacer ---
        respuesta = ollama.chat(model=model, messages=messages)
        contenido = respuesta["message"]["content"]

         # Limpiar posible formato markdown (```json ... ```) que añaden algunos modelos
        limpio = contenido.strip()
        if limpio.startswith("```"):
            # Quitar la primera línea (```json) y la última (```)
            lineas = limpio.split("\n")
            limpio = "\n".join(lineas[1:-1]) if len(lineas) > 2 else limpio
            limpio = limpio.strip()

        # Intentar leer la decisión del LLM como JSON
        try:
            decision = json.loads(limpio)
        except json.JSONDecodeError:
            # Si no devolvió JSON válido, lo tratamos como respuesta final
            steps.append({"type": "answer", "content": contenido})
            return {"answer": contenido, "steps": steps}

        accion = decision.get("action")

        # --- RESPONDER: el LLM tiene la respuesta final ---
        if accion == "final_answer":
            answer = decision.get("answer", "")
            steps.append({"type": "answer", "content": answer})
            return {"answer": answer, "steps": steps}

        # --- ACTUAR: el LLM quiere explorar una API ---
        elif accion == "explore_api":
            url = decision.get("url", "")
            steps.append({"type": "reason", "content": f"Decido explorar: {url}"})
            steps.append({"type": "act", "url": url})

            # --- OBSERVAR: ejecutar la herramienta y ver el resultado ---
            observacion = await explore_api(url, headers=headers)
            steps.append({"type": "observe", "content": observacion})

            # Devolver la observación al LLM para que siga razonando
            messages.append({"role": "assistant", "content": contenido})
            messages.append({
                "role": "user",
                "content": f"Resultado de explore_api: {json.dumps(observacion)[:1500]}",
            })

        else:
            # Acción desconocida
            steps.append({"type": "answer", "content": "No supe qué hacer."})
            return {"answer": "No supe qué hacer.", "steps": steps}

    # Si se acaban los pasos sin respuesta final
    return {"answer": "Alcancé el límite de pasos sin una respuesta final.", "steps": steps}

# Herramienta que el agente puede usar: explorar una API
async def explore_api(url: str, headers: dict = None):
    """Hace una petición GET a una API y devuelve un resumen del resultado."""
    headers = headers or {}
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            response = await client.get(url, headers=headers)  # SOLO GET, por seguridad
        return {
            "ok": True,
            "status": response.status_code,
            "body": response.text[:1500],
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
    

if __name__ == "__main__":
    import asyncio

    async def test():
        pregunta = "Explora la API pública de GitHub y dime el nombre y la descripción del repositorio 'python/cpython'."
        resultado = await run_agent(pregunta)
        print("\n=== RESPUESTA FINAL ===")
        print(resultado["answer"])
        print("\n=== PASOS ===")
        for s in resultado["steps"]:
            print(s)

    asyncio.run(test())