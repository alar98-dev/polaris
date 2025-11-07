name: "POLARIS-agent"
version: "1.0.0"
summary: "Agente orquestrador responsável por planejar ações e invocar modelos do servidor (LLM, Embeddings, etc.)."
owner: "ml-team@example.com"
license: "proprietary"
model_type: "agent"
framework: "python"
input_schema: |
  {
    "type": "object",
    "properties": {
      "task_id": {"type": "string"},
      "prompt": {"type": "string"},
      "context_uris": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["task_id", "prompt"]
  }
output_schema: |
  {
    "type": "object",
    "properties": {
      "task_id": {"type": "string"},
      "status": {"type": "string"},
      "result": {"type": "object"}
    }
  }
metrics:
  - name: "avg_response_time"
    value: ""
    dataset: "system_metrics"
training_dataset: "N/A"
weights_uri: "N/A"
checksum: ""
quantized: false
deploy_instructions: |
  - Requisitos: Python 3.11, dependencies list em requirements.txt
  - Variáveis de ambiente: AI_API_URL, EMBEDDING_URL, AUTH_TOKEN
  - Como executar: `python polaris_service.py` (ou containerize com Dockerfile de exemplo)
notes: |
  - POLARIS não armazena dados sensíveis por padrão; registre qualquer persistência em logs ou DB com consentimento.
contact: "ml-team@example.com"
