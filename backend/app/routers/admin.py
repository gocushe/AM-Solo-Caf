from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models import Meal, MealDay, MealSignup, MenuUpload, Role, TokenPeriod, User, UserRole
from app.schemas import MealCountResponse, UploadResponse
from app.security import hash_password

router = APIRouter(prefix="/admin", tags=["admin"])
UPLOAD_DIR = Path("uploads")


@router.post("/menu/upload", response_model=UploadResponse)
async def upload_menu(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> UploadResponse:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    target = UPLOAD_DIR / file.filename
    content = await file.read()
    target.write_bytes(content)

    upload = MenuUpload(
        uploaded_by=admin.id,
        source_filename=file.filename,
        storage_path=str(target),
        parsed_success=False,
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)

    return UploadResponse(upload_id=upload.id, filename=upload.source_filename, parsed_success=upload.parsed_success)


@router.get("/meal-counts", response_model=MealCountResponse)
def meal_counts(
    target_date: date,
    meal_type: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> MealCountResponse:
    if meal_type not in {"Breakfast", "Lunch", "Supper", "Snack"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid meal type")

    meal = db.execute(
        select(Meal)
        .join(MealDay, MealDay.id == Meal.meal_day_id)
        .where(and_(MealDay.service_date == target_date, Meal.meal_type == meal_type))
    ).scalar_one_or_none()

    if meal is None:
        return MealCountResponse(date=target_date, meal_type=meal_type, active_signups=0)

    count = db.execute(
        select(func.count(MealSignup.id)).where(MealSignup.meal_id == meal.id, MealSignup.status == "active")
    ).scalar_one()

    return MealCountResponse(date=target_date, meal_type=meal_type, active_signups=count)


@router.post("/users/import-csv")
async def import_users_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict[str, int]:
    raw = (await file.read()).decode("utf-8")
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if not lines:
        return {"imported": 0}

    student_role = db.execute(select(Role).where(Role.name == "Student")).scalar_one_or_none()
    imported = 0

    for line in lines[1:]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 2:
            continue
        student_number, last_name = parts[0], parts[1]

        existing = db.execute(select(User).where(User.student_number == student_number)).scalar_one_or_none()
        if existing:
            continue

        user = User(
            student_number=student_number,
            last_name=last_name,
            password_hash=hash_password(last_name.lower()),
            is_active=True,
        )
        db.add(user)
        db.flush()

        if student_role:
            db.add(UserRole(user_id=user.id, role_id=student_role.id))
        imported += 1

    db.commit()
    return {"imported": imported}


@router.patch("/token-periods/{period_id}")
def update_token_period(
    period_id: int,
    start_date: date,
    end_date: date,
    is_active: bool,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict[str, str]:
    period = db.execute(select(TokenPeriod).where(TokenPeriod.id == period_id)).scalar_one_or_none()
    if period is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token period not found")

    if is_active:
        for row in db.execute(select(TokenPeriod).where(TokenPeriod.id != period.id)).scalars().all():
            row.is_active = False

    period.start_date = start_date
    period.end_date = end_date
    period.is_active = is_active
    db.commit()
    return {"message": "Token period updated"}
