# POLARIS — Notas de Deploy

Ambiente: Docker Compose (desenvolvimento) / Kubernetes (produção).

Requisitos mínimos
- Python 3.11
- Memória: 2-4 GB para o serviço do agente (dependendo do volume de concorrência)
- Rede: acesso aos serviços `ai-agent`, `embedding`, `postgres`, `redis` conforme necessário

Variáveis de ambiente esperadas
- AI_AGENT_URL (ex.: http://ai-agent:8002)
- EMBEDDING_URL (ex.: http://embedding:8001)
- AI_API_KEY (se aplicável)
- LOG_LEVEL (INFO/DEBUG)

Exemplo de Dockerfile (simplificado)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "polaris_service.py"]
```

Exemplo de docker-compose service

```yaml
polaris:
  build: ./models/agents/POLARIS
  image: server_orion/polaris:latest
  environment:
    - AI_AGENT_URL=http://ai-agent:8002
    - EMBEDDING_URL=http://embedding:8001
    - AI_API_KEY=${AI_API_KEY}
  networks:
    - ai_network
  restart: unless-stopped
```

Observações
- Em produção, rode POLARIS com readiness/liveness probes e limites de recursos; adicione logs estruturados para permitir correlação via `X-Request-ID`.
