# FRONTLINE — AI Customer Support Triage

Frontline accepts customer support requests, classifies and prioritises them with AI, stores messages and decisions in PostgreSQL, and gives support agents a private workspace.

## Architecture

- **React + Vite:** public customer portal and private staff workspace.
- **FastAPI:** validates requests, coordinates AI triage, stores records, authenticates staff and serves the dashboard.
- **Groq API:** model inference using `openai/gpt-oss-120b`.
- **Neon PostgreSQL:** persistent customer messages, AI decisions, staff accounts and review history.
- **SQLAlchemy:** database ORM.
- **Pydantic:** API request/response validation.
- **JWT + Argon2:** short-lived staff sessions and one-way password hashing.

The browser calls our FastAPI backend. Only the backend calls Groq; the Groq API key is never sent to the browser.

## Customer workflow

1. A customer opens the public customer-support page.
2. They submit their name, email and message without creating an account.
3. FastAPI validates and saves the original message first.
4. The triage service reuses the existing `triage.py` engine and calls Groq when required.
5. The AI decision is saved privately in PostgreSQL.
6. The customer receives only a confirmation and ticket reference. The customer-facing API response does not contain the original message or internal AI analysis.

## Staff workflow

1. A staff account is created by an administrator using the backend CLI.
2. A staff member signs in with their own email and password.
3. Passwords are stored as Argon2 hashes, never as plaintext.
4. FastAPI issues a signed, expiring JWT access token.
5. The React app sends that token in the standard `Authorization: Bearer` header.
6. Protected endpoints return the inbox, customer details, AI decisions and dashboard statistics only to authenticated, active staff.
7. Review actions are recorded with the signed-in staff member's email.

There is no public staff registration endpoint and no shared support access token.

## 1. Configure environment

Copy `.env.example` to `.env` in the repository root. Set:
- `GROQ_API_KEY`: your Groq API key.
- `DATABASE_URL`: your Neon connection string, using the SQLAlchemy driver prefix `postgresql+psycopg://`.
- `JWT_SECRET_KEY`: a long random secret. Generate one with `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
- `CORS_ORIGINS`: the frontend origin, usually `http://localhost:5173` for local development.

Never commit `.env` or expose the Groq key or JWT secret in frontend code. Use a unique JWT secret in production; do not use the development fallback.

## 2. Install and start the backend

From the repository root (Windows Git Bash):

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

The API creates missing tables on startup for this MVP. Health check: http://localhost:8000/api/health

## 3. Create the first staff account

Open a second terminal in the repository root, activate the same virtual environment, and run:

```bash
python -m backend.create_staff
```

Enter the staff email and a password of at least 12 characters when prompted. The password is hashed before it is saved. Repeat this command to create additional staff accounts. There is intentionally no public sign-up page.

## 4. Start the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The customer portal is the default view. Choose **Staff workspace** to sign in.

## API endpoints

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| POST | `/api/messages` | Public | Submit a customer message; returns a receipt only |
| POST | `/api/auth/login` | Public | Authenticate a staff member |
| GET | `/api/auth/me` | Staff JWT | Validate the current staff session |
| GET | `/api/messages` | Staff JWT | List message history |
| GET | `/api/messages/{id}` | Staff JWT | Retrieve a message and its AI decision |
| PATCH | `/api/messages/{id}/review` | Staff JWT | Update review status |
| GET | `/api/dashboard/stats` | Staff JWT | Dashboard statistics |
| GET | `/api/health` | Public | Health check |

## Existing AI challenge workflow

The original CLI tools remain available:

```bash
python triage.py
python eval.py
python dashboard_generator.py
```

- `triage.py` runs inference and produces structured decisions.
- `eval.py` independently compares saved decisions with hand-labelled examples. **triage.py does not call eval.py.**
- `dashboard_generator.py` creates the original static HTML report. The React dashboard reads persistent records through FastAPI.

## Tests

```bash
python -m unittest discover -s tests -v
cd frontend
npm install
npm run build
```

GitHub Actions runs backend tests and the frontend build on pushes to `main`.

## MVP limitations before production

Use HTTPS, rotate and protect JWT secrets, add login rate limiting and account lockout, introduce role-based permissions and password-reset procedures, use Alembic migrations instead of relying on `create_all`, and consider moving AI inference to a background worker. JWTs are stored in browser session storage in this MVP; a production deployment should consider secure, HttpOnly cookies and CSRF protection.
