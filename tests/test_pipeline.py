from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app
from app.models import CaseResponse


client = TestClient(app)


def test_langgraph_order_issue_without_order_id_triggers_clarification() -> None:
    payload = {
        "issue": "My order says delivered but I never received it.",
        "tenant_id": "demo-tenant",
        "app_id": "web-frontend",
        "time_range": "last_7d",
    }

    response = client.post("/cases/langgraph", json=payload)
    assert response.status_code == 200

    body = response.json()
    assert body["verified"] is False
    assert body["needs_clarification"] is True
    assert any(
        "order id" in q.lower() for q in body["clarification_questions"]
    )


def test_langgraph_order_issue_with_order_id_returns_verified_resolution() -> None:
    payload = {
        "issue": "Order ORD-1001 says delivered but I never got it.",
        "tenant_id": "demo-tenant",
        "app_id": "web-frontend",
        "time_range": "last_7d",
    }

    response = client.post("/cases/langgraph", json=payload)
    assert response.status_code == 200

    body = response.json()
    assert body["needs_clarification"] is False
    assert body["verified"] is True
    assert body["escalated"] is False
    assert body["predicted_intent"] == "orders.order_issue"
    assert isinstance(body["trace"], list)
    assert body["trace"], "trace should not be empty"


def test_langgraph_endpoint_is_wired() -> None:
    payload = {
        "issue": "My order was delivered with wrong items.",
        "tenant_id": "shop-acme",
        "app_id": "order-service",
        "time_range": "last_7d",
    }

    def _fake_run_case_langgraph(_payload: object) -> CaseResponse:
        return CaseResponse(
            case_id="demo-case-id",
            verified=True,
            resolution="Validated fix from LangGraph path.",
            confidence=0.9,
            escalated=False,
            predicted_intent="orders.order_issue",
            trace=[],
        )

    original = main_module.run_case_langgraph
    main_module.run_case_langgraph = _fake_run_case_langgraph
    try:
        response = client.post("/cases/langgraph", json=payload)
    finally:
        main_module.run_case_langgraph = original

    assert response.status_code == 200
    body = response.json()
    assert body["case_id"] == "demo-case-id"
    assert body["resolution"] == "Validated fix from LangGraph path."
