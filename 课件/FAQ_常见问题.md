# 🙋 常见问题 FAQ

> 整理自学习过程中提出的所有问题，按课程顺序排列

---

## 第 01 课：热身 RPC

### Q1: RPC 的全称是什么？
**A:** Remote Procedure Call，中文叫"远程过程调用"。
- Remote（远程）— 函数不在本机执行
- Procedure（过程/函数）— 调的就是一个函数
- Call（调用）— 写法跟调本地函数一样

### Q2: RPC 用的是 TCP 协议吗？
**A:** 是的，底层走 TCP。RPC 不自己发明传输协议，骑在 TCP 上面：
```
应用层:  gRPC / xmlrpc / jsonrpc
传输层:  TCP（保证数据可靠到达）
网络层:  IP
```

### Q3: RPC 是应用层协议吗？
**A:** RPC 是一种**编程范式/思想**，不是单一协议。它的具体实现（gRPC、xmlrpc、Thrift）才是应用层协议。好比"开车"是思想，"开宝马"才是具体行为。

### Q4: 为什么 xmlrpc 不用 proto，gRPC 要？
**A:** xmlrpc 靠"口头约定"（函数名对得上就行），gRPC 靠"白纸黑字签合同"（proto 编译时检查类型）。proto 的好处：编译时就能发现参数传错，不用等运行时报错。

### Q5: xmlrpc 为什么感觉比本地函数慢？
**A:** 即使没写 sleep，每次调用背后都在"跑腿"：
```
序列化为 XML → TCP 发送 → 服务端反序列化 → 执行 → 序列化返回 → TCP 发回 → 反序列化
```
这就是 gRPC 用 Protobuf（二进制）替代 XML（文本）的原因——序列化这一步快很多。

### Q6: 为什么 xmlrpc 不弹防火墙框，gRPC 弹？
**A:** 监听地址不同：
```python
# xmlrpc — 只监听本地
SimpleXMLRPCServer(("localhost", 8000))

# gRPC — 监听所有网卡
server.add_insecure_port('[::]:50051')
```
Windows 防火墙只对"允许外部访问"的端口弹框。

---

## 第 03 课：Proto 文件

### Q7: proto 是什么语言的文件？
**A:** Protocol Buffers 语言（protobuf），Google 发明。不是通用编程语言，是**接口定义语言（IDL）**——专门描述"数据结构长什么样、服务有哪些方法"。类比 Swagger/OpenAPI 的 YAML。

### Q8: 一个服务只有一个 proto 吗？
**A:** 不是。实际项目按功能拆分：
```
protos/
├── common/common.proto  ← 共享类型
├── user/user.proto      ← 用户服务
└── order/order.proto    ← 订单服务
```
可以 `import` 复用，一个 gRPC 服务器可以注册多个 service。

### Q9: 我需要关注生成的 `_pb2.py` 和 `_pb2_grpc.py` 吗？
**A:** 不用深究，知道三个关键类就行：
```python
user_pb2.UserResponse(...)                 # 数据类（当成 Pydantic 用）
user_pb2_grpc.UserServiceServicer          # 服务端继承它
user_pb2_grpc.add_..._to_server(...)       # 注册到服务器
```

---

## 第 07 课：错误处理

### Q10: 错误处理是默认的吗？
**A:** 不是。开发者需要手动写：
```python
context.abort(grpc.StatusCode.NOT_FOUND, "用户不存在")
```
gRPC 只提供"管道"（StatusCode、RpcError），什么情况返回什么错误由你决定。

### Q11: 两种错误处理方式有什么区别？
**A:**
| | `abort()` | `set_code()` |
|---|:---:|:---:|
| 后续代码 | 不执行 | 继续执行 |
| 需要 return | 不需要 | 必须手动 return |
| 适用场景 | 快速失败 | 需要清理后再返回 |

---

## 第 08 课：拦截器

### Q12: 拦截器需要改 proto 文件吗？
**A:** 不需要。proto 管"接口长什么样"，拦截器管"请求怎么被处理"，互不干扰。和 FastAPI 加 Middleware 不需要改路由代码一个道理。

### Q13: 拦截器的方法和参数是固定的吗？
**A:** 是的，gRPC 框架规定好的，不能改：
```python
# 服务端 — 固定签名
class LogInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, continuation, handler_call_details):
        ...

# 客户端 — 固定签名
class AuthInterceptor(grpc.UnaryUnaryClientInterceptor):
    def intercept_unary_unary(self, continuation, client_call_details, request):
        ...
```
只能改方法体里面的逻辑，方法签名碰不得。就像 FastAPI Middleware 的参数也是框架定死的。

