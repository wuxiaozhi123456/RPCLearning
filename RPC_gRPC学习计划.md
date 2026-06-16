# RPC / gRPC 学习计划

> 适用人群：有 REST (Spring Boot / FastAPI) 开发经验，想用 Python 学习 RPC 和 gRPC。
> 核心理念：始终用你熟悉的 REST 作为对照，通过对比深刻理解两种架构风格的本质区别。

---

## 一、总体时间估算

| 学习节奏 | 所需时间 |
|----------|----------|
| 每天 1 ~ 2 小时 | **约 2 周** |
| 集中全天学习 | **3 ~ 5 天** |

---

## 二、学习路线总览

```
热身(RPC概念) → 核心(一元RPC+对比) → 进阶(流式/安全) → 集成(生态/混合架构) → 可选(性能测试)
   30分钟           4~6小时              4~6小时             2~4小时              2小时
```

---

## 三、详细学习步骤

---

### 第 0 步：热身 —— 理解 RPC 是什么（约 30 分钟）

#### 核心认知

在 REST 中，远程调用是**手动拼 URL + HTTP 方法**：

```python
requests.post("http://user-service:8080/users", json={"name": "Alice"})
```

而 RPC 的目标是让你写成：

```python
user_stub.CreateUser(CreateUserRequest(name="Alice"))
```

本质上就是把**寻址、序列化、网络传输**全部封装起来，让你感觉在调本地函数。

#### 动手练习（15 分钟）

先用 Python 标准库 `xmlrpc` 跑一个极简例子，感受"远程调用像本地函数"的效果：

**服务端 (`rpc_server.py`)**：

```python
from xmlrpc.server import SimpleXMLRPCServer

def say_hello(name):
    return f"Hello, {name}!"

def add(a, b):
    return a + b

server = SimpleXMLRPCServer(("localhost", 8000))
server.register_function(say_hello)
server.register_function(add)
print("XML-RPC server on port 8000")
server.serve_forever()
```

**客户端 (`rpc_client.py`)**：

```python
import xmlrpc.client

proxy = xmlrpc.client.ServerProxy("http://localhost:8000")
print(proxy.say_hello("World"))   # 像调本地函数！
print(proxy.add(3, 5))            # 像调本地函数！
```

> 这个小练习帮你消除"RPC 很神秘"的错觉。本质上就是：**客户端 → 序列化参数 → 网络传输 → 服务端反序列化 → 执行函数 → 返回**。

---

### 第 1 步：核心实战 —— 以 FastAPI 为对照学习 gRPC（4 ~ 6 小时）

这是最关键的一步。用一个简单的"用户服务"（CreateUser + GetUser），分别用 FastAPI 和 gRPC 实现，然后从多个维度对比。

---

#### 1.1 环境准备（20 分钟）

安装依赖：

```bash
pip install grpcio grpcio-tools
pip install fastapi uvicorn httpx
```

工具说明：

| 包名 | 作用 |
|------|------|
| `grpcio` | gRPC 核心库 |
| `grpcio-tools` | 包含 `protoc` 编译器 + Python 代码生成插件 |
| `fastapi` | REST 框架（对照用） |
| `uvicorn` | ASGI 服务器 |
| `httpx` | HTTP 客户端（调用 FastAPI 用） |

---

#### 1.2 先写 FastAPI 版本（30 分钟，巩固已有知识）

**服务端 (`fastapi_app.py`)**：

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class UserCreate(BaseModel):
    name: str
    email: str

class User(BaseModel):
    id: int
    name: str
    email: str

db = {}
next_id = 1

@app.post("/users", response_model=User)
def create_user(user: UserCreate):
    global next_id
    new_user = User(id=next_id, name=user.name, email=user.email)
    db[next_id] = new_user
    next_id += 1
    return new_user

@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int):
    return db[user_id]
```

**客户端 (`fastapi_client.py`)**：

```python
import httpx

BASE_URL = "http://localhost:8000"

with httpx.Client(base_url=BASE_URL, timeout=2.0) as client:
    # 创建用户
    resp = client.post("/users", json={"name": "Alice", "email": "alice@example.com"})
    print(f"Created: {resp.json()}")

    # 获取用户
    resp = client.get("/users/1")
    print(f"Got: {resp.json()}")

    # 故意查不存在用户，看错误
    resp = client.get("/users/999")
    print(f"Error: {resp.status_code} - {resp.text}")
