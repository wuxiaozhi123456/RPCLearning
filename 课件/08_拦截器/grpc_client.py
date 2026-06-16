"""
第08课：拦截器 —— 客户端（演示有 Token 成功 + 无 Token 被拒）
运行: python grpc_client.py
"""
import grpc
import user_pb2, user_pb2_grpc

# ===== 客户端拦截器：自动附加认证 token =====
class AuthClientInterceptor(grpc.UnaryUnaryClientInterceptor):
    def __init__(self, token):
        self.token = token

    def intercept_unary_unary(self, cont, details, request):
        md = list(details.metadata) if details.metadata else []
        md.append(('authorization', f'Bearer {self.token}'))
        return cont(details._replace(metadata=md), request)

# ===== 测试1：带 Token 调用（成功）=====
print("=" * 40)
print("测试1: 带 Token 调用")
print("=" * 40)

raw = grpc.insecure_channel('localhost:50051')
channel_with_auth = grpc.intercept_channel(raw, AuthClientInterceptor('my-token'))
stub = user_pb2_grpc.UserServiceStub(channel_with_auth)

try:
    resp = stub.CreateUser(
        user_pb2.CreateUserRequest(name="Alice", email="alice@e.com"),
        timeout=2.0
    )
    print(f"[OK] 创建成功: ID={resp.id}, Name={resp.name}")
except grpc.RpcError as e:
    print(f"[ERR] {e.code().name}: {e.details()}")

channel_with_auth.close()

# ===== 测试2：不带 Token 调用（被拒）=====
print("\n" + "=" * 40)
print("测试2: 不带 Token 调用（应被拒绝）")
print("=" * 40)

raw2 = grpc.insecure_channel('localhost:50051')
# 注意：没有 intercept_channel，不注入 token！
stub_no_auth = user_pb2_grpc.UserServiceStub(raw2)

try:
    resp = stub_no_auth.CreateUser(
        user_pb2.CreateUserRequest(name="Hacker", email="hack@e.com"),
        timeout=2.0
    )
    print(f"[OK] 创建成功: ID={resp.id}")  # 不应该走到这里
except grpc.RpcError as e:
    print(f"[ERR] {e.code().name}: {e.details()}")
    if e.code() == grpc.StatusCode.UNAUTHENTICATED:
        print("   -> 认证失败，请求被拦截！")

raw2.close()

print("\n--- 测试完成")
