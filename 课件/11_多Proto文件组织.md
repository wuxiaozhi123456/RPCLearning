# 第 11 课：多 Proto 文件组织 —— 真实项目的管理方式

> **目标**：学会拆分 proto 文件，使用 `import` 复用公共定义，组织清晰的项目结构  
> **对比**：就像 FastAPI 里你不会把所有路由写在一个文件里

---

## 一、为什么需要多个 proto 文件？

回想你写 FastAPI 项目时的目录结构：

```
fastapi_project/
├── main.py              # 入口
├── routers/
│   ├── users.py         # 用户相关路由
│   └── orders.py        # 订单相关路由
├── schemas/
│   ├── user.py          # 用户模型
│   ├── order.py         # 订单模型
│   └── common.py        # 共享模型（Address 等）
```

proto 文件也应该这样组织！把所有定义塞进一个 `all.proto` 会：
- [ERR] 文件太长，难以维护
- [ERR] 不同服务的 message 容易命名冲突
- [ERR] 无法按模块复用

---

## 二、推荐的目录结构

```
protos/
├── common/
│   └── common.proto       # ← 共享的数据结构和枚举
├── user/
│   └── user.proto         # ← 用户服务的接口和消息
├── order/
│   └── order.proto        # ← 订单服务的接口和消息
└── generate.sh            # ← 一键生成所有代码的脚本
```

---

## 三、实战：拆分用户 + 订单服务

### 3.1 共享定义：`protos/common/common.proto`

```protobuf
syntax = "proto3";

package common;

// 通用地址结构（用户和订单都可能用到）
message Address {
    string street = 1;
    string city = 2;
    string state = 3;
    string zip_code = 4;
}

// 通用时间戳
message Timestamp {
    int64 seconds = 1;
    int32 nanos = 2;
}

// 通用状态枚举
enum Status {
    UNKNOWN = 0;
    ACTIVE = 1;
    INACTIVE = 2;
    DELETED = 3;
}
```

### 3.2 用户服务：`protos/user/user.proto`

```protobuf
syntax = "proto3";

package user;

// 引入共享定义
import "common/common.proto";

// ===== 用户服务 =====
service UserService {
    rpc CreateUser (CreateUserRequest) returns (UserResponse);
    rpc GetUser (GetUserRequest) returns (UserResponse);
    rpc ListUsers (ListUsersRequest) returns (stream UserResponse);
}

// ===== 请求/响应消息 =====
message CreateUserRequest {
    string name = 1;
    string email = 2;
    common.Address address = 3;   // ← 使用共享的 Address
}

message GetUserRequest {
    int32 id = 1;
}

message ListUsersRequest {
    int32 page_size = 1;
    int32 page_token = 2;
}

message UserResponse {
    int32 id = 1;
    string name = 2;
    string email = 3;
    common.Address address = 4;
    common.Status status = 5;     // ← 使用共享的枚举
    common.Timestamp created_at = 6;
}
```

### 3.3 订单服务：`protos/order/order.proto`

```protobuf
syntax = "proto3";

package order;

import "common/common.proto";

// ===== 订单服务 =====
service OrderService {
    rpc CreateOrder (CreateOrderRequest) returns (OrderResponse);
    rpc GetOrder (GetOrderRequest) returns (OrderResponse);
}

// ===== 消息定义 =====
message OrderItem {
    int32 product_id = 1;
    int32 quantity = 2;
    double price = 3;
}

message CreateOrderRequest {
    int32 user_id = 1;
    repeated OrderItem items = 2;          // repeated = 数组
    common.Address shipping_address = 3;    // ← 复用共享类型
}

message GetOrderRequest {
    string order_id = 1;
}

message OrderResponse {
    string order_id = 1;
    int32 user_id = 2;
    repeated OrderItem items = 3;
    double total_amount = 4;
    common.Status status = 5;
    common.Timestamp created_at = 6;
}
```

---

## 四、编译所有 proto 文件

### 4.1 手动编译

```bash
# 注意：-I 参数要指向 proto 文件的根目录
python -m grpc_tools.protoc \
  -Iprotos \
  --python_out=. \
  --grpc_python_out=. \
  protos/common/common.proto \
  protos/user/user.proto \
  protos/order/order.proto
```

> **关键**：`-Iprotos` 是 import 的搜索根目录。  
> 当 `user.proto` 写 `import "common/common.proto"` 时，实际查找路径是 `protos/common/common.proto`。

### 4.2 建议：写一个生成脚本 `generate.sh`（或 `generate.py`）

