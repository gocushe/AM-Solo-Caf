from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

MealType = Literal["Breakfast", "Lunch", "Supper", "Snack"]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserSummary(BaseModel):
    id: int
    name: str
    student_number: str | None
    username: str | None
    roles: list[str]


class AuthResponse(TokenResponse):
    user: UserSummary


class RegisterRequest(BaseModel):
    student_number: str = Field(min_length=1, max_length=32)
    last_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=3, max_length=120)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=120)
    admin_login: bool = False


class PasswordChangeRequest(BaseModel):
    old_password: str = Field(min_length=1, max_length=120)
    new_password: str = Field(min_length=3, max_length=120)


class MealInfo(BaseModel):
    id: int
    meal_type: MealType
    title: str | None
    is_signup_allowed: bool


class DayMeals(BaseModel):
    date: date
    is_open: bool
    meals: list[MealInfo]


class DashboardResponse(BaseModel):
    user: UserSummary
    lunches_remaining: int
    suppers_remaining: int
    days: list[DayMeals]


class SignupCreateRequest(BaseModel):
    meal_id: int


class SignupItem(BaseModel):
    signup_id: int
    meal_id: int
    meal_type: MealType
    date: date
    signed_up_at: datetime


class UploadResponse(BaseModel):
    upload_id: int
    filename: str
    parsed_success: bool


class MealCountResponse(BaseModel):
    date: date
    meal_type: MealType
    active_signups: int
