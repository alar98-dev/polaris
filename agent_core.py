"""Core Polaris agent implementation with Native Aeon / SWA Integration.

Integrates:
- Córtex Superior (Gemma-3 1B) on http://127.0.0.1:20003 (/v1/chat/completions)
- Subcórtex (Gemma-3 270M) on http://127.0.0.1:20002 (/v1/embeddings - 640D)
- PostgreSQL 17 swa_matrix schema polaris (pgvector HNSW)
"""

import os
import uuid
import time
import json
from typing import List, Dict, Optional, Any

import httpx

from .utils import generate_mock_examples

try:
    from .adapters import embeddings as embedding_adapter
except Exception:
    embedding_adapter = None

try:
    from .db import save_conversation_turn, save_artifact_with_chunks, search_similar_chunks
except Exception:
    save_conversation_turn = None
    save_artifact_with_chunks = None
    search_similar_chunks = None


class PolarisAgent:
    """PolarisAgent with native bi-cameral inference and pgvector persistence."""

    def __init__(self, llm_url: Optional[str] = None, embedding_url: Optional[str] = None):
        self.llm_url = llm_url or os.getenv('LLM_URL', 'http://127.0.0.1:20003')
        self.embedding_url = embedding_url or os.getenv('EMBEDDING_URL', 'http://127.0.0.1:20002')
        self.sessions: Dict[str, Dict] = {}

    def create_session(self, client_id: Optional[str] = None, metadata: Optional[dict] = None) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            'session_id': session_id,
            'client_id': client_id,
            'metadata': metadata or {},
            'turns': [],
            'created_at': time.time(),
        }
        if save_conversation_turn:
            try:
                save_conversation_turn(session_id, client_id, [], metadata or {})
            except Exception:
                pass
        return session_id

    async def health_check(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {'ok': True, 'components': {}}
        async with httpx.AsyncClient() as client:
            # Check LLM (Cortex)
            try:
                r = await client.get(f"{self.llm_url}/health", timeout=3.0)
                results['components']['llm'] = {'ok': r.status_code == 200, 'status_code': r.status_code}
                if r.status_code != 200:
                    results['ok'] = False
            except Exception as e:
                results['components']['llm'] = {'ok': False, 'error': str(e)}
                results['ok'] = False

            # Check Subcortex (Embedding)
            try:
                r_emb = await client.get(f"{self.embedding_url}/health", timeout=3.0)
                results['components']['embedding'] = {'ok': r_emb.status_code == 200, 'status_code': r_emb.status_code}
            except Exception as e:
                results['components']['embedding'] = {'ok': False, 'error': str(e)}

        return results

    async def ask_discovery_questions(self, session_id: str, message: str) -> Dict[str, Any]:
        s = self.sessions.get(session_id)
        if not s:
            raise KeyError('session not found')
        s['turns'].append({'from': 'client', 'text': message, 'ts': time.time()})

        # Persist turn
        if save_conversation_turn:
            try:
                save_conversation_turn(session_id, s.get('client_id'), s['turns'], s.get('metadata'))
            except Exception:
                pass

        # Attempt extraction
        try:
            await self._extract_slots_from_message(s, message)
        except Exception:
            pass

        slots = s.get('slots', {})
        required = ['pain', 'users', 'kpi', 'budget']
        missing = [k for k in required if k not in slots]
        if missing:
            next_q = {
                'pain': 'Qual a dor principal que você quer resolver com essa solução?',
                'users': 'Quem são os usuários-alvo (descrição breve)?',
                'kpi': 'Qual a métrica de sucesso principal (ex.: conversão, retenção)?',
                'budget': 'Qual a faixa de orçamento disponível para esse projeto?'
            }[missing[0]]
            return {'next_question': next_q, 'slots': slots, 'complete': False}
        candidates = await self.select_portfolio(message, top_k=5)
        return {'next_question': None, 'slots': slots, 'complete': True, 'actions': [{'type': 'suggest_portfolio', 'candidates': candidates}]}

    async def _extract_slots_from_message(self, session: Dict[str, Any], message: str) -> None:
        prompt = (
            f"Você é um analisador de requisitos técnicos. Extraia as informações da mensagem a seguir no formato JSON estrito:\n"
            f'{{"pain": "dor principal", "users": "usuarios alvo", "kpi": "metrica chave", "budget": "orcamento estimado"}}\n'
            f'Mensagem: "{message}"'
        )
        res = await self.call_llm(prompt, max_tokens=256, temperature=0.0)
        if not res.get('ok'):
            return
        text = res.get('text') or ''
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        try:
            parsed = json.loads(text)
        except Exception:
            parsed = None
        if isinstance(parsed, dict):
            slots = session.get('slots') or {}
            for k in ('pain', 'users', 'kpi', 'budget'):
                if k in parsed and parsed[k] is not None:
                    slots[k] = parsed[k]
            if 'confidence' in parsed and isinstance(parsed['confidence'], dict):
                slots['_confidence'] = parsed['confidence']
            session['slots'] = slots

    async def select_portfolio(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if embedding_adapter and search_similar_chunks:
            try:
                emb = embedding_adapter.get_embedding([query])
                if emb:
                    similar = search_similar_chunks(emb[0], top_k=top_k)
                    if similar:
                        return [
                            {
                                'id': s['artifact_id'],
                                'title': s['metadata'].get('title', f"Solução #{s['artifact_id']}"),
                                'score': round(s['similarity'], 3),
                                'rationale': s['text'][:120]
                            }
                            for s in similar
                        ]
            except Exception:
                pass

        examples = [
            {'id': 1, 'title': 'E-commerce básico', 'score': 0.95, 'rationale': 'MVP de loja online com checkout'},
            {'id': 2, 'title': 'SaaS B2B (subscrição)', 'score': 0.85, 'rationale': 'Plataforma com usuários corporativos'},
            {'id': 3, 'title': 'Marketplace simples', 'score': 0.80, 'rationale': 'Multi-seller marketplace mínimo'},
        ]
        return examples[:top_k]

    async def generate_prototype(self, choice_id: int, context: dict) -> Dict[str, Any]:
        title = f"Protótipo - escolha {choice_id}"
        content = f"# {title}\n\n" + (context.get('summary', 'Resumo não fornecido') + '\n\n')
        content += '## Requisitos principais\n'
        for i, f in enumerate(context.get('features', ['Funcionalidade A', 'Funcionalidade B']), start=1):
            content += f"\n{i}. {f}\n"

        if save_artifact_with_chunks and embedding_adapter:
            try:
                chunks_text = [context.get('summary', title)] + [f"Feature: {feat}" for feat in context.get('features', [])]
                embeddings = embedding_adapter.get_embedding(chunks_text)
                chunks_data = [
                    {'text': t, 'embedding': emb, 'metadata': {'choice_id': choice_id}}
                    for t, emb in zip(chunks_text, embeddings)
                ]
                save_artifact_with_chunks(
                    project_id=None,
                    artifact_type='prototipo',
                    content=content,
                    chunks=chunks_data,
                    metadata={'choice_id': choice_id, 'title': title}
                )
            except Exception:
                pass

        return {'artifact': {'path': None, 'content': content}}

    async def generate_mock(self, contract_name: str, context: dict, count: int = 10) -> List[Dict[str, Any]]:
        return generate_mock_examples(contract_name, context, count=count)

    async def estimate_development(self, features: List[str]) -> Dict[str, Any]:
        hours_per_feature = {'simple': 8, 'medium': 24, 'complex': 80}
        total_hours = 0
        breakdown: List[Dict[str, Any]] = []
        for f in features:
            if len(f) < 20:
                h = hours_per_feature['simple']
                c = 'simple'
            elif len(f) < 60:
                h = hours_per_feature['medium']
                c = 'medium'
            else:
                h = hours_per_feature['complex']
                c = 'complex'
            total_hours += h
            breakdown.append({'feature': f, 'complexity': c, 'hours': h})
        return {'total_hours': total_hours, 'breakdown': breakdown, 't_shirt': self._hours_to_tshirt(total_hours)}

    def _hours_to_tshirt(self, hours: int) -> str:
        if hours <= 40:
            return 'S'
        if hours <= 160:
            return 'M'
        if hours <= 400:
            return 'L'
        return 'XL'

    async def call_llm(self, prompt: str, max_tokens: int = 256, temperature: float = 0.2, timeout: int = 15) -> Dict[str, Any]:
        """Calls the upstream LLM supporting OpenAI chat completions, native completion, or /v1/generate."""
        endpoints = [
            ('/v1/chat/completions', {'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': max_tokens, 'temperature': temperature}),
            ('/completion', {'prompt': prompt, 'n_predict': max_tokens, 'temperature': temperature}),
            ('/v1/generate', {'prompt': prompt, 'max_tokens': max_tokens, 'temperature': temperature})
        ]

        async with httpx.AsyncClient() as client:
            last_err = None
            for path, payload in endpoints:
                url = f"{self.llm_url.rstrip('/')}{path}"
                try:
                    r = await client.post(url, json=payload, timeout=timeout)
                    if r.status_code == 200:
                        body = r.json()
                        text = ""
                        if 'choices' in body and body['choices']:
                            msg = body['choices'][0].get('message', {})
                            text = msg.get('content', '')
                        elif 'content' in body:
                            text = body['content']
                        elif 'text' in body:
                            text = body['text']
                        return {'ok': True, 'text': text, 'meta': body}
                except Exception as e:
                    last_err = e
                    continue
            return {'ok': False, 'error': str(last_err)}

    async def call_llm_stream(self, prompt: str, max_tokens: int = 256, temperature: float = 0.2, timeout: int = 30):
        url = f"{self.llm_url.rstrip('/')}/v1/chat/completions"
        payload = {
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': max_tokens,
            'temperature': temperature,
            'stream': True
        }
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream('POST', url, json=payload, timeout=timeout) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith('data: '):
                            data = line[6:]
                            if data == '[DONE]':
                                break
                            try:
                                chunk = json.loads(data)
                                choices = chunk.get('choices', [])
                                if choices:
                                    delta = choices[0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        yield {'type': 'token', 'text': content}
                            except Exception:
                                continue
                    yield {'type': 'done'}
            except Exception as e:
                yield {'type': 'error', 'error': str(e)}