```

启动 FastAPI 服务：

```bash
uvicorn fastapi_app:app --reload
```

访问 `http://localhost:8000/docs` 可以看到自动生成的 Swagger UI。

运行客户端：

```bash
python fastapi_client.py
```

---

#### 1.3 书写第一个 `.proto` 文件（40 分钟）

创建 `user.proto`：

```protobuf
syntax = "proto3";

package user;

// 定义服务（类似你的 Controller）
service UserService {
  rpc CreateUser (CreateUserRequest) returns (UserResponse);
  rpc GetUser (GetUserRequest) returns (UserResponse);
}

// 定义请求/响应消息（类似你的 DTO / Pydantic 模型）
message CreateUserRequest {
  string name = 1;
  string email = 2;
}

message GetUserRequest {
  int32 id = 1;
}

message UserResponse {
  int32 id = 1;
  string name = 2;
  string email = 3;
}
```

**关键概念掌握**：

| proto 元素 | 对应 FastAPI | 说明 |
|-----------|-------------|------|
| `message` | Pydantic `BaseModel` | 数据结构定义 |
| `service` | `FastAPI()` + Router | 服务定义，包含多个 rpc |
| `rpc` | `@app.post("/path")` | 单个接口方法 |
| 字段编号 `= 1, = 2` | 无对应 | Protobuf 序列化标识，**不可变** |

---

#### 1.4 生成 Python 代码（20 分钟）

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. user.proto
```

生成两个文件：

| 文件 | 内容 |
|------|------|
| `user_pb2.py` | 消息类（`CreateUserRequest`、`UserResponse` 等） |
| `user_pb2_grpc.py` | 服务类（`UserServiceServicer`、`UserServiceStub` 等） |

快速浏览生成的文件，了解里面有什么：
- `_pb2.py`：每个 message 变成一个 Python 类，字段变成属性
- `_pb2_grpc.py`：`UserServiceServicer`（你继承它写服务端）、`UserServiceStub`（客户端用它调远程）、`add_UserServiceServicer_to_server`（注册函数）

---

#### 1.5 实现 gRPC 服务端（40 分钟）

**服务端 (`grpc_server.py`)**：

```python
import grpc
from concurrent import futures
import user_pb2
import user_pb2_grpc

