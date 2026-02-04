import requests
import uuid
from sentence_transformers import SentenceTransformer

# Endee config

ENDEE_BASE_URL = "http://localhost:8080/api/v1"
INDEX_NAME = "labyrinth"
VECTOR_DIM = 32

# Embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

def project_to_32(vec):
    return vec[:VECTOR_DIM]

# Load documents
ROOM_PATHS = {
    1: "data/room1/documents.txt",
    2: "data/room2/documents.txt",
    3: "data/room3/documents.txt",
}

def load_documents():
    docs = []
    for _, path in ROOM_PATHS.items():
        with open(path, "r", encoding="utf-8") as f:
            chunks = [c.strip() for c in f.read().split("\n\n") if c.strip()]
            for text in chunks:
                docs.append({
                    "id": str(uuid.uuid4()),
                    "text": text
                })
    return docs

# Insert vectors
def insert_vectors(docs):
    endpoint = f"{ENDEE_BASE_URL}/index/{INDEX_NAME}/vector/insert"
    payload = []

    for doc in docs:
        emb = model.encode(doc["text"])
        payload.append({
            "id": doc["id"],
            "vector": project_to_32(emb).tolist(),
            "meta": {
                "text": doc["text"]
            }
        })

    response = requests.post(endpoint, json=payload)
    return response.status_code

# Semantic search
def semantic_search(query, k=3):
    endpoint = f"{ENDEE_BASE_URL}/index/{INDEX_NAME}/search"

    emb = model.encode(query)

    payload = {
        "vector": project_to_32(emb).tolist(),
        "k": k,
        "include_vectors": True
    }

    response = requests.post(endpoint, json=payload)
    return response.status_code, response.content

#  Main
if __name__ == "__main__":
    docs = load_documents()
    insert_status = insert_vectors(docs)

    search_status, search_response = semantic_search("memory loss")

    print("Insert status:", insert_status)
    print("Search status:", search_status)
    print("Search response length:", len(search_response))
