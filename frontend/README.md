# OrderSupportAgent Frontend (React + Vite + TailwindCSS)

Modern web UI for the OrderSupportAgent FastAPI backend.  
Calls the `POST /cases/langgraph` endpoint to run the reason-then-verify order support flow.

---

## 1. Prerequisites

- Node.js **18+** (recommended)
- Backend API running locally on `http://127.0.0.1:8000` (see root `README.md`)

---

## 2. Install dependencies

From the repo root:

```bash
cd frontend

# using npm
npm install

# (or) using yarn / pnpm if you prefer
# yarn
# pnpm install
```

---

## 3. Run the dev server

Make sure the FastAPI backend is running:

```bash
# from project root
source .venv/bin/activate          # if using a virtualenv
uvicorn app.main:app --reload
```

Then, in a separate terminal, start the frontend:

```bash
cd frontend
npm run dev
```

Vite will output a local URL, typically:

- `http://127.0.0.1:5173`

Open that URL in your browser.

> The Vite dev server is configured to proxy `/api/*` requests to  
> `http://127.0.0.1:8000`, so the frontend calls `/api/cases/langgraph`
> and Vite forwards it to the FastAPI backend.

---

## 4. Build for production

```bash
cd frontend
npm run build
```

This creates a static build in the `dist/` folder.

You can preview the production build locally with:

```bash
npm run preview
```

---

## 5. Project structure (frontend)

Key files and folders:

- `src/main.tsx` – React entry point.
- `src/App.tsx` – wires layout, form, and outcome components together.
- `src/layout/AppShell.tsx` – top-level layout (background, header, shell).
- `src/features/cases/CaseForm.tsx` – order issue form (issue, tenant/app/time).
- `src/features/cases/CaseOutcome.tsx` – displays resolution, clarifications, trace.
- `src/api.ts` – typed client for `POST /cases/langgraph`.
- `tailwind.config.js` / `src/index.css` – TailwindCSS configuration and styles.

---

## 6. Demo flow

Use the following example inputs:

1. **First request (no order ID)**  
   Example issue:

   ```text
   My order says delivered but I never received it.
   ```

   You should see `needs_clarification: true` and clarification questions.

2. **Follow-up request (with order ID)**  
   Example issue:

   ```text
   Order ORD-1001 says delivered but I never got it.
   ```

   The UI will show a verified resolution plus execution trace, powered by the
   LangGraph orchestrator and sandbox verification in the backend.

