from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Meal, MealDay, Role, TokenPeriod, User, UserRole, UserTokenBalance
from app.security import hash_password

MEAL_TYPES = ["Breakfast", "Lunch", "Supper", "Snack"]


def _get_or_create_role(db: Session, name: str) -> Role:
    role = db.execute(select(Role).where(Role.name == name)).scalar_one_or_none()
    if role:
        return role
    role = Role(name=name)
    db.add(role)
    db.flush()
    return role


def _ensure_user_role(db: Session, user: User, role: Role) -> None:
    existing = db.execute(
        select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role.id)
    ).scalar_one_or_none()
    if existing is None:
        db.add(UserRole(user_id=user.id, role_id=role.id))


def _ensure_month_meals(db: Session, year: int, month: int) -> None:
    first = date(year, month, 1)
    next_month = date(year + (1 if month == 12 else 0), 1 if month == 12 else month + 1, 1)
    days = (next_month - first).days

    for i in range(days):
        d = first + timedelta(days=i)
        meal_day = db.execute(select(MealDay).where(MealDay.service_date == d)).scalar_one_or_none()
        if not meal_day:
            meal_day = MealDay(service_date=d, is_open=True)
            db.add(meal_day)
            db.flush()

        for meal_type in MEAL_TYPES:
            meal = db.execute(
                select(Meal).where(Meal.meal_day_id == meal_day.id, Meal.meal_type == meal_type)
            ).scalar_one_or_none()
            if not meal:
                db.add(
                    Meal(
                        meal_day_id=meal_day.id,
                        meal_type=meal_type,
                        title=f"{meal_type} Special",
                        is_signup_allowed=(meal_type != "Snack"),
                    )
                )


def seed_initial_data(db: Session) -> None:
    student_role = _get_or_create_role(db, "Student")
    _get_or_create_role(db, "Apartment Resident")
    _get_or_create_role(db, "Staff")
    admin_role = _get_or_create_role(db, "Admin")

    admin = db.execute(select(User).where(User.username == "admin")).scalar_one_or_none()
    if admin is None:
        admin = User(username="admin", password_hash=hash_password("admin"), is_active=True)
        db.add(admin)
        db.flush()
    _ensure_user_role(db, admin, admin_role)

    student = db.execute(select(User).where(User.student_number == "123")).scalar_one_or_none()
    if student is None:
        student = User(
            student_number="123",
            last_name="student",
            password_hash=hash_password("student"),
            is_active=True,
        )
        db.add(student)
        db.flush()
    _ensure_user_role(db, student, student_role)

    today = date.today()
    default_period = db.execute(select(TokenPeriod).where(TokenPeriod.is_active.is_(True))).scalar_one_or_none()
    if default_period is None:
        end = today + timedelta(weeks=6)
        default_period = TokenPeriod(name="Default 6-week period", start_date=today, end_date=end, is_active=True)
        db.add(default_period)
        db.flush()

    for user in [student]:
        bal = db.execute(
            select(UserTokenBalance).where(
                UserTokenBalance.user_id == user.id,
                UserTokenBalance.token_period_id == default_period.id,
            )
        ).scalar_one_or_none()
        if bal is None:
            db.add(
                UserTokenBalance(
                    user_id=user.id,
                    token_period_id=default_period.id,
                    lunches_remaining=4,
                    suppers_remaining=2,
                )
            )

    _ensure_month_meals(db, today.year, today.month)
    db.commit()
