"""
第14课：性能测试 —— FastAPI vs gRPC 压测对比
运行前确保两个服务都在运行：
  终端1: cd 课件 && uvicorn 06_FastAPI对比/fastapi_app:app --port 8000
  终端2: python 04_服务端/grpc_server.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import grpc
import httpx
import user_pb2, user_pb2_grpc

N = 500  # 请求数（调小快速跑，调大看差距）

# --- gRPC ---
channel = grpc.insecure_channel('localhost:50051')
stub = user_pb2_grpc.UserServiceStub(channel)

# 预热
stub.GetUser(user_pb2.GetUserRequest(id=1), timeout=2.0)

start = time.time()
for i in range(N):
    stub.GetUser(user_pb2.GetUserRequest(id=1), timeout=2.0)
grpc_time = time.time() - start

# --- REST ---
client = httpx.Client(base_url="http://localhost:8000", timeout=2.0)

# 预热
client.get("/users/1")

start = time.time()
for i in range(N):
    client.get("/users/1")
rest_time = time.time() - start

# --- 结果 ---
print(f"\n{'='*50}")
print(f"📊 性能对比 (各 {N} 次请求)")
print(f"{'='*50}")
print(f"  gRPC:  {grpc_time:.2f}s  |  QPS={N/grpc_time:.0f}  |  均延={grpc_time/N*1000:.2f}ms")
print(f"  REST:  {rest_time:.2f}s  |  QPS={N/rest_time:.0f}  |  均延={rest_time/N*1000:.2f}ms")
print(f"\n  🚀 gRPC 比 REST 快 {(rest_time/grpc_time):.1f}x")

# --- 序列化大小对比 ---
import json
json_size = len(json.dumps({"id":1,"name":"Alice","email":"alice@example.com"}))
pb_size = len(user_pb2.UserResponse(id=1, name="Alice", email="alice@example.com").SerializeToString())
print(f"\n  序列化大小: JSON={json_size}B  Protobuf={pb_size}B  (PB小{json_size-pb_size}B)")

channel.close()
client.close()
