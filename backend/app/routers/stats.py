from collections import defaultdict
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Activity, BodyWeight, User
from app.routers.auth import get_current_user
from app.schemas import DashboardOut, DayStars, MonthStars, UserDashboard, BodyWeightOut

router = APIRouter(prefix="/stats", tags=["stats"])

MONTHS_DE = ["", "Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
             "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]


def _month_label(year: int, month: int) -> str:
    return f"{MONTHS_DE[month]} {str(year)[2:]}"


async def build_user_dashboard(db: AsyncSession, user: User) -> UserDashboard:
    today = date.today()
    two_weeks_ago = today - timedelta(days=13)

    # Last 14 days
    result = await db.execute(
        select(Activity.activity_date, Activity.stars)
        .where(Activity.user_id == user.id, Activity.activity_date >= two_weeks_ago)
    )
    by_date: dict[date, int] = defaultdict(int)
    for d, s in result.all():
        by_date[d] = min(by_date[d] + s, 3)

    week = [DayStars(date=today - timedelta(days=i), stars=by_date.get(today - timedelta(days=i), 0))
            for i in range(6, -1, -1)]
    today_stars = by_date.get(today, 0)
    two_week_total_stars = sum(by_date.values())
    two_week_training_days = sum(1 for s in by_date.values() if s > 0)

    # Last 6 months
    six_months_ago = date(today.year, today.month, 1)
    for _ in range(5):
        if six_months_ago.month == 1:
            six_months_ago = date(six_months_ago.year - 1, 12, 1)
        else:
            six_months_ago = date(six_months_ago.year, six_months_ago.month - 1, 1)

    monthly_result = await db.execute(
        select(Activity.activity_date, Activity.stars)
        .where(Activity.user_id == user.id, Activity.activity_date >= six_months_ago)
    )
    # Per day capped, then sum per month
    day_stars: dict[date, int] = defaultdict(int)
    for d, s in monthly_result.all():
        day_stars[d] = min(day_stars[d] + s, 3)

    month_data: dict[tuple, dict] = {}
    for d, s in day_stars.items():
        key = (d.year, d.month)
        if key not in month_data:
            month_data[key] = {"stars": 0, "training_days": 0}
        month_data[key]["stars"] += s
        if s > 0:
            month_data[key]["training_days"] += 1

    monthly_stars = []
    cur = six_months_ago
    for _ in range(6):
        key = (cur.year, cur.month)
        data = month_data.get(key, {"stars": 0, "training_days": 0})
        monthly_stars.append(MonthStars(
            year=cur.year,
            month=cur.month,
            label=_month_label(cur.year, cur.month),
            stars=data["stars"],
            training_days=data["training_days"],
        ))
        if cur.month == 12:
            cur = date(cur.year + 1, 1, 1)
        else:
            cur = date(cur.year, cur.month + 1, 1)

    # Body weight
    bw_result = await db.execute(
        select(BodyWeight)
        .where(BodyWeight.user_id == user.id)
        .order_by(BodyWeight.measured_at.desc())
        .limit(60)
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
        monthly_stars=monthly_stars,
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
