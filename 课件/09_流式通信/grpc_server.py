"""
第09课：流式通信 —— 服务端（三种流式）
运行: python grpc_server.py
"""
import grpc
import time
from concurrent import futures
import user_pb2, user_pb2_grpc

class UserService(user_pb2_grpc.UserServiceServicer):
    def __init__(self):
        self.db = {}
        self.next_id = 1

    # ---- 一元 RPC（创建几个数据供测试）----
    def CreateUser(self, req, ctx):
        u = user_pb2.UserResponse(id=self.next_id, name=req.name, email=req.email)
        self.db[self.next_id] = u
        self.next_id += 1
        return u

    def GetUser(self, req, ctx):
        if req.id not in self.db:
            ctx.abort(grpc.StatusCode.NOT_FOUND, f"用户 {req.id} 不存在")
        return self.db[req.id]

    # ===== 1. 服务端流式：yield 逐个推送 =====
    def ListUsers(self, req, ctx):
        print(f"[ListUsers] 推送 {len(self.db)} 个用户...")
        for uid, user in self.db.items():
            time.sleep(0.3)  # 模拟间隔推送
            yield user
        print("[ListUsers] 推送完成")

    # ===== 2. 客户端流式：收多个 -> 汇总返回 =====
    def BatchCreateUsers(self, req_iter, ctx):
        created, errors = [], []
        for req in req_iter:
            print(f"[BatchCreate] 收到: {req.name}")
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

    # ===== 3. 双向流式：读一条 -> 回一条 =====
    def Chat(self, req_iter, ctx):
        for msg in req_iter:
            print(f"[Chat] {msg.user}: {msg.text}")
            yield user_pb2.ChatMessage(
                user="Server",
                text=f"已收到: {msg.text}",
                timestamp=time.strftime("%H:%M:%S")
            )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("[gRPC] 流式通信服务已启动: [::]:50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
