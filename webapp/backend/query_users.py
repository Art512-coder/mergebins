from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import User  # Adjust import if User model is in a different file
from app.database import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db = SessionLocal()
try:
    users = db.query(User).all()
    for user in users:
        print(f"ID: {user.id}, Email: {user.email}, Username: {user.username}")  # Adjust fields as per your User model
finally:
    db.close()