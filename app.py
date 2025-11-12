from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Any
import time
import json

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

@app.patch("/api/v1/sessions/{session_id}/slots")
async def update_session_slots(session_id: str, slots: Dict[str, Any]):
    """Update session slots manually. Body should be a JSON object with slot keys/values.

    This endpoint is intentionally permissive and designed for debugging and tests. In
    production, restrict to authenticated clients and validate fields.
    """
    s = agent.sessions.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="session not found")
    current = s.get("slots") or {}
    current.update(slots)
    s["slots"] = current
    return {"session_id": session_id, "slots": s["slots"]}

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

@app.post("/api/v1/chat")
async def chat_endpoint(body: dict):
    """Lightweight conversational endpoint for free-form chat.

    Expects JSON with at least: {"message": "..."}
    Optionally: {"session_id": "..."}

    This endpoint uses the agent.call_llm helper to generate a humanized
    conversational reply. It will create a session if none is provided.
    """
    msg = body.get("message") if isinstance(body, dict) else None
    session_id = None
    if isinstance(body, dict):
        session_id = body.get("session_id")

    if not msg:
        raise HTTPException(status_code=400, detail="missing message")

    # ensure we have a session
    if not session_id:
        session_id = agent.create_session()

    # record the user turn
    s = agent.sessions.get(session_id)
    if s is None:
        raise HTTPException(status_code=404, detail="session not found")
    s.setdefault("turns", []).append({"from": "client", "text": msg, "ts": time.time()})

    # Build a simple prompt for the LLM that asks for a short, human reply.
    prompt = f"You are a helpful assistant. Reply in a concise, friendly and human tone to the user message: \"{msg}\""
    llm_res = await agent.call_llm(prompt, max_tokens=256, temperature=0.7)
    if not llm_res.get("ok"):
        raise HTTPException(status_code=502, detail="llm_error")
    text = llm_res.get("text") or ""

    # record assistant turn
    s.setdefault("turns", []).append({"from": "assistant", "text": text, "ts": time.time()})

    return {"response": text, "session_id": session_id}

@app.post("/api/v1/estimate", response_model=EstimateResponse)
async def estimate(body: EstimateRequest):
    e = await agent.estimate_development(body.features)
    return e


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for streaming chat with the agent."""
    await websocket.accept()

    # Connection state
    session_id = None
    full_response = ""

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            message = data.get('message', '')
            session_id = data.get('session_id', session_id)

            if not message:
                await websocket.send_json({
                    'type': 'error',
                    'error': 'Message is required'
                })
                continue

            # Ensure we have a session
            if not session_id:
                session_id = agent.create_session()
                await websocket.send_json({
                    'type': 'session_created',
                    'session_id': session_id
                })

            # Record user turn
            s = agent.sessions.get(session_id)
            if s is None:
                await websocket.send_json({
                    'type': 'error',
                    'error': 'Session not found'
                })
                continue

            s.setdefault("turns", []).append({
                "from": "client",
                "text": message,
                "ts": time.time()
            })

            # Build prompt for LLM
            prompt = f"You are a helpful assistant. Reply in a concise, friendly and human tone to the user message: \"{message}\""

            # Stream response
            full_response = ""
            try:
                async for chunk in agent.call_llm_stream(prompt, max_tokens=512, temperature=0.7):
                    if chunk['type'] == 'token':
                        full_response += chunk['text']
                        await websocket.send_json({
                            'type': 'token',
                            'text': chunk['text'],
                            'session_id': session_id
                        })
                    elif chunk['type'] == 'done':
                        # Record assistant turn
                        s.setdefault("turns", []).append({
                            "from": "assistant",
                            "text": full_response,
                            "ts": time.time()
                        })
                        await websocket.send_json({
                            'type': 'done',
                            'full_response': full_response,
                            'session_id': session_id
                        })
                        break
                    elif chunk['type'] == 'error':
                        await websocket.send_json({
                            'type': 'error',
                            'error': chunk['error']
                        })
                        break

            except Exception as e:
                await websocket.send_json({
                    'type': 'error',
                    'error': f'LLM error: {str(e)}'
                })

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        try:
            await websocket.send_json({
                'type': 'error',
                'error': f'Unexpected error: {str(e)}'
            })
        except:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
