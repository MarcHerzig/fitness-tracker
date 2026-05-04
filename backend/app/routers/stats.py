from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Activity, BodyWeight, User
from app.routers.auth import get_current_user
from app.schemas import DashboardOut, DayStars, UserDashboard, BodyWeightOut

router = APIRouter(prefix="/stats", tags=["stats"])


async def build_user_dashboard(db: AsyncSession, user: User) -> UserDashboard:
    today = date.today()
    two_weeks_ago = today - timedelta(days=13)

    # All activities in last 14 days
    result = await db.execute(
        select(Activity.activity_date, Activity.stars)
        .where(Activity.user_id == user.id, Activity.activity_date >= two_weeks_ago)
    )
    rows = result.all()

    # Group by date, sum stars capped at 3
    from collections import defaultdict
    by_date: dict[date, int] = defaultdict(int)
    for d, s in rows:
        by_date[d] = min(by_date[d] + s, 3)

    # Week strip (last 7 days)
    week = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        week.append(DayStars(date=d, stars=by_date.get(d, 0)))

    # Today stars
    today_stars = by_date.get(today, 0)

    # 2-week totals
    two_week_total_stars = sum(by_date.values())
    two_week_training_days = len([s for s in by_date.values() if s > 0])

    # Body weight
    bw_result = await db.execute(
        select(BodyWeight)
        .where(BodyWeight.user_id == user.id)
        .order_by(BodyWeight.measured_at.desc())
        .limit(30)
    )
    weights = bw_result.scalars().all()
    last_weight = weights[0].weight_kg if weights else None

    return UserDashboard(
        user_id=user.id,
        username=user.username,
        today_stars=today_stars,
        week=week,
        two_week_total_stars=two_week_total_stars,
        two_week_training_days=two_week_training_days,
        last_weight=last_weight,
        weight_history=[BodyWeightOut.model_validate(w) for w in reversed(weights)],
    )


@router.get("/dashboard", response_model=DashboardOut)
async def dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.is_active == True))
    all_users = result.scalars().all()

    marc = next((u for u in all_users if u.username.lower() == "marc"), None)
    pia = next((u for u in all_users if u.username.lower() == "pia"), None)

    return DashboardOut(
        marc=await build_user_dashboard(db, marc) if marc else None,
        pia=await build_user_dashboard(db, pia) if pia else None,
    )


@router.get("/stars/week", response_model=list[DayStars])
async def stars_week(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = date.today()
    week_ago = today - timedelta(days=6)
    result = await db.execute(
        select(Activity.activity_date, func.sum(Activity.stars))
        .where(Activity.user_id == current_user.id, Activity.activity_date >= week_ago)
        .group_by(Activity.activity_date)
    )
    by_date = {d: min(int(s), 3) for d, s in result.all()}
    return [DayStars(date=today - timedelta(days=i), stars=by_date.get(today - timedelta(days=i), 0)) for i in range(6, -1, -1)]
