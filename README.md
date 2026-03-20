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

## Vercel deployment (frontend)

This repository is a monorepo. The Next.js app is inside `frontend/`, so Vercel must build from that folder.

1. In Vercel, import this GitHub repository.
2. Open Project Settings -> General -> Root Directory.
3. Set Root Directory to `frontend`.
4. Framework preset should be Next.js.
5. Build command: `npm run build` (default is fine).
6. Install command: `npm install` (default is fine).
7. Add environment variable:
	- `NEXT_PUBLIC_API_BASE_URL` = your deployed backend URL
8. Redeploy.

If Root Directory is not set to `frontend`, Vercel may return a 404 NOT_FOUND page because it is trying to deploy from the repository root.

## Backend hosting note

The FastAPI backend in `backend/` is not configured as a Vercel serverless project in this repository. Deploy it as a separate service (for example Railway, Render, Fly.io, or a VPS), then point `NEXT_PUBLIC_API_BASE_URL` to that backend URL.
