"""
第10课：TLS 安全通信 —— 服务端
运行前先生成证书:
  MSYS_NO_PATHCONV=1 openssl genrsa -out server.key 2048
  MSYS_NO_PATHCONV=1 openssl req -new -x509 -key server.key -out server.crt -days 365 -subj "/CN=localhost"
"""
import grpc
from concurrent import futures
import user_pb2, user_pb2_grpc

class UserService(user_pb2_grpc.UserServiceServicer):
    def __init__(self):
        self.db = {}
        self.next_id = 1

    def CreateUser(self, req, ctx):
        u = user_pb2.UserResponse(id=self.next_id, name=req.name, email=req.email)
        self.db[self.next_id] = u
        self.next_id += 1
        return u

    def GetUser(self, req, ctx):
        if req.id not in self.db:
            ctx.abort(grpc.StatusCode.NOT_FOUND, f"用户 {req.id} 不存在")
        return self.db[req.id]

def serve():
    # 读取证书和私钥
    with open('server.key', 'rb') as f:
        key = f.read()
    with open('server.crt', 'rb') as f:
        cert = f.read()

    # 创建 TLS 凭证
    creds = grpc.ssl_server_credentials([(key, cert)])

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)

    # 关键区别：add_secure_port 而不是 add_insecure_port
    server.add_secure_port('[::]:50051', creds)
    server.start()
    print("[gRPC] TLS 加密服务已启动: [::]:50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
