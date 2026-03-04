from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal, TypedDict

from app.agents.pipeline import (
    build_clarification_questions,
    classify_issue,
    intake,
    needs_clarification,
    resolve_case,
)
from app.models import CaseContext, CaseCreateRequest, CaseResponse


class GraphState(TypedDict, total=False):
    """State payload shared across LangGraph nodes."""

    context: CaseContext
    verified: bool
    resolution: str
    confidence: float
    escalated: bool
    clarification_questions: list[str]


def _intake_node(state: GraphState) -> GraphState:
    """Record intake metadata into the shared case trace."""
    context = state["context"]
    intake(context)
    return {"context": context}


def _classify_node(state: GraphState) -> GraphState:
    """Classify issue intent and confidence for downstream routing."""
    context = state["context"]
    classify_issue(context)
    return {"context": context}


def _route_after_classify(state: GraphState) -> Literal["clarify", "proceed"]:
    """Route low-confidence cases to clarification, others to resolution."""
    context = state["context"]
    return "clarify" if needs_clarification(context) else "proceed"


def _clarification_node(state: GraphState) -> GraphState:
    """Build clarification response when intent confidence is below threshold."""
    context = state["context"]
    return {
        "context": context,
        "verified": False,
        "resolution": "Need more details before safe investigation and verification.",
        "confidence": context.intent_confidence,
        "escalated": False,
        "clarification_questions": build_clarification_questions(context),
    }


def _resolve_node(state: GraphState) -> GraphState:
    """Run full investigation/verification flow and produce final response fields."""
    context = state["context"]
    verified, resolution, confidence, escalated = resolve_case(context)
    return {
        "context": context,
        "verified": verified,
        "resolution": resolution,
        "confidence": confidence,
        "escalated": escalated,
    }


@lru_cache(maxsize=1)
def _get_graph() -> Any:
    """Compile and cache the LangGraph app used by the endpoint."""
    try:
        from langgraph.graph import END, START, StateGraph
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "LangGraph is not installed. Install dependencies from requirements.txt first."
        ) from exc

    graph = StateGraph(GraphState)
    graph.add_node("intake", _intake_node)
    graph.add_node("classify", _classify_node)
    graph.add_node("clarify", _clarification_node)
    graph.add_node("resolve", _resolve_node)

    graph.add_edge(START, "intake")
    graph.add_edge("intake", "classify")
    graph.add_conditional_edges(
        "classify",
        _route_after_classify,
        {"clarify": "clarify", "proceed": "resolve"},
    )
    graph.add_edge("clarify", END)
    graph.add_edge("resolve", END)

    return graph.compile()


def run_case_langgraph(request: CaseCreateRequest) -> CaseResponse:
    """Execute case handling through LangGraph and map final state to API model."""
    context = CaseContext(request=request)
    app = _get_graph()
    state = app.invoke({"context": context})
    questions = state.get("clarification_questions", [])

    if questions:
        return CaseResponse(
            case_id=context.case_id,
            verified=False,
            resolution=state["resolution"],
            confidence=state["confidence"],
            escalated=state["escalated"],
            predicted_intent=context.predicted_intent,
            needs_clarification=True,
            clarification_questions=questions,
            trace=context.trace,
        )

    return CaseResponse(
        case_id=context.case_id,
        verified=state.get("verified", False),
        resolution=state.get("resolution", ""),
        confidence=state.get("confidence", 0.0),
        escalated=state.get("escalated", True),
        predicted_intent=context.predicted_intent,
        trace=context.trace,
    )
