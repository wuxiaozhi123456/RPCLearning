"""
第07课：错误处理 —— 客户端演示捕获不同错误
运行: python grpc_client.py
"""
import grpc
import user_pb2, user_pb2_grpc

channel = grpc.insecure_channel('localhost:50051')
stub = user_pb2_grpc.UserServiceStub(channel)

# ----- 测试1: 正常请求 -----
print("=" * 40)
print("测试1: 创建正常用户")
try:
    r = stub.CreateUser(
        user_pb2.CreateUserRequest(name="Alice", email="alice@e.com"),
        timeout=2.0
    )
    print(f"✅ 成功: ID={r.id}")
except grpc.RpcError as e:
    print(f"❌ {e.code().name}: {e.details()}")

# ----- 测试2: 名称为空 -> INVALID_ARGUMENT -----
print("\n测试2: 名称为空")
try:
    stub.CreateUser(
        user_pb2.CreateUserRequest(name="", email="bad@e.com"),
        timeout=2.0
    )
except grpc.RpcError as e:
    print(f"❌ {e.code().name}: {e.details()}")
    # 根据错误类型做不同处理
    if e.code() == grpc.StatusCode.INVALID_ARGUMENT:
        print("   → 提示用户：名称不能为空")

# ----- 测试3: 邮箱格式错误 -> INVALID_ARGUMENT -----
print("\n测试3: 邮箱格式错误")
try:
    stub.CreateUser(
        user_pb2.CreateUserRequest(name="Bob", email="not-an-email"),
        timeout=2.0
    )
except grpc.RpcError as e:
    print(f"❌ {e.code().name}: {e.details()}")

# ----- 测试4: 重复邮箱 -> ALREADY_EXISTS -----
print("\n测试4: 重复注册")
try:
    stub.CreateUser(
        user_pb2.CreateUserRequest(name="Alice2", email="alice@e.com"),
        timeout=2.0
    )
except grpc.RpcError as e:
    print(f"❌ {e.code().name}: {e.details()}")

# ----- 测试5: 查询不存在的用户 -> NOT_FOUND -----
print("\n测试5: 查询不存在的用户")
try:
    stub.GetUser(user_pb2.GetUserRequest(id=999), timeout=2.0)
except grpc.RpcError as e:
    print(f"❌ {e.code().name}: {e.details()}")
    if e.code() == grpc.StatusCode.NOT_FOUND:
        print("   → 返回 404 给前端")

# ----- 测试6: 非法 ID -> INVALID_ARGUMENT -----
print("\n测试6: 非法 ID（负数）")
try:
    stub.GetUser(user_pb2.GetUserRequest(id=-1), timeout=2.0)
except grpc.RpcError as e:
    print(f"❌ {e.code().name}: {e.details()}")

print("\n👋 全部测试完成")
channel.close()
