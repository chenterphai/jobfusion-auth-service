from typing import Annotated
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pydantic import BeforeValidator
from src.config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None

db_instance = Database()

async def connect_to_mongo():
    db_instance.client = AsyncIOMotorClient("mongodb+srv://chenter404:c3Futureapps@zynx-auth.yxarrsu.mongodb.net/?retryWrites=true&w=majority&appName=zynx-auth")
    db_instance.db = db_instance.client[settings.MONGODB_DATABASE]
    logger.info(" ✅ Connected to MongoDB")

async def close_mongo_connection():
    db_instance.client.close()
    logger.info(" ❌ Disconnected from MongoDB")

async def get_async_db ():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DATABASE]
    try:
        yield db
    finally:
        client.close()


# Represents an ObjectId field in the database.
# It will be represented as a `str` on the model so that it can be serialized to JSON.
PyObjectId = Annotated[str, BeforeValidator(str)]

# class StudentModel(BaseModel):
#     """
#     Container for a single student record.
#     """

#     # The primary key for the StudentModel, stored as a `str` on the instance.
#     # This will be aliased to `_id` when sent to MongoDB,
#     # but provided as `id` in the API requests and responses.
#     id: Optional[PyObjectId] = Field(alias="_id", default=None)
#     name: str = Field(...)
#     email: EmailStr = Field(...)
#     course: str = Field(...)
#     gpa: float = Field(..., le=4.0)
#     model_config = ConfigDict(
#         populate_by_name=True,
#         arbitrary_types_allowed=True,
#         json_schema_extra={
#             "example": {
#                 "name": "Jane Doe",
#                 "email": "jdoe@example.com",
#                 "course": "Experiments, Science, and Fashion in Nanophotonics",
#                 "gpa": 3.0,
#             }
#         },
#     )

