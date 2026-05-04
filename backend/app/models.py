import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    activities: Mapped[list["Activity"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    exercise_templates: Mapped[list["ExerciseTemplate"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    body_weights: Mapped[list["BodyWeight"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class ExerciseTemplate(Base):
    """User's personal exercise list (e.g. Bizeps, Klimmzüge, Laufen)."""
    __tablename__ = "exercise_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    is_duration_based: Mapped[bool] = mapped_column(Boolean, default=False)  # True for Laufen (10min/set)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship(back_populates="exercise_templates")
    activity_exercises: Mapped[list["ActivityExercise"]] = relationship(back_populates="template")


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'endurance' | 'strength'
    subtype: Mapped[str] = mapped_column(String(50), nullable=False)
    activity_date: Mapped[date] = mapped_column(Date, nullable=False)
    distance_km: Mapped[float | None] = mapped_column(Float)  # endurance only
    stars: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="activities")
    activity_exercises: Mapped[list["ActivityExercise"]] = relationship(back_populates="activity", cascade="all, delete-orphan")


class ActivityExercise(Base):
    """A specific exercise done in a strength activity."""
    __tablename__ = "activity_exercises"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("activities.id"), nullable=False)
    template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("exercise_templates.id"), nullable=False)
    sets_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    activity: Mapped["Activity"] = relationship(back_populates="activity_exercises")
    template: Mapped["ExerciseTemplate"] = relationship(back_populates="activity_exercises")


class BodyWeight(Base):
    __tablename__ = "body_weights"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    measured_at: Mapped[date] = mapped_column(Date, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)

    user: Mapped["User"] = relationship(back_populates="body_weights")
