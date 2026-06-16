# 第 03 课：第一个 Proto 文件 —— gRPC 的"接口定义语言"

> **目标**：学会写 `.proto` 文件，理解 `syntax`、`message`、`service`、`rpc`、字段编号  
> **核心理念**：proto = 独立于语言的强类型接口契约

---

## 一、为什么需要 proto？

回忆一下你在 FastAPI 里怎么定义接口：

```python
# FastAPI 定义接口的方式 —— 代码即接口
class UserCreate(BaseModel):      # ← DTO 定义
    name: str
    email: str

@app.post("/users")               # ← 路由定义
def create_user(user: UserCreate): # ← 处理函数
    ...
```

gRPC 的思路不一样：**先把"接口"从代码里抽出来，写成一个独立文件**，然后交给工具自动生成各种语言的代码。

这个独立的接口文件，就是 `.proto` 文件。

---

## 二、第一个 proto 文件：用户服务

创建 `user.proto`：

```protobuf
// user.proto —— 用户服务的接口定义

syntax = "proto3";              // 1️⃣ 声明使用 proto3 语法（最新版）

package user;                   // 2️⃣ 包名，防止命名冲突（类似 Python 的包）

// 3️⃣ Service：定义服务，就是你的"Controller"类
service UserService {
    // 4️⃣ rpc：定义方法，就是你的接口
    rpc CreateUser (CreateUserRequest) returns (UserResponse);
    rpc GetUser (GetUserRequest) returns (UserResponse);
}

// 5️⃣ Message：定义数据结构，就是你的"DTO / Pydantic 模型"
message CreateUserRequest {
    string name = 1;            // 字段类型 + 名称 + 唯一编号
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

## 三、逐行讲解

### 3.1 `syntax = "proto3";`

- 声明使用 proto3 版本的语法
- proto3 是目前的主流，比 proto2 更简洁
- **每个 `.proto` 文件的第一行（非注释行）必须是这个**

### 3.2 `package user;`

- 定义包名，避免不同 proto 文件间的命名冲突
- 生成 Python 代码后，会变成模块的命名空间
- 类比：Python 的 `from user import xxx` 中的 `user`

### 3.3 `service UserService { ... }`

这是 proto 文件**最核心**的部分。一个 service 对应一个"服务"：

```protobuf
service UserService {
    rpc CreateUser (CreateUserRequest) returns (UserResponse);
    rpc GetUser (GetUserRequest) returns (UserResponse);
}
```

| proto 概念 | FastAPI 对应 | 说明 |
|-----------|-------------|------|
| `service` | `class Router` 或 `FastAPI()` | 一组相关的接口 |
| `rpc` 方法 | `@app.post("/path")` | 单个接口 |
| 括号里的参数 | 请求体类型（Pydantic） | 入参 |
| `returns` 后面 | 响应体类型（Pydantic） | 返回值 |

> **关键区别**：FastAPI 里路由是用 URL 路径来区分的（`/users`、`/users/{id}`），  
> gRPC 里是用 **方法名** 来区分的（`CreateUser`、`GetUser`）。  
> 没有 URL，没有 HTTP 方法（GET/POST），只有方法名。

### 3.4 `message` —— 数据结构

```protobuf
message CreateUserRequest {
    string name = 1;      // 字段编号 1
    string email = 2;     // 字段编号 2
}
```

| proto message | FastAPI Pydantic |
|---------------|-----------------|
| `message UserResponse` | `class User(BaseModel)` |
| `string name = 1;` | `name: str` |
| `int32 id = 1;` | `id: int` |

### 3.5 ⭐ 关键：字段编号（`= 1`, `= 2`）

这是 proto 里**最重要也最容易忽略**的概念：

```
字段编号不是"初始值"！它是 Protobuf 二进制序列化时
用来标识字段的，一旦定义，永远不要改！
```

| 操作 | 可以吗 | 原因 |
|------|:---:|------|
| 新增字段，用新编号 | [OK] | 旧客户端跳过未知字段 |
| 删除字段，其编号不再使用 | [OK] | 但要标记 `reserved` |
| 修改已有字段的编号 | [ERR] | 破坏新旧兼容！ |
| 修改字段名称 | [OK]（要慎重） | 编号不变就兼容 |

**类比**：字段编号就像数据库表的主键 `id`——你不能今天把 `name` 的编号从 1 改成 2。

---

## 四、常用 Protobuf 类型速查

| proto 类型 | 对应 Python 类型 | 说明 |
|-----------|-----------------|------|
| `string` | `str` | 字符串 |
| `int32` | `int` | 32 位整数 |
| `int64` | `int` | 64 位整数 |
| `float` | `float` | 浮点数 |
| `double` | `float` | 双精度浮点数 |
| `bool` | `bool` | 布尔值 |
| `bytes` | `bytes` | 二进制数据 |
| `repeated string` | `list[str]` | 数组/列表 |
| `map<string, int32>` | `dict[str, int]` | 字典 |

---

## 五、动手练习

### 练习 1：照抄一遍

打开编辑器，把上面的 `user.proto` 原样敲一遍（不要复制粘贴）。

### 练习 2：加一个方法

在 `UserService` 里加一个 `DeleteUser` 方法：

> 提示：你需要定义一个 `DeleteUserRequest` message（只需要 `int32 id = 1;`），  
> 返回类型可以用 `google.protobuf.Empty`（或者自己定义一个 `DeleteUserResponse`，里面放 `bool success = 1;`）。

### 练习 3：加一个字段

在 `UserResponse` 里加一个 `phone` 字段（string 类型），想想该用什么编号？

---

## 六、本课小结

```
.proto 文件 = gRPC 的接口定义

┌─────────────────────────────────────────┐
│  syntax = "proto3";       // 版本声明    │
│  package user;            // 包名        │
│                                         │
│  service UserService {     // 服务       │
│    rpc CreateUser(...)     // 方法       │
│  }                                      │
│                                         │
│  message CreateUserRequest { // 数据结构 │
│    string name = 1;        // 字段+编号  │
│  }                                      │
└─────────────────────────────────────────┘

和你熟悉的 FastAPI 对比：
  service   ≈ Router / Controller
  rpc       ≈ @app.post("/path")
  message   ≈ Pydantic BaseModel
  字段编号   ≈ proto 特有（序列化标识）
```

---

## [TEST] 课后小测

1. `.proto` 文件中 `syntax = "proto3";` 必须放在第几行？
2. `message` 和 `service` 分别对应 FastAPI 里的什么概念？
3. 为什么字段编号（`= 1, = 2`）一旦定义就不能改？
4. proto 里怎么表示一个字符串数组？

> 👉 下一课：[04 gRPC 服务端](04_gRPC服务端.md) —— 把 proto 编译成代码，写第一个 gRPC 服务器