class UserService(user_pb2_grpc.UserServiceServicer):
    def __init__(self):
        self.db = {}
        self.next_id = 1

    def CreateUser(self, request, context):
        """对应 proto 中的 rpc CreateUser"""
        user = user_pb2.UserResponse(
            id=self.next_id,
            name=request.name,
            email=request.email
        )
        self.db[self.next_id] = user
        self.next_id += 1
        return user

    def GetUser(self, request, context):
        """对应 proto 中的 rpc GetUser"""
        user_id = request.id
        if user_id not in self.db:
            # 返回 gRPC 错误状态码（类似 HTTP 404）
            context.abort(grpc.StatusCode.NOT_FOUND, f"User {user_id} not found")
        return self.db[user_id]

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("gRPC server on port 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
```

---

#### 1.6 实现 gRPC 客户端（30 分钟）

**客户端 (`grpc_client.py`)**：

```python
import grpc
import user_pb2
import user_pb2_grpc

def run():
    # 1. 创建连接通道（一次性指定 IP + 端口）
    channel = grpc.insecure_channel('localhost:50051')

    # 2. 创建 Stub（客户端代理）
    stub = user_pb2_grpc.UserServiceStub(channel)

    # 3. 调用 CreateUser
    print("Creating user 'Alice' ...")
    try:
        resp = stub.CreateUser(
            user_pb2.CreateUserRequest(name="Alice", email="alice@example.com"),
            timeout=2.0
        )
        print(f"Created: ID={resp.id}, Name={resp.name}, Email={resp.email}")
    except grpc.RpcError as e:
        print(f"CreateUser failed: {e.code()} - {e.details()}")

    # 4. 调用 GetUser
    print("\nFetching user with ID=1 ...")
    try:
        resp = stub.GetUser(user_pb2.GetUserRequest(id=1), timeout=2.0)
        print(f"Got: ID={resp.id}, Name={resp.name}, Email={resp.email}")
    except grpc.RpcError as e:
        print(f"GetUser failed: {e.code()} - {e.details()}")

    # 5. 查询不存在的用户
    print("\nFetching non-existent user (ID=999) ...")
    try:
        stub.GetUser(user_pb2.GetUserRequest(id=999), timeout=2.0)
    except grpc.RpcError as e:
        print(f"Expected error: {e.code()} - {e.details()}")

    channel.close()

if __name__ == '__main__':
    run()
```

**运行步骤**：

```bash
# 终端1：启动服务端
python grpc_server.py

# 终端2：运行客户端
python grpc_client.py
```

---

#### 1.7 对比学习 —— 总结一张对比表（1 小时）

| 维度 | FastAPI (REST) | gRPC | 理解要点 |
|------|---------------|------|----------|
| **接口定义方式** | Pydantic + 装饰器 `@app.post()` | `.proto` 文件 (IDL) | proto 是独立于语言的契约 |
| **契约强度** | 运行时校验，文档约定 | 编译时强类型 | gRPC 更不容易写错字段名 |
| **序列化格式** | JSON（人类可读） | Protobuf（二进制高效） | gRPC 数据体积更小、解析更快 |
| **调用方式** | 手动构造 URL/Method/JSON | 生成 Stub，像调本地函数 | gRPC 代码更简洁、类型安全 |
| **寻址方式** | 每次请求拼 URL | 创建 Channel 时指定一次 | gRPC 分离了寻址和方法路由 |
| **路由机制** | URL 路径 + HTTP 方法 | 服务名 + 方法名（编译时确定） | gRPC 不需要手动写路由 |
| **错误处理** | HTTP 状态码（200, 404, 500） | gRPC 状态码（`NOT_FOUND`, `INTERNAL` 等） | 概念类似，名称不同 |
| **流式处理** | 需 WebSocket / SSE | 原生支持三种流式 | gRPC 流式是最大优势之一 |
| **性能** | 一般（JSON + HTTP/1.1） | 高（PB + HTTP/2 多路复用） | 内部微服务倾向 gRPC |
| **浏览器友好** | ✅ 原生支持 | ❌ 需 grpc-web 或网关 | REST 对外，gRPC 对内 |
| **工具生态** | Swagger, curl, Postman | grpcurl, grpcui, BloomRPC | 两边都有成熟工具 |
| **学习曲线** | 低（就是写 HTTP） | 中（需学 proto 语法和生成流程） | 但一旦习惯 proto，效率很高 |

---

#### 1.8 深入错误处理（30 分钟）

在服务端返回错误状态码：

```python
def GetUser(self, request, context):
    if request.id not in self.db:
        context.abort(grpc.StatusCode.NOT_FOUND, f"User {request.id} not found")
    if request.id < 0:
        context.abort(grpc.StatusCode.INVALID_ARGUMENT, "ID must be positive")
    return self.db[request.id]
```

客户端捕获并处理：

```python
try:
    resp = stub.GetUser(user_pb2.GetUserRequest(id=-1))
except grpc.RpcError as e:
    if e.code() == grpc.StatusCode.NOT_FOUND:
        print("用户不存在")
    elif e.code() == grpc.StatusCode.INVALID_ARGUMENT:
        print(f"参数错误: {e.details()}")
```

**对比理解**：

| REST | gRPC |
|------|------|
| `404 Not Found` | `StatusCode.NOT_FOUND` |
| `400 Bad Request` | `StatusCode.INVALID_ARGUMENT` |
| `500 Internal Server Error` | `StatusCode.INTERNAL` |
| Header 传元数据 | `context.invocation_metadata()` |

---

#### 1.9 尝试拦截器（30 分钟）

gRPC 拦截器类比 FastAPI 的 Middleware：

**服务端日志拦截器**：

```python
class LoggingInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, continuation, handler_call_details):
        method = handler_call_details.method
        print(f"[收到请求] {method}")
        # 记录开始时间
        import time
        start = time.time()
        response = continuation(handler_call_details)
        print(f"[完成请求] {method} 耗时: {time.time() - start:.3f}s")
        return response

