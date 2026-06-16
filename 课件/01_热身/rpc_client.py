import xmlrpc.client

# 连接远程服务器——只需要一个 URL！
proxy = xmlrpc.client.ServerProxy("http://localhost:8000")

# 注意下面两行：像不像调本地函数？
print(proxy.say_hello("小明"))         # 你好, 小明!
print(f"3 + 5 = {proxy.add(3, 5)}")   # 3 + 5 = 8
