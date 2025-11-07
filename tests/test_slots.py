import asyncio
import json

import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_patch_slots_updates_session():
    from polaris.app import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # create session
        r = await ac.post('/api/v1/sessions', json={"client_id": "test"})
        assert r.status_code == 200 or r.status_code == 201
        data = r.json()
        sid = data.get('session_id')
        assert sid

        # patch slots
        r2 = await ac.patch(f'/api/v1/sessions/{sid}/slots', json={"budget": "30000"})
        assert r2.status_code == 200
        body = r2.json()
        assert body['session_id'] == sid
        assert body['slots'].get('budget') == '30000'


@pytest.mark.asyncio
async def test_discovery_flow_with_extractor(monkeypatch):
    from polaris import app as pol_app
    app = pol_app.app

    # fake call_llm to return an extraction JSON
    async def fake_call_llm(prompt, max_tokens=256, temperature=0.0, timeout=10):
        return {
            'ok': True,
            'text': json.dumps({
                'pain': 'Preciso reduzir churn',
                'users': 'Clientes B2C mobile',
                'kpi': 'retenção',
                'budget': '20000',
                'confidence': {'pain': 0.9, 'users': 0.8, 'kpi': 0.85, 'budget': 0.7}
            })
        }

    # patch the agent instance in the app
    monkeypatch.setattr(pol_app, 'agent', pol_app.agent)
    monkeypatch.setattr(pol_app.agent, 'call_llm', fake_call_llm)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post('/api/v1/sessions', json={"client_id": "tester"})
        assert r.status_code in (200, 201)
        sid = r.json()['session_id']

        # send discovery message
        payload = {"session_id": sid, "message": "Quero reduzir churn entre usuários mobile"}
        r2 = await ac.post('/api/v1/discovery', json=payload)
        assert r2.status_code == 200
        out = r2.json()
        # extractor should have filled slots
        slots = out.get('slots')
        assert slots
        assert slots.get('pain') == 'Preciso reduzir churn'
        assert slots.get('users') == 'Clientes B2C mobile'
        # flow should eventually be complete because all slots are present
        assert out.get('complete') is True
