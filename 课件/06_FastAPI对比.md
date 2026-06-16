# 第 06 课：FastAPI 对比学习 —— REST vs gRPC 全方位对照

> **目标**：用同一套"用户服务"业务，分别用 FastAPI 和 gRPC 实现，从十个维度做对比  
> **价值**：这是整个课程最重要的一课。对比越深刻，对两种架构的理解就越透彻

---

## 一、FastAPI 版本（对照实现）

### 1.1 服务端 (`fastapi_app.py`)

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# ===== DTO 定义 =====
class UserCreate(BaseModel):
    name: str
    email: str

class User(BaseModel):
    id: int
    name: str
    email: str

# ===== 内存数据库 =====
db = {}
next_id = 1

# ===== 接口实现 =====
@app.post("/users", response_model=User)
def create_user(user: UserCreate):
    global next_id
    new_user = User(id=next_id, name=user.name, email=user.email)
    db[next_id] = new_user
    next_id += 1
    return new_user

@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int):
    if user_id not in db:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"用户 {user_id} 不存在")
    return db[user_id]

# 启动: uvicorn fastapi_app:app --reload --port 8000
```

### 1.2 客户端 (`fastapi_client.py`)

```python
import httpx

BASE_URL = "http://localhost:8000"

with httpx.Client(base_url=BASE_URL, timeout=2.0) as client:
    # 创建用户
    resp = client.post("/users", json={"name": "Alice", "email": "alice@example.com"})
    user = resp.json()
    print(f"✅ Created: {user['id']} - {user['name']} ({user['email']})")

    # 获取用户
    resp = client.get("/users/1")
    user = resp.json()
    print(f"✅ Got: {user['id']} - {user['name']} ({user['email']})")

    # 查不存在用户
    resp = client.get("/users/999")
    print(f"❌ Error: {resp.status_code} - {resp.text}")
```

---

## 二、gRPC 版本（复习）

### 2.1 proto 定义

```protobuf
service UserService {
    rpc CreateUser (CreateUserRequest) returns (UserResponse);
    rpc GetUser (GetUserRequest) returns (UserResponse);
}
```

### 2.2 服务端核心代码

```python
class UserService(user_pb2_grpc.UserServiceServicer):
    def CreateUser(self, request, context):
        return user_pb2.UserResponse(id=..., name=request.name, ...)

    def GetUser(self, request, context):
        return self.db[request.id]

server = grpc.server(...)
user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
```

### 2.3 客户端核心代码

```python
channel = grpc.insecure_channel('localhost:50051')
stub = user_pb2_grpc.UserServiceStub(channel)
resp = stub.CreateUser(user_pb2.CreateUserRequest(name="Alice", email="..."))
```

---

## 三、十维度对比表

| # | 维度 | FastAPI (REST) | gRPC |
|:---:|------|---------------|------|
| 1 | **接口定义** | `@app.post("/users")` 装饰器写 Python | `.proto` 文件用 IDL 语言定义 |
| 2 | **数据结构** | Pydantic `BaseModel`（运行时校验） | proto `message`（编译时生成） |
| 3 | **序列化** | JSON 文本（人类可读，体积大） | Protobuf 二进制（机器可读，体积小） |
| 4 | **调用方式** | `client.post("/users", json={...})` | `stub.CreateUser(request)` |
| 5 | **路由机制** | URL 路径 + HTTP 方法 | 方法名（底层自动映射） |
| 6 | **寻址方式** | 每次请求带完整 URL | Channel 创建时指定一次 |
| 7 | **类型安全** | 运行时 Pydantic 校验 | 编译时强类型保证 |
| 8 | **错误处理** | HTTP 状态码（200/404/500） + JSON | gRPC StatusCode + `RpcError` |
| 9 | **流式传输** | 需 WebSocket / SSE | ✅ 原生支持三种流式 |
| 10 | **跨语言** | 手动写各语言客户端 | proto 编译一次，生成多语言代码 |

---

## 四、代码级对比（同一操作的两种写法）

### 4.1 创建用户

| | FastAPI | gRPC |
|------|---------|------|
| 请求构造 | `json={"name":"Alice","email":"..."}` | `CreateUserRequest(name="Alice", email="...")` |
| 发起调用 | `client.post("/users", json=data)` | `stub.CreateUser(request)` |
| 响应解析 | `resp.json()["id"]` | `response.id`（属性访问） |
| 类型提示 | 无（dict） | ✅ IDE 自动补全 |

### 4.2 获取用户

| | FastAPI | gRPC |
|------|---------|------|
| 请求 | `client.get(f"/users/{user_id}")` | `stub.GetUser(GetUserRequest(id=user_id))` |
| 路径参数 | URL 模板 `/users/{id}` | 请求对象的字段 `id` |

### 4.3 错误处理

**FastAPI**：
```python
resp = client.get("/users/999")
if resp.status_code == 404:
    print("用户不存在")
elif resp.status_code == 500:
    print("服务器错误")
```

**gRPC**：
```python
try:
    resp = stub.GetUser(GetUserRequest(id=999))
except grpc.RpcError as e:
    if e.code() == grpc.StatusCode.NOT_FOUND:
        print("用户不存在")
    elif e.code() == grpc.StatusCode.INTERNAL:
        print("服务器错误")
```

---

## 五、直观感受总结

### FastAPI 的优势

- ✅ 浏览器直接可访问（`http://localhost:8000/docs` 有 Swagger UI）
- ✅ 用 curl / Postman 就能调试
- ✅ JSON 可读，出问题时一眼能看懂
- ✅ 学习曲线低，就是写 HTTP

### gRPC 的优势

- ✅ 强类型，IDE 自动补全，不会写错字段名
- ✅ 性能更高（Protobuf 二进制 + HTTP/2 多路复用）
- ✅ 原生流式传输（服务端推送、双向通信）
- ✅ 一份 proto 生成所有语言客户端（多语言微服务团队友好）
- ✅ 调用体验像本地函数，代码更简洁

---

## 六、什么时候用哪个？

```
对外接口（浏览器、App、第三方）
        │
        ▼
       REST (FastAPI)     ← 人类友好、通用性强
        
内部微服务之间
        │
        ▼
       gRPC               ← 性能高、类型安全、多语言
```

> **结论**：不是二选一，而是各取所长。REST 对外，gRPC 对内。

---

## 七、本课小结

```
这一课你学到了：

  不只是"gRPC 怎么写代码"
  而是"gRPC 为什么这样设计"

  每个 gRPC 概念，你心里都有一个对应的 REST 概念：
  
  message  ←→  Pydantic
  service  ←→  Router
  rpc      ←→  @app.post()
  Stub     ←→  requests.post()
  Channel  ←→  base_url
  
  这种对照思维，比单纯学习语法有用 10 倍。
```

---

## 📝 课后练习

1. 把上面 FastAPI 和 gRPC 的客户端+服务端都跑一遍
2. 尝试在两个服务端代码里加入打印日志，对比请求到达时分别打印了什么
3. 自己补充两个维度到对比表里，比如：文件上传、分页查询

---

> 👉 下一课：[07 错误处理](07_错误处理.md) —— 深入 gRPC 的错误状态码和异常处理
