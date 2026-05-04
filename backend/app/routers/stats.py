from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Activity, EnduranceData, Exercise, ExerciseSet, User
from app.routers.auth import get_current_user
from app.schemas import MonthlySummary, PersonalRecord, StreakInfo, WeeklySummary

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/weekly", response_model=list[WeeklySummary])
async def weekly_stats(
    weeks: int = 8,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    # Start from Monday of current week
    start_monday = today - timedelta(days=today.weekday())
    summaries = []

    for i in range(weeks):
        week_start = start_monday - timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)

        result = await db.execute(
            select(Activity)
            .options(selectinload(Activity.endurance_data), selectinload(Activity.exercises).selectinload(Exercise.sets))
            .where(Activity.user_id == current_user.id, Activity.activity_date >= week_start, Activity.activity_date <= week_end)
        )
        activities = result.scalars().all()

        total_distance = sum(a.endurance_data.distance_km for a in activities if a.endurance_data)
        total_volume = sum(
            (s.weight_kg or 0) * (s.reps or 0)
            for a in activities
            for ex in a.exercises
            for s in ex.sets
        )

        summaries.append(WeeklySummary(
            week_start=week_start,
            total_activities=len(activities),
            total_duration_minutes=sum(a.duration_minutes for a in activities),
            total_distance_km=round(total_distance, 2),
            total_volume_kg=round(total_volume, 2),
        ))

    return summaries


@router.get("/monthly", response_model=list[MonthlySummary])
async def monthly_stats(
    months: int = 12,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    summaries = []

    for i in range(months):
        month = today.month - i
        year = today.year
        while month <= 0:
            month += 12
            year -= 1

        first_day = date(year, month, 1)
        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)

        result = await db.execute(
            select(Activity)
            .options(selectinload(Activity.endurance_data), selectinload(Activity.exercises).selectinload(Exercise.sets))
            .where(Activity.user_id == current_user.id, Activity.activity_date >= first_day, Activity.activity_date <= last_day)
        )
        activities = result.scalars().all()

        total_distance = sum(a.endurance_data.distance_km for a in activities if a.endurance_data)
        total_volume = sum(
            (s.weight_kg or 0) * (s.reps or 0)
            for a in activities
            for ex in a.exercises
            for s in ex.sets
        )

        summaries.append(MonthlySummary(
            year=year,
            month=month,
            total_activities=len(activities),
            total_duration_minutes=sum(a.duration_minutes for a in activities),
            total_distance_km=round(total_distance, 2),
            total_volume_kg=round(total_volume, 2),
        ))

    return list(reversed(summaries))


@router.get("/prs", response_model=list[PersonalRecord])
async def personal_records(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(
            Exercise.name,
            func.max(ExerciseSet.weight_kg).label("max_weight"),
            func.max(ExerciseSet.reps).label("max_reps"),
            func.max(Activity.activity_date).label("achieved_on"),
        )
        .join(ExerciseSet, ExerciseSet.exercise_id == Exercise.id)
        .join(Activity, Activity.id == Exercise.activity_id)
        .where(Activity.user_id == current_user.id, ExerciseSet.weight_kg.isnot(None))
        .group_by(Exercise.name)
        .order_by(func.max(ExerciseSet.weight_kg).desc())
    )
    rows = result.all()
    return [
        PersonalRecord(
            exercise_name=row.name,
            max_weight_kg=row.max_weight,
            max_reps=row.max_reps,
            achieved_on=row.achieved_on,
        )
        for row in rows
    ]


@router.get("/streak", response_model=StreakInfo)
async def streak(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Activity.activity_date)
        .where(Activity.user_id == current_user.id)
        .order_by(Activity.activity_date.desc())
    )
    dates = sorted(set(row[0] for row in result.all()), reverse=True)

    if not dates:
        return StreakInfo(current_streak=0, longest_streak=0, last_activity_date=None)

    today = date.today()
    current_streak = 0
    check = today
    for d in dates:
        if d == check or d == check - timedelta(days=1):
            current_streak += 1
            check = d
        elif d < check - timedelta(days=1):
            break

    # Longest streak
    longest = 1
    current_run = 1
    for i in range(1, len(dates)):
        if (dates[i - 1] - dates[i]).days == 1:
            current_run += 1
            longest = max(longest, current_run)
        else:
            current_run = 1

    return StreakInfo(current_streak=current_streak, longest_streak=longest, last_activity_date=dates[0])
