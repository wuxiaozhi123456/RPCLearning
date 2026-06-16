"""
第08课：拦截器 —— 客户端（自动加 Token）
运行: python grpc_client.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import grpc
import user_pb2, user_pb2_grpc

# 客户端拦截器：自动附加认证 token
class AuthClientInterceptor(grpc.UnaryUnaryClientInterceptor):
    def __init__(self, token):
        self.token = token

    def intercept_unary_unary(self, cont, details, request):
        md = list(details.metadata) if details.metadata else []
        md.append(('authorization', f'Bearer {self.token}'))
        return cont(details._replace(metadata=md), request)

# 创建通道 + 注入拦截器
raw = grpc.insecure_channel('localhost:50051')
channel = grpc.intercept_channel(raw, AuthClientInterceptor('my-token'))
stub = user_pb2_grpc.UserServiceStub(channel)

# 调用
resp = stub.CreateUser(
    user_pb2.CreateUserRequest(name="Alice", email="alice@example.com"),
    timeout=2.0
)
print(f"✅ 创建成功: ID={resp.id}, Name={resp.name}")
channel.close()
