"""
全量验证：测试所有课程的代码能否正常运行
"""
import subprocess, sys, os, time, socket, threading

BASE = os.path.dirname(os.path.abspath(__file__))
PASS, FAIL = 0, 0

def kill_port(port):
    try:
        for p in [50051, 8000]:
            s = socket.socket()
            s.settimeout(1)
            try:
                s.bind(('', p))
                s.close()
            except:
                pass
    except:
        pass

def test(name, setup_cmd, test_cmd, cwd=None, timeout=15):
    global PASS, FAIL
    print(f"\n{'='*50}")
    print(f"Testing: {name}")
    print(f"{'='*50}")
    try:
        if setup_cmd:
            s = subprocess.Popen(setup_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                cwd=cwd or BASE, shell=True)
            time.sleep(2)
        r = subprocess.run(test_cmd, capture_output=True, text=True, timeout=timeout, 
                          cwd=cwd or BASE, shell=True)
        ok = r.returncode == 0
        if ok:
            print(f"[PASS] {name}")
            PASS += 1
        else:
            print(f"[FAIL] {name} (exit={r.returncode})")
            if r.stderr:
                print(f"  stderr: {r.stderr.strip()[:200]}")
            FAIL += 1
        if setup_cmd:
            try: s.terminate(); s.wait(timeout=3)
            except: pass
    except subprocess.TimeoutExpired:
        print(f"[FAIL] {name} (timeout)")
        FAIL += 1
        if setup_cmd:
            try: s.terminate()
            except: pass
    except Exception as e:
        print(f"[FAIL] {name}: {e}")
        FAIL += 1

kill_port(None)

# ==== 01 热身 ====
test("01 xmlrpc server+client",
     [sys.executable, "01_热身/rpc_server.py"],
     [sys.executable, "01_热身/rpc_client.py"],
     cwd=os.path.join(BASE, "课件"))

# ==== 04 + 05 gRPC 服务端+客户端 ====
kill_port(None)
proc_04 = subprocess.Popen([sys.executable, "grpc_server.py"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    cwd=os.path.join(BASE, "课件/04_服务端"))
time.sleep(1.5)

test("04+05 gRPC 客户端",
     None,
     [sys.executable, "grpc_client.py"],
     cwd=os.path.join(BASE, "课件/05_客户端"))
proc_04.terminate(); proc_04.wait()

# ==== 06 FastAPI ====
kill_port(None)
proc_06 = subprocess.Popen([sys.executable, "-m", "uvicorn", "fastapi_app:app", "--port", "8000"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    cwd=os.path.join(BASE, "课件/06_FastAPI对比"))
time.sleep(1.5)

test("06 FastAPI 客户端",
     None,
     [sys.executable, "fastapi_client.py"],
     cwd=os.path.join(BASE, "课件/06_FastAPI对比"))
proc_06.terminate(); proc_06.wait()

# ==== 07 错误处理 ====
kill_port(None)
proc_07 = subprocess.Popen([sys.executable, "grpc_server.py"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    cwd=os.path.join(BASE, "课件/07_错误处理"))
time.sleep(1.5)

test("07 错误处理",
     None,
     [sys.executable, "grpc_client.py"],
     cwd=os.path.join(BASE, "课件/07_错误处理"))
proc_07.terminate(); proc_07.wait()

# ==== 08 拦截器 ====
kill_port(None)
proc_08 = subprocess.Popen([sys.executable, "grpc_server.py"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    cwd=os.path.join(BASE, "课件/08_拦截器"))
time.sleep(1.5)

test("08 拦截器",
     None,
     [sys.executable, "grpc_client.py"],
     cwd=os.path.join(BASE, "课件/08_拦截器"))
proc_08.terminate(); proc_08.wait()

# ==== 09 流式通信 ====
kill_port(None)
proc_09 = subprocess.Popen([sys.executable, "grpc_server.py"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    cwd=os.path.join(BASE, "课件/09_流式通信"))
time.sleep(1.5)

test("09 流式通信",
     None,
     [sys.executable, "grpc_client.py"],
     cwd=os.path.join(BASE, "课件/09_流式通信"),
     timeout=25)
proc_09.terminate(); proc_09.wait()

# ==== 10 TLS ====
kill_port(None)
proc_10 = subprocess.Popen([sys.executable, "grpc_server_tls.py"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    cwd=os.path.join(BASE, "课件/10_TLS"))
time.sleep(1.5)

test("10 TLS 客户端",
     None,
     [sys.executable, "grpc_client_tls.py"],
     cwd=os.path.join(BASE, "课件/10_TLS"))
proc_10.terminate(); proc_10.wait()

# ==== 11 多Proto ====
test("11 多Proto 编译",
     None,
     [sys.executable, "generate.py"],
     cwd=os.path.join(BASE, "课件/11_多Proto"))

# ==== 13 混合架构 ====
kill_port(None)
proc_13_g = subprocess.Popen([sys.executable, "grpc_user_server.py"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    cwd=os.path.join(BASE, "课件/13_混合架构"))
time.sleep(1)

proc_13_f = subprocess.Popen([sys.executable, "-m", "uvicorn", "fastapi_gateway:app", "--port", "8000"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    cwd=os.path.join(BASE, "课件/13_混合架构"))
time.sleep(1.5)

import httpx
try:
    r = httpx.get("http://localhost:8000/api/health", timeout=2.0)
    if r.json()["status"] == "healthy":
        print(f"[PASS] 13 混合架构 health check")
        PASS += 1
    else:
        print(f"[FAIL] 13 health degraded")
        FAIL += 1
except Exception as e:
    print(f"[FAIL] 13: {e}")
    FAIL += 1

proc_13_g.terminate(); proc_13_f.terminate()
proc_13_g.wait(); proc_13_f.wait()

# ==== 14 性能测试 ====
kill_port(None)
test("14 性能测试",
     None,
     [sys.executable, "benchmark.py"],
     cwd=os.path.join(BASE, "课件/14_性能测试"),
     timeout=50)

# ==== 总结 ====
print(f"\n{'='*50}")
print(f"Result: {PASS} PASS, {FAIL} FAIL")
print(f"{'='*50}")
