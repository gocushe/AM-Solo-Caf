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
2. If Root Directory is currently set to repository root, keep it as-is and redeploy.
	- This repository now includes `vercel.json` at root to explicitly build the app from `frontend/package.json`.
3. If you prefer, you can still set Root Directory to `frontend` instead. Either approach now works.
4. Add environment variable:
	- `NEXT_PUBLIC_API_BASE_URL` = your deployed backend URL
5. Redeploy.

If you still get 404 after redeploy:

1. Go to Vercel -> Deployments -> open latest deployment -> check Build Logs.
2. Confirm it shows Next.js build from `frontend/package.json`.
3. In Vercel Domains, confirm the correct domain is attached to the current project.
4. Clear old preview/domain cache by triggering a new redeploy from latest commit.

## Backend hosting note

The FastAPI backend in `backend/` should be deployed as a separate service (for example Railway, Render, Fly.io, or a VPS), then `NEXT_PUBLIC_API_BASE_URL` should point to that backend URL.

## Railway backend deployment

1. Create a new Railway project from this GitHub repository.
2. For the service settings, set Root Directory to `backend`.
3. Add PostgreSQL in Railway project and copy its connection string.
4. In backend service variables set:
	- `DATABASE_URL` = Railway Postgres connection URL
	- `JWT_SECRET` = strong random secret
	- `JWT_ALGORITHM` = `HS256`
	- `ACCESS_TOKEN_EXPIRE_MINUTES` = `120`
	- `CORS_ORIGINS` = your Vercel frontend URL (for example `https://your-app.vercel.app`)
5. In Railway backend service, run migration command once:
	- `alembic upgrade head`
6. Start command should be:
	- `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
7. Copy Railway backend public URL.
8. Put that URL into Vercel as `NEXT_PUBLIC_API_BASE_URL` and redeploy frontend.
