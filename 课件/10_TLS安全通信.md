# 第 10 课：TLS 安全通信 —— 给 gRPC 上锁

> **目标**：学会生成自签名证书，配置 gRPC 的加密传输  
> **原则**：开发环境用自签名，生产环境用 CA 签发的证书

---

## 一、为什么需要 TLS？

到目前为止，我们的 gRPC 通信都是明文的：

```python
# 不安全：数据明文传输，任何人都能看到
channel = grpc.insecure_channel('localhost:50051')
```

生产环境必须加密 → 用 TLS（Transport Layer Security）。

---

## 二、第一步：生成自签名证书

在项目目录执行（需要 openssl，Windows 可用 Git Bash 或 WSL）：

```bash
# 生成私钥
openssl genrsa -out server.key 2048

# 生成自签名证书（有效期 365 天）
openssl req -new -x509 -key server.key -out server.crt -days 365 \
  -subj "/C=CN/ST=Guangdong/L=Shenzhen/O=MyCompany/CN=localhost"
```

> **`-subj` 参数说明**：`/CN=localhost` 是关键，证书的 Common Name 必须匹配你连接的主机名。

生成后得到两个文件：

```
server.key   ← 私钥（保密！不要提交到 git）
server.crt   ← 证书（可以公开）
```

---

## 三、第二步：服务端启用 TLS

```python
import grpc
from concurrent import futures
import user_pb2, user_pb2_grpc

class UserService(user_pb2_grpc.UserServiceServicer):
    # ... 实现不变 ...

def serve():
    # ===== 读取证书和私钥 =====
    with open('server.key', 'rb') as f:
        private_key = f.read()
    with open('server.crt', 'rb') as f:
        certificate_chain = f.read()

    # ===== 创建 TLS 凭证 =====
    credentials = grpc.ssl_server_credentials(
        [(private_key, certificate_chain)]
    )

    # ===== 创建服务器 =====
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)

    # ===== ⚠️ 注意：这里用 add_secure_port，不是 add_insecure_port =====
    server.add_secure_port('[::]:50051', credentials)

    server.start()
    print("🔒 gRPC 服务已启动（TLS 加密）: [::]:50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
```

---

## 四、第三步：客户端连接 TLS 服务

### 方式 1：使用自签名证书（推荐测试用）

```python
import grpc
import user_pb2, user_pb2_grpc

# ===== 读取服务端的证书 =====
with open('server.crt', 'rb') as f:
    trusted_certs = f.read()

# ===== 创建 TLS 凭证（信任服务端证书）=====
credentials = grpc.ssl_channel_credentials(
    root_certificates=trusted_certs
)

# ===== 创建安全通道 =====
channel = grpc.secure_channel('localhost:50051', credentials)

# 之后的使用方式和 insecure 完全一样！
stub = user_pb2_grpc.UserServiceStub(channel)
resp = stub.GetUser(user_pb2.GetUserRequest(id=1))
print(f"✅ {resp.name}")
```

### 方式 2：本地开发跳过验证（不推荐生产用！）

```python
# ⚠️ 仅限本地开发！不做任何证书验证
channel = grpc.secure_channel(
    'localhost:50051',
    grpc.ssl_channel_credentials(),   # 不传 root_certificates
    options=[('grpc.ssl_target_name_override', 'localhost')]
)
```

> 生产环境必须用方式 1 或 CA 签发的证书。

---

## 五、完整对比：不安全 vs 安全

| | 不安全（开发） | TLS 安全（生产） |
|------|:---:|:---:|
| 服务端端口注册 | `add_insecure_port(...)` | `add_secure_port(..., creds)` |
| 服务端凭证 | 无 | `ssl_server_credentials()` |
| 客户端通道 | `insecure_channel(...)` | `secure_channel(..., creds)` |
| 客户端凭证 | 无 | `ssl_channel_credentials(root_certs=...)` |
| 数据加密 | ❌ 明文 | ✅ 加密 |
| 身份验证 | ❌ 无 | ✅ 证书验证 |

---

## 六、生产环境的证书管理

```mermaid
开发环境                      生产环境
────────                      ────────
openssl 自签名          →     Let's Encrypt / CA 签发
server.key (本地)        →     密钥管理服务 (KMS/Vault)
server.crt (本地)        →     证书自动轮换
手动配置                 →     自动加载 + 热更新
```

生产环境建议：
- 使用 **Let's Encrypt**（免费）或公司 CA 签发的证书
- 证书和密钥不要写在代码里，用环境变量或配置中心
- 实现证书自动续期和热加载

---

## 七、mTLS（双向 TLS）简介

上面的 TLS 只是**客户端验证服务端**。在某些高安全场景，还需要**服务端验证客户端**，这叫 mTLS（Mutual TLS）。

```
普通 TLS:     客户端 ──验证──→ 服务端
mTLS:         客户端 ←──互相验证──→ 服务端
```

mTLS 需要：
1. 客户端也生成自己的证书和私钥
2. 服务端配置 `root_certificates` 来验证客户端证书

> 本课程不深入 mTLS，知道这个概念即可。需要时查 gRPC 官方文档。

---

## 八、`.gitignore` 提醒

```bash
# 密钥文件绝对不能提交！
server.key
*.key

# 自签名证书可以根据团队决定
# server.crt   ← 可以提交（因为没有私钥也没用）
```

---

## 九、本课小结

```
从明文到加密，只需要改两行代码：

  服务端：
    add_insecure_port(...)   →   add_secure_port(..., creds)

  客户端：
    insecure_channel(...)    →   secure_channel(..., creds)

  gRPC 的 TLS 集成非常简单，底层基于 HTTP/2 + TLS 1.3，
  和 HTTPS 是完全相同的安全机制。
```

---

## 📝 课后练习

1. 用 openssl 生成自签名证书
2. 把之前写的服务端和客户端都改成 TLS 版本，确保能正常通信
3. 尝试用 insecure_channel 连接 secure_port，观察报错信息
4. 了解一下 Let's Encrypt 的工作原理

---

> 👉 下一课：[11 多 Proto 文件组织](11_多Proto文件组织.md) —— 真实项目的 proto 管理方式
