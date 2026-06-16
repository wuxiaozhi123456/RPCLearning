# 🎓 RPC & gRPC 从入门到实战

> 14 节课，每天 1-2 小时，用 Python 系统学习 RPC 和 gRPC

## 📚 课程结构

```
课件/
├── 00_课程目录.md              ← 总览
├── 01_热身/                    ← 理解 RPC 概念
├── 02_环境准备.md              ← 安装依赖
├── 03_Proto/                   ← 第一个 proto 文件
├── 04_服务端/                  ← gRPC 服务端实现
├── 05_客户端/                  ← gRPC 客户端实现
├── 06_FastAPI对比/             ← REST vs gRPC 全方位对照
├── 07_错误处理/                ← StatusCode、RpcError
├── 08_拦截器/                  ← Middleware 等效
├── 09_流式通信/                ← 三种流式 RPC
├── 10_TLS/                     ← 加密传输
├── 11_多Proto/                 ← 项目组织结构
├── 12_调试工具.md              ← grpcurl、grpcui
├── 13_混合架构/                ← FastAPI 网关 + gRPC 微服务
└── 14_性能测试/                ← 压测对比
```

## 🚀 快速开始

```bash
# 安装依赖
pip install grpcio grpcio-tools fastapi uvicorn httpx

# 编译 proto
cd 课件
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. user.proto

# 按课程顺序学习
cd 01_热身 && python rpc_server.py    # 终端1
cd 01_热身 && python rpc_client.py    # 终端2
```

## 💡 适用人群

- 有 REST (FastAPI / Spring Boot) 开发经验
- 想用 Python 系统学习 gRPC
- 需要做微服务技术选型
