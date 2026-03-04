# Frontend Integration Guide

This document explains how a frontend (web or mobile) should integrate with the VRSP order support API.

The backend exposes a FastAPI service with a single main endpoint:

- `POST /cases/langgraph` – LangGraph-based orchestrator

This endpoint accepts the JSON payload below and returns the same response model.

---

## 1. Core concepts

**Case**
- A single customer issue (e.g. "My order says delivered but I never received it.").
- Frontend sends one case at a time.

**Clarification**
- If the backend does not have enough information (especially missing `order_id`), it returns:
  - `needs_clarification: true`
  - `clarification_questions: [...]`
- The frontend must display these questions and collect answers from the user.

**Sandboxed resolution**
- Once the backend has an order ID and a clear order-related issue, it:
  - loads a mock order
  - simulates a fix in a sandbox
  - returns a **verified** customer-facing `resolution` string.

---

## 2. Request payload

The `/cases/langgraph` endpoint expects:

```json
{
  "issue": "string, required",
  "tenant_id": "string, required",
  "app_id": "string, required",
  "time_range": "string, optional (e.g. 'last_24h')",
  "attachments": ["optional list of attachment IDs"]
}
```

For this MVP you can usually set:

- `tenant_id`: a fixed string for the environment, e.g. `"demo-tenant"`
- `app_id`: identifier for the calling app, e.g. `"web-frontend"`
- `time_range`: `"last_7d"` or similar.

The important field is **`issue`**, which should contain the free-text description from the customer, including the order ID if available (e.g. `"Order ORD-1001 says delivered but I never got it"`).

---

## 3. Response shape

The response from both endpoints looks like:

```json
{
  "case_id": "string",
  "verified": true,
  "resolution": "string",
  "confidence": 0.9,
  "escalated": false,
  "predicted_intent": "orders.order_issue",
  "needs_clarification": false,
  "clarification_questions": [],
  "trace": [
    {
      "step": "classifier",
      "status": "ok",
      "details": {"predicted_intent": "orders.order_issue"},
      "timestamp": "..."
    }
  ]
}
```

Key fields for frontend:

- `needs_clarification` (bool)
- `clarification_questions` (array of strings)
- `resolution` (string)
- `verified` (bool)

You can ignore the low-level `trace` for UI purposes (but it is useful for debugging / demos).

---

## 4. Typical frontend flow

### 4.1 First message (no order ID)

1. User types: "My order says delivered but I never received it."
2. Frontend POSTs to `/cases/langgraph`:

```json
{
  "issue": "My order says delivered but I never received it.",
  "tenant_id": "demo-tenant",
  "app_id": "web-frontend",
  "time_range": "last_7d"
}
```

3. Backend responds with `needs_clarification: true` and questions like:
   - "What is your order ID?"
   - "Was any item missing, wrong, or damaged?"

4. Frontend shows these questions (one by one or as a list) and captures the answers.

### 4.2 Second message (with order ID)

Once the user provides the order ID, send a **new** request, embedding the ID into `issue`:

```json
{
  "issue": "Order ORD-1001 says delivered but I never got it.",
  "tenant_id": "demo-tenant",
  "app_id": "web-frontend",
  "time_range": "last_7d"
}
```

The backend will:

- detect an order-related issue,
- extract `ORD-1001` as the order ID,
- load the mock order from its in-memory store,
- run sandbox verification and simulate a fix,
- return a **final** resolution (usually with `needs_clarification: false`).

The frontend should now:

- display `resolution` to the user as the answer,
- optionally show a small "Verified automatically" label if `verified == true` and `escalated == false`.

---

## 5. Endpoint to use

Use `POST /cases/langgraph` for all integrations. It is the single source of truth and runs the LangGraph-based execution.

---

## 6. Error handling and timeouts

From the frontend perspective:

- Treat non-2xx HTTP responses as errors (show a generic "Something went wrong" and log details).
- For 500s from `/cases/langgraph`, the backend will return a JSON `detail` field with a message. Log this for debugging.
- Implement a reasonable timeout (e.g. 10–20 seconds) on the HTTP request.

If you see repeated errors in development, share the full response payload and the `trace` with the backend owner.

---

## 7. Local development URLs

When running locally with Uvicorn:

- Base URL: `http://127.0.0.1:8000`
- Health: `GET /health`
- Cases (LangGraph): `POST /cases/langgraph`
- Swagger UI: `GET /docs`

