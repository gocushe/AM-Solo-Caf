from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Meal, MealDay, MealSignup, TokenPeriod, User, UserRole, UserTokenBalance
from app.schemas import DashboardResponse, DayMeals, MealInfo, SignupCreateRequest, SignupItem, UserSummary

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(year: int, month: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> DashboardResponse:
    period = db.execute(select(TokenPeriod).where(TokenPeriod.is_active.is_(True))).scalar_one_or_none()
    lunches = 0
    suppers = 0

    if period:
        bal = db.execute(
            select(UserTokenBalance).where(
                UserTokenBalance.user_id == current_user.id,
                UserTokenBalance.token_period_id == period.id,
            )
        ).scalar_one_or_none()
        if bal:
            lunches = bal.lunches_remaining
            suppers = bal.suppers_remaining

    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)

    day_rows = db.execute(
        select(MealDay).where(and_(MealDay.service_date >= start, MealDay.service_date < end)).order_by(MealDay.service_date.asc())
    ).scalars().all()

    day_ids = [d.id for d in day_rows]
    meals_by_day: dict[int, list[MealInfo]] = {day_id: [] for day_id in day_ids}

    if day_ids:
        meals = db.execute(select(Meal).where(Meal.meal_day_id.in_(day_ids)).order_by(Meal.id.asc())).scalars().all()
        for meal in meals:
            meals_by_day[meal.meal_day_id].append(
                MealInfo(
                    id=meal.id,
                    meal_type=meal.meal_type,
                    title=meal.title,
                    is_signup_allowed=meal.is_signup_allowed,
                )
            )

    days = [DayMeals(date=d.service_date, is_open=d.is_open, meals=meals_by_day.get(d.id, [])) for d in day_rows]

    user_full = db.execute(
        select(User).options(joinedload(User.roles).joinedload(UserRole.role)).where(User.id == current_user.id)
    ).unique().scalar_one()

    summary = UserSummary(
        id=user_full.id,
        name=user_full.username or user_full.student_number or "User",
        student_number=user_full.student_number,
        username=user_full.username,
        roles=[rel.role.name for rel in user_full.roles],
    )

    return DashboardResponse(user=summary, lunches_remaining=lunches, suppers_remaining=suppers, days=days)


@router.get("/signups", response_model=list[SignupItem])
def list_signups(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[SignupItem]:
    rows = db.execute(
        select(MealSignup, Meal, MealDay)
        .join(Meal, Meal.id == MealSignup.meal_id)
        .join(MealDay, MealDay.id == Meal.meal_day_id)
        .where(MealSignup.user_id == current_user.id, MealSignup.status == "active")
        .order_by(MealDay.service_date.asc(), Meal.meal_type.asc())
    ).all()

    return [
        SignupItem(
            signup_id=signup.id,
            meal_id=meal.id,
            meal_type=meal.meal_type,
            date=meal_day.service_date,
            signed_up_at=signup.signed_up_at,
        )
        for signup, meal, meal_day in rows
    ]


@router.post("/signups", response_model=SignupItem)
def create_signup(
    payload: SignupCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SignupItem:
    meal = db.execute(select(Meal).where(Meal.id == payload.meal_id)).scalar_one_or_none()
    if meal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found")

    if meal.meal_type == "Snack" or not meal.is_signup_allowed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Meal is read-only")

    existing = db.execute(
        select(MealSignup).where(
            MealSignup.user_id == current_user.id,
            MealSignup.meal_id == meal.id,
            MealSignup.status == "active",
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already signed up")

    signup = MealSignup(user_id=current_user.id, meal_id=meal.id, status="active")
    db.add(signup)

    _apply_token_delta(db, current_user.id, meal.meal_type, -1)
    db.commit()
    db.refresh(signup)

    meal_day = db.execute(select(MealDay).where(MealDay.id == meal.meal_day_id)).scalar_one()
    return SignupItem(
        signup_id=signup.id,
        meal_id=meal.id,
        meal_type=meal.meal_type,
        date=meal_day.service_date,
        signed_up_at=signup.signed_up_at,
    )


@router.delete("/signups/{signup_id}")
def delete_signup(signup_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict[str, str]:
    row = db.execute(
        select(MealSignup, Meal)
        .join(Meal, Meal.id == MealSignup.meal_id)
        .where(MealSignup.id == signup_id, MealSignup.user_id == current_user.id, MealSignup.status == "active")
    ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signup not found")

    signup, meal = row
    signup.status = "cancelled"
    _apply_token_delta(db, current_user.id, meal.meal_type, 1)
    db.commit()
    return {"message": "Signup cancelled"}


def _apply_token_delta(db: Session, user_id: int, meal_type: str, delta: int) -> None:
    if meal_type not in {"Lunch", "Supper"}:
        return

    period = db.execute(select(TokenPeriod).where(TokenPeriod.is_active.is_(True))).scalar_one_or_none()
    if period is None:
        return

    balance = db.execute(
        select(UserTokenBalance).where(
            UserTokenBalance.user_id == user_id,
            UserTokenBalance.token_period_id == period.id,
        )
    ).scalar_one_or_none()
    if balance is None:
        balance = UserTokenBalance(user_id=user_id, token_period_id=period.id, lunches_remaining=0, suppers_remaining=0)
        db.add(balance)
        db.flush()

    if meal_type == "Lunch":
        new_value = balance.lunches_remaining + delta
        if new_value < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No lunch tokens remaining")
        balance.lunches_remaining = new_value
    if meal_type == "Supper":
        new_value = balance.suppers_remaining + delta
        if new_value < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No supper tokens remaining")
        balance.suppers_remaining = new_value
