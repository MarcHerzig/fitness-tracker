import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr


# Auth
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    created_at: datetime
    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


# Exercise templates
class ExerciseTemplateCreate(BaseModel):
    name: str
    weight_kg: float | None = None
    is_duration_based: bool = False
    sort_order: int = 0


class ExerciseTemplateUpdate(BaseModel):
    name: str | None = None
    weight_kg: float | None = None
    is_duration_based: bool | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class ExerciseTemplateOut(BaseModel):
    id: uuid.UUID
    name: str
    weight_kg: float | None
    is_duration_based: bool
    sort_order: int
    is_active: bool
    model_config = {"from_attributes": True}


# Activities
class ActivityExerciseIn(BaseModel):
    template_id: uuid.UUID
    sets_completed: int


class ActivityExerciseOut(BaseModel):
    id: uuid.UUID
    template_id: uuid.UUID
    sets_completed: int
    template: ExerciseTemplateOut
    model_config = {"from_attributes": True}


class ActivityCreate(BaseModel):
    type: str  # 'endurance' | 'strength'
    subtype: str
    activity_date: date
    distance_km: float | None = None
    notes: str | None = None
    exercises: list[ActivityExerciseIn] = []


class ActivityOut(BaseModel):
    id: uuid.UUID
    type: str
    subtype: str
    activity_date: date
    distance_km: float | None
    stars: int
    notes: str | None
    created_at: datetime
    activity_exercises: list[ActivityExerciseOut] = []
    model_config = {"from_attributes": True}


# Body weight
class BodyWeightCreate(BaseModel):
    measured_at: date
    weight_kg: float


class BodyWeightOut(BaseModel):
    id: uuid.UUID
    measured_at: date
    weight_kg: float
    model_config = {"from_attributes": True}


# Dashboard / Stats
class DayStars(BaseModel):
    date: date
    stars: int  # 0–3 combined across all activities


class UserDashboard(BaseModel):
    user_id: uuid.UUID
    username: str
    today_stars: int
    week: list[DayStars]  # last 7 days
    two_week_total_stars: int
    two_week_training_days: int
    last_weight: float | None
    weight_history: list[BodyWeightOut]


class DashboardOut(BaseModel):
    marc: UserDashboard | None
    pia: UserDashboard | None


class WeeklyStarsOut(BaseModel):
    days: list[DayStars]
