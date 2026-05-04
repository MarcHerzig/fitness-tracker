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


# Activities
class ExerciseSetIn(BaseModel):
    set_number: int
    reps: int | None = None
    weight_kg: float | None = None
    rest_seconds: int | None = None


class ExerciseSetOut(ExerciseSetIn):
    id: uuid.UUID
    model_config = {"from_attributes": True}


class ExerciseIn(BaseModel):
    name: str
    order: int = 0
    sets: list[ExerciseSetIn] = []


class ExerciseOut(BaseModel):
    id: uuid.UUID
    name: str
    order: int
    sets: list[ExerciseSetOut]
    model_config = {"from_attributes": True}


class ActivityCreate(BaseModel):
    type: str  # 'endurance' | 'strength'
    subtype: str
    activity_date: date
    duration_minutes: int
    notes: str | None = None
    distance_km: float | None = None  # endurance only
    exercises: list[ExerciseIn] = []  # strength only


class ActivityOut(BaseModel):
    id: uuid.UUID
    type: str
    subtype: str
    activity_date: date
    duration_minutes: int
    notes: str | None
    created_at: datetime
    distance_km: float | None = None
    exercises: list[ExerciseOut] = []
    model_config = {"from_attributes": True}


# Stats
class WeeklySummary(BaseModel):
    week_start: date
    total_activities: int
    total_duration_minutes: int
    total_distance_km: float
    total_volume_kg: float


class MonthlySummary(BaseModel):
    year: int
    month: int
    total_activities: int
    total_duration_minutes: int
    total_distance_km: float
    total_volume_kg: float


class PersonalRecord(BaseModel):
    exercise_name: str
    max_weight_kg: float
    max_reps: int | None
    achieved_on: date


class StreakInfo(BaseModel):
    current_streak: int
    longest_streak: int
    last_activity_date: date | None
