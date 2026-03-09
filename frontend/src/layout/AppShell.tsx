import { ReactNode } from "react";

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 bg-radial-fade" />
      <div className="absolute inset-0 opacity-40 [background-image:radial-gradient(circle_at_1px_1px,#0f172a_1px,transparent_0)] [background-size:32px_32px]" />

      <div className="relative z-10 flex min-h-screen items-center justify-center px-4 py-10">
        <div className="w-full max-w-5xl space-y-8">
          <header className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-[11px] font-medium text-emerald-300 shadow-sm shadow-emerald-500/30">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-400" />
                Reason-then-verify order support
              </div>
              <h1 className="text-3xl md:text-4xl font-semibold tracking-tight">
                Order Support Assistant
              </h1>
              <p className="max-w-xl text-sm text-slate-400">
                Capture a customer&apos;s order issue, route it through a
                LangGraph orchestrator, and show a{" "}
                <span className="text-emerald-300">
                  sandbox-verified resolution
                </span>{" "}
                in real time.
              </p>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/70 px-3 py-2 text-xs text-slate-300 shadow-lg shadow-black/40">
              <p className="flex items-center justify-between gap-2">
                <span className="text-slate-400">Backend</span>
                <span className="font-mono text-[11px] text-slate-100">
                  POST /cases/langgraph
                </span>
              </p>
              <p className="mt-1 text-[11px] text-slate-500">
                Powered by FastAPI + LangGraph
              </p>
            </div>
          </header>

          {children}
        </div>
      </div>
    </div>
  );
}

