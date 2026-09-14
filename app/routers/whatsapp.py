from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app import models, schemas
from app.services.whatsapp_service import mock_groups_for_new_connection

router = APIRouter(prefix="/api/whatsapp", tags=["WhatsApp"])


@router.post("/connect", response_model=list[schemas.WhatsAppGroupOut])
def connect_whatsapp(
    payload: schemas.WhatsAppConnectRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    DEMO NOTICE: this does not open a real WhatsApp session. It simulates
    the official WhatsApp Business API hand-off and returns a sample list
    of groups, matching what a real connection would surface in-app.
    """
    current_user.whatsapp_connected = True
    current_user.whatsapp_number = payload.whatsapp_number

    # Clear any previous demo groups then insert fresh mock ones.
    db.query(models.WhatsAppGroup).filter(
        models.WhatsAppGroup.user_id == current_user.id
    ).delete()

    groups = []
    for g in mock_groups_for_new_connection():
        group = models.WhatsAppGroup(user_id=current_user.id, **g)
        db.add(group)
        groups.append(group)

    db.commit()
    for g in groups:
        db.refresh(g)
    return groups


@router.get("/groups", response_model=list[schemas.WhatsAppGroupOut])
def list_groups(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.WhatsAppGroup)
        .filter(models.WhatsAppGroup.user_id == current_user.id)
        .all()
    )
