# 🎓 RPC & gRPC 从入门到实战

> 14 节课，每天 1-2 小时，用 Python 系统学习 RPC 和 gRPC

## 📚 课程结构

| 课时 | 课件 | 代码 |
|:---:|------|------|
| 00 | [课程目录](课件/00_课程目录.md) | - |
| 01 | [热身：理解 RPC](课件/01_热身_理解RPC.md) | [代码](课件/01_热身/) |
| 02 | [环境准备](课件/02_环境准备.md) | - |
| 03 | [第一个 Proto 文件](课件/03_第一个Proto文件.md) | [proto](课件/03_Proto/) |
| 04 | [gRPC 服务端](课件/04_gRPC服务端.md) | [代码](课件/04_服务端/) |
| 05 | [gRPC 客户端](课件/05_gRPC客户端.md) | [代码](课件/05_客户端/) |
| 06 | [FastAPI 对比](课件/06_FastAPI对比.md) | [代码](课件/06_FastAPI对比/) |
| 07 | [错误处理](课件/07_错误处理.md) | [代码](课件/07_错误处理/) |
| 08 | [拦截器](课件/08_拦截器.md) | [代码](课件/08_拦截器/) |
| 09 | [流式通信](课件/09_流式通信.md) | [代码](课件/09_流式通信/) |
| 10 | [TLS 安全](课件/10_TLS安全通信.md) | [代码](课件/10_TLS/) |
| 11 | [多 Proto 组织](课件/11_多Proto文件组织.md) | [代码](课件/11_多Proto/) |
| 12 | [调试工具](课件/12_调试工具.md) | - |
| 13 | [混合架构](课件/13_混合架构实战.md) | [代码](课件/13_混合架构/) |
| 14 | [性能测试](课件/14_性能测试.md) | [代码](课件/14_性能测试/) |

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
