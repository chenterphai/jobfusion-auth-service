from datetime import datetime, timedelta
from fastapi import APIRouter, Body, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import grpc
from google.protobuf.json_format import MessageToDict, ParseDict

from src.client.models.user import UserModel, UserResponse
from src.config.settings import settings
from src.utils.jwt import create_jwt_token, get_hashed_password
from src.utils.response import ResponseModel, Result, Status
from src.server.grpc import user_pb2, user_pb2_grpc

router = APIRouter()


@router.post(
        "/",
        response_description="Sign Up",
        status_code=status.HTTP_201_CREATED,
        response_model_by_alias=False
)
async def signup(user: UserModel = Body(...)):
    social_providers = {"google", "github", "apple", "linkedin"}
    email_provider = "email"
    phone_provider = "phone"
    all_providers = social_providers.union({email_provider, phone_provider})

    # Ensure only one provider is selected
    if len(user.provider) != 1:
        return JSONResponse(
            content=ResponseModel(
                status=Status(code=1, msg="Exactly one provider must be specified.", status="failed"),
                result=Result(data=None)
            ).model_dump()
        )
    provider = user.provider[0].lower()

    # Validate provider
    if provider not in all_providers:
        return JSONResponse(
            content=ResponseModel(
                status=Status(code=1, msg="Invalid provider.", status="failed"),
                result=Result(data=None)
            ).model_dump()
        )

    # Validate required fields
    if provider == email_provider and not user.email:
        return JSONResponse(
            content=ResponseModel(
                status=Status(code=1, msg="Email is required for email registration.", status="failed"),
                result=Result(data=None)
            ).model_dump()
        )

    if provider == phone_provider and not user.phone:
        return JSONResponse(
            content=ResponseModel(
                status=Status(code=1, msg="Phone is required for phone registration.", status="failed"),
                result=Result(data=None)
            ).model_dump()
        )

    if provider in {email_provider, phone_provider} and not user.password:
        return JSONResponse(
            content=ResponseModel(
                status=Status(code=1, msg="Password is required for email or phone registration.", status="failed"),
                result=Result(data=None)
            ).model_dump()
        )
    # Hash password only for email/phone registration
    hashed_password = get_hashed_password(user.password) if provider in {email_provider, phone_provider} else None
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_jwt_token(data={"sub": user.username}, expires_delta=access_token_expires)

    async with grpc.aio.insecure_channel("localhost:50051") as channel:
        stub = user_pb2_grpc.UserServicesStub(channel)

        try:

            request_data = {
                "username": user.username,
                "password": hashed_password,
                "provider": [provider],
                "ip_address": user.ip_address,
                "is_verified": user.is_verified,
                "url": user.url,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "token": access_token,
            }

            if user.email:
                request_data["email"] = user.email
            if user.phone:
                request_data["phone"] = user.phone
            if user.firstname:
                request_data["firstname"] = user.firstname
            if user.lastname:
                request_data["lastname"] = user.lastname

            for field in ['created_at', 'updated_at']:
                if isinstance(request_data.get(field), datetime):
                    request_data[field] = request_data[field].isoformat()

            message = ParseDict(request_data, user_pb2.UserSignUpRequest())

            response = await stub.UserSignUp(message)

            user_dict = MessageToDict(response, preserving_proto_field_name=True)

            return JSONResponse(
                    content=jsonable_encoder(ResponseModel(
                        status=Status(
                            code=user_dict.get("code", 0),
                            msg=user_dict["message"],
                            status="success"
                        ),
                        result=Result(data=UserResponse(**user_dict.get("user")) if user_dict.get("code", 0) == 0 else None)
                    )),
                    status_code=status.HTTP_200_OK
                )
        except grpc.aio.AioRpcError as e:
            return JSONResponse(
                    content=jsonable_encoder(ResponseModel(
                        status=Status(
                            code=1,
                            msg=f"Exception: {e}",
                            status="error"
                        ),
                        result=Result(data=None)
                    )),
                    status_code=status.HTTP_200_OK
                )