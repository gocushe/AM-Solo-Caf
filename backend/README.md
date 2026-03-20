# CMU Cafeteria Backend (FastAPI + PostgreSQL)

## Run API locally

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy env file and update values:

```bash
cp .env.example .env
```

4. Run migrations:

```bash
alembic upgrade head
```

5. Start FastAPI server:

```bash
uvicorn app.main:app --reload
```

## Migration files

- Alembic config: `alembic.ini`
- Environment: `alembic/env.py`
- Initial schema migration: `alembic/versions/20260319_0001_initial_schema.py`

## API summary

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `POST /auth/change-password`
- `GET /me/dashboard?year=YYYY&month=MM`
- `GET /me/signups`
- `POST /me/signups`
- `DELETE /me/signups/{signup_id}`
- `POST /admin/menu/upload`
- `GET /admin/meal-counts?target_date=YYYY-MM-DD&meal_type=Lunch`
- `POST /admin/users/import-csv`
- `PATCH /admin/token-periods/{period_id}`

## Notes

- Snack meals are modeled but read-only for students in signup flow.
- Default seeded credentials: `admin/admin` and `123/student`.
- Startup also auto-seeds current month meal days/meals for dashboard rendering.
