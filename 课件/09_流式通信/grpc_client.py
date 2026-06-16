"""
第09课：流式通信 —— 客户端演示三种流式
运行前请先启动服务端
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import grpc
import user_pb2, user_pb2_grpc

channel = grpc.insecure_channel('localhost:50051')
stub = user_pb2_grpc.UserServiceStub(channel)

# ===== 1. 服务端流式 =====
print("=" * 40)
print("📋 服务端流式：获取用户列表")
print("=" * 40)
for user in stub.ListUsers(user_pb2.ListUsersRequest(), timeout=5.0):
    print(f"   收到: ID={user.id}, Name={user.name}")


# ===== 2. 客户端流式 =====
print("\n" + "=" * 40)
print("📦 客户端流式：批量创建用户")
print("=" * 40)

def user_gen():
    for name, email in [("张三","zs@e.com"),("李四","ls@e.com"),("","bad")]:
        print(f"   → 发送: {name or '(空)'}")
        yield user_pb2.CreateUserRequest(name=name, email=email)

resp = stub.BatchCreateUsers(user_gen(), timeout=5.0)
print(f"\n✅ 成功 {resp.success_count}, 失败 {resp.fail_count}, IDs={list(resp.created_ids)}")


# ===== 3. 双向流式 =====
print("\n" + "=" * 40)
print("💬 双向流式：聊天")
print("=" * 40)

import threading, time

call = stub.Chat(timeout=10.0)

def recv():
    for msg in call:
        print(f"   📩 {msg.user}: {msg.text}")

t = threading.Thread(target=recv, daemon=True)
t.start()

for text in ["你好", "今天天气不错", "再见"]:
    print(f"   📤 Alice: {text}")
    call.write(user_pb2.ChatMessage(user="Alice", text=text))
    time.sleep(0.5)

call.done_writing()
t.join(timeout=3)

channel.close()
print("\n👋 完成")