### Q14: 客户端拦截器的 `cont` 是 CreateUser 函数指针吗？
**A:** 不是。`cont` 是"继续往下走"——下一个拦截器或真正的网络发送函数。不知道你调的是 CreateUser 还是 GetUser，对所有一元方法通用。和 FastAPI 的 `call_next` 一个道理：
```python
# FastAPI
async def middleware(request, call_next):
    response = await call_next(request)  # "下一棒"

# gRPC  
def intercept_unary_unary(self, cont, details, request):
    return cont(details, request)         # "下一棒"
```

### Q15: `details` 参数哪里来的？
**A:** 框架自动生成的。当你调 `stub.CreateUser(...)` 时，gRPC 内部构造了 `client_call_details`，包含方法名、超时时间、metadata 等。你不用手动创建，拦截器只是给你一个"看和改"的机会。

### Q16: `request` 参数就是传给 stub 的那个吗？
**A:** 对，就是你传的：
```python
stub.CreateUser(user_pb2.CreateUserRequest(name="Alice", ...))
#                                              ↑ 这个对象就是 request
```

### Q17: 客户端拦截器和服务端拦截器都在真正处理之前执行吗？
**A:** 位置不同：
```
客户端                                   服务端
stub.CreateUser(request)                 
    ↓                                    
[客户端拦截器] ← 发之前                     
    ↓                                    
~~~~ 网络传输 ~~~~                         
    ↓                                    
[服务端拦截器] ← 收之后、业务之前             
    ↓                                    
UserService.CreateUser()  ← 真正干活
```

---

## 第 09 课：流式通信

### Q18: 流式通信就是参数前面加 `stream` 吗？
**A:** 对，核心就这么简单：
```protobuf
// 一元：一发一回
rpc GetUser (GetUserRequest) returns (UserResponse);

// 服务端流：一发多回 → returns 前加 stream
rpc ListUsers (ListUsersRequest) returns (stream UserResponse);

// 客户端流：多发一回 → 参数前加 stream
rpc BatchCreateUsers (stream CreateUserRequest) returns (BatchCreateResponse);

// 双向流：多发多回 → 两边都加 stream
rpc Chat (stream ChatMessage) returns (stream ChatMessage);
```
`stream` 放哪里，哪里就可以多发/多收。

### Q19: `yield` 和 `return` 的关系是什么？
**A:** 在 gRPC 服务端流中：
```python
# return：回一次就结束（一元 RPC）
def GetUser(self, request, context):
    return self.db[request.id]

# yield：回多次，每次一条（服务端流式）
def ListUsers(self, request, context):
    yield user1    # 推送第1条，函数暂停
    yield user2    # 推送第2条，函数暂停
    yield user3    # 推送第3条，函数结束
```
本质上是 Python 的生成器机制。

### Q20: 流式需要重新编译 proto 吗？
**A:** 对，需要。03_Proto 的 proto 只有一元 RPC 方法，流式方法需要编译完整版 proto。各课程目录里已包含编译好的 pb2 文件。

---

## 第 10 课：TLS

### Q21: TLS 和不安全模式的区别在哪里？
**A:** 只需要改两行：
```python
# 之前（明文）
server.add_insecure_port('[::]:50051')
channel = grpc.insecure_channel('localhost:50051')

# 之后（加密）
server.add_secure_port('[::]:50051', creds)
channel = grpc.secure_channel('localhost:50051', creds)
```
其余代码完全不变。

---

## 通用概念

### Q22: proto 和 gRPC 的关系？
**A:** proto = 接口定义语言，gRPC = 框架实现。关系类似：Swagger/OpenAPI YAML 之于 REST，proto 之于 gRPC。

### Q23: gRPC 和 REST 各适合什么场景？
**A:**
| 场景 | 推荐 | 原因 |
|------|:---:|------|
| 对外 API（浏览器/App） | REST | 通用、易调试、浏览器原生支持 |
| 内部微服务高并发 | gRPC | 吞吐量高 3-5 倍，延迟更低 |
| 流式传输 | gRPC | 原生支持，REST 需 WebSocket |
| 多语言团队 | gRPC | 一份 proto 生成所有客户端 |
