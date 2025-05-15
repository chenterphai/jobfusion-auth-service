import asyncio
import grpc
from src.server.grpc import user_pb2_grpc
from src.server.services import user

async def serve() -> None:
    server = grpc.aio.server()
    user_pb2_grpc.add_UserServicesServicer_to_server(user.UserServices(), server)
    server.add_insecure_port("[::]:50051")
    await server.start()
    print("✅ gRPC Server is running on port 50051")
    await server.wait_for_termination()

if __name__ == "__main__":
    asyncio.run(serve())