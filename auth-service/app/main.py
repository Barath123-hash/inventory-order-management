from jose import jwt
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from passlib.context import CryptContext

app = FastAPI(title="Authentication Service")

SECRET_KEY = "dev-secret-change-before-submission"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(user_id: int, role: str):
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)



DATABASE_URL = "sqlite:///./auth.db"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="customer", nullable=False)


Base.metadata.create_all(bind=engine)


class RegisterData(BaseModel):
    email: EmailStr
    password: str


@app.get("/")
def home():
    return {"message": "Authentication Service is running"}


@app.post("/auth/register")
def register(data: RegisterData):
    db = SessionLocal()
    try:
        existing = db.query(User).filter(
            User.email == data.email
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        if len(data.password) < 8:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 8 characters"
            )

        user = User(
            email=data.email,
            hashed_password=pwd_context.hash(data.password)
        )
        db.add(user)
        db.commit()

        return {"message": "Registration successful"}
    finally:
        db.close()


@app.post("/auth/login")
def login(data: RegisterData):
    db = SessionLocal()
    try:
        user = db.query(User).filter(
            User.email == data.email
        ).first()

        if not user or not pwd_context.verify(
            data.password, user.hashed_password
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        token = create_access_token(user.id, user.role)

        return {
           "message": "Login successful",
            "access_token": token,
            "token_type": "bearer",
            "user_id": user.id,
             "email": user.email,
              "role": user.role
            }
    
     
    finally:
        db.close()
