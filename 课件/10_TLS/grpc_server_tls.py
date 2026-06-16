"""
第10课：TLS 安全通信 —— 服务端
先运行这个生成证书（需要 openssl）:
  openssl genrsa -out server.key 2048
  openssl req -new -x509 -key server.key -out server.crt -days 365 -subj "/CN=localhost"
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

    def ListUsers(self, req, ctx):
        for u in self.db.values():
            yield u

    def BatchCreateUsers(self, req_iter, ctx):
        created, errors = [], []
        for req in req_iter:
            if not req.name.strip():
                errors.append("名称为空")
                continue
            u = user_pb2.UserResponse(id=self.next_id, name=req.name, email=req.email)
            self.db[self.next_id] = u
            created.append(self.next_id)
            self.next_id += 1
        return user_pb2.BatchCreateResponse(
            success_count=len(created), fail_count=len(errors),
            created_ids=created, errors=errors
        )

    def Chat(self, req_iter, ctx):
        import time
        for msg in req_iter:
            yield user_pb2.ChatMessage(
                user="Server", text=f"已收到: {msg.text}",
                timestamp=time.strftime("%H:%M:%S")
            )

def serve():
    with open('server.key', 'rb') as f:
        key = f.read()
    with open('server.crt', 'rb') as f:
        cert = f.read()
    creds = grpc.ssl_server_credentials([(key, cert)])

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    server.add_secure_port('[::]:50051', creds)  # ← secure
    server.start()
    print("🔒 gRPC TLS 服务已启动: [::]:50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
