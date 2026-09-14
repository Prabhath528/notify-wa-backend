from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.config import settings
from app import models, schemas

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.get("/me/home-summary", response_model=schemas.HomeSummary)
def home_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    active_schedules = (
        db.query(models.ScheduleReminder)
        .filter(
            models.ScheduleReminder.user_id == current_user.id,
            models.ScheduleReminder.status == models.ScheduleStatus.active,
        )
        .count()
    )
    sent_messages = (
        db.query(models.MessageLog)
        .filter(models.MessageLog.user_id == current_user.id)
        .count()
    )
    upcoming = (
        db.query(models.ScheduleReminder)
        .filter(
            models.ScheduleReminder.user_id == current_user.id,
            models.ScheduleReminder.status == models.ScheduleStatus.active,
        )
        .order_by(models.ScheduleReminder.scheduled_date, models.ScheduleReminder.scheduled_time)
        .limit(5)
        .all()
    )

    limit = current_user.message_limit(settings)

    return schemas.HomeSummary(
        username=current_user.username,
        plan=current_user.plan,
        messages_used_this_month=current_user.messages_used_this_month,
        message_limit=limit,
        active_schedules=active_schedules,
        sent_messages=sent_messages,
        upcoming=upcoming,
    )