# 创建服务器时注册拦截器
server = grpc.server(
    futures.ThreadPoolExecutor(max_workers=10),
    interceptors=[LoggingInterceptor()]
)
```

**客户端拦截器**（给每个请求加认证头）：

```python
class AuthInterceptor(grpc.UnaryUnaryClientInterceptor):
    def intercept_unary_unary(self, continuation, client_call_details, request):
        # 添加认证 metadata
        metadata = [('authorization', 'Bearer your-token')]
        new_details = client_call_details._replace(metadata=metadata)
        return continuation(new_details, request)

# 创建通道时注册
channel = grpc.intercept_channel(
    grpc.insecure_channel('localhost:50051'),
    AuthInterceptor()
)
```

> ✅ 第 1 步完成标志：能手写包含 GET/CREATE 的一元 gRPC 服务，并与 FastAPI 版本对比出优劣。

---

### 第 2 步：进阶技能 —— 流式通信与安全（4 ~ 6 小时）

gRPC 最大的优势之一是原生支持流式传输，这是 REST 难以做到的。

---

#### 2.1 服务端流式 —— 服务端推送多条数据（1 小时）

**场景**：查询所有用户，服务端逐条推送。

**proto 定义新增**：

```protobuf
service UserService {
  // ... 之前的一元 RPC ...

  // 服务端流式：request -> stream response
  rpc ListUsers (ListUsersRequest) returns (stream UserResponse);
}

message ListUsersRequest {
  int32 page_size = 1;   // 每页条数
}
```

**服务端实现**：

```python
def ListUsers(self, request, context):
    """服务端流式：不断 yield 数据，客户端逐个接收"""
    for user_id, user in self.db.items():
        yield user
        # 模拟流式推送间隔
        import time
        time.sleep(0.5)
```

**客户端调用**：

```python
# 调用服务端流式方法，返回一个迭代器
responses = stub.ListUsers(user_pb2.ListUsersRequest(page_size=10))
for user in responses:
    print(f"收到用户: ID={user.id}, Name={user.name}")
```

---

#### 2.2 客户端流式 —— 客户端批量上传（1 小时）

**场景**：批量创建用户，客户端逐个发送，服务端汇总后返回结果。

**proto 定义**：

```protobuf
// 客户端流式：stream request -> response
rpc BatchCreateUsers (stream CreateUserRequest) returns (BatchCreateResponse);

message BatchCreateResponse {
  int32 created_count = 1;
  repeated int32 ids = 2;
}
```

**服务端实现**：

```python
def BatchCreateUsers(self, request_iterator, context):
    """客户端流式：接收多个请求，最后返回一个汇总"""
    created_ids = []
    for request in request_iterator:
        user = user_pb2.UserResponse(
            id=self.next_id, name=request.name, email=request.email
        )
        self.db[self.next_id] = user
        created_ids.append(self.next_id)
        self.next_id += 1
        print(f"创建用户: {request.name}")

    return user_pb2.BatchCreateResponse(
        created_count=len(created_ids),
        ids=created_ids
    )
```

**客户端调用**：

```python
def generate_users():
    """生成器函数，逐个产生请求"""
    users_data = [
        ("Alice", "alice@example.com"),
        ("Bob", "bob@example.com"),
        ("Charlie", "charlie@example.com"),
    ]
    for name, email in users_data:
        yield user_pb2.CreateUserRequest(name=name, email=email)

# 调用客户端流式方法
resp = stub.BatchCreateUsers(generate_users())
print(f"批量创建完成: {resp.created_count} 个用户, IDs={list(resp.ids)}")
```

---

#### 2.3 双向流式 —— 双方同时读写（1.5 小时）

**场景**：实现一个简单的 Chat，双方可以持续收发消息。

**proto 定义**：

```protobuf
rpc Chat (stream ChatMessage) returns (stream ChatMessage);

message ChatMessage {
  string user = 1;
  string text = 2;
}
```

**服务端实现**：

```python
def Chat(self, request_iterator, context):
    """双向流：同时接收和发送消息"""
    for message in request_iterator:
        print(f"[收到] {message.user}: {message.text}")
        # 回复一条确认消息
        yield user_pb2.ChatMessage(
            user="Server",
            text=f"已收到: {message.text}"
        )
```

**客户端调用**：

```python
import threading

def send_messages(stub):
    messages = [
        user_pb2.ChatMessage(user="Alice", text="你好"),
        user_pb2.ChatMessage(user="Alice", text="在吗"),
    ]
    for msg in messages:
        yield msg
        time.sleep(1)

