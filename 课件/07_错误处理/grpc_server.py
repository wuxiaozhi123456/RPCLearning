"""
第07课：错误处理 —— 改造后的服务端
演示两种方式: abort() 和 set_code()
运行: python grpc_server.py
"""
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
        # 方式1: abort() —— 直接抛出异常，后面的代码不执行
        if request.id <= 0:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT,
                          f"ID 必须为正数: {request.id}")
            # ↑ 这行之后的代码永远不会执行！

        # 方式2: set_code() —— 设置错误码，但继续执行，必须手动 return
        if request.id not in self.db:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"用户 {request.id} 不存在")
            return user_pb2.UserResponse()  # ← 必须手动返回一个空消息

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
