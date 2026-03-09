export type CaseRequest = {
  issue: string;
  tenant_id: string;
  app_id: string;
  time_range?: string;
  attachments?: string[];
};

export type StepTrace = {
  step: string;
  status: string;
  details: Record<string, unknown>;
  timestamp: string;
};

export type CaseResponse = {
  case_id: string;
  verified: boolean;
  resolution: string;
  confidence: number;
  escalated: boolean;
  predicted_intent: string;
  needs_clarification: boolean;
  clarification_questions: string[];
  trace: StepTrace[];
};

export async function createCase(request: CaseRequest): Promise<CaseResponse> {
  const response = await fetch("/api/cases/langgraph", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const detail = await response.text().catch(() => "");
    throw new Error(
      `Request failed with status ${response.status}${
        detail ? `: ${detail}` : ""
      }`
    );
  }

  return (await response.json()) as CaseResponse;
}

