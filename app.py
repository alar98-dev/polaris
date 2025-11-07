from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any

from .agent import PolarisAgent
from .schemas import (
    HealthResponse,
    SessionCreate,
    SessionResponse,
    DiscoveryMessage,
    DiscoveryResponse,
    PrototypeRequest,
    PrototypeResponse,
    MockRequest,
    MockResponse,
    EstimateRequest,
    EstimateResponse,
)

app = FastAPI(title="POLARIS Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


agent = PolarisAgent()


@app.get("/api/v1/health", response_model=HealthResponse)
async def health():
    return await agent.health_check()


@app.post("/api/v1/sessions", response_model=SessionResponse)
async def create_session(body: SessionCreate):
    sid = agent.create_session(client_id=body.client_id, metadata=body.metadata)
    return {"session_id": sid}


@app.patch('/api/v1/sessions/{session_id}/slots')
async def update_session_slots(session_id: str, slots: Dict[str, Any]):
    """Update session slots manually. Body should be a JSON object with slot keys/values.

    This endpoint is intentionally permissive and designed for debugging and tests. In
    production, restrict to authenticated clients and validate fields.
    """
    s = agent.sessions.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail='session not found')
    current = s.get('slots') or {}
    current.update(slots)
    s['slots'] = current
    return {"session_id": session_id, "slots": s['slots']}


@app.post("/api/v1/discovery", response_model=DiscoveryResponse)
async def discovery(msg: DiscoveryMessage):
    try:
        out = await agent.ask_discovery_questions(msg.session_id, msg.message)
        return out
    except KeyError:
        raise HTTPException(status_code=404, detail="session not found")


@app.post("/api/v1/prototype", response_model=PrototypeResponse)
async def prototype(body: PrototypeRequest):
    res = await agent.generate_prototype(body.choice_id, body.context or {})
    return res


@app.post("/api/v1/mocks", response_model=MockResponse)
async def mocks(body: MockRequest):
    m = await agent.generate_mock(body.contract_name, body.context or {}, count=body.count)
    return {"mocks": m}


@app.post("/api/v1/estimate", response_model=EstimateResponse)
async def estimate(body: EstimateRequest):
    e = await agent.estimate_development(body.features)
    return e