```bash
#!/bin/bash
# generate.sh —— 一键生成所有 Python 代码

python -m grpc_tools.protoc \
  -Iprotos \
  --python_out=. \
  --grpc_python_out=. \
  protos/common/*.proto \
  protos/user/*.proto \
  protos/order/*.proto

echo "[OK] 代码生成完成"
```

Windows 上也可以用 Python 脚本 `generate.py`：

```python
# generate.py
import subprocess
import glob

proto_files = glob.glob("protos/**/*.proto", recursive=True)

cmd = [
    "python", "-m", "grpc_tools.protoc",
    "-Iprotos",
    "--python_out=.",
    "--grpc_python_out=.",
] + proto_files

subprocess.run(cmd, check=True)
print(f"[OK] 代码生成完成，共处理 {len(proto_files)} 个 proto 文件")
```

---

## 五、使用生成的代码

编译后，你会在当前目录看到：

```
common/
  common_pb2.py
  common_pb2_grpc.py
user/
  user_pb2.py
  user_pb2_grpc.py
order/
  order_pb2.py
  order_pb2_grpc.py
```

**导入时要注意包路径**：

```python
# 服务端
from user import user_pb2, user_pb2_grpc
from order import order_pb2, order_pb2_grpc

# 如果 import common 的类型
from common import common_pb2

# 创建 Address
addr = common_pb2.Address(
    street="科技园路1号",
    city="深圳"
)
```

> ⚠️ 如果你的项目结构让导入有问题，可能需要在相应目录下添加空的 `__init__.py` 文件。

---

## 六、一个 gRPC 服务器注册多个服务

```python
import grpc
from concurrent import futures

from user import user_pb2, user_pb2_grpc
from order import order_pb2, order_pb2_grpc

# ===== 创建服务器 =====
server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

# ===== 注册多个服务 =====
user_pb2_grpc.add_UserServiceServicer_to_server(
    UserServiceImpl(), server
)
order_pb2_grpc.add_OrderServiceServicer_to_server(
    OrderServiceImpl(), server
)

# ===== 启动 =====
server.add_insecure_port('[::]:50051')
server.start()
print("[gRPC] 服务器已启动，托管了 UserService 和 OrderService")
server.wait_for_termination()
```

---

## 七、最佳实践清单

| 实践 | 说明 |
|------|------|
| [OK] 共享类型放 `common.proto` | Address、Timestamp、Status 等 |
| [OK] 一个 `service` 一个 proto 文件 | 用户服务 = `user.proto`，订单 = `order.proto` |
| [OK] 使用 `package` 避免冲突 | `package user;` 和 `package order;` |
| [OK] proto 目录结构和包名对应 | `protos/user/user.proto` ↔ `package user;` |
| [OK] 写生成脚本自动化 | 一键编译所有 proto |
| [ERR] 不要把生成代码提交到 git | `*_pb2.py` 和 `*_pb2_grpc.py` 应 `.gitignore` |
| [ERR] 不要在 message 间循环引用 | proto 不支持嵌套 import 循环 |

---

## 八、对比 FastAPI

| FastAPI 项目结构 | gRPC 项目结构 |
|-----------------|-------------|
| `routers/users.py` | `protos/user/user.proto` |
| `routers/orders.py` | `protos/order/order.proto` |
| `schemas/common.py` | `protos/common/common.proto` |
| `app.include_router(user_router)` | `add_UserServiceServicer_to_server(...)` |
| `app.include_router(order_router)` | `add_OrderServiceServicer_to_server(...)` |

> 思维模式完全一样：按业务模块拆分，共享类型抽取到 common。

---

## 九、本课小结

```
单文件 proto：       学习阶段用（前几课）
多文件 proto：       真实项目用（本课）

组织原则：
  ① 一个 proto 文件对应一个 service
  ② 共享的 message/enum 放到 common.proto
  ③ import 路径相对于 -I 指定的根目录
  ④ 一个 gRPC 服务器可以注册多个 service
```

---

## [TEST] 课后练习

1. 把之前的 `user.proto` 拆分成 `common/common.proto` 和 `user/user.proto`
2. 新增一个 `order.proto`，在 OrderResponse 中引用 `common.Address`
3. 写一个 `generate.py` 脚本，一键编译所有 proto
4. 给一个 gRPC 服务器同时注册 `UserService` 和 `OrderService`

---

> 👉 下一课：[12 调试工具](12_调试工具.md) —— grpcurl、grpcui，像 curl 和 Postman 一样调试 gRPC
