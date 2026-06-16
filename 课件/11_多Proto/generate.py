"""
一键生成所有 proto 的 Python 代码
运行: python generate.py
"""
import subprocess
import glob

proto_files = glob.glob("protos/**/*.proto", recursive=True)

cmd = [
    "python", "-m", "grpc_tools.protoc",
    "-Iprotos",
    "--python_out=.",
    "--grpc_python_out=.",
] + proto_files

subprocess.run(cmd, check=True)
print(f"✅ 已生成 {len(proto_files)} 个 proto 的代码")