# 双向流需要使用流式调用方式
# 开两个线程：一个发送，一个接收
```

> 双向流式是三种中最复杂的，只需要理解 `StreamObserver` / 迭代器模式即可，实际项目中用得不多。

---

#### 2.4 三种流式对比总结

| 类型 | Proto 定义 | 服务端写法 | 客户端写法 | 典型场景 |
|------|-----------|-----------|-----------|----------|
| 一元 RPC | `rpc X(A) returns (B)` | `return response` | `resp = stub.X(req)` | 普通 CRUD |
| 服务端流 | `rpc X(A) returns (stream B)` | `yield response` 多次 | `for r in stub.X(req):` | 列表查询、推送通知 |
| 客户端流 | `rpc X(stream A) returns (B)` | `for req in iterator:` | `resp = stub.X(generator())` | 批量上传、文件上传 |
| 双向流 | `rpc X(stream A) returns (stream B)` | 读写同时进行 | 多线程/协程 | 聊天、实时协作 |

---

#### 2.5 加入 TLS 安全传输（40 分钟）

生产环境中 gRPC 需要加密通信。

**生成自签名证书**：

```bash
# 生成私钥
openssl genrsa -out server.key 2048

# 生成证书
openssl req -new -x509 -key server.key -out server.crt -days 365 -subj "/CN=localhost"
```

**服务端启用 TLS**：

```python
# 读取证书
with open('server.key', 'rb') as f:
    private_key = f.read()
with open('server.crt', 'rb') as f:
    certificate_chain = f.read()

credentials = grpc.ssl_server_credentials([(private_key, certificate_chain)])
server.add_secure_port('[::]:50051', credentials)
```

**客户端连接**：

```python
# 方式1：信任服务端证书（生产环境）
with open('server.crt', 'rb') as f:
    creds = grpc.ssl_channel_credentials(f.read())
channel = grpc.secure_channel('localhost:50051', creds)

# 方式2：本地开发跳过验证（不推荐生产用）
# channel = grpc.secure_channel('localhost:50051',
#     grpc.ssl_channel_credentials(), 
#     options=[('grpc.ssl_target_name_override', 'localhost')])
```

---

#### 2.6 多 proto 文件组织（30 分钟）

实际项目不会把所有定义塞一个文件。按资源拆分：

```
protos/
├── common.proto      # 共享的 message（Address, Timestamp 等）
├── user.proto        # 用户服务
└── order.proto       # 订单服务
```

`common.proto`（被其他文件 import）：

```protobuf
syntax = "proto3";
package common;

message Address {
  string street = 1;
  string city = 2;
  string zip_code = 3;
}
```

`user.proto`（引用 common）：

```protobuf
syntax = "proto3";
package user;

import "common.proto";

message User {
  int32 id = 1;
  string name = 2;
  common.Address address = 3;  // 引用 common 包的 message
}
```

**一次生成所有代码**：

```bash
python -m grpc_tools.protoc -Iprotos \
  --python_out=. --grpc_python_out=. \
  protos/common.proto protos/user.proto protos/order.proto
```

**与 FastAPI 类比**：

| FastAPI | gRPC / proto |
|---------|-------------|
| 一个 `.py` 模块 | 一个 `.proto` 文件 |
| `routers/users.py` | `user.proto` |
| `schemas/common.py` | `common.proto` |
| `app.include_router(router)` | `add_xxxServicer_to_server()` |

> ✅ 第 2 步完成标志：实现服务端推送通知服务（每隔 1 秒向客户端推送一条消息），并理解双向流的应用场景。

---

### 第 3 步：生态与生产集成（2 ~ 4 小时）

---

#### 3.1 gRPC 调试工具（30 分钟）

对比 REST 用 curl / Postman，gRPC 也有对应工具：

| 工具 | 对应 REST 工具 | 安装命令 |
|------|---------------|----------|
| `grpcurl` | `curl` | `go install github.com/fullstorydev/grpcurl/cmd/grpcurl@latest` |
| `grpcui` | Postman / Swagger UI | `go install github.com/fullstorydev/grpcui/cmd/grpcui@latest` |
| `evans` | 交互式 REPL | `go install github.com/ktr0731/evans@latest` |

**grpcurl 示例**：

```bash
# 列出服务的方法
grpcurl -plaintext localhost:50051 list

