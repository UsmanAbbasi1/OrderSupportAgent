from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class CaseCreateRequest(BaseModel):
    issue: str = Field(min_length=5, max_length=3000)
    tenant_id: str = Field(min_length=2, max_length=128)
    app_id: str = Field(min_length=2, max_length=128)
    time_range: str = Field(default="last_24h")
    attachments: list[str] = Field(default_factory=list)


class StepTrace(BaseModel):
    step: str
    status: str
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: str


class CaseResponse(BaseModel):
    case_id: str
    verified: bool
    resolution: str
    confidence: float = Field(ge=0.0, le=1.0)
    escalated: bool
    predicted_intent: str
    needs_clarification: bool = False
    clarification_questions: list[str] = Field(default_factory=list)
    trace: list[StepTrace]


class CaseContext(BaseModel):
    case_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    request: CaseCreateRequest
    # Parsed order identifier (if present in the customer message).
    order_id: str | None = Field(default=None)
    raw_data: dict[str, Any] = Field(default_factory=dict)
    evidence: dict[str, Any] = Field(default_factory=dict)
    hypotheses: list[dict[str, Any]] = Field(default_factory=list)
    verified_fix: dict[str, Any] | None = None
    predicted_intent: str = "general.unknown"
    intent_confidence: float = 0.0
    intent_signals: list[str] = Field(default_factory=list)
    trace: list[StepTrace] = Field(default_factory=list)
