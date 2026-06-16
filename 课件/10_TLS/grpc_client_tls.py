"""
第10课：TLS 安全通信 —— 客户端
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import grpc
import user_pb2, user_pb2_grpc

# 读取服务端证书
with open('server.crt', 'rb') as f:
    cert = f.read()

creds = grpc.ssl_channel_credentials(root_certificates=cert)
channel = grpc.secure_channel('localhost:50051', creds)  # ← secure
stub = user_pb2_grpc.UserServiceStub(channel)

resp = stub.CreateUser(
    user_pb2.CreateUserRequest(name="Alice", email="alice@example.com"),
    timeout=2.0
)
print(f"✅ TLS 加密通信成功: ID={resp.id}, Name={resp.name}")
channel.close()
