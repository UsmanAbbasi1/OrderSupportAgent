# OrderSupportAgent – Reason-then-Verify Order Support

Minimal starter for a **reason-then-verify order support engine**:
- Accepts an order support case via API
- Classifies intent (order vs unknown)
- Extracts/requests an **order ID**
- Loads a mock order from an in-memory store
- Simulates a fix in a sandbox (e.g. status/payment/shipment consistency)
- Responds only after basic business rules pass verification
- Returns a full step trace for learning/debugging
- Uses a LangGraph-based orchestrator for the main case flow

---

## 1. Project setup

**Requirements**

- Python **3.10+**

**Create virtualenv and install deps**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If your system Python / `pytest` is misconfigured, fix that first (e.g. via `pyenv` or by reinstalling Python 3.10+), then re-run the above.

---

## 2. Environment variables

Optional LLM classifier (used to refine intent beyond simple rules):

- `OPENAI_API_KEY` – required **only** if you want to use the OpenAI-based classifier
- `VRSP_CLASSIFIER_MODEL` – optional, default: `gpt-4o-mini`

Example env setup (bash/zsh):

```bash
export OPENAI_API_KEY="your_api_key_here"
export VRSP_CLASSIFIER_MODEL="gpt-4o-mini"
```

The core order sandbox logic (mock DB + verification) does **not** depend on OpenAI.

---

## 3. Run the FastAPI server

From the project root:

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

FastAPI docs: <http://127.0.0.1:8000/docs>

Basic health check:

```bash
curl http://127.0.0.1:8000/health
```

---

## 4. Order support API endpoint

### 4.1 LangGraph orchestrator – `POST /cases/langgraph`

This is the only supported case endpoint. It runs the pipeline via LangGraph nodes and conditional edges:

- classification (order vs unknown)
- order ID extraction / clarification
- order sandbox + verification

Example (no order ID yet – expect clarification questions):

```bash
curl -X POST http://127.0.0.1:8000/cases/langgraph \
  -H "Content-Type: application/json" \
  -d '{
    "issue":"My order says delivered but I never received it.",
    "tenant_id":"demo-tenant",
    "app_id":"web-frontend",
    "time_range":"last_7d"
  }'
```

You should see `needs_clarification: true` and questions including "What is your order ID?".

Now include an order ID that exists in the mock store (e.g. `ORD-1001`, `ORD-1002`, `ORD-1003`):

```bash
curl -X POST http://127.0.0.1:8000/cases/langgraph \
  -H "Content-Type: application/json" \
  -d '{
    "issue":"Order ORD-1001 says delivered but I never got it.",
    "tenant_id":"demo-tenant",
    "app_id":"web-frontend",
    "time_range":"last_7d"
  }'
```

The response will include:

- `verified`: whether the sandboxed fix passes checks
- `resolution`: customer-facing explanation
- `trace`: step-by-step execution trace

Use this endpoint to demonstrate graph-based orchestration in client demos.

---

## 5. Technical flow (sticky-note style)

1. User describes an **order issue** in free text
2. FastAPI `/cases/langgraph` receives request
3. Input validation (`CaseCreateRequest`) + context initialization (`CaseContext`)
4. Classifier predicts intent (`orders.order_issue` vs `general.unknown`)
5. For order issues, try to parse `order_id` from the message
6. If intent is low-confidence or `order_id` is missing → respond with clarification questions
7. Once `order_id` is known, load mock order from the in-memory store
8. Run sandbox verification rules (status vs payment vs shipment)
9. Simulate a fix and re-run verification
10. If verified: respond with validated resolution + trace
11. If not verified: mark as escalated to a human Tier-2 agent


COMMANDS

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt