from datetime import datetime, timedelta, timezone
from bson import ObjectId
from grpc import ServicerContext
import logging

from pymongo import ReturnDocument

from src.client.models.user import UserModel, UserUpdateRequest
from src.config.settings import settings
from src.server.grpc import user_pb2, user_pb2_grpc
from src.config.database import db_instance, connect_to_mongo
from src.utils import clean_data
from src.utils.serial import serial_doc
from src.utils.jwt import authenticate_user, create_jwt_token, get_current_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserServices(user_pb2_grpc.UserServicesServicer):
    
    ## User Detail Function
    async def UserDetail(self, request: user_pb2.UserRequest, context: ServicerContext):
        if db_instance.db is None:
            await connect_to_mongo()

        try:
            collection = db_instance.db.get_collection("fa_users")

            user = await get_current_user(token=request.token, collection=collection)

            if user:
                serialized_user = serial_doc(user)

                user_data = user_pb2.UserBase(
                    id = str(serialized_user["_id"]),
                    username = serialized_user["username"],
                    email = serialized_user["email"],
                    phone = serialized_user["phone"],
                    ip_address = serialized_user["ip_address"],
                    url = serialized_user["url"],
                    provider = serialized_user["provider"],
                    is_verified = serialized_user["is_verified"],
                    avatar = serialized_user["avatar"],
                    firstname = serialized_user["firstname"],
                    lastname = serialized_user["lastname"],
                    created_at = serialized_user["created_at"],
                    updated_at = serialized_user["updated_at"],
                    token = serialized_user["token"]
                )

                return user_pb2.UserResponse(
                    code = 0,
                    message = "Successfully",
                    user = user_data
                )
            
            return user_pb2.UserResponse(
                code = 1,
                message = "Not Found."
            )

        except Exception as e:
            return user_pb2.UserResponse(
                code = 0,
                message = f"Exception: {e}"
            )
        

    async def UserSignIn(self, request: user_pb2.UserSignInRequest, context: ServicerContext):
        if db_instance.db is None:
            await connect_to_mongo()

        try:
            collection = db_instance.db.get_collection("fa_users")

            user = await authenticate_user(
                identifier=request.identifier,
                password=request.password,
                collection=collection,
            )
            if user:

                serialized_user = serial_doc(user)

                access_token_expires = timedelta(
                    minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
                )
                access_token = create_jwt_token(
                    data={"sub": serialized_user["username"]},
                    expires_delta=access_token_expires,
                )

                # UPDATE
                await collection.update_one(
                    {"username": serialized_user["username"]},
                    {
                        "$set": {
                            "last_login": datetime.now(timezone.utc),
                            # "ip_address": params.client.host,
                            "token": access_token,
                        }
                    },
                )

                user_data = user_pb2.UserBase(
                    id = str(serialized_user["_id"]),
                    username = serialized_user["username"],
                    email = serialized_user["email"],
                    phone = serialized_user["phone"],
                    ip_address = serialized_user["ip_address"],
                    url = serialized_user["url"],
                    provider = serialized_user["provider"],
                    is_verified = serialized_user["is_verified"],
                    avatar = serialized_user["avatar"],
                    firstname = serialized_user["firstname"],
                    lastname = serialized_user["lastname"],
                    created_at = serialized_user["created_at"],
                    updated_at = serialized_user["updated_at"],
                    token = access_token
                )

                return user_pb2.UserResponse(
                    code=0,
                    message="Successfully login.",
                    user=user_data
                )
            
            return user_pb2.UserResponse(
                code=1,
                message="Unsuccessfully Authenticated!"
            )

            
        except Exception as e:
            return user_pb2.UserResponse(
                code=1,
                message=f"Something went wrong: {e}"
            )
        
        
    async def UserSignUp(self, request: user_pb2.UserSignUpRequest, context: ServicerContext):
        if db_instance.db is None:
            await connect_to_mongo()

        try:
            query_conditions = [{"username": request.username}]

            if request.email:
                query_conditions.append({"email": request.email})

            if request.phone:
                query_conditions.append({"phone": request.phone})

            collection = db_instance.db.get_collection("fa_users")

            existing_user = await collection.find_one({"$or": query_conditions})

            if existing_user:
                if existing_user.get("username") == request.username:
                    msg = "Username already taken."
                elif request.email and existing_user.get("email") == request.email:
                    msg = "Email already registered."
                elif request.phone and existing_user.get("phone") == request.phone:
                    msg = "Phone already registered."
                else:
                    msg = "User already exists."

                return user_pb2.UserResponse(
                    code = 1,
                    message = msg
                )
            
            user_doc = UserModel(
                username=request.username,
                email=request.email,
                phone=request.phone,
                password=request.password,
                firstname=request.firstname,
                lastname=request.lastname,
                is_verified=request.is_verified,
                provider=request.provider,
                url=request.url,
                ip_address=request.ip_address,
                token=request.token,
                created_at=request.created_at,
                updated_at=request.updated_at
            )

            new_user = await collection.insert_one(user_doc.model_dump(by_alias=True, exclude=["id"]))

            if not new_user.acknowledged:
                return user_pb2.UserResponse(
                    code = 1,
                    message = "Unfortunately, you have failed try to sign up."
                )
            
            created_user = await collection.find_one({"_id": ObjectId(new_user.inserted_id)})

            serialized_user = serial_doc(created_user)

            user = user_pb2.UserBase(
                    id = str(serialized_user["_id"]),
                    username = serialized_user["username"],
                    email = serialized_user.get("email", ""),
                    phone = serialized_user.get("phone", ""),
                    ip_address = serialized_user["ip_address"],
                    url = serialized_user["url"],
                    provider = serialized_user["provider"],
                    is_verified = serialized_user["is_verified"],
                    avatar = serialized_user.get("avatar", ""),
                    firstname = serialized_user.get("firstname", ""),
                    lastname = serialized_user.get("lastname", ""),
                    created_at = serialized_user["created_at"],
                    updated_at = serialized_user["updated_at"],
                    token = serialized_user["token"]
                )
            
            return user_pb2.UserResponse(
                code = 0,
                message = "Successfully sign up.",
                user = user
            )


        except Exception as e:
            return user_pb2.UserResponse(
                code = 1,
                message = f"Something went wrong: {e}"
            )
        


    async def UserUpdate(self, request: user_pb2.UserUpdateRequest, context: ServicerContext):
        if db_instance.db is None:
            await connect_to_mongo()

        try:
            collection = db_instance.db.get_collection("fa_users")

            # Validate presence of token
            if not request.token:
                return user_pb2.UserResponse(
                    code=1,
                    message="Token is required for update."
                )

            # Prepare update data
            request_data = UserUpdateRequest(
                avatar=request.avatar,
                email=request.email,
                firstname=request.firstname,
                ip_address=request.ip_address,
                is_verified=request.is_verified,
                lastname=request.lastname,
                phone=request.phone,
                provider=list(request.provider),
                updated_at=request.updated_at,
                url=request.url,
                username=request.username,
                token=request.token
            ).model_dump(by_alias=True, exclude_none=True)

            # Clean data recursively
            data = clean_data.clean_data_recursively(request_data)

            # Perform update
            update_result = await collection.find_one_and_update(
                {"token": request.token},
                {"$set": data},
                return_document=ReturnDocument.AFTER
            )

            # If update fails or user not found
            if not update_result:
                return user_pb2.UserResponse(
                    code=1,
                    message="User not found or update failed."
                )

            return user_pb2.UserResponse(
                code=0,
                message="Successfully updated profile."
            )

        except Exception as e:
            logger.error(f"Error in UserUpdate: {e}")
            return user_pb2.UserResponse(
                code=1,
                message="Something went wrong, please try again later."
            )
