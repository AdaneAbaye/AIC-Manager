# AIC-Manager — Frontend

Next.js 16 (App Router) + React 19 + Tailwind CSS client for the AIC-Manager API. RTL / Hebrew-friendly.

## Run

```bash
npm install
npm run dev
```

Open http://localhost:3000. The backend must be running (see the root [README](../README.md)).

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Base URL of the FastAPI backend |

Put it in `frontend/.env.local` (gitignored).

## Structure

| Path | Role |
|------|------|
| `src/app/` | App Router pages and layout |
| `src/components/` | Stock cards, committee agents, research logs, rejection list, investor sidebar |
| `src/services/api.ts` | API client |
| `src/lib/sanitize.ts` | Client-side input sanitization |
| `src/lib/formatNumbers.ts` | Number and currency formatting |
