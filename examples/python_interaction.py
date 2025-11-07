"""Exemplo de interação do agente POLARIS com serviços de embeddings e ai-agent.
Substitua as variáveis de ambiente conforme seu ambiente (docker compose ou localhost).
"""
import os
import requests
import time

AI_AGENT_URL = os.getenv('AI_AGENT_URL', 'http://localhost:8002')
EMBED_URL = os.getenv('EMBEDDING_URL', 'http://localhost:8001')
API_KEY = os.getenv('AI_API_KEY', '')

HEADERS = {'Content-Type': 'application/json'}
if API_KEY:
    HEADERS['Authorization'] = f'Bearer {API_KEY}'


def generate_embedding(text):
    url = f"{EMBED_URL}/embed"
    resp = requests.post(url, json={'text': text}, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.json()['embedding']


def search_vector(query):
    url = f"{EMBED_URL}/search"
    resp = requests.post(url, json={'query': query, 'collection': 'knowledge_base', 'limit': 5}, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.json().get('results', [])


def create_agent_task(prompt, context_texts):
    # montar prompt com contexto
    combined = prompt + "\n\nContext:" + "\n".join(context_texts)
    url = f"{AI_AGENT_URL}/api/tasks"
    payload = {
        'name': 'POLARIS: Chat Completion',
        'description': 'Task from POLARIS agent',
        'task_type': 'chat_completion',
        'input_data': {
            'prompt': combined,
            'max_tokens': 512
        }
    }
    resp = requests.post(url, json=payload, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


if __name__ == '__main__':
    query = 'Como reduzir latência em APIs REST?'
    emb = generate_embedding(query)
    print('Embedding gerado (len):', len(emb))

    results = search_vector(query)
    context_texts = [r.get('text','') for r in results]

    task = create_agent_task(query, context_texts)
    print('Task criada:', task)
