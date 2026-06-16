"""
第09课：流式通信 —— 客户端演示三种流式
运行前请先启动服务端: python grpc_server.py
"""
import grpc
import threading
import time
import queue
import user_pb2, user_pb2_grpc

channel = grpc.insecure_channel('localhost:50051')
stub = user_pb2_grpc.UserServiceStub(channel)

# 先造几条测试数据
for name, email in [("Alice","a@e.com"),("Bob","b@e.com"),("Charlie","c@e.com")]:
    stub.CreateUser(user_pb2.CreateUserRequest(name=name, email=email))

# ===== 1. 服务端流式：客户端发一个请求，服务端逐个推送 =====
print("=" * 50)
print("1. 服务端流式: ListUsers（服务端逐个推送）")
print("=" * 50)
print("   vs 一元RPC: stub.Method(req) -> resp")
print("   vs 服务端流: for r in stub.Method(req): ...")
print()
for i, user in enumerate(stub.ListUsers(user_pb2.ListUsersRequest(), timeout=5.0), 1):
    print(f"   [{i}] ID={user.id}, Name={user.name}, Email={user.email}")

# ===== 2. 客户端流式：客户端逐个发送，服务端汇总返回 =====
print("\n" + "=" * 50)
print("2. 客户端流式: BatchCreateUsers（客户端逐个上传）")
print("=" * 50)
print("   vs 一元RPC: stub.Method(req) -> resp")
print("   vs 客户端流: stub.Method(generator()) -> resp")
print()

def user_generator():
    users = [
        ("张三", "zs@e.com"),
        ("", "bad@e.com"),        # 空名称，会被服务端拒绝
        ("李四", "ls@e.com"),
    ]
    for name, email in users:
        print(f"   -> 发送: {name or '(空名称)'}")
        yield user_pb2.CreateUserRequest(name=name, email=email)

resp = stub.BatchCreateUsers(user_generator(), timeout=5.0)
print(f"\n   结果: 成功 {resp.success_count}, 失败 {resp.fail_count}")
print(f"   新ID: {list(resp.created_ids)}")
if resp.errors:
    for e in resp.errors:
        print(f"   错误: {e}")

# ===== 3. 双向流式：双方同时收发 =====
print("\n" + "=" * 50)
print("3. 双向流式: Chat（双方同时收发）")
print("=" * 50)
print("   vs 一元RPC: stub.Method(req) -> resp")
print("   vs 双向流: stub.Method(iterator) -> iterator")
print()

import queue

# 用队列在线程间传递消息
send_queue = queue.Queue()

def message_generator():
    """生成器：从队列取消息发送"""
    while True:
        msg = send_queue.get()
        if msg is None:  # None 表示结束
            break
        yield msg

# 发起双向流调用
responses = stub.Chat(message_generator(), timeout=10.0)

# 接收线程
def receive():
    for msg in responses:
        print(f"   [收到] {msg.user}: {msg.text}")

recv_thread = threading.Thread(target=receive, daemon=True)
recv_thread.start()

# 主线程发送消息
for text in ["你好!", "今天天气不错", "再见!"]:
    print(f"   [发送] Alice: {text}")
    send_queue.put(user_pb2.ChatMessage(user="Alice", text=text))
    time.sleep(0.5)

# 发送结束信号
send_queue.put(None)
recv_thread.join(timeout=3)

channel.close()
print("\n--- 三种流式全部测试完成")
