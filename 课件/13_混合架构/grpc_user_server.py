"""
第13课：gRPC 用户微服务（纯后端，不对外暴露 HTTP）
"""
import grpc
from concurrent import futures
import user_pb2, user_pb2_grpc

class UserService(user_pb2_grpc.UserServiceServicer):
    def __init__(self):
        self.db = {}
        self.next_id = 1

    def CreateUser(self, req, ctx):
        if not req.name.strip():
            ctx.abort(grpc.StatusCode.INVALID_ARGUMENT, "名称不能为空")
        u = user_pb2.UserResponse(id=self.next_id, name=req.name, email=req.email)
        self.db[self.next_id] = u
        self.next_id += 1
        print(f"[gRPC] 创建用户: {u.name} (ID={u.id})")
        return u

    def GetUser(self, req, ctx):
        if req.id not in self.db:
            ctx.abort(grpc.StatusCode.NOT_FOUND, f"用户 {req.id} 不存在")
        return self.db[req.id]

    def ListUsers(self, req, ctx):
        for u in self.db.values():
            yield u

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("[gRPC] 用户微服务: [::]:50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
