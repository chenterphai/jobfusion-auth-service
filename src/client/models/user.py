from datetime import datetime, timezone
from typing import List, Optional
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
    token: str = Field(...)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "username": "chenterphai"
            }
        }
    )
