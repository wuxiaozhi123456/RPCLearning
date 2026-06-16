# 第 01 课：热身 —— 理解 RPC 是什么

> **目标**：用 30 分钟理解 RPC 的核心思想，并亲手跑通一个极简 RPC 例子  
> **关键认知**：RPC 就是把网络调用的细节封装起来，让你"像调本地函数一样调远程服务"

---

## 一、你已经会的：REST 调用

假设你有一个用户服务，别人要调你的接口创建用户，在 REST 里通常这么写：

```python
import requests

# 客户端需要知道：
# 1. 服务地址（IP + 端口）
# 2. URL 路径（/users）
# 3. HTTP 方法（POST）
# 4. 请求体格式（JSON）
response = requests.post(
    "http://192.168.1.100:8080/users",
    json={"name": "Alice", "email": "alice@example.com"}
)
user = response.json()
print(user["id"], user["name"])
```

这一切都很清晰，但你有没有觉得 ——

> 我明明就是想 **"创建一个用户"**，为什么要关心 URL 路径是什么、HTTP 方法是 POST 还是 PUT、请求体是 JSON 还是 Form？

---

## 二、RPC 的理想：像调本地函数一样

RPC（Remote Procedure Call，远程过程调用）的想法很简单：

```python
# 理想中的代码：
user = user_service.CreateUser(name="Alice", email="alice@example.com")
print(user.id, user.name)
```

> 就像调用一个本地函数！你不需要知道：
> - 服务在哪个 IP
> - 用的是什么协议
> - 数据怎么序列化

**RPC 的使命**：把「寻址 + 序列化 + 网络传输」全部打包隐藏，只暴露一个函数调用。

---

## 三、RPC 是如何做到的？

```
┌─────────────┐                           ┌─────────────┐
│   客户端     │                           │   服务端     │
│             │                           │             │
│ stub.Add(3,5)│ ─── 序列化为网络消息 ───→ │ 收到请求     │
│             │                           │ 执行 Add(3,5)│
│ 拿到结果 8  │ ←─── 序列化返回结果 ──── │ 返回 8       │
└─────────────┘                           └─────────────┘
```

中间有个关键角色：**Stub（桩/代理）**

- 客户端的 Stub 是一个假对象，看起来有和远程服务一样的方法
- 当你调 `stub.Add(3, 5)` 时，它悄悄把参数打包、发网络请求、等结果、解包返回
- 你完全感觉不到这是远程调用

---

## 四、动手！用 xmlrpc 体验最简 RPC（15 分钟）

Python 标准库自带一个最简单的 RPC 实现：`xmlrpc`。只用十几行代码就能体验 RPC。

### 4.1 服务端代码

创建 `rpc_server.py`：

```python
from xmlrpc.server import SimpleXMLRPCServer

# 这就是我们的"远程函数"
def say_hello(name):
    return f"你好, {name}!"

def add(a, b):
    return a + b

def get_user(user_id):
    """模拟查数据库"""
    users = {
        1: {"name": "Alice", "email": "alice@example.com"},
        2: {"name": "Bob", "email": "bob@example.com"},
    }
    return users.get(user_id, f"用户 {user_id} 不存在")

# 创建 RPC 服务器，监听 8000 端口
server = SimpleXMLRPCServer(("localhost", 8000))
server.register_function(say_hello)    # 注册函数
server.register_function(add)
server.register_function(get_user)
print("RPC 服务器已启动: http://localhost:8000")
server.serve_forever()
```

### 4.2 客户端代码

创建 `rpc_client.py`：

```python
import xmlrpc.client

# 连接远程服务 —— 只需要一个 URL
proxy = xmlrpc.client.ServerProxy("http://localhost:8000")

# 像调本地函数一样调用！
print(proxy.say_hello("世界"))       # 你好, 世界!
print(f"3 + 5 = {proxy.add(3, 5)}") # 3 + 5 = 8

user = proxy.get_user(1)
print(f"用户1: {user}")              # 用户1: {'name': 'Alice', ...}

print(proxy.get_user(999))           # 用户 999 不存在
```

### 4.3 运行

```bash
# 终端1：启动服务端
python rpc_server.py

# 终端2：运行客户端
python rpc_client.py
```

---

## 五、观察与思考

运行完上面代码，停下来想几个问题：

| 问题 | 答案 |
|------|------|
| 客户端代码里有 URL 吗？ | 有，但在 `ServerProxy` 初始化时**只写了一次** |
| 客户端的 `proxy.add(3,5)` 看起来像什么？ | 像调本地函数！ |
| 参数（3, 5）怎么传到服务端的？ | xmlrpc 自动序列化为 XML |
| 你写代码时要管序列化吗？ | 不用，框架自动搞定 |

这就是 RPC 的核心哲学。

---

## 六、xmlrpc vs gRPC 是什么关系？

| | xmlrpc | gRPC |
|------|--------|------|
| 出身 | 90 年代的 RPC 标准 | Google 2015 年开源 |
| 序列化 | XML（文本，冗长） | Protobuf（二进制，高效） |
| 传输协议 | HTTP/1.1 | HTTP/2（多路复用） |
| 接口定义 | 无（靠函数名） | `.proto` 文件（强类型契约） |
| 适用 | 学习 RPC 概念 | 生产级微服务 |

> xmlrpc 就像"学骑自行车用的三轮车"，帮你理解 RPC 是什么。  
> gRPC 就是"真正的公路自行车"，性能更强、功能更全。

---

## 七、本课小结

```
你已掌握的核心概念：

  REST 调用           RPC 调用
  ─────────           ────────
  手动拼 URL          →  只需 Channel 地址（一次）
  手动选 HTTP 方法    →  方法名即接口
  手动序列化 JSON     →  框架自动处理
  手动解析响应        →  直接拿到返回值
  
  RPC 的目标：让远程调用看起来像本地函数调用。
```

---

## [TEST] 课后小测

1. RPC 的英文全称是什么？中文叫什么？
2. Stub（桩）的作用是什么？
3. xmlrpc 和 gRPC 的序列化方式有什么不同？
4. 你在客户端写 `proxy.add(3,5)` 时，实际上发生了什么？

> 👉 下一课：[02 环境准备](02_环境准备.md) —— 安装 gRPC 全家桶
