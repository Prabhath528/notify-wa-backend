from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app import models, schemas
from app.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.UserRegister, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(
        or_(
            models.User.username == payload.username,
            models.User.email == payload.email,
            models.User.phone_number == payload.phone_number,
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Username, email or phone number is already registered",
        )

    user = models.User(
        username=payload.username,
        email=payload.email,
        phone_number=payload.phone_number,
        hashed_password=hash_password(payload.password),
        agreed_to_terms=payload.agree_to_terms,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return schemas.Token(access_token=token, user=schemas.UserOut.model_validate(user))


@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        or_(
            models.User.username == payload.identifier,
            models.User.phone_number == payload.identifier,
        )
    ).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username/phone or password")

    # remember_me only affects how long the client keeps the token stored
    # locally (handled in the Flutter app); the server still issues a
    # normal-length token either way.
    token = create_access_token({"sub": str(user.id)})
    return schemas.Token(access_token=token, user=schemas.UserOut.model_validate(user))
