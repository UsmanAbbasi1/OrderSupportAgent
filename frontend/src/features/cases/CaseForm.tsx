import { FormEvent } from "react";

type Props = {
  issue: string;
  tenantId: string;
  appId: string;
  timeRange: string;
  busy: boolean;
  onChange: (field: "issue" | "tenantId" | "appId" | "timeRange", value: string) => void;
  onSubmit: (e: FormEvent) => void;
};

export function CaseForm({
  issue,
  tenantId,
  appId,
  timeRange,
  busy,
  onChange,
  onSubmit,
}: Props) {
  return (
    <section className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 shadow-xl shadow-black/40 backdrop-blur-sm">
      <form className="space-y-4" onSubmit={onSubmit}>
        <div className="space-y-2">
          <div className="flex items-center justify-between gap-2">
            <label className="text-sm font-medium text-slate-100">
              Describe your order issue
            </label>
            <span className="text-[11px] text-slate-500">
              Include order ID if you have it (e.g.{" "}
              <code className="rounded bg-slate-800 px-1 py-0.5 text-[10px] text-slate-200">
                ORD-1001
              </code>
              )
            </span>
          </div>
          <textarea
            className="w-full h-32 rounded-xl border border-slate-700/80 bg-slate-950/70 px-3 py-2 text-sm text-slate-50 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/70 focus:border-emerald-500/70 resize-none"
            placeholder='e.g. "My order says delivered but I never received it." or "Order ORD-1001 says delivered but I never got it."'
            value={issue}
            onChange={(e) => onChange("issue", e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-xs">
          <div className="space-y-1.5">
            <label className="block text-slate-300">Tenant ID</label>
            <input
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-2 py-1.5 text-slate-50 focus:outline-none focus:ring-1 focus:ring-emerald-500/70"
              value={tenantId}
              onChange={(e) => onChange("tenantId", e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <label className="block text-slate-300">App ID</label>
            <input
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-2 py-1.5 text-slate-50 focus:outline-none focus:ring-1 focus:ring-emerald-500/70"
              value={appId}
              onChange={(e) => onChange("appId", e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <label className="block text-slate-300">Time range</label>
            <input
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-2 py-1.5 text-slate-50 focus:outline-none focus:ring-1 focus:ring-emerald-500/70"
              value={timeRange}
              onChange={(e) => onChange("timeRange", e.target.value)}
            />
          </div>
        </div>

        <div className="flex items-center justify-between gap-3 pt-1">
          <button
            type="submit"
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-500 px-4 py-2 text-sm font-medium text-emerald-950 shadow-md shadow-emerald-500/30 hover:bg-emerald-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/80 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
            disabled={busy || !issue.trim()}
          >
            {busy && (
              <span className="inline-flex h-3 w-3 animate-spin rounded-full border-[2px] border-emerald-900 border-t-transparent" />
            )}
            {busy ? "Running case..." : "Submit case"}
          </button>
          <p className="hidden md:block text-[11px] text-slate-500">
            Demo orders:{" "}
            <code className="rounded bg-slate-800 px-1 py-0.5 text-[10px] text-slate-200">
              ORD-1001
            </code>
            ,{" "}
            <code className="rounded bg-slate-800 px-1 py-0.5 text-[10px] text-slate-200">
              ORD-1002
            </code>
            ,{" "}
            <code className="rounded bg-slate-800 px-1 py-0.5 text-[10px] text-slate-200">
              ORD-1003
            </code>
          </p>
        </div>
      </form>
    </section>
  );
}

