# FRONTLINE — AI Customer Support Triage

Frontline receives customer messages, classifies and prioritises them with AI, stores the original message and its decision, and presents the history to a support team.

## Application architecture

- **React + Vite:** customer message portal and internal support dashboard.
- **FastAPI:** our application API. It validates requests, coordinates triage, stores records and serves dashboard data.
- **Groq API:** external inference provider running `openai/gpt-oss-120b`.
- **PostgreSQL:** persistent message, decision and review storage.
- **SQLAlchemy:** Python ORM for database operations.
- **Pydantic:** request and response validation.

The browser calls our FastAPI backend. Only the backend calls Groq; the Groq API key is never sent to the browser.

## Request workflow

1. A customer submits their name, email and message in the React portal.
2. React sends `POST /api/messages` to FastAPI.
3. FastAPI validates the request and commits the original message to the database first.
4. The triage service reuses the existing `triage.py` engine. Local guardrails run before Groq inference.
5. The model output is parsed, schema-validated and passed through risk-escalation rules.
6. The decision and processing metadata are stored in PostgreSQL.
7. The API returns the structured decision to the customer portal.
8. The support dashboard retrieves historical messages and statistics from the API. Agents can update review status.

If automated processing fails, the original message remains saved and a human-review fallback is recorded.

## 1. Configuration

Copy the example environment file in the repository root:

```bash
cp .env.example .env
```

Set your Groq key and replace the support dashboard token with a long random secret. Never commit `.env` or expose either secret in frontend code.

## 2. Start PostgreSQL

Docker Desktop must be running:

```bash
docker compose up -d db
```

The supplied local database uses:
- Database: `frontline`
- User: `frontline`
- Port: `5432`

The connection string is already shown in `.env.example`. You can also use SQLite for a quick local smoke test by leaving `DATABASE_URL` unset; PostgreSQL is the intended application database.

## 3. Start the backend

From the repository root:

```bash
python -m venv .venv
```

Windows Git Bash:

```bash
source .venv/Scripts/activate
```

Install dependencies and start FastAPI:

```bash
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

API health check: http://localhost:8000/api/health

Interactive API documentation: http://localhost:8000/docs

## 4. Start the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

The **Customer portal** is for submitting a message. The **Support dashboard** requires the support token configured in the backend environment.

## API endpoints

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| POST | `/api/messages` | Public | Submit and triage a customer message |
| GET | `/api/messages` | Support token | List message history |
| GET | `/api/messages/{id}` | Support token | Retrieve one message |
| PATCH | `/api/messages/{id}/review` | Support token | Update review status |
| GET | `/api/dashboard/stats` | Support token | Dashboard statistics |
| GET | `/api/health` | Public | Health check |

The support dashboard sends `X-Support-Token` in its API requests. This is a minimal demo access gate, not a replacement for production user accounts, role-based access, token rotation, rate limiting or a full authentication provider.

## Existing AI challenge workflow

The original CLI tools remain available:

```bash
python triage.py
python eval.py
python dashboard_generator.py
```

- `triage.py` runs inference and produces structured decisions.
- `eval.py` independently compares saved decisions with the hand-labelled examples. **triage.py does not call eval.py.**
- `dashboard_generator.py` creates the original static HTML report. The new React dashboard reads persistent records through FastAPI instead.

## Tests

Backend tests do not require a live Groq key:

```bash
python -m unittest discover -s tests -v
```

Frontend production build:

```bash
cd frontend
npm install
npm run build
```

GitHub Actions runs both checks on pushes to `main`.

## Current scope and next steps

This is the first full-stack MVP foundation. Before production use, add proper support-agent authentication and roles, Alembic-managed migrations, pagination/retention policies, rate limiting, audit logging, background retries for failed inference, and deployment configuration. The current API uses synchronous inference to keep the first workflow understandable and testable.
