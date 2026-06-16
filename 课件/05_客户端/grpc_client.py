"""
第05课：gRPC 客户端
运行前请先启动服务端
直接运行: python grpc_client.py
"""
import grpc
import user_pb2, user_pb2_grpc

channel = grpc.insecure_channel('localhost:50051')
stub = user_pb2_grpc.UserServiceStub(channel)

# --- 创建用户 ---
print("=" * 40)
print("📝 创建用户 Alice")
resp = stub.CreateUser(
    user_pb2.CreateUserRequest(name="Alice", email="alice@example.com"),
    timeout=2.0
)
print(f"✅ ID={resp.id}, Name={resp.name}, Email={resp.email}")

# --- 批量创建 ---
print("\n📝 批量创建...")
for name, email in [("Bob","bob@e.com"),("Charlie","charlie@e.com")]:
    r = stub.CreateUser(user_pb2.CreateUserRequest(name=name, email=email))
    print(f"   ✅ {r.name} (ID={r.id})")

# --- 查询用户 ---
print("\n📝 查询用户...")
for uid in [1, 2, 999]:
    try:
        r = stub.GetUser(user_pb2.GetUserRequest(id=uid), timeout=2.0)
        print(f"   ✅ {uid}: {r.name}")
    except grpc.RpcError as e:
        print(f"   ❌ {uid}: {e.code().name} - {e.details()}")

channel.close()
print("\n👋 完成")
