from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class HealthResponse(BaseModel):
    ok: bool
    components: Dict[str, Any]


class SessionCreate(BaseModel):
    client_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SessionResponse(BaseModel):
    session_id: str


class DiscoveryMessage(BaseModel):
    session_id: str
    message: str


class PortfolioCandidate(BaseModel):
    id: int
    title: str
    score: float
    rationale: Optional[str]


class DiscoveryResponse(BaseModel):
    next_question: Optional[str]
    slots: Dict[str, Any]
    complete: bool
    actions: Optional[List[Dict[str, Any]]] = None


class PrototypeRequest(BaseModel):
    session_id: str
    choice_id: int
    context: Optional[Dict[str, Any]] = None


class PrototypeResponse(BaseModel):
    artifact: Dict[str, Any]


class MockRequest(BaseModel):
    session_id: str
    contract_name: str
    context: Optional[Dict[str, Any]] = None
    count: int = Field(default=10, ge=1, le=100)


class MockResponse(BaseModel):
    mocks: List[Dict[str, Any]]


class EstimateRequest(BaseModel):
    session_id: str
    features: List[str]


class EstimateResponse(BaseModel):
    total_hours: int
    breakdown: List[Dict[str, Any]]
    t_shirt: str
