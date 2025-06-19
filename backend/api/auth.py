from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Query

from backend.schemas.user import UserCreate, UserRead
from backend.schemas.token import Token
from backend.models.user import User
from backend.db import get_async_db
from backend.auth import hash_password, verify_password, create_access_token
from uuid import uuid4
import smtplib
from email.message import EmailMessage
from jose import jwt, JWTError
from backend.auth import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/auth", tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def send_confirmation_email(to_email: str, token: str):
    link = f"http://localhost:3000/confirm-email/{token}"

    msg = EmailMessage()
    msg["Subject"] = "Confirmă adresa ta de email"
    msg["From"] = "razvantoderean@gmail.com"
    msg["To"] = to_email
    msg.set_content(f"Salut! Apasă pe link pentru a-ți confirma emailul:\n\n{link}")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login("razvantoderean@gmail.com", "obsd xyuo eire ttmm")
            smtp.send_message(msg)
        print(f"Email trimis către {to_email}")
    except Exception as e:
        print("Eroare la trimiterea emailului:", e)


#xhji ooov zsmp rhqy

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise

@router.post("/register", response_model=UserRead)
async def register(user: UserCreate, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(User).where(User.username == user.username))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    token = str(uuid4())
    db_user = User(
        username=user.username,
        password_hash=hash_password(user.password),
        email=user.email,
        public_key=user.public_key,
        confirmation_token=token,
        email_confirmed=False,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    send_confirmation_email(db_user.email, token)

    return db_user

@router.get("/confirm-email/{token}")
async def confirm_email(token: str, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(User).where(User.confirmation_token == token))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Token invalid")

    user.email_confirmed = True
    user.confirmation_token = None
    db.add(user)
    await db.commit()

    return {"message": "Email confirmat cu succes!"}


@router.post("/login", response_model=Token)
async def login(user: UserCreate, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(
        select(User).where(
            (User.username == user.username) | (User.email == user.username)
        )
    )
    db_user = result.scalar_one_or_none()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not db_user.email_confirmed:
        raise HTTPException(status_code=403, detail="Email need confirmation.")

    token = create_access_token(data={"sub": db_user.username})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/email-confirmed", response_model=bool)
async def is_email_confirmed(username: str = Query(...), db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.email_confirmed

@router.post("/resend-confirmation")
async def resend_confirmation_email(data: dict, db: AsyncSession = Depends(get_async_db)):
    username = data.get("username")
    if not username:
        raise HTTPException(status_code=400, detail="Missing username")

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.email_confirmed:
        raise HTTPException(status_code=400, detail="Email already confirmed")

    send_confirmation_email(user.email, user.confirmation_token)
    return {"message": "Confirmation email sent"}





