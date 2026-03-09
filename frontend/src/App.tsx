import { FormEvent, useState } from "react";
import { createCase, CaseResponse } from "./api";
import { AppShell } from "./layout/AppShell";
import { CaseForm } from "./features/cases/CaseForm";
import { CaseOutcome } from "./features/cases/CaseOutcome";

type UiState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "success"; data: CaseResponse };

function App() {
  const [issue, setIssue] = useState("");
  const [tenantId, setTenantId] = useState("demo-tenant");
  const [appId, setAppId] = useState("web-frontend");
  const [timeRange, setTimeRange] = useState("last_7d");
  const [ui, setUi] = useState<UiState>({ status: "idle" });

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!issue.trim()) return;

    setUi({ status: "loading" });
    try {
      const data = await createCase({
        issue: issue.trim(),
        tenant_id: tenantId.trim(),
        app_id: appId.trim(),
        time_range: timeRange.trim(),
      });
      setUi({ status: "success", data });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Unknown error occurred";
      setUi({ status: "error", message });
    }
  }

  return (
    <AppShell>
      <main className="grid gap-6 md:grid-cols-[minmax(0,2.2fr)_minmax(0,1.6fr)]">
        <CaseForm
          issue={issue}
          tenantId={tenantId}
          appId={appId}
          timeRange={timeRange}
          busy={ui.status === "loading"}
          onChange={(field, value) => {
            if (field === "issue") setIssue(value);
            if (field === "tenantId") setTenantId(value);
            if (field === "appId") setAppId(value);
            if (field === "timeRange") setTimeRange(value);
          }}
          onSubmit={handleSubmit}
        />
        <CaseOutcome ui={ui} />
      </main>
    </AppShell>
  );
}

export default App;

