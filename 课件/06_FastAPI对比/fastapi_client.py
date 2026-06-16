"""
第06课：FastAPI 对照客户端
"""
import httpx

BASE = "http://localhost:8000"

with httpx.Client(base_url=BASE, timeout=2.0) as c:
    # 创建
    r = c.post("/users", json={"name": "Alice", "email": "alice@example.com"})
    print(f"[OK] Created: {r.json()}")

    # 查询
    r = c.get("/users/1")
    print(f"[OK] Got: {r.json()}")

    # 查不存在
    r = c.get("/users/999")
    print(f"[ERR] Error: {r.status_code} - {r.text}")
