import { CaseResponse } from "../../api";

type Props = {
  ui:
    | { status: "idle" }
    | { status: "loading" }
    | { status: "error"; message: string }
    | { status: "success"; data: CaseResponse };
};

export function CaseOutcome({ ui }: Props) {
  if (ui.status === "error") {
    return (
      <section className="space-y-3">
        <OutcomeCard>
          <h2 className="text-sm font-semibold text-rose-300">Error</h2>
          <p className="mt-1 text-xs text-rose-200">{ui.message}</p>
          <p className="mt-2 text-[11px] text-rose-300/80">
            Check that your FastAPI server is running on{" "}
            <code className="rounded bg-rose-900/40 px-1 py-0.5 text-[10px]">
              http://127.0.0.1:8000
            </code>{" "}
            and that you are using the{" "}
            <code className="rounded bg-rose-900/40 px-1 py-0.5 text-[10px]">
              /cases/langgraph
            </code>{" "}
            endpoint.
          </p>
        </OutcomeCard>
      </section>
    );
  }

  const success = ui.status === "success" ? ui.data : null;
  const clarificationQuestions =
    success && success.needs_clarification
      ? success.clarification_questions
      : [];

  return (
    <section className="space-y-3">
      <OutcomeCard>
        <div className="flex items-center justify-between gap-2">
          <h2 className="text-sm font-semibold text-slate-100">
            {success ? "Outcome" : "Outcome preview"}
          </h2>
          {success && (
            <span className="text-[11px] text-slate-500 font-mono">
              {success.case_id}
            </span>
          )}
        </div>

        {ui.status === "idle" && (
          <p className="mt-2 text-xs text-slate-500">
            Submit an issue to see the verified resolution or clarification
            questions here. Start without an order ID to see the clarification
            flow, then follow up with a message that includes{" "}
            <code className="rounded bg-slate-800 px-1 py-0.5 text-[10px] text-slate-200">
              ORD-1001
            </code>
            .
          </p>
        )}

        {ui.status === "loading" && (
          <div className="mt-3 space-y-2 text-xs">
            <p className="text-emerald-300">
              Running orchestrator and sandbox verification...
            </p>
            <div className="flex gap-1">
              <span className="h-1.5 w-16 rounded-full bg-emerald-500/50 animate-pulse" />
              <span className="h-1.5 w-10 rounded-full bg-emerald-500/30 animate-pulse" />
            </div>
          </div>
        )}

        {success && (
          <div className="mt-3 space-y-3 text-xs">
            <div className="flex items-center gap-2">
              <span
                className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ${
                  success.verified && !success.escalated
                    ? "bg-emerald-500/15 text-emerald-300 border border-emerald-500/50"
                    : success.escalated
                    ? "bg-amber-500/15 text-amber-300 border border-amber-500/50"
                    : "bg-slate-700/60 text-slate-100 border border-slate-500/60"
                }`}
              >
                {success.verified && !success.escalated
                  ? "Verified automatically"
                  : success.escalated
                  ? "Escalated to human"
                  : "Unverified"}
              </span>
              <span className="text-slate-500">
                Confidence: {(success.confidence * 100).toFixed(0)}%
              </span>
              <span className="ml-auto text-[11px] text-slate-500">
                {success.predicted_intent}
              </span>
            </div>

            {clarificationQuestions.length > 0 && (
              <div className="space-y-1.5">
                <p className="font-medium text-slate-100">
                  Clarification needed
                </p>
                <ul className="list-disc list-inside space-y-1 text-slate-200">
                  {clarificationQuestions.map((q, idx) => (
                    <li key={idx}>{q}</li>
                  ))}
                </ul>
                <p className="text-slate-400">
                  Answer these questions in your next message and include your
                  order ID so the sandbox can load the correct mock order.
                </p>
              </div>
            )}

            {(!success.needs_clarification ||
              success.resolution.trim().length > 0) && (
              <div className="space-y-1.5">
                <p className="font-medium text-slate-100">Resolution</p>
                <p className="whitespace-pre-line text-slate-200">
                  {success.resolution}
                </p>
              </div>
            )}
          </div>
        )}
      </OutcomeCard>

      {success && (
        <OutcomeCard>
          <details className="group">
            <summary className="flex cursor-pointer items-center justify-between text-xs text-slate-400">
              <span>Execution trace</span>
              <span className="text-[10px] group-open:rotate-180 transition-transform">
                ▼
              </span>
            </summary>
            <div className="mt-2 max-h-52 overflow-y-auto space-y-1 text-slate-300">
              {success.trace.map((step) => (
                <div
                  key={`${step.step}-${step.timestamp}`}
                  className="rounded border border-slate-800/80 bg-slate-950/70 px-2 py-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium">{step.step}</span>
                    <span className="text-[10px] text-slate-400">
                      {step.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </details>
        </OutcomeCard>
      )}
    </section>
  );
}

function OutcomeCard({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-4 h-full flex flex-col gap-2">
      {children}
    </div>
  );
}

