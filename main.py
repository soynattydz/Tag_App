from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, List
import jwt
import json
from pydantic import BaseModel, EmailStr, confloat, conint, ConfigDict
from database import SessionLocal, engine
import models
from dotenv import load_dotenv
import os
from math import radians, sin, cos, sqrt, atan2

load_dotenv()

# Initialize FastAPI app
app = FastAPI()

@app.get("/")
def home():
    return {"message": "Welcome to tag!"}

# Security configs
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Pydantic models for request/response
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class User(BaseModel):
    email: EmailStr
    full_name: str
    is_active: bool = True
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    interests: Optional[List[str]] = None
    max_distance: Optional[float] = None
    preferred_age_range_min: Optional[int] = None
    preferred_age_range_max: Optional[int] = None
    age: Optional[int] = None
    gender: Optional[str] = None

    model_config = ConfigDict(from_attributes=True) 

class Token(BaseModel):
    access_token: str
    token_type: str

class ProfileUpdate(BaseModel):
    latitude: Optional[confloat(ge=-90, le=90)]
    longitude: Optional[confloat(ge=-180, le=180)]
    interests: Optional[List[str]]
    max_distance: Optional[confloat(ge=0, le=100)]
    preferred_age_range_min: Optional[conint(ge=18)]
    preferred_age_range_max: Optional[conint(ge=18)]
    age: Optional[conint(ge=18)]
    gender: Optional[str]

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in kilometers using Haversine formula"""
    R = 6371  # Earth's radius in kilometers

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c

    return distance

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception
    
    user = get_user(db, email)
    if user is None:
        raise credentials_exception
    return user

# User operations
def get_user(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def authenticate_user(db: Session, email: str, password: str):
    user = get_user(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

# Endpoints
@app.post("/register", response_model=User)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.put("/users/profile", response_model=User)
async def update_profile(
    profile: ProfileUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_data = profile.dict(exclude_unset=True)
    if user_data.get("interests"):
        user_data["interests"] = json.dumps(user_data["interests"])
    
    db_user = db.query(models.User).filter(models.User.id == current_user.id)
    db_user.update(user_data)
    db.commit()
    
    return db_user.first()

@app.get("/users/nearby", response_model=List[User])
async def get_nearby_users(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.latitude or not current_user.longitude:
        raise HTTPException(status_code=400, detail="User location not set")

    max_distance = current_user.max_distance or 10  # Default to 10km if not set
    
    # Get all users except current user
    all_users = db.query(models.User).filter(
        models.User.id != current_user.id,
        models.User.latitude.isnot(None),
        models.User.longitude.isnot(None)
    ).all()
    
    # Filter users by distance
    nearby_users = [
        user for user in all_users
        if calculate_distance(
            current_user.latitude,
            current_user.longitude,
            user.latitude,
            user.longitude
        ) <= max_distance
    ]
    
    return nearby_users