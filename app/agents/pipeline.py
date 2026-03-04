from __future__ import annotations

import json
import os
import re
from copy import deepcopy
from datetime import datetime, timezone

from app.models import CaseContext, StepTrace


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_order_issue(context: CaseContext) -> bool:
    return context.predicted_intent.startswith("orders.")


MOCK_ORDERS: dict[str, dict] = {
    # Delivery status mismatch: marked DELIVERED but shipment not delivered.
    "ORD-1001": {
        "id": "ORD-1001",
        "user_id": "U-1",
        "status": "DELIVERED",
        "payment_status": "CAPTURED",
        "shipment_status": "IN_TRANSIT",
        "total_amount": 49.99,
    },
    # Payment captured but order still pending.
    "ORD-1002": {
        "id": "ORD-1002",
        "user_id": "U-1",
        "status": "PENDING",
        "payment_status": "CAPTURED",
        "shipment_status": "NOT_SHIPPED",
        "total_amount": 79.00,
    },
    # Healthy order with no issues.
    "ORD-1003": {
        "id": "ORD-1003",
        "user_id": "U-2",
        "status": "DELIVERED",
        "payment_status": "CAPTURED",
        "shipment_status": "DELIVERED",
        "total_amount": 19.99,
    },
}


ORDER_ID_PATTERN = re.compile(r"\b(?:order\s*#?|order_id\s*#?|id\s*#?)\s*([A-Za-z0-9-]+)\b", re.IGNORECASE)


def _extract_order_id(issue: str) -> str | None:
    """Best-effort extraction of an order ID from free-form text.

    Looks for patterns like "order 1234", "order #1234", or "order_id ABC-1".
    """

    match = ORDER_ID_PATTERN.search(issue)
    if match:
        return match.group(1)
    return None


def _rule_classify(issue: str) -> tuple[str, float, list[str]]:
    """Very small rule-based classifier focused only on order/delivery issues.

    On real systems this would be replaced by a richer rule engine or LLM.
    """

    order_strong = [
        "wrong item",
        "wrong items",
        "wrong sku",
        "incorrect item",
        "item mismatch",
        "delivered but",
        "never received",
        "charged twice",
        "double charged",
    ]
    order_medium = ["order", "delivery", "package", "refund", "charge", "status"]
    order_weak = ["tracking", "courier", "shipment", "shipping"]

    order_score = 0.0
    signals: list[str] = []

    for token in order_strong:
        if token in issue:
            order_score += 0.55
            signals.append(f"rule:order_strong:{token}")
    for token in order_medium:
        if token in issue:
            order_score += 0.25
            signals.append(f"rule:order_medium:{token}")
    for token in order_weak:
        if token in issue:
            order_score += 0.10
            signals.append(f"rule:order_weak:{token}")

    if order_score >= 0.5:
        return "orders.order_issue", min(0.95, 0.6 + order_score / 2), signals

    # Fall back to unknown if the signal is weak.
    return "general.unknown", 0.45, signals or ["rule:ambiguous_or_low_signal"]


def _llm_classify(issue: str, tenant_id: str, app_id: str) -> tuple[str, float, list[str]] | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI
    except Exception:
        return None

    client = OpenAI(api_key=api_key)
    model = os.getenv("VRSP_CLASSIFIER_MODEL", "gpt-4o-mini")
    prompt = (
        "Classify the support issue into one intent from this list: "
        "orders.order_issue, general.unknown. "
        "Return strict JSON with keys: intent, confidence, signals. "
        "confidence must be a float in [0,1]. signals must be a short string array."
    )
    user_input = {
        "issue": issue,
        "tenant_id": tenant_id,
        "app_id": app_id,
    }

    try:
        response = client.responses.create(
            model=model,
            temperature=0,
            input=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(user_input)},
            ],
            text={"format": {"type": "json_object"}},
        )
        content = getattr(response, "output_text", None) or "{}"
        payload = json.loads(content)
        intent = str(payload.get("intent", "general.unknown"))
        confidence = float(payload.get("confidence", 0.5))
        signals = payload.get("signals", [])
        if not isinstance(signals, list):
            signals = ["llm:malformed_signals"]
        if intent not in {"orders.order_issue", "general.unknown"}:
            intent = "general.unknown"
        confidence = max(0.0, min(1.0, confidence))
        return intent, confidence, [f"llm:{s}" for s in signals]
    except Exception:
        return None


