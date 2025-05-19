from typing import Annotated
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status

from src.config.settings import settings

from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection

from src.config.database import get_async_db

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

TOKEN_BLACKLIST = set()

PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")
OAUTH2_SCHEMA = OAuth2PasswordBearer(tokenUrl="sign-in")

##
# Function for Create new JWT Token
# For user login or register
# #
def create_jwt_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


##
# Function for Decode JWT Token
# And make sure that token is not expired
# #
def decode_jwt_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    

##
# Function for Verify Password fro User Input
# Use it when user login with Password
# #
def verify_password(plain_password, hashed_password):
    return PWD_CONTEXT.verify(plain_password, hashed_password)



##
# Function for Generate Hash Password
# For security ecrypt before store in database
# #
def get_hashed_password(password):
    return PWD_CONTEXT.hash(password)


##
# Helper Function for Get User Data
# #
async def get_user_collection (db: AsyncIOMotorDatabase = Depends(get_async_db)):
    return db["fa_users"]

# Fetch user data from database
async def get_user(identifier: str, collection: AsyncIOMotorCollection = Depends(get_user_collection)):
    collection.create_index({"username": 1})
    collection.create_index({"email": 1})
    collection.create_index({"phone": 1})
    user = await collection.find_one({
        "$or": [
            {"username": identifier},
            {"email": identifier},
            {"phone": identifier}
        ]
    })

    if not user:
        return None
    return user


##
# Authentication Dependency
# Get user Data by Injection
# #
async def get_current_user(
    token: Annotated[str, Depends(OAUTH2_SCHEMA)],
    collection: AsyncIOMotorCollection = Depends(get_user_collection)
):
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token in TOKEN_BLACKLIST:
        raise credentials_exception
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception

    user_data = await get_user(username, collection)

    if not user_data:
        raise credentials_exception
    return user_data


##
# Authenticate user function
# This use for user login
# #
async def authenticate_user(
    identifier: str, 
    password: str,
    collection: AsyncIOMotorCollection = Depends(get_user_collection)
):
    user_data = await get_user(identifier, collection)
    if not user_data:
        return None
    if not verify_password(password, user_data["password"]):
        return None
    return user_data