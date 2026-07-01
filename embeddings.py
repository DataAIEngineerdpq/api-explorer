from sentence_transformers import SentenceTransformer

# Se carga UNA vez, al importar el módulo (cargar el modelo es costoso)
print("Cargando modelo de embeddings…")
_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
print("Modelo de embeddings listo.")

# Dimensión de los vectores que produce este modelo
EMBEDDING_DIM = 384


def generate_embedding(text: str) -> list[float]:
    """Convierte un texto en su vector de embedding (lista de 384 floats)."""
    vector = _model.encode(text)
    return vector.tolist()
