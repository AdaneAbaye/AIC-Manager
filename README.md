# AIC-Manager — Autonomous Investment Committee

Multi-agent investment research: **Scout → Analyst → Risk Manager → Architect**.  
Includes a **FastAPI** JSON API and a **Next.js** + Tailwind frontend (RTL / Hebrew-friendly).

**Disclaimer:** Not financial advice. For research and education only.

## Repository layout

| Path | Role |
|------|------|
| `src/` | Python package: `config`, `agents`, `tools`, `research_flow`, `security` |
| `main.py` | FastAPI app (`GET /health`, `POST /api/research`) |
| `frontend/` | Next.js 14 (App Router) + Tailwind |
| `scripts/` | Utilities (e.g. `list_models.py`) |
| `docs/` | Project documentation |

## Security

- **Secrets:** Store API keys only in a root `.env` file. It is gitignored. Use `os.getenv` / `python-dotenv` in Python; `process.env` / `NEXT_PUBLIC_*` in Next.js where appropriate.
- **Never commit** `.env`, PEM files, or tokens. If a key was ever committed, rotate it and purge history (e.g. `git filter-repo` or GitHub secret scanning).
- **CORS:** Defaults to `http://localhost:3000`. Override with `CORS_ALLOW_ORIGINS` (comma-separated) in `.env`.
- **Inputs:** Thesis and investor name are sanitized server-side (`src/security.py`) and on the client (`frontend/src/lib/sanitize.ts`).
- **Markdown:** Agent reports use `rehype-sanitize` to reduce XSS risk from model-generated markdown.

## Quick start

### 1. Python (API)

```bash
python -m venv venv
# Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` in the repo root (see `.env.example` if present, or set at least):

- `ANTHROPIC_API_KEY` — required for Claude agents  
- Optional: `TAVILY_API_KEY`, `OPENAI_API_KEY`, etc.

```bash
uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
# optional: NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Open `http://localhost:3000`.

## Dependency audits

- **Python:** `pip install pip-audit && pip-audit` (or review `requirements.txt` pins in CI).
- **Node:** `cd frontend && npm audit` — address reported issues; avoid `npm audit fix --force` without review.

## License

Add your license here before publishing publicly.