def add_trace(context: CaseContext, step: str, status: str, details: dict) -> None:
    context.trace.append(
        StepTrace(
            step=step,
            status=status,
            details=details,
            timestamp=_now_iso(),
        )
    )


def intake(context: CaseContext) -> None:
    add_trace(
        context,
        "intake",
        "ok",
        {
            "issue_excerpt": context.request.issue[:120],
            "tenant_id": context.request.tenant_id,
            "app_id": context.request.app_id,
        },
    )


def classify_issue(context: CaseContext) -> None:
    raw_issue = context.request.issue
    issue = raw_issue.lower()
    intent, confidence, signals = _rule_classify(issue)
    mode = "rules"

    if confidence < 0.75:
        llm_result = _llm_classify(issue, context.request.tenant_id, context.request.app_id)
        if llm_result is not None:
            intent, confidence, llm_signals = llm_result
            signals = signals + llm_signals
            mode = "rules+llm"
        else:
            signals = signals + ["llm:unavailable_or_skipped"]

    context.predicted_intent = intent
    context.intent_confidence = confidence
    context.intent_signals = signals

    if _is_order_issue(context):
        context.order_id = _extract_order_id(raw_issue)

    add_trace(
        context,
        "classifier",
        "ok",
        {
            "predicted_intent": context.predicted_intent,
            "intent_confidence": context.intent_confidence,
            "signals": context.intent_signals,
            "mode": mode,
        },
    )


def needs_clarification(context: CaseContext, threshold: float = 0.75) -> bool:
    """Decide whether the agent should ask the user for more information.

    For order issues, we *always* ask for clarification if we do not yet have
    an order ID, even when the intent classification is confident. For other
    intents we fall back to the confidence threshold only.
    """

    if _is_order_issue(context) and not context.order_id:
        return True
    return context.intent_confidence < threshold


def build_clarification_questions(context: CaseContext) -> list[str]:
    issue_lower = context.request.issue.lower()
    if _is_order_issue(context) or "package" in issue_lower or "delivery" in issue_lower:
        questions: list[str] = ["What is your order ID?"]
        if "wrong" in issue_lower or "item" in issue_lower:
            questions.append("Which item did you expect, and which item did you receive?")
        questions.append("Was any item missing, wrong, or damaged?")
        return questions

    return [
        "Can you share the exact error message you see?",
        "When did this issue start, and is it still happening now?",
        "Which feature or page were you using when it happened?",
    ]


def _load_order(order_id: str) -> dict | None:
    """Load an order from the in-memory sandbox store.

    In a real system, this would query a database or upstream Order Service.
    """

    order = MOCK_ORDERS.get(order_id)
    return deepcopy(order) if order is not None else None


def _verify_order(order: dict) -> tuple[bool, list[str]]:
    """Check basic consistency rules for an order.

    This is our "sandbox" verification step: instead of trusting a fix blindly,
    we assert simple business invariants.
    """

    issues: list[str] = []
    status = order.get("status")
    payment_status = order.get("payment_status")
    shipment_status = order.get("shipment_status")

    if status == "DELIVERED" and shipment_status != "DELIVERED":
        issues.append("Order marked DELIVERED but shipment_status is not DELIVERED.")

    if payment_status == "CAPTURED" and status == "PENDING":
        issues.append("Payment captured but order status is still PENDING.")

    return (len(issues) == 0), issues


def _simulate_fix(order: dict) -> tuple[dict, list[str]]:
    """Propose and apply a simple fix, then re-verify the order.

    This function is intentionally simple but demonstrates the
    reason-then-verify pattern: we look at issues, change fields, and then
    call ``_verify_order`` again on the modified order.
    """

    fixed = deepcopy(order)
    _, issues = _verify_order(order)

    for issue in issues:
        if "shipment_status is not DELIVERED" in issue:
            # Safer move in absence of shipment confirmation is to roll the
            # order status back from DELIVERED.
            fixed["status"] = "IN_TRANSIT"
            fixed["shipment_status"] = "IN_TRANSIT"
        if "status is still PENDING" in issue:
            # If payment is captured but the order is PENDING, move it to PAID.
            fixed["status"] = "PAID"

    verified, remaining = _verify_order(fixed)
    if not verified and not remaining:
        # Should not normally happen, but keep behaviour explicit.
        remaining = ["Unknown verification failure after applying fixes."]
    return fixed, remaining


