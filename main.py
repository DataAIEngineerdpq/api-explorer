from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import time
from fastapi.responses import FileResponse
from profiler import flatten, to_graph
from database import init_db, save_request, get_requests
from exporter import export_fields

app = FastAPI()
init_db()

class ProxyRequest(BaseModel):
    method: str = "GET"
    url: str
    headers: dict[str, str] = {}
    body: str | None = None
    timeout: float = 30.0

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.get("/api/health")
def health():
    return {"mensaje": "API Explorer está vivo"}

@app.post("/api/proxy")
async def proxy(req: ProxyRequest):
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=req.timeout) as client:
            response = await client.request(
                method=req.method,
                url=req.url,
                headers=req.headers,
                content=req.body,
            )
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        save_request(req.method, req.url, response.status_code, elapsed_ms, len(response.content))
        return {
            "ok": True,
            "status": response.status_code,
            "statusText": response.reason_phrase,
            "headers": dict(response.headers),
            "body": response.text,
            "timeMs": elapsed_ms,
            "sizeBytes": len(response.content),
        }
    except httpx.TimeoutException:
        return {"ok": False, "error": f"La petición superó el tiempo límite ({req.timeout}s)."}
    except httpx.ConnectError:
        return {"ok": False, "error": "No se pudo conectar. Revisa la URL o tu conexión."}
    except httpx.InvalidURL:
        return {"ok": False, "error": "La URL no es válida."}
    except Exception as exc:
        return {"ok": False, "error": f"Error inesperado: {type(exc).__name__}: {exc}"}
    

@app.post("/api/flatten")
async def flatten_endpoint(data: dict):
    rows = flatten(data)
    return {"fields": rows, "count": len(rows)}

@app.post("/api/graph")
async def graph_endpoint(data: dict):
    return to_graph(data)

@app.get("/api/history")
async def history_endpoint():
    return {"requests": get_requests()}


@app.post("/api/export")
async def export_endpoint(payload: dict):
    fields = payload.get("fields", [])
    fmt = payload.get("format", "csv")

    path = export_fields(fields, fmt)

    filename = f"export.{fmt}"
    return FileResponse(path, filename=filename, media_type="application/octet-stream")