# 列出某个服务的方法
grpcurl -plaintext localhost:50051 list user.UserService

# 调用方法（需要指定请求体为 JSON）
grpcurl -plaintext -d '{"name":"Alice","email":"alice@example.com"}' \
  localhost:50051 user.UserService/CreateUser
```

**grpcui 启动**（启动一个 Web UI）：

```bash
grpcui -plaintext localhost:50051
# 浏览器打开 http://localhost:... 即可交互式调试
```

---

#### 3.2 FastAPI 与 gRPC 混合使用（1 小时）

实际项目中，常见架构是：**对外 REST（FastAPI）+ 对内 gRPC 微服务**。

**场景**：FastAPI 作为网关，接收外部 HTTP 请求，内部通过 gRPC 调下游服务。

```python
# fastapi_gateway.py
from fastapi import FastAPI
from pydantic import BaseModel
import grpc
import user_pb2
import user_pb2_grpc

app = FastAPI()

# 创建 gRPC 连接（应用启动时初始化，复用连接）
channel = grpc.insecure_channel('localhost:50051')
stub = user_pb2_grpc.UserServiceStub(channel)

class UserCreate(BaseModel):
    name: str
    email: str

@app.post("/api/users")
def create_user(user: UserCreate):
    """FastAPI 接口，内部通过 gRPC 调下游"""
    try:
        resp = stub.CreateUser(
            user_pb2.CreateUserRequest(name=user.name, email=user.email),
            timeout=2.0
        )
        return {"id": resp.id, "name": resp.name, "email": resp.email}
    except grpc.RpcError as e:
        # 把 gRPC 错误转成 HTTP 错误
        if e.code() == grpc.StatusCode.ALREADY_EXISTS:
            from fastapi import HTTPException
            raise HTTPException(status_code=409, detail=e.details())
        raise

@app.get("/api/users/{user_id}")
def get_user(user_id: int):
    try:
        resp = stub.GetUser(user_pb2.GetUserRequest(id=user_id))
        return {"id": resp.id, "name": resp.name, "email": resp.email}
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="User not found")
        raise
```

启动方式（可以同一个进程启动两个 server）：

```python
# main.py - 同时启动 HTTP 和 gRPC 两个端口
import threading
import uvicorn
import grpc
from concurrent import futures

def start_grpc():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("gRPC on :50051")
    server.wait_for_termination()

# 在主线程启动 FastAPI，子线程启动 gRPC
if __name__ == '__main__':
    threading.Thread(target=start_grpc, daemon=True).start()
    uvicorn.run("fastapi_gateway:app", host="0.0.0.0", port=8000)
```

---

#### 3.3 了解 Spring Boot + gRPC 集成（30 分钟）

既然你有 Spring Boot 背景，了解 Java 生态的 gRPC 会让你感受更完整。

开源库：[yidongnan/grpc-spring-boot-starter](https://github.com/yidongnan/grpc-spring-boot-starter)

**核心特点**：

- 用 `@GrpcService` 注解写服务端（类似 `@RestController`）
- 用 `@GrpcClient` 注解注入客户端 Stub（类似 `@Autowired`）
- 自动扫描和启动 gRPC Server，端口可配置

**示例代码**：

```java
@GrpcService
public class GreeterService extends GreeterGrpc.GreeterImplBase {
    @Override
    public void sayHello(HelloRequest request, StreamObserver<HelloResponse> responseObserver) {
        // 业务逻辑，和写 @PostMapping 方法体一样
        HelloResponse response = HelloResponse.newBuilder()
            .setMessage("Hello, " + request.getName())
            .build();
        responseObserver.onNext(response);
        responseObserver.onComplete();
    }
}
```

是不是和 Controller 非常像了？只是把 `@PostMapping` 换成了 proto 里定义的方法名。

> ✅ 第 3 步完成标志：能画出混合架构图 —— 外部 REST 网关对内提供 gRPC 微服务调用。

---

### 第 4 步（可选）：性能测试与原理理解（约 2 小时）

#### 4.1 使用 `ghz` 做压力测试

`ghz` 是 gRPC 的压测工具（类似 `ab` / `wrk` 对 HTTP 的压测）。

```bash
# 安装 ghz
go install github.com/bojand/ghz/cmd/ghz@latest

