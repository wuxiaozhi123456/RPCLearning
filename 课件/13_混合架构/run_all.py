"""
第13课：一键启动（gRPC 微服务 + FastAPI 网关）
运行: python run_all.py
然后打开 http://localhost:8000/docs 看 Swagger UI
"""
import threading
import time
import uvicorn
import grpc_user_server

# 后台线程启动 gRPC 微服务
grpc_thread = threading.Thread(target=grpc_user_server.serve, daemon=True)
grpc_thread.start()
time.sleep(1)

# 主线程启动 FastAPI 网关
print("[HTTP] FastAPI 网关: http://localhost:8000")
print("[DOC] Swagger UI: http://localhost:8000/docs")
uvicorn.run("fastapi_gateway:app", host="0.0.0.0", port=8000)
