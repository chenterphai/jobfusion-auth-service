from fastapi import APIRouter

from .v1 import user

routes = APIRouter()

routes.include_router(router=user.router, prefix="/user", tags=["Authentication"])
