from xmlrpc.server import SimpleXMLRPCServer

# 这些就是"远程函数"——客户端会通过网络来调用它们
def say_hello(name):
    return f"你好, {name}!"

def add(a, b):
    return a + b

# 创建服务器，监听 8000 端口
server = SimpleXMLRPCServer(("localhost", 8000))
server.register_function(say_hello)
server.register_function(add)
print("[gRPC] RPC 服务器启动: http://localhost:8000")
server.serve_forever()
