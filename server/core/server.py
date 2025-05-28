'''
核心逻辑
'''
from lib.common import *
from core.urls import route_mode
from multiprocessing import Process,Manager
import asyncio


class ChatServer:
    def __init__(self,host="127.0.0.1",port=3001,q_list=None,idx=0,users_list=None):
        self.host = host
        self.port = port
        MyConn.q_list = q_list
        MyConn.bcst_q = q_list[idx]
        MyConn.users_list = users_list
        asyncio.run(asyncio.wait([self.run_server(),MyConn.send_all()]))

        asyncio.create_task(self.run_server())
    async def client_handler(self,reader,writer):
        LOGGER.debug(f"<用户连接>进程号:{os.getpid()}  端口号:{self.port}")
        async with MyConn(reader,writer) as conn:
            while True:
                request_dic = await conn.recv()
                fn = route_mode.get(request_dic.get("mode"))
                await fn(conn,request_dic)

    async def run_server(self):
        server = await asyncio.start_server(self.client_handler,self.host,self.port)
        async with server:
            LOGGER.info("服务端启动{}:{}".format(self.host,self.port))
            await server.serve_forever()

def run():
    # cpu_count = os.cpu_count()
    cpu_count=1 #10
    users_list = Manager().list()
    q_list = [Queue()for _ in range(cpu_count)]
    for i in range(1,cpu_count):
        Process(target=ChatServer,args=(HOST,PORT+i,q_list,i,users_list)).start()
    ChatServer(HOST,PORT+cpu_count,q_list,0,users_list)



