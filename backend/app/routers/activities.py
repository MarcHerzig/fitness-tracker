import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Activity, ActivityExercise, User
from app.routers.auth import get_current_user
from app.schemas import ActivityCreate, ActivityOut

router = APIRouter(prefix="/activities", tags=["activities"])


def calc_endurance_stars(km: float) -> int:
    if km >= 30:
        return 3
    if km >= 20:
        return 2
    if km >= 10:
        return 1
    return 0


def calc_strength_stars(total_sets: int) -> int:
    if total_sets >= 18:
        return 3
    if total_sets >= 10:
        return 2
    if total_sets >= 3:
        return 1
    return 0


async def get_day_stars(db: AsyncSession, user_id: uuid.UUID, day: date) -> int:
    result = await db.execute(
        select(func.sum(Activity.stars)).where(
            Activity.user_id == user_id,
            Activity.activity_date == day,
        )
    )
    return min(int(result.scalar() or 0), 3)


def _load_opts():
    return selectinload(Activity.activity_exercises).selectinload(ActivityExercise.template)


@router.get("", response_model=list[ActivityOut])
async def list_activities(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Activity)
        .options(_load_opts())
        .where(Activity.user_id == current_user.id)
        .order_by(Activity.activity_date.desc(), Activity.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.post("", response_model=ActivityOut, status_code=201)
async def create_activity(
    data: ActivityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.type == "endurance":
        if not data.distance_km:
            raise HTTPException(status_code=400, detail="distance_km required for endurance")
        stars = calc_endurance_stars(data.distance_km)
    else:
        total_sets = sum(e.sets_completed for e in data.exercises)
        stars = calc_strength_stars(total_sets)

    activity = Activity(
        user_id=current_user.id,
        type=data.type,
        subtype=data.subtype,
        activity_date=data.activity_date,
        distance_km=data.distance_km,
        stars=stars,
        notes=data.notes,
    )
    db.add(activity)
    await db.flush()

    for ex in data.exercises:
        if ex.sets_completed > 0:
            db.add(ActivityExercise(
                activity_id=activity.id,
                template_id=ex.template_id,
                sets_completed=ex.sets_completed,
            ))

    await db.commit()

    result = await db.execute(
        select(Activity).options(_load_opts()).where(Activity.id == activity.id)
    )
    return result.scalar_one()


@router.get("/{activity_id}", response_model=ActivityOut)
async def get_activity(
    activity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Activity)
        .options(_load_opts())
        .where(Activity.id == activity_id, Activity.user_id == current_user.id)
    )
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Not found")
    return activity


@router.delete("/{activity_id}", status_code=204)
async def delete_activity(
    activity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Activity).where(Activity.id == activity_id, Activity.user_id == current_user.id)
    )
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(activity)
    await db.commit()
