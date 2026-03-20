from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user
from app.models import PasswordChangeAudit, Role, User, UserRole
from app.schemas import AuthResponse, LoginRequest, PasswordChangeRequest, RegisterRequest, UserSummary
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_summary(user: User) -> UserSummary:
    roles = [rel.role.name for rel in user.roles]
    display_name = user.username or user.student_number or "User"
    return UserSummary(
        id=user.id,
        name=display_name,
        student_number=user.student_number,
        username=user.username,
        roles=roles,
    )


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    exists = db.execute(select(User).where(User.student_number == payload.student_number)).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student already exists")

    user = User(
        student_number=payload.student_number,
        last_name=payload.last_name,
        password_hash=hash_password(payload.password),
        is_active=True,
    )
    db.add(user)
    db.flush()

    student_role = db.execute(select(Role).where(Role.name == "Student")).scalar_one_or_none()
    if student_role:
        db.add(UserRole(user_id=user.id, role_id=student_role.id))

    db.commit()
    user = db.execute(
        select(User).options(joinedload(User.roles).joinedload(UserRole.role)).where(User.id == user.id)
    ).unique().scalar_one()

    token = create_access_token(str(user.id))
    return AuthResponse(access_token=token, user=_user_summary(user))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    if payload.admin_login:
        user = db.execute(select(User).where(User.username == payload.username)).scalar_one_or_none()
    else:
        user = db.execute(select(User).where(User.student_number == payload.username)).scalar_one_or_none()

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user = db.execute(
        select(User).options(joinedload(User.roles).joinedload(UserRole.role)).where(User.id == user.id)
    ).unique().scalar_one()

    token = create_access_token(str(user.id))
    return AuthResponse(access_token=token, user=_user_summary(user))


@router.get("/me", response_model=UserSummary)
def me(current_user: User = Depends(get_current_user)) -> UserSummary:
    return _user_summary(current_user)


@router.post("/change-password")
def change_password(
    payload: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    if not verify_password(payload.old_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is incorrect")

    current_user.password_hash = hash_password(payload.new_password)
    db.add(PasswordChangeAudit(user_id=current_user.id, changed_by=current_user.id))
    db.commit()
    return {"message": "Password updated"}
