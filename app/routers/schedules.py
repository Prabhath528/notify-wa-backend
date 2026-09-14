from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app import models, schemas

router = APIRouter(prefix="/api/schedules", tags=["Schedules"])


@router.post("", response_model=schemas.ScheduleOut, status_code=201)
def create_schedule(
    payload: schemas.ScheduleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    schedule = models.ScheduleReminder(
        user_id=current_user.id,
        target_group_id=payload.target_group_id,
        target_group_name=payload.target_group_name,
        message_body=payload.message_body,
        frequency=payload.frequency,
        scheduled_date=payload.scheduled_date,
        scheduled_time=payload.scheduled_time,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.get("", response_model=list[schemas.ScheduleOut])
def list_schedules(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.ScheduleReminder)
        .filter(models.ScheduleReminder.user_id == current_user.id)
        .order_by(models.ScheduleReminder.scheduled_date, models.ScheduleReminder.scheduled_time)
        .all()
    )


@router.put("/{schedule_id}", response_model=schemas.ScheduleOut)
def update_schedule(
    schedule_id: int,
    payload: schemas.ScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    schedule = (
        db.query(models.ScheduleReminder)
        .filter(
            models.ScheduleReminder.id == schedule_id,
            models.ScheduleReminder.user_id == current_user.id,
        )
        .first()
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(schedule, field, value)

    db.commit()
    db.refresh(schedule)
    return schedule


@router.delete("/{schedule_id}", status_code=204)
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    schedule = (
        db.query(models.ScheduleReminder)
        .filter(
            models.ScheduleReminder.id == schedule_id,
            models.ScheduleReminder.user_id == current_user.id,
        )
        .first()
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    db.delete(schedule)
    db.commit()
    return None
