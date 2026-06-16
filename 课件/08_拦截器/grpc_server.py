"""
第08课：拦截器 —— 服务端（日志 + 认证）
运行: python grpc_server.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import grpc
import time
from concurrent import futures
import user_pb2, user_pb2_grpc

# ===== 拦截器1：日志 =====
class LogInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, cont, details):
        method = details.method
        print(f"[{time.strftime('%H:%M:%S')}] → {method}")
        start = time.time()
        resp = cont(details)
        print(f"[{time.strftime('%H:%M:%S')}] ← {method} ({time.time()-start:.3f}s)")
        return resp

# ===== 拦截器2：认证 =====
class AuthInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, cont, details):
        md = dict(details.invocation_metadata)
        if md.get('authorization') != 'Bearer my-token':
            def deny(req, ctx):
                ctx.abort(grpc.StatusCode.UNAUTHENTICATED, "Token 无效")
            return grpc.unary_unary_rpc_method_handler(deny)
        return cont(details)

# ===== 服务实现（同上）=====
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
        for msg in req_iter:
            yield user_pb2.ChatMessage(
                user="Server", text=f"已收到: {msg.text}",
                timestamp=time.strftime("%H:%M:%S")
            )

def serve():
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=[LogInterceptor(), AuthInterceptor()]
    )
    user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("🚀 gRPC 服务（日志 + 认证拦截器）: [::]:50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
