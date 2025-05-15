from datetime import datetime, timezone
from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.config.database import PyObjectId


class UserModel(BaseModel):

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    username: str = Field(...)
    password: Optional[str] = Field(None)
    email: Optional[EmailStr] = Field(None)
    phone: Optional[str] = Field(None)
    ip_address: str = Field(...)
    url: str = Field(...)
    provider: List[str] = Field(...)
    is_verified: int = Field(default=0)
    avatar: Optional[str] = Field(None)
    firstname: Optional[str] = Field(None)
    lastname: Optional[str] = Field(None)
    created_at: datetime = Field(default=datetime.now(timezone.utc))
    updated_at: datetime = Field(default=datetime.now(timezone.utc))
    token: Optional[str] = Field(None)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        # json_schema_extra={
        #     "example": {
        #         "username": "chenterphai",
        #         "ip_address": "192.168.1.5",
        #         "url":"https://chenterphai.jobfusion.com",
        #         "provider": ["email"],
        #         "email": "chenterphai61@gmail.com",
        #         "password": "123456"
        #     }
        # }
    )

class UserLoginRequest(BaseModel):
    identifier: str = Field(...)
    password: str = Field(...)

class UserDetailRequest(BaseModel):
    token: str = Field(...)

class UserUpdateRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    ip_address: Optional[str] = None
    url: Optional[str] = None
    provider: Optional[List[str]] = None
    is_verified: Optional[int] = None
    avatar: Optional[str] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    token: str
    updated_at: datetime = Field(default=datetime.now(timezone.utc))
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class UserResponse(BaseModel):

    id: Optional[PyObjectId] = Field(alias="id", default=None)
    username: str = Field(...)
    email: Optional[EmailStr] = Field(None)
    phone: Optional[str] = Field(None)
    ip_address: str = Field(...)
    url: str = Field(...)
    provider: List[str] = Field(...)
    is_verified: int = Field(default=0)
    avatar: Optional[str] = Field(None)
    firstname: Optional[str] = Field(None)
    lastname: Optional[str] = Field(None)
    created_at: datetime = Field(default=datetime.now(timezone.utc))
    updated_at: datetime = Field(default=datetime.now(timezone.utc))
    token: Optional[str] = Field(None)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
