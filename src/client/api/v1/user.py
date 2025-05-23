from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Body, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import grpc
from google.protobuf.json_format import MessageToDict, ParseDict

from src.client.models.user import UserDetailRequest, UserLoginRequest, UserModel, UserResponse, UserUpdateRequest
from src.config.settings import settings
from src.utils.jwt import create_jwt_token, get_hashed_password
from src.utils.response import ResponseModel, Result, Status
from src.server.grpc import user_pb2, user_pb2_grpc

router = APIRouter()


@router.post("/check_health")
async def check_health():
    return {"status": "ok"}


@router.post(
        "/sign-up",
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

    # validate username
    if user.username is None or user.username == "":
        return JSONResponse(
            content=jsonable_encoder(ResponseModel(
                status=Status(code=1, msg="Username is required.", status="failed"),
                result=Result(data=None)
            )
        ))

    # validate ip_address
    if user.ip_address is None or user.ip_address == "":
        return JSONResponse(
            content=jsonable_encoder(ResponseModel(
                status=Status(code=1, msg="IP Address is required.", status="failed"),
                result=Result(data=None)
            ))
        )

    # validate url
    if user.url is None or user.url == "":
        return JSONResponse(
            content=jsonable_encoder(ResponseModel(
                status=Status(code=1, msg="URL is required.", status="failed"),
                result=Result(data=None)
            ))
        )

    async with grpc.aio.insecure_channel("localhost:50051") as channel:
        stub = user_pb2_grpc.UserServicesStub(channel)

        # Hash password only for email/phone registration
        hashed_password = get_hashed_password(user.password) if provider in {email_provider, phone_provider} else None

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_jwt_token(data={"sub": user.username}, expires_delta=access_token_expires)

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
        
@router.post(
    "/sign-in",
    status_code=status.HTTP_200_OK,
    response_description="User Login via Identifier / Password",
    response_model_by_alias=False
)
async def signin(request: Request, form_data: UserLoginRequest = Body(...)):
    async with grpc.aio.insecure_channel("localhost:50051") as channel:
        stub = user_pb2_grpc.UserServicesStub(channel)

        # validate form_data
        if not form_data.identifier or not form_data.password:
            return JSONResponse(
                content=jsonable_encoder(ResponseModel(
                    status=Status(
                        code=1,
                        msg="Identifier and Password are required.",
                        status="fail"
                    ),
                    result=Result(data=None)
                ))
            )

        try:

            request_data = {
                "identifier": form_data.identifier,
                "password": form_data.password,
                "ip_address": request.client.host,
            }

            request_message = ParseDict(request_data, user_pb2.UserSignInRequest())

            response = await stub.UserSignIn(request_message)

            user_dict = MessageToDict(response, preserving_proto_field_name=True)

            if user_dict.get("code", 0) == 1:
                return  JSONResponse(
                    content=jsonable_encoder(ResponseModel(
                        status=Status(
                            code=1,
                            msg="Failed to login. Please check your credentials.",
                            status="fail"
                        ),
                        result=Result(data=None),
                    ))
                )

            return JSONResponse(
                content=jsonable_encoder(ResponseModel(
                    status=Status(
                        code=0,
                        msg="Successfully logged in.",
                        status="success"
                    ),
                    result=Result(data=UserResponse(**user_dict.get("user")) if user_dict.get("code", 0) == 0 else None)
                ))
            )

        except Exception as e:
            return JSONResponse(
                content=jsonable_encoder(ResponseModel(
                    status=Status(
                        code=1,
                        msg=f"Exception: {e}",
                        status="fail"
                    ),
                    result=Result(data=None)
                ))
            )
        
@router.post(
    "/me",
    response_model_by_alias=False,
    status_code=status.HTTP_200_OK
)
async def profile(form_data: UserDetailRequest = Body(...)):
    async with grpc.aio.insecure_channel("localhost:50051") as channel:
        stub = user_pb2_grpc.UserServicesStub(channel)

        try:
            request_data = {
                "token": form_data.token
            }

            request_message = ParseDict(request_data, user_pb2.UserRequest())

            response = await stub.UserDetail(request_message)

            user_dict = MessageToDict(response, preserving_proto_field_name=True)

            return JSONResponse(
                content=jsonable_encoder(ResponseModel(
                    status=Status(
                        code=0,
                        msg="Successfully",
                        status="success"
                    ),
                    result=Result(data=UserResponse(**user_dict.get("user")) if user_dict.get("code", 0) == 0 else None)
                ))
            )

        except Exception as e:
            return JSONResponse(
                content=jsonable_encoder(ResponseModel(
                    status=Status(
                        code=1,
                        msg=f"Exception: {e}",
                        status="fail"
                    ),
                    result=Result(data=None)
                ))
            )
        
@router.post("/profile", response_model_by_alias=False, status_code=status.HTTP_200_OK)
async def update(form_data: UserUpdateRequest = Body(...)):
    async with grpc.aio.insecure_channel("localhost:50051") as channel:
        stub = user_pb2_grpc.UserServicesStub(channel)

        try:

            require_field = {
                "token": form_data.token,
                "updated_at": str(datetime.now(timezone.utc))
            }

            optional = {
                "username": form_data.username,
                "firstname": form_data.firstname,
                "lastname": form_data.lastname,
                "email": form_data.email,
                "phone": form_data.phone,
                "avatar": form_data.avatar,
                "ip_address": form_data.ip_address,
                "url": form_data.url,
                "provider": form_data.provider,
                "is_verified": form_data.is_verified
            }
            for key, value in optional.items():
                if isinstance(value, list):
                    if value:
                        require_field[key] = value
                elif value not in (None, ""):
                    require_field[key] = value


            request_message = ParseDict(require_field, user_pb2.UserUpdateRequest())

            response = await stub.UserUpdate(request_message)

            user_dict = MessageToDict(response, preserving_proto_field_name=True)

            return JSONResponse(
                content=jsonable_encoder(ResponseModel(
                    status=Status(
                        code=0,
                        msg=user_dict.get("username"),
                        status="success"
                    ),
                    result=Result(data=None)
                ))
            )

        except Exception as e:
            return JSONResponse(
                content=jsonable_encoder(ResponseModel(
                    status=Status(
                        code=1,
                        msg=f"Exception: {e}",
                        status="fail"
                    ),
                    result=Result(data=None)
                ))
            )