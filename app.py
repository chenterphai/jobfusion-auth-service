from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.client.api.routes import routes
from src.config.database import close_mongo_connection, connect_to_mongo

@asynccontextmanager
async def lifespan(_: FastAPI):

    await connect_to_mongo()

    # redis_connection = await get_redis_client()

    # await FastAPILimiter().init(
    #     redis=redis_connection,
    #     identifier=default_identifier,
    #     http_callback=default_callback
    # )

    yield

    await close_mongo_connection()

    # await FastAPILimiter.close()

app = FastAPI(title="JobFusion - Auth Services", version="1.0.1", lifespan=lifespan)

app.include_router(router=routes)

@app.get("/")
async def index():
    return {"Success": "Success"}