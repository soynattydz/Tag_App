# models.py
from sqlalchemy import Boolean, Column, Integer, String, Float, ForeignKey, Table
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    latitude = Column(Float)
    longitude = Column(Float)
    interests = Column(String)  # Store as JSON string
    max_distance = Column(Float, default=10.0)  # in kilometers
    preferred_age_range_min = Column(Integer, default=18)
    preferred_age_range_max = Column(Integer, default=100)
    age = Column(Integer)
    gender = Column(String)