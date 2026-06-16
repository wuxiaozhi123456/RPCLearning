"""
第10课：TLS 安全通信 —— 客户端
"""
import grpc
import user_pb2, user_pb2_grpc

# 读取服务端证书（客户端用它验证服务端身份）
with open('server.crt', 'rb') as f:
    cert = f.read()

# 创建 TLS 凭证
creds = grpc.ssl_channel_credentials(root_certificates=cert)

# 关键区别：secure_channel 而不是 insecure_channel
channel = grpc.secure_channel('localhost:50051', creds)
stub = user_pb2_grpc.UserServiceStub(channel)

# 调用和之前完全一样
resp = stub.CreateUser(
    user_pb2.CreateUserRequest(name="Alice", email="alice@e.com"),
    timeout=2.0
)
print(f"[OK] TLS 加密通信成功: ID={resp.id}, Name={resp.name}")

# 查询验证
resp = stub.GetUser(user_pb2.GetUserRequest(id=1), timeout=2.0)
print(f"[OK] 查询成功: {resp.name}")

channel.close()