# 对 CreateUser 方法做压测
ghz --insecure \
  --proto user.proto \
  --call user.UserService/CreateUser \
  -d '{"name":"Test","email":"test@example.com"}' \
  -c 10 -n 1000 \
  localhost:50051
```

#### 4.2 用 Python 简单对比 FastAPI vs gRPC 性能

```python
import time
import grpc
import httpx
import user_pb2, user_pb2_grpc

N = 1000

# 测 gRPC
channel = grpc.insecure_channel('localhost:50051')
stub = user_pb2_grpc.UserServiceStub(channel)

start = time.time()
for i in range(N):
    stub.GetUser(user_pb2.GetUserRequest(id=1))
grpc_time = time.time() - start
print(f"gRPC: {N} 次请求，总耗时 {grpc_time:.2f}s，QPS={N/grpc_time:.0f}")

# 测 FastAPI
with httpx.Client(base_url="http://localhost:8000") as client:
    start = time.time()
    for i in range(N):
        client.get("/users/1")
    rest_time = time.time() - start
    print(f"REST: {N} 次请求，总耗时 {rest_time:.2f}s，QPS={N/rest_time:.0f}")

channel.close()
```

运行后你会直观感受到 Protobuf + HTTP/2 带来的性能优势。

---

## 四、学习路径图示

```
                    ┌─────────────────────────────────────────────┐
                    │           第 1 步：核心实战 (4~6h)            │
                    │                                             │
  第 0 步：热身      │  FastAPI 版  ←→  对比  ←→  gRPC 版         │
  (30min)           │                                             │
     │              │  接口定义   调用方式   错误处理   拦截器       │
     │              └──────────────────┬──────────────────────────┘
     │                                 │
     │              ┌──────────────────▼──────────────────────────┐
     │              │           第 2 步：进阶技能 (4~6h)            │
     │              │                                             │
     └──────────────►  服务端流式 → 客户端流式 → 双向流式           │
                    │                                             │
                    │  TLS 安全  →  多 proto 组织                  │
                    │                                             │
                    └──────────────────┬──────────────────────────┘
                                       │
                    ┌──────────────────▼──────────────────────────┐
                    │         第 3 步：生态集成 (2~4h)              │
                    │                                             │
                    │  grpcurl/grpcui → FastAPI 混用 gRPC          │
                    │                                             │
                    │  Spring Boot + gRPC → 混合架构图             │
                    │                                             │
                    └──────────────────┬──────────────────────────┘
                                       │
                    ┌──────────────────▼──────────────────────────┐
                    │       第 4 步：性能测试 (可选, 2h)            │
                    │                                             │
                    │  ghz 压测 → FastAPI vs gRPC 性能对比         │
                    │                                             │
                    └─────────────────────────────────────────────┘
```

---

## 五、关键心法

### 1. 不要一次性搞懂所有细节

先跑通一元 RPC 的完整链路（proto → 生成代码 → 服务端 → 客户端），建立整体感觉，再逐步深入。

### 2. 始终和 REST 对比

用你熟悉的 FastAPI 反推 gRPC 的设计动机，对比越细致，理解越深刻。每学一个概念，都在心里问："这在 REST 里对应什么？"

### 3. 优先用 Python

Python 语法负担最低，环境搭建最快，让你专注于 RPC 的核心思想。掌握了 Python 版，后面再看 Java/Go 的 gRPC 只会更顺手。

### 4. 多动手，少空想

gRPC 的所有"奇怪"之处（proto文件、代码生成、stub调用），实际操作一遍就能理解。代码比文字更有说服力。

---

## 六、参考资料

- [gRPC 官方文档](https://grpc.io/docs/)
- [Protocol Buffers 文档](https://protobuf.dev/)
- [grpc-spring-boot-starter](https://github.com/yidongnan/grpc-spring-boot-starter)
- [grpcurl](https://github.com/fullstorydev/grpcurl) / [grpcui](https://github.com/fullstorydev/grpcui)
- [ghz 压测工具](https://github.com/bojand/ghz)
- [betterproto - 更 Pythonic 的 protobuf](https://github.com/danielgtaylor/python-betterproto)

---

> **最终目标**：两周后，你不仅能写出 gRPC 服务，还能清楚地告诉同事 —— **什么时候该用 REST，什么时候该用 gRPC**。
