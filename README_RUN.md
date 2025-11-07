Polaris agent - quick run

Prereqs:
- Python 3.10+
- Install deps: pip install -r requirements.txt

Run (development):
- uvicorn polaris.app:app --host 0.0.0.0 --port 8080 --reload

Endpoints:
- GET /api/v1/health
- POST /api/v1/sessions
- POST /api/v1/discovery
- POST /api/v1/prototype
- POST /api/v1/mocks
- POST /api/v1/estimate

Embedding service
-----------------
POLARIS expects an embeddings service reachable via the `EMBEDDING_URL` env var (default: http://localhost:8001).

The polaris package includes a synchronous adapter at `polaris.adapters.embeddings` which assumes the following endpoints (adjust if needed):
- POST {EMBEDDING_URL}/v1/embeddings  -> returns { "embeddings": [[...], ...] } or OpenAI-like { "data": [{"embedding": [...]}, ...] }
- POST {EMBEDDING_URL}/v1/upsert      -> accepts { items: [{id, vector, metadata}] }
- POST {EMBEDDING_URL}/v1/search      -> accepts { vector, top_k } and returns { results: [{id, score, metadata}, ...] }

If you have the embedding service located in this repository at `/models/embedings/embedding/`, run it (FastAPI) and set the env var before starting POLARIS:

```bash
export EMBEDDING_URL=http://localhost:8001
uvicorn polaris.app:app --host 0.0.0.0 --port 8080
```

The `select_portfolio` flow in `polaris.agent.PolarisAgent` will attempt to call the adapter and, on failure, fall back to static examples for demo purposes.
