"""Core Polaris agent implementation (clean single-file version).

This file intentionally keeps a compact, single definition of PolarisAgent used by tests
and the FastAPI app. It provides lightweight, test-friendly behavior and defers heavy
integrations (DB, external embedding stores) to adapters.
"""

import os
import uuid
import time
from typing import List, Dict, Optional, Any

import httpx

from .utils import generate_mock_examples

try:
    from .adapters import embeddings as embedding_adapter
except Exception:
    embedding_adapter = None


class PolarisAgent:
    """Minimal, clean PolarisAgent implementation used by tests and API.

    Methods implemented are the ones required by the test-suite and the FastAPI app.
    """

    def __init__(self, llm_url: Optional[str] = None, embedding_url: Optional[str] = None):
        self.llm_url = llm_url or os.getenv('LLM_URL', 'http://localhost:8100')
        self.embedding_url = embedding_url or os.getenv('EMBEDDING_URL', 'http://localhost:8001')
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
        return session_id

    async def health_check(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {'ok': True, 'components': {}}
        async with httpx.AsyncClient() as client:
            try:
                r = await client.get(f"{self.llm_url}/v1/health", timeout=3.0)
                results['components']['llm'] = {'ok': r.status_code == 200, 'status_code': r.status_code}
                if r.status_code != 200:
                    results['ok'] = False
            except Exception as e:
                results['components']['llm'] = {'ok': False, 'error': str(e)}
                results['ok'] = False
        return results

    async def ask_discovery_questions(self, session_id: str, message: str) -> Dict[str, Any]:
        s = self.sessions.get(session_id)
        if not s:
            raise KeyError('session not found')
        s['turns'].append({'from': 'client', 'text': message, 'ts': time.time()})
        # ensure slots dict exists
        slots = s.get('slots', {})
        # attempt extraction (best-effort)
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
        # small, robust extractor that uses the LLM via call_llm and parses JSON if possible
        prompt = f'Extract pain, users, kpi, budget from the message as a JSON object. Message: "{message}"'
        res = await self.call_llm(prompt, max_tokens=256, temperature=0.0)
        if not res.get('ok'):
            return
        text = res.get('text') or ''
        # try parse JSON
        try:
            import json
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
        # simple static fallback used by tests
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

    async def call_llm(self, prompt: str, max_tokens: int = 256, temperature: float = 0.2, timeout: int = 10) -> Dict[str, Any]:
        url = f"{self.llm_url}/v1/generate"
        payload = {'prompt': prompt, 'max_tokens': max_tokens, 'temperature': temperature}
        async with httpx.AsyncClient() as client:
            try:
                r = await client.post(url, json=payload, timeout=timeout)
                r.raise_for_status()
                body = r.json()
                t = body.get('text')
                if isinstance(t, str):
                    text = t
                elif isinstance(t, dict):
                    parts = t.get('parts') or []
                    if parts:
                        part = parts[0]
                        text = part if isinstance(part, str) else part.get('text')
                    else:
                        text = str(t)
                else:
                    text = str(t)
                return {'ok': True, 'text': text, 'meta': body}
            except Exception as e:
                return {'ok': False, 'error': str(e)}
 
import os
import uuid
import time
from typing import List, Dict, Optional, Any

import httpx

from .utils import generate_mock_examples

try:
    from .adapters import embeddings as embedding_adapter
except Exception:
    embedding_adapter = None


class PolarisAgent:
    """Async core implementation of POLARIS agent.

    Keeps the embedding integration pending and uses a static fallback.
    """

    def __init__(self, llm_url: Optional[str] = None, embedding_url: Optional[str] = None):
        self.llm_url = llm_url or os.getenv('LLM_URL', 'http://localhost:8100')
        self.embedding_url = embedding_url or os.getenv('EMBEDDING_URL', 'http://localhost:8001')
        self.sessions: Dict[str, Dict] = {}

    def create_session(self, client_id: Optional[str] = None, metadata: Optional[dict] = None) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            'session_id': session_id,
            'client_id': client_id,
            import os
            import uuid
            import time
            from typing import List, Dict, Optional, Any

            import httpx

            from .utils import generate_mock_examples

            try:
                from .adapters import embeddings as embedding_adapter
            except Exception:
                embedding_adapter = None


            class PolarisAgent:
                """Async core implementation of POLARIS agent.

                Keeps the embedding integration pending and uses a static fallback.
                """

                def __init__(self, llm_url: Optional[str] = None, embedding_url: Optional[str] = None):
                    self.llm_url = llm_url or os.getenv('LLM_URL', 'http://localhost:8100')
                    self.embedding_url = embedding_url or os.getenv('EMBEDDING_URL', 'http://localhost:8001')
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
                    return session_id

                async def health_check(self) -> Dict[str, Any]:
                    results: Dict[str, Any] = {'ok': True, 'components': {}}
                    async with httpx.AsyncClient() as client:
                        try:
                            r = await client.get(f"{self.llm_url}/v1/health", timeout=3.0)
                            results['components']['llm'] = {'ok': r.status_code == 200, 'status_code': r.status_code}
                            if r.status_code != 200:
                                results['ok'] = False
                        except Exception as e:
                            results['components']['llm'] = {'ok': False, 'error': str(e)}
                            results['ok'] = False
                    return results

                async def ask_discovery_questions(self, session_id: str, message: str) -> Dict[str, Any]:
                    s = self.sessions.get(session_id)
                    if not s:
                        raise KeyError('session not found')
                    s['turns'].append({'from': 'client', 'text': message, 'ts': time.time()})
                    # ensure slots dict exists
                    slots = s.get('slots', {})
                    # attempt to extract fields from incoming message and update session slots
                    try:
                        await self._extract_slots_from_message(s, message)
                    except Exception:
                        # extraction is best-effort; don't fail the whole flow on extractor errors
                        pass
                    # reload slots after attempted extraction
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
                    """Best-effort extraction of discovery slots from a user message using the LLM.

                    Writes to session['slots'] a dict with keys: pain, users, kpi, budget and optional confidence map.
                    The extractor will call `call_llm` with a prompt asking for strict JSON output. On parse failure
                    it will retry once with a corrective instruction.
                    """
                    prompt_template = (
                        'Extract the following fields from the user message as a JSON object with keys '
                        'pain, users, kpi, budget and confidence (0.0-1.0 per field). Return only valid JSON.\n\n'
                        'Message: "{message}"\n\n'
                        'Output example: {"pain": null, "users": null, "kpi": null, "budget": null, '
                        '"confidence": {"pain":0.0,"users":0.0,"kpi":0.0,"budget":0.0}}'
                    )
                    prompt = prompt_template.format(message=message)

                    # helper to try parse LLM response as JSON
                    def try_parse(resp_text: str) -> Optional[Dict[str, Any]]:
                        import json
                        try:
                            return json.loads(resp_text)
                        except Exception:
                            # attempt to find first JSON substring
                            import re
                            m = re.search(r"\{.*\}", resp_text, re.DOTALL)
                            if m:
                                try:
                                    return json.loads(m.group(0))
                                except Exception:
                                    return None
                            return None

                    # call LLM (best-effort)
                    res = await self.call_llm(prompt, max_tokens=256, temperature=0.0)
                    parsed = None
                    if res.get('ok'):
                        parsed = try_parse(res.get('text', '') or '')

                    # retry once with stricter instruction if parsing failed
                    if parsed is None:
                        retry_prompt = (
                            'You MUST output valid JSON only. Extract pain, users, kpi, budget and confidence. '\
                            'If unknown, use null. Message: "{message}"'
                        ).format(message=message)
                        res2 = await self.call_llm(retry_prompt, max_tokens=256, temperature=0.0)
                        if res2.get('ok'):
                            parsed = try_parse(res2.get('text', '') or '')

                    # if we have parsed output, sanitize and write to session slots
                    if isinstance(parsed, dict):
                        slots = session.get('slots') or {}
                        for key in ['pain', 'users', 'kpi', 'budget']:
                            v = parsed.get(key)
                            if v is not None:
                                slots[key] = v
                        # attach confidence map if present
                        if 'confidence' in parsed and isinstance(parsed['confidence'], dict):
                            slots['_confidence'] = parsed['confidence']
                        session['slots'] = slots

                async def select_portfolio(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
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

                async def call_llm(self, prompt: str, max_tokens: int = 256, temperature: float = 0.2, timeout: int = 10) -> Dict[str, Any]:
                    url = f"{self.llm_url}/v1/generate"
                    payload = {'prompt': prompt, 'max_tokens': max_tokens, 'temperature': temperature}
                    async with httpx.AsyncClient() as client:
                        try:
                            r = await client.post(url, json=payload, timeout=timeout)
                            r.raise_for_status()
                            body = r.json()
                            t = body.get('text')
                            if isinstance(t, str):
                                text = t
                            elif isinstance(t, dict):
                                parts = t.get('parts') or []
                                if parts:
                                    part = parts[0]
                                    text = part if isinstance(part, str) else part.get('text')
                                else:
                                    text = str(t)
                            else:
                                text = str(t)
                            return {'ok': True, 'text': text, 'meta': body}
                        except Exception as e:
                            return {'ok': False, 'error': str(e)}


class PolarisAgent:
    """Async core implementation of POLARIS agent.

    Keeps the embedding integration pending and uses a static fallback.
    """

    def __init__(self, llm_url: Optional[str] = None, embedding_url: Optional[str] = None):
        self.llm_url = llm_url or os.getenv('LLM_URL', 'http://localhost:8100')
        self.embedding_url = embedding_url or os.getenv('EMBEDDING_URL', 'http://localhost:8001')
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
        return session_id

    async def health_check(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {'ok': True, 'components': {}}
        async with httpx.AsyncClient() as client:
            try:
                r = await client.get(f"{self.llm_url}/v1/health", timeout=3.0)
                results['components']['llm'] = {'ok': r.status_code == 200, 'status_code': r.status_code}
                if r.status_code != 200:
                    results['ok'] = False
            except Exception as e:
                results['components']['llm'] = {'ok': False, 'error': str(e)}
                results['ok'] = False
        return results

    async def ask_discovery_questions(self, session_id: str, message: str) -> Dict[str, Any]:
        s = self.sessions.get(session_id)
        if not s:
            raise KeyError('session not found')
        s['turns'].append({'from': 'client', 'text': message, 'ts': time.time()})
        # ensure slots dict exists
        slots = s.get('slots', {})
        # attempt to extract fields from incoming message and update session slots
        try:
            await self._extract_slots_from_message(s, message)
        except Exception:
            # extraction is best-effort; don't fail the whole flow on extractor errors
            pass
        # reload slots after attempted extraction
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
        """Best-effort extraction of discovery slots from a user message using the LLM.

        Writes to session['slots'] a dict with keys: pain, users, kpi, budget and optional confidence map.
        The extractor will call `call_llm` with a prompt asking for strict JSON output. On parse failure
        it will retry once with a corrective instruction.
        """
        prompt_template = (
            'Extract the following fields from the user message as a JSON object with keys '
            'pain, users, kpi, budget and confidence (0.0-1.0 per field). Return only valid JSON.\n\n'
            'Message: "{message}"\n\n'
            'Output example: {"pain": null, "users": null, "kpi": null, "budget": null, '
            '"confidence": {"pain":0.0,"users":0.0,"kpi":0.0,"budget":0.0}}'
        )
        prompt = prompt_template.format(message=message)

        # helper to try parse LLM response as JSON
        def try_parse(resp_text: str) -> Optional[Dict[str, Any]]:
            import json
            try:
                return json.loads(resp_text)
            except Exception:
                # attempt to find first JSON substring
                import re
                m = re.search(r"\{.*\}", resp_text, re.DOTALL)
                if m:
                    try:
                        return json.loads(m.group(0))
                    except Exception:
                        return None
                return None

        # call LLM (best-effort)
        res = await self.call_llm(prompt, max_tokens=256, temperature=0.0)
        parsed = None
        if res.get('ok'):
            parsed = try_parse(res.get('text', '') or '')

        # retry once with stricter instruction if parsing failed
        if parsed is None:
            retry_prompt = (
                'You MUST output valid JSON only. Extract pain, users, kpi, budget and confidence. '\
                'If unknown, use null. Message: "{message}"'
            ).format(message=message)
            res2 = await self.call_llm(retry_prompt, max_tokens=256, temperature=0.0)
            if res2.get('ok'):
                parsed = try_parse(res2.get('text', '') or '')

        # if we have parsed output, sanitize and write to session slots
        if isinstance(parsed, dict):
            slots = session.get('slots') or {}
            for key in ['pain', 'users', 'kpi', 'budget']:
                v = parsed.get(key)
                if v is not None:
                    slots[key] = v
            # attach confidence map if present
            if 'confidence' in parsed and isinstance(parsed['confidence'], dict):
                slots['_confidence'] = parsed['confidence']
            session['slots'] = slots

    async def select_portfolio(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
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

    async def call_llm(self, prompt: str, max_tokens: int = 256, temperature: float = 0.2, timeout: int = 10) -> Dict[str, Any]:
        url = f"{self.llm_url}/v1/generate"
        payload = {'prompt': prompt, 'max_tokens': max_tokens, 'temperature': temperature}
        async with httpx.AsyncClient() as client:
            try:
                r = await client.post(url, json=payload, timeout=timeout)
                r.raise_for_status()
                body = r.json()
                t = body.get('text')
                if isinstance(t, str):
                    text = t
                elif isinstance(t, dict):
                    parts = t.get('parts') or []
                    if parts:
                        part = parts[0]
                        text = part if isinstance(part, str) else part.get('text')
                    else:
                        text = str(t)
                else:
                    text = str(t)
                return {'ok': True, 'text': text, 'meta': body}
            except Exception as e:
                return {'ok': False, 'error': str(e)}

    embedding_adapter = None


class PolarisAgent:
    """Async core implementation of POLARIS agent.

    Keeps the embedding integration pending and uses a static fallback.
    """

    def __init__(self, llm_url: Optional[str] = None, embedding_url: Optional[str] = None):
        self.llm_url = llm_url or os.getenv('LLM_URL', 'http://localhost:8100')
        self.embedding_url = embedding_url or os.getenv('EMBEDDING_URL', 'http://localhost:8001')
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
        return session_id

    async def health_check(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {'ok': True, 'components': {}}
        async with httpx.AsyncClient() as client:
            try:
                r = await client.get(f"{self.llm_url}/v1/health", timeout=3.0)
                results['components']['llm'] = {'ok': r.status_code == 200, 'status_code': r.status_code}
                if r.status_code != 200:
                    results['ok'] = False
            except Exception as e:
                results['components']['llm'] = {'ok': False, 'error': str(e)}
                results['ok'] = False
        return results

    async def ask_discovery_questions(self, session_id: str, message: str) -> Dict[str, Any]:
        s = self.sessions.get(session_id)
        if not s:
            raise KeyError('session not found')
        s['turns'].append({'from': 'client', 'text': message, 'ts': time.time()})
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

    async def select_portfolio(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
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

    async def call_llm(self, prompt: str, max_tokens: int = 256, temperature: float = 0.2, timeout: int = 10) -> Dict[str, Any]:
        url = f"{self.llm_url}/v1/generate"
        payload = {'prompt': prompt, 'max_tokens': max_tokens, 'temperature': temperature}
        async with httpx.AsyncClient() as client:
            try:
                r = await client.post(url, json=payload, timeout=timeout)
                r.raise_for_status()
                body = r.json()
                t = body.get('text')
                if isinstance(t, str):
                    text = t
                elif isinstance(t, dict):
                    parts = t.get('parts') or []
                    if parts:
                        part = parts[0]
                        text = part if isinstance(part, str) else part.get('text')
                    else:
                        text = str(t)
                else:
                    text = str(t)
                return {'ok': True, 'text': text, 'meta': body}
            except Exception as e:
                return {'ok': False, 'error': str(e)}
