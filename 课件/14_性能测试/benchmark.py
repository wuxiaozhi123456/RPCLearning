"""
第14课：性能测试 —— 一键自测（自动启停服务）
运行: python benchmark.py
"""
import subprocess, time, sys, os, json
import grpc, httpx
import user_pb2, user_pb2_grpc

N = 300  # 请求数

# ===== 1. 启动 gRPC 服务 =====
grpc_proc = subprocess.Popen(
    [sys.executable, 'grpc_server.py'],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    cwd=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '04_服务端')
)
time.sleep(1.5)

# ===== 2. 启动 FastAPI =====
rest_proc = subprocess.Popen(
    [sys.executable, '-m', 'uvicorn', 'fastapi_app:app', '--port', '8000'],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    cwd=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '06_FastAPI对比')
)
time.sleep(1.5)

# ===== 3. 造测试数据 =====
try:
    ch = grpc.insecure_channel('localhost:50051')
    st = user_pb2_grpc.UserServiceStub(ch)
    st.CreateUser(user_pb2.CreateUserRequest(name="Bench", email="b@e.com"), timeout=2.0)
    ch.close()

    hc = httpx.Client(base_url="http://localhost:8000", timeout=2.0)
    hc.post("/users", json={"name": "Bench", "email": "b@e.com"})
    hc.close()
except Exception as e:
    print(f"[ERR] 服务启动失败: {e}")
    grpc_proc.terminate()
    rest_proc.terminate()
    sys.exit(1)

# ===== 4. gRPC 压测 =====
channel = grpc.insecure_channel('localhost:50051')
stub = user_pb2_grpc.UserServiceStub(channel)
stub.GetUser(user_pb2.GetUserRequest(id=1), timeout=2.0)  # 预热

start = time.time()
for _ in range(N):
    stub.GetUser(user_pb2.GetUserRequest(id=1), timeout=2.0)
grpc_time = time.time() - start
channel.close()

# ===== 5. REST 压测 =====
client = httpx.Client(base_url="http://localhost:8000", timeout=2.0)
client.get("/users/1")  # 预热

start = time.time()
for _ in range(N):
    client.get("/users/1")
rest_time = time.time() - start
client.close()

# ===== 6. 报告 =====
print(f"\n{'='*50}")
print(f"[STATS] FastAPI vs gRPC (各 {N} 次请求)")
print(f"{'='*50}")
print(f"  gRPC  耗时: {grpc_time:.2f}s  QPS: {N/grpc_time:.0f}  均延: {grpc_time/N*1000:.2f}ms")
print(f"  REST  耗时: {rest_time:.2f}s  QPS: {N/rest_time:.0f}  均延: {rest_time/N*1000:.2f}ms")
print(f"  -> gRPC 比 REST 快 {(rest_time/grpc_time):.1f}x")

# 序列化大小
js = len(json.dumps({"id":1,"name":"Alice","email":"alice@example.com"}))
pb = len(user_pb2.UserResponse(id=1, name="Alice", email="alice@example.com").SerializeToString())
print(f"\n  序列化: JSON={js}B  Protobuf={pb}B  (PB 小 {js-pb}B)")

# ===== 7. 清理 =====
grpc_proc.terminate()
rest_proc.terminate()
grpc_proc.wait()
rest_proc.wait()
