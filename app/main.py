from fastapi import FastAPI, HTTPException

from app.core.langgraph_orchestrator import run_case_langgraph
from app.models import CaseCreateRequest, CaseResponse

app = FastAPI(title="OrderSupportAgent", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
@app.post("/cases/langgraph", response_model=CaseResponse)
def create_case_langgraph(payload: CaseCreateRequest) -> CaseResponse:
    try:
        return run_case_langgraph(payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
