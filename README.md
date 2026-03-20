# CMU Cafeteria Workspace

Monorepo-style starter setup:

- `frontend/` -> Next.js + Tailwind UI (login/register/dashboard wired to API)
- `backend/` -> FastAPI + SQLAlchemy + Alembic + PostgreSQL

## Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

## Database

Create PostgreSQL database first, then run migrations:

```bash
cd backend
alembic upgrade head
```

## Current implemented scope

- Auth API: register, login, me, change password
- Student API: dashboard, meal signup list/create/delete
- Admin API: menu upload, meal counts, CSV student import, token period update
- Seed data on startup: admin/admin and student 123/student
- CMU-themed frontend integrated with backend endpoints (no mock dashboard state)
