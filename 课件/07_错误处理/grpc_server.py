"""
第07课：错误处理 —— 改造后的服务端
运行: python grpc_server.py
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

    def CreateUser(self, request, context):
        # 参数校验
        if not request.name.strip():
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "名称不能为空")
        if "@" not in request.email:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "邮箱格式无效")

        # 查重
        for u in self.db.values():
            if u.email == request.email:
                context.abort(grpc.StatusCode.ALREADY_EXISTS,
                              f"邮箱 '{request.email}' 已被注册")

        user = user_pb2.UserResponse(
            id=self.next_id, name=request.name, email=request.email
        )
        self.db[self.next_id] = user
        self.next_id += 1
        print(f"[创建] {user.name} (ID={user.id})")
        return user

    def GetUser(self, request, context):
        if request.id <= 0:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT,
                          f"ID 必须为正数: {request.id}")
        if request.id not in self.db:
            context.abort(grpc.StatusCode.NOT_FOUND,
                          f"用户 {request.id} 不存在")
        return self.db[request.id]

    def ListUsers(self, request, context):
        for u in self.db.values():
            yield u

    def BatchCreateUsers(self, request_iterator, context):
        created, errors = [], []
        for req in request_iterator:
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

    def Chat(self, request_iterator, context):
        import time
        for msg in request_iterator:
            yield user_pb2.ChatMessage(
                user="Server", text=f"已收到: {msg.text}",
                timestamp=time.strftime("%H:%M:%S")
            )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("🚀 gRPC 服务已启动（带错误处理）: [::]:50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
