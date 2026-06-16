# 第 04 课：gRPC 服务端 —— 从 proto 到可运行的服务

> **目标**：把 proto 编译成 Python 代码，实现 gRPC 服务端  
> **核心步骤**：proto → 编译 → 继承 Servicer → 实现方法 → 注册到 Server → 启动

---

## 一、第一步：确认 proto 文件

确保上一课的 `user.proto` 存在：

```protobuf
syntax = "proto3";
package user;

service UserService {
    rpc CreateUser (CreateUserRequest) returns (UserResponse);
    rpc GetUser (GetUserRequest) returns (UserResponse);
}

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

---

## 二、第二步：编译 proto → Python 代码

在 `user.proto` 同级目录下，执行：

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. user.proto
```

### 参数说明

| 参数 | 含义 |
|------|------|
| `-I.` | proto 文件搜索路径（`.`=当前目录） |
| `--python_out=.` | 把 message 类生成到当前目录 |
| `--grpc_python_out=.` | 把 service 类生成到当前目录 |
| `user.proto` | 要编译的 proto 文件 |

### 生成结果

执行后会生成两个文件：

```
user_pb2.py        ← 消息类（UserResponse, CreateUserRequest 等）
user_pb2_grpc.py   ← 服务类（UserServiceServicer, UserServiceStub 等）
```

浏览一下生成的文件（不用细看，知道里面有什么就行）：

```bash
# 看看消息类里有什么
python -c "import user_pb2; print(dir(user_pb2))"
# 会看到: CreateUserRequest, GetUserRequest, UserResponse ...

# 看看服务类里有什么
python -c "import user_pb2_grpc; print(dir(user_pb2_grpc))"
# 会看到: UserServiceServicer, UserServiceStub, add_UserServiceServicer_to_server ...
```

**重点**：你只需要知道三个关键类/函数：

| 生成的类/函数 | 在哪儿用 | 作用 |
|--------------|---------|------|
| `UserServiceServicer` | **服务端**：继承它 | 定义了你要实现的方法签名 |
| `UserServiceStub` | **客户端**：实例化它 | 用来调用远程方法 |
| `add_UserServiceServicer_to_server` | **服务端**：调用它 | 把你的实现注册到 gRPC 服务器 |

---

## 三、第三步：实现服务端

创建 `grpc_server.py`：

```python
import grpc
from concurrent import futures
import user_pb2
import user_pb2_grpc

# ===== 1. 继承生成的 Servicer，实现业务逻辑 =====
class UserService(user_pb2_grpc.UserServiceServicer):

    def __init__(self):
        # 用内存字典模拟数据库
        self.db = {}
        self.next_id = 1

    def CreateUser(self, request, context):
        """
        实现 proto 中定义的 rpc CreateUser
        - request: CreateUserRequest 对象（自动反序列化）
        - context: 请求上下文（可以用来读取 metadata、设置状态码等）
        - return: UserResponse 对象（自动序列化）
        """
        print(f"[收到请求] CreateUser: name={request.name}, email={request.email}")

        user = user_pb2.UserResponse(
            id=self.next_id,
            name=request.name,
            email=request.email
        )
        self.db[self.next_id] = user
        self.next_id += 1

        print(f"[创建成功] User: ID={user.id}, Name={user.name}")
        return user   # ← 直接返回 UserResponse 对象

    def GetUser(self, request, context):
        """
        实现 proto 中定义的 rpc GetUser
        """
        print(f"[收到请求] GetUser: id={request.id}")

        user_id = request.id
        if user_id in self.db:
            return self.db[user_id]
        else:
            # 设置错误状态码（类似 HTTP 404）
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"用户 {user_id} 不存在")
            return user_pb2.UserResponse()   # 返回一个空的

# ===== 2. 创建 gRPC 服务器 =====
def serve():
    # 创建服务器，指定线程池（处理并发请求）
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # 把 UserService 注册到服务器上（类似 app.include_router(router)）
    user_pb2_grpc.add_UserServiceServicer_to_server(
        UserService(),    # 你的实现
        server            # 目标服务器
    )

    # 监听端口（不安全模式，仅开发用）
    server.add_insecure_port('[::]:50051')

    # 启动服务器
    server.start()
    print("=" * 40)
    print("[gRPC] gRPC 用户服务已启动: [::]:50051")
    print("=" * 40)

    # 保持服务器运行
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
```

---

## 四、第四步：运行！

```bash
python grpc_server.py
```

你应该看到：

```
========================================
[gRPC] gRPC 用户服务已启动: [::]:50051
========================================
```

---

## 五、理解"注册服务"

这行代码是 gRPC 服务端的核心：

```python
user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
```

它做了什么？

```
      生成的代码里存储了 proto 定义的"服务描述符"
      ┌──────────────────────────────────┐
      │ service UserService {            │
      │   rpc CreateUser (...)           │
      │   rpc GetUser (...)              │
      │ }                                │
      └──────────────┬───────────────────┘
                     │
     add_UserServiceServicer_to_server   │
                     │                   │
         ┌───────────▼───────────┐       │
         │   方法名 → 处理函数    │       │
         │  "CreateUser" → 你的  │ ←─── 内部路由表
         │  "GetUser"    → 你的  │
         └───────────────────────┘
```

> 不需要手动写任何路由！proto 文件已经定义好了方法名，框架自动完成分发。

---

## 六、与 FastAPI 服务端对比

| | FastAPI | gRPC |
|------|---------|------|
| 定义接口 | `@app.post("/users")` 装饰器 | proto 文件中 `rpc CreateUser(...)` |
| 实现逻辑 | 写在装饰器下面的函数里 | 继承 `Servicer`，实现对应方法 |
| 注册路由 | 自动（框架扫描装饰器） | `add_xxxServicer_to_server` 手动注册 |
| 启动服务器 | `uvicorn.run(app)` | `server.start()` |
| 请求参数 | 函数参数 + Pydantic 自动校验 | `request` 对象（强类型，proto 定义） |
| 返回响应 | `return dict/Pydantic` | `return proto message 对象` |

---

## 七、本课小结

```
gRPC 服务端的 4 个步骤：

  ① 写 .proto   →   ② 编译成代码   →   ③ 实现 Servicer   →   ④ 注册 + 启动

  user.proto        grpc_tools.protoc   class UserService(   add_xxx_to_server()
                                         ...Servicer):       server.start()
```

---

## [TEST] 课后小测

1. `grpc_tools.protoc` 命令的两个 `--xxx_out` 参数分别生成什么？
2. 服务端实现必须要继承哪个类？
3. `add_UserServiceServicer_to_server` 这行代码的作用是什么？
4. `context.set_code()` 和 HTTP 的什么概念对应？

---
> 👉 下一课：[05 gRPC 客户端](05_gRPC客户端.md) —— 写一个客户端，真正调用你的服务
