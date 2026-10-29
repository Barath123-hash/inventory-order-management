from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker

app = FastAPI(title="Notification Service")

engine = create_engine(
    "sqlite:///./notifications.db",
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String, default="UNREAD")


Base.metadata.create_all(bind=engine)


class NotificationData(BaseModel):
    user_id: int
    message: str


@app.get("/")
def home():
    return {"message": "Notification Service is running"}


@app.post("/notifications")
def create_notification(data: NotificationData):
    db = SessionLocal()
    try:
        notification = Notification(
            user_id=data.user_id,
            message=data.message,
            status="UNREAD"
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

        return {
            "message": "Notification created",
            "notification_id": notification.id,
            "user_id": notification.user_id,
            "notification": notification.message,
            "status": notification.status
        }
    finally:
        db.close()


@app.get("/notifications/{user_id}")
def get_notifications(user_id: int):
    db = SessionLocal()
    try:
        items = db.query(Notification).filter(
            Notification.user_id == user_id
        ).all()

        return [
            {
                "notification_id": item.id,
                "message": item.message,
                "status": item.status
            }
            for item in items
        ]
    finally:
        db.close()