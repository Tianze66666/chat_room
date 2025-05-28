# import asyncio
#
# async def client_handler(reader,writer):
#     print("连接成功")
#     while True:
#         try:
#             data = await reader.read(1024)
#             if not data :
#                 break
#             writer.write(data.upper())
#             await writer.drain()
#         except ConnectionResetError:
#             break
#     writer.close()
#
# async def run_server():
#     print("服务器启动")
#     server = await asyncio.start_server(client_handler,"127.0.0.1",8081)
#     async with server:
#         await server.serve_forever()
#
# asyncio.run(run_server())

# from conf.settings import *
# class Text():
#     def __enter__(self):
#         return self
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         if not exc_type is None:
#             ERROR_LOGGER.error("{}: {} {}".format(
#                 exc_type.__name__, exc_val, exc_tb.tb_frame
#             ))

# with Text() as t:
#     t.xxx
#
# print("aaaa")

# import os
# print(os.cpu_count())
li = [i for i in range(10)]
print(li)