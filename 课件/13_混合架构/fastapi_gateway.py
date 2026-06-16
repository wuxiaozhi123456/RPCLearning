"""
第13课：FastAPI 网关（对外 REST，内部调 gRPC）
运行: uvicorn fastapi_gateway:app --port 8000
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import grpc
import user_pb2, user_pb2_grpc

app = FastAPI(title="用户服务 API 网关")

# 连接 gRPC 微服务（应用启动时创建，全局复用）
channel = grpc.insecure_channel('localhost:50051')
stub = user_pb2_grpc.UserServiceStub(channel)

# REST DTO
class UserCreate(BaseModel):
    name: str
    email: str

class UserOut(BaseModel):
    id: int
    name: str
    email: str

# gRPC 错误码 -> HTTP 状态码 映射
ERROR_MAP = {
    grpc.StatusCode.NOT_FOUND: 404,
    grpc.StatusCode.INVALID_ARGUMENT: 400,
    grpc.StatusCode.ALREADY_EXISTS: 409,
    grpc.StatusCode.UNAUTHENTICATED: 401,
}

@app.post("/api/users", response_model=UserOut)
def create_user(user: UserCreate):
    """REST: POST /api/users  ->  内部: gRPC CreateUser"""
    try:
        r = stub.CreateUser(
            user_pb2.CreateUserRequest(name=user.name, email=user.email),
            timeout=2.0
        )
        return UserOut(id=r.id, name=r.name, email=r.email)
    except grpc.RpcError as e:
        status = ERROR_MAP.get(e.code(), 500)
        raise HTTPException(status, detail=e.details())

@app.get("/api/users/{user_id}", response_model=UserOut)
def get_user(user_id: int):
    """REST: GET /api/users/{id}  ->  内部: gRPC GetUser"""
    try:
        r = stub.GetUser(user_pb2.GetUserRequest(id=user_id), timeout=2.0)
        return UserOut(id=r.id, name=r.name, email=r.email)
    except grpc.RpcError as e:
        status = ERROR_MAP.get(e.code(), 500)
        raise HTTPException(status, detail=e.details())

@app.get("/api/users")
def list_users():
    """REST: GET /api/users  ->  内部: gRPC ListUsers（服务端流）"""
    try:
        return [
            {"id": u.id, "name": u.name, "email": u.email}
            for u in stub.ListUsers(user_pb2.ListUsersRequest(), timeout=5.0)
        ]
    except grpc.RpcError as e:
        raise HTTPException(500, detail=e.details())

@app.get("/api/health")
def health():
    """健康检查：确认网关 + gRPC 微服务都正常"""
    try:
        stub.GetUser(user_pb2.GetUserRequest(id=1), timeout=1.0)
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            return {"status": "healthy", "grpc": "connected"}
        return {"status": "degraded", "grpc": str(e.code())}
    return {"status": "healthy", "grpc": "connected"}