def resolve_case(context: CaseContext) -> tuple[bool, str, float, bool]:
    """Resolve a support case from intent to final customer response.

    This function is intentionally "all-in-one": it does the full decision flow in one
    place instead of many small internal agent steps.

    What it does:
    1) Reads the predicted intent already stored in ``context`` (for example:
       ``orders.wrong_item``).
    2) Loads the relevant data for that intent into ``context.raw_data``.
    3) Produces investigation findings in ``context.evidence``.
    4) Chooses a candidate fix and stores it in ``context.verified_fix``.
    5) Decides whether the fix is verified or should be escalated.
    6) Builds confidence + response text and appends trace entries.

    Example (missing/wrong item case):
    - Input intent: ``orders.wrong_item``.
    - Data loaded: order record + warehouse scans + shipment event + runbook.
    - Finding: picked SKU does not match expected order SKU.
    - Fix selected: create replacement shipment and issue return label.
    - Output: verified=True, escalated=False, confidence=0.91, and a validated
      customer-facing resolution string.

    Returns:
        tuple[bool, str, float, bool]:
        ``(verified, resolution, confidence, escalated)``
    """

    if _is_order_issue(context):
        order_id = context.order_id
        if not order_id:
            # Should normally be caught earlier by needs_clarification, but keep
            # a safety net here.
            context.raw_data = {"error": "missing_order_id"}
            context.evidence = {
                "likely_component": "order_intake",
                "root_signal": "order_id_missing",
                "impact": "cannot safely identify which order to fix",
            }
            context.verified_fix = None
            verified = False
            confidence = context.intent_confidence
            escalated = True
            resolution = "I need a valid order ID to safely investigate and fix this order."
        else:
            original_order = _load_order(order_id)
            if original_order is None:
                context.raw_data = {"order_id": order_id, "found": False}
                context.evidence = {
                    "likely_component": "order_lookup",
                    "root_signal": "order_not_found",
                    "impact": "cannot validate any fix without the order record",
                }
                context.verified_fix = None
                verified = False
                confidence = 0.6
                escalated = True
                resolution = (
                    f"I could not find an order with ID {order_id}. Please double-check "
                    "the ID or contact support."
                )
            else:
                ok_before, issues_before = _verify_order(original_order)
                fixed_order, issues_after = _simulate_fix(original_order)
                ok_after, _ = _verify_order(fixed_order)

                context.raw_data = {
                    "order_before": original_order,
                    "order_after": fixed_order,
                }
                context.evidence = {
                    "likely_component": "order_state",
                    "issues_before": issues_before,
                    "issues_after": issues_after,
                }
                context.verified_fix = {
                    "order_id": order_id,
                    "before": original_order,
                    "after": fixed_order,
                }

                verified = ok_after
                escalated = not ok_after
                if ok_before and ok_after:
                    confidence = 0.9
                    resolution = (
                        "I checked the current state of your order in our sandbox and it "
                        "already looks consistent and delivered correctly. No changes "
                        "were needed."
                    )
                elif ok_after:
                    confidence = 0.9
                    resolution = (
                        "I identified inconsistencies in the order data (for example, "
                        "delivery or payment status not lining up). I simulated a fix in "
                        "a sandbox by updating the order status and re-running checks. "
                        "The updated order now passes all verification rules."
                    )
                else:
                    confidence = 0.6
                    resolution = (
                        "I attempted to automatically fix the order in a sandbox, but the "
                        "data still violates one or more safety checks. I'm escalating "
                        "this case to a human agent to avoid making an incorrect change."
                    )
    else:
        context.raw_data = {
            "ticket_history": ["Mixed signals in recent customer messages"],
            "logs": [],
            "metrics": {},
            "runbooks": ["General triage checklist"],
        }
        context.evidence = {
            "likely_component": "unknown",
            "root_signal": "insufficient issue specificity",
            "impact": "cannot safely propose a verified fix",
        }
        context.verified_fix = None
        verified = False
        confidence = 0.42
        escalated = True
        resolution = "Unable to validate a safe fix within retry budget. Escalating to Tier-2 human engineer."

    add_trace(
        context,
        "resolver",
        "ok",
        {
            "predicted_intent": context.predicted_intent,
            "likely_component": context.evidence.get("likely_component"),
            "verified": verified,
        },
    )
    add_trace(
        context,
        "response",
        "ok",
        {"verified": verified, "confidence": confidence, "escalated": escalated},
    )
    return verified, resolution, confidence, escalated
