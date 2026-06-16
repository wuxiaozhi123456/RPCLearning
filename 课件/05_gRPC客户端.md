# 第 05 课：gRPC 客户端 —— 像调本地函数一样调用远程服务

> **目标**：写一个 gRPC 客户端，调用上一课的服务端，感受 RPC 的核心魅力  
> **核心体验**：`stub.xxx()` 就像调本地函数，网络细节对你是透明的

---

## 一、前提：服务端必须运行

在学习客户端之前，先确认服务端在运行：

```bash
# 终端1：启动服务端（如果还没启动）
python grpc_server.py

# 终端2：我们在这里写客户端
```

---

## 二、客户端三要素

gRPC 客户端只需要三个东西：

```
  ① Channel（通道）     →  知道服务器在哪（IP + 端口）
  ② Stub（代理/桩）      →  知道有哪些方法可以调
  ③ Request（请求对象）  →  知道要传什么参数
```

### 代码框架

```python
import grpc
import user_pb2
import user_pb2_grpc

# ① 创建通道：一次指定 IP + 端口
channel = grpc.insecure_channel('localhost:50051')

# ② 创建 Stub：通过 channel 构建
stub = user_pb2_grpc.UserServiceStub(channel)

# ③ 构造请求 + 发起调用
response = stub.CreateUser(
    user_pb2.CreateUserRequest(name="Alice", email="alice@example.com")
)

# ④ 使用响应
print(f"创建成功: ID={response.id}, Name={response.name}")
```

---

## 三、完整客户端代码

创建 `grpc_client.py`：

```python
import grpc
import user_pb2
import user_pb2_grpc

def run():
    # ===== 1. 建立连接 =====
    print("📡 正在连接 gRPC 服务器...")
    channel = grpc.insecure_channel('localhost:50051')

    # ===== 2. 创建 Stub（客户端代理）=====
    stub = user_pb2_grpc.UserServiceStub(channel)
    print("✅ 连接成功！\n")

    # ===== 3. 调用 CreateUser =====
    print("=" * 40)
    print("📝 测试 1: 创建用户 Alice")
    print("=" * 40)

    try:
        response = stub.CreateUser(
            user_pb2.CreateUserRequest(
                name="Alice",
                email="alice@example.com"
            ),
            timeout=2.0                    # ← 超时设置
        )
        print(f"✅ 创建成功!")
        print(f"   ID:    {response.id}")
        print(f"   Name:  {response.name}")
        print(f"   Email: {response.email}")
    except grpc.RpcError as e:
        print(f"❌ 创建失败: {e.code()} - {e.details()}")

    # ===== 4. 再创建几个用户 =====
    print("\n📝 批量创建用户...")
    users_data = [
        ("Bob",   "bob@example.com"),
        ("Charlie", "charlie@example.com"),
    ]
    for name, email in users_data:
        try:
            resp = stub.CreateUser(
                user_pb2.CreateUserRequest(name=name, email=email),
                timeout=2.0
            )
            print(f"   ✅ {resp.name} (ID={resp.id})")
        except grpc.RpcError as e:
            print(f"   ❌ {name}: {e.details()}")

    # ===== 5. 调用 GetUser =====
    print("\n" + "=" * 40)
    print("📝 测试 2: 查询用户")
    print("=" * 40)

    for user_id in [1, 2, 3, 999]:
        try:
            resp = stub.GetUser(
                user_pb2.GetUserRequest(id=user_id),
                timeout=2.0
            )
            print(f"   ✅ 用户 {user_id}: {resp.name} ({resp.email})")
        except grpc.RpcError as e:
            print(f"   ❌ 用户 {user_id}: {e.code().name} - {e.details()}")

    # ===== 6. 关闭连接 =====
    channel.close()
    print("\n👋 连接已关闭")

if __name__ == '__main__':
    run()
```

---

## 四、运行

```bash
python grpc_client.py
```

### 预期输出

```
📡 正在连接 gRPC 服务器...
✅ 连接成功！

========================================
📝 测试 1: 创建用户 Alice
========================================
✅ 创建成功!
   ID:    1
   Name:  Alice
   Email: alice@example.com

📝 批量创建用户...
   ✅ Bob (ID=2)
   ✅ Charlie (ID=3)

========================================
📝 测试 2: 查询用户
========================================
   ✅ 用户 1: Alice (alice@example.com)
   ✅ 用户 2: Bob (bob@example.com)
   ✅ 用户 3: Charlie (charlie@example.com)
   ❌ 用户 999: NOT_FOUND - 用户 999 不存在

👋 连接已关闭
```

---

## 五、关键理解：为什么不用写 URL？

对比 REST 调用，你会注意到 gRPC 客户端**没有 URL 路径、没有 HTTP 方法**：

### REST 方式

```python
# 每次调用都需要指定完整 URL
requests.post("http://localhost:8000/users", json={"name": "Alice"})
requests.get("http://localhost:8000/users/1")
```

### gRPC 方式

```python
# IP + 端口在创建 Channel 时一次性指定
channel = grpc.insecure_channel('localhost:50051')

# 之后调方法，不需要再写任何地址
stub.CreateUser(CreateUserRequest(name="Alice"))
stub.GetUser(GetUserRequest(id=1))
```

**为什么？因为 gRPC 把"寻址"和"方法路由"分离了：**

```
┌──────────── 一次性设置 ────────────┐  ┌── 每次都不同 ──┐
│                                    │  │                 │
│  Channel: localhost:50051          │  │  CreateUser()   │
│  (我要和谁通信)                     │  │  GetUser()      │
│                                    │  │  (我要调哪个方法) │
└────────────────────────────────────┘  └─────────────────┘
```

- **寻址**（IP + 端口）→ 在 Channel 创建时绑定，之后复用
- **路由**（调哪个方法）→ 由 Stub 的方法名决定，proto 编译时已确定

---

## 六、与 FastAPI 客户端对比

| | FastAPI 客户端 (httpx) | gRPC 客户端 |
|------|----------------------|-----------|
| 连接方式 | `httpx.Client(base_url=...)` | `grpc.insecure_channel(...)` |
| 代理对象 | `client` | `stub` |
| 创建用户 | `client.post("/users", json={...})` | `stub.CreateUser(CreateUserRequest(...))` |
| 获取用户 | `client.get("/users/1")` | `stub.GetUser(GetUserRequest(id=1))` |
| 参数类型 | `dict`（手动构造） | 生成的强类型对象 |
| 序列化 | JSON（可读文本） | Protobuf（二进制，自动） |
| 超时 | `timeout=2.0` | `timeout=2.0` |
| 错误处理 | HTTP 状态码 | `grpc.RpcError` + `StatusCode` |

---

## 七、本课小结

```
gRPC 客户端的 3 个核心对象：

  Channel →  "我要和谁通信"（IP:Port）
  Stub    →  "我能调哪些方法"（proto 编译时确定）
  Request →  "这次调用的参数是什么"（强类型）

调用体验：stub.Method(Request) → Response
就像调本地函数一样简单。
```

---

## 📝 课后小测

1. 客户端需要哪三个核心对象？
2. 为什么 gRPC 客户端方法调用时不需要写 URL 路径？
3. `stub.GetUser()` 的参数是一个什么类型的对象？
4. 如果服务端没有启动，客户端会报什么错误？试试看。

---

> 👉 下一课：[06 FastAPI 对比学习](06_FastAPI对比.md) —— 用同一套业务逻辑，REST vs gRPC 十维度大对比
