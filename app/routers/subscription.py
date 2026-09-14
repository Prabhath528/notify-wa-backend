import os
import shutil
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.config import settings
from app import models, schemas
from app.services.payhere_service import create_payhere_order, verify_payhere_notify_signature

router = APIRouter(prefix="/api/subscription", tags=["Subscription"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "receipts")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/plans", response_model=list[schemas.PlanOut])
def get_plans():
    return [
        schemas.PlanOut(
            id="free", name="Free", price_lkr=0,
            message_limit=settings.FREE_PLAN_MESSAGE_LIMIT,
        ),
        schemas.PlanOut(
            id="pro_500", name="Pro 500", price_lkr=settings.PRO_PLAN_PRICE_LKR,
            message_limit=settings.PRO_PLAN_MESSAGE_LIMIT, badge="Most Popular",
        ),
        schemas.PlanOut(
            id="unlimited", name="Pro Unlimited", price_lkr=settings.UNLIMITED_PLAN_PRICE_LKR,
            message_limit=-1,
        ),
    ]


@router.get("/bank-details", response_model=schemas.BankTransferOut)
def bank_details():
    return schemas.BankTransferOut(
        bank_name=settings.BANK_NAME,
        account_name=settings.BANK_ACCOUNT_NAME,
        account_number=settings.BANK_ACCOUNT_NUMBER,
        branch=settings.BANK_BRANCH,
    )


@router.post("/payhere/init", response_model=schemas.PayHereInitResponse)
def payhere_init(
    payload: schemas.PayHereInitRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if payload.plan == models.PlanType.free:
        raise HTTPException(status_code=400, detail="Free plan does not need payment")

    order = create_payhere_order(current_user, payload.plan)

    tx = models.PaymentTransaction(
        user_id=current_user.id,
        plan=payload.plan,
        amount_lkr=float(order["amount"]),
        method=models.PaymentMethod.payhere,
        status=models.PaymentStatus.pending,
        payhere_order_id=order["order_id"],
    )
    db.add(tx)
    db.commit()

    return schemas.PayHereInitResponse(**order)


@router.post("/payhere/notify")
def payhere_notify(
    merchant_id: str = Form(...),
    order_id: str = Form(...),
    payhere_amount: str = Form(...),
    payhere_currency: str = Form(...),
    status_code: str = Form(..., alias="status_code"),
    md5sig: str = Form(...),
    db: Session = Depends(get_db),
):
    """Webhook PayHere calls after a payment attempt. Not hit directly by the app."""
    valid = verify_payhere_notify_signature(
        merchant_id, order_id, payhere_amount, payhere_currency, status_code, md5sig
    )
    if not valid:
        raise HTTPException(status_code=400, detail="Invalid PayHere signature")

    tx = db.query(models.PaymentTransaction).filter(
        models.PaymentTransaction.payhere_order_id == order_id
    ).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if status_code == "2":  # PayHere: 2 = success
        tx.status = models.PaymentStatus.completed
        user = db.query(models.User).filter(models.User.id == tx.user_id).first()
        if user:
            user.plan = tx.plan
    else:
        tx.status = models.PaymentStatus.rejected

    db.commit()
    return {"received": True}


@router.post("/bank-transfer", response_model=schemas.PaymentTransactionOut)
def submit_bank_transfer(
    plan: models.PlanType = Form(...),
    receipt: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if plan == models.PlanType.free:
        raise HTTPException(status_code=400, detail="Free plan does not need payment")

    amount = (
        settings.PRO_PLAN_PRICE_LKR if plan == models.PlanType.pro_500
        else settings.UNLIMITED_PLAN_PRICE_LKR
    )

    ext = os.path.splitext(receipt.filename)[1] or ".jpg"
    filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(receipt.file, buffer)

    tx = models.PaymentTransaction(
        user_id=current_user.id,
        plan=plan,
        amount_lkr=amount,
        method=models.PaymentMethod.bank_transfer,
        status=models.PaymentStatus.pending,  # an admin reviews the slip manually
        receipt_image_path=filename,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx
