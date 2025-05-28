'''
公共方法
'''
import asyncio
import hashlib
import re
import aiofiles
from datetime import datetime,timezone
from conf.settings import *
from multiprocessing import Queue
import pickle


#生成token
def generate_token(user):
    hash_obj = hashlib.sha256()
    hash_obj.update(user.encode("utf-8"))
    hash_obj.update(str(datetime.now().date()).encode("utf-8"))
    hash_obj.update("天泽1344".encode("utf-8"))
    return hash_obj.hexdigest()

def get_utc_time():
    utc_time = datetime.utcnow().replace(microsecond=0,tzinfo=timezone.utc)
    return utc_time

class ResponseData:
    @staticmethod
    def register_success_dic(msg, *args, **kwargs):
        '''
        组织注册成功字典
        :param msg:
        :param args:
        :param kwargs:
        :return:
        '''
        response_dic = {
            "code": RESPONSE_SUCCESS_CODE,
            "mode": RESPONSE_REGISTER,
            "msg": msg
        }
        return response_dic

    @staticmethod
    def register_error_dic(msg, *args, **kwargs):
        '''
        组织注册失败字典
        :param msg:
        :param args:
        :param kwargs:
        :return:
        '''
        response_dic = {
            "code": RESPONSE_ERROR_CODE,
            "mode": RESPONSE_REGISTER,
            "msg": msg
        }
        return response_dic

    @staticmethod
    def login_success_dic(user,msg,token, *args, **kwargs):
        '''
        组织登录成功字典
        :param token:
        :param user:
        :param msg:
        :param args:
        :param kwargs:
        :return:
        '''
        response_dic = {
            "code": RESPONSE_SUCCESS_CODE,
            "mode": RESPONSE_LOGIN,
            "user": user,
            "msg": msg,
            "token": token,
            "notice": NOTICE,
            "users": tuple(MyConn.users_list)
        }
        return response_dic

    @staticmethod
    def login_error_dic(user,msg, *args, **kwargs):
        '''
        组织登录失败字典
        :param user:
        :param msg:
        :param args:
        :param kwargs:
        :return:
        '''
        response_dic = {
            "code": RESPONSE_ERROR_CODE,
            "mode": RESPONSE_LOGIN,
            "user":user,
            "msg": msg,
        }
        return response_dic

    @staticmethod
    def online_dic(user,*args, **kwargs):
        '''
        上线广播字典
        :param user:
        :param args:
        :param kwargs:
        :return:
        '''
        respoense_dic = {
            "code":RESPONSE_SUCCESS_CODE,
            "mode":RESPONSE_BROADCAST,
            "status":RESPONSE_ONLINE,
            "user":user
        }
        return respoense_dic

    @staticmethod
    def offline_dic(user,*args, **kwargs):
        '''
        下线广播字典
        :param user:
        :param args:
        :param kwargs:
        :return:
        '''
        respoense_dic = {
            "code":RESPONSE_SUCCESS_CODE,
            "mode":RESPONSE_BROADCAST,
            "status":RESPONSE_OFFLINE,
            "user":user
        }
        return respoense_dic

    @staticmethod
    def reconnect_success_dic(*args, **kwargs):
        '''
        重连成功字典
        :param args:
        :param kwargs:
        :return:
        '''
        response_dic = {
            "code":RESPONSE_SUCCESS_CODE,
            "mode":RESPONSE_RECONNECT,
            "users":tuple(MyConn.users_list)
        }
        return response_dic

    @staticmethod
    def reconnect_error_dic(msg,*args, **kwargs):
        '''
        重连失败字典
        :param args:
        :param kwargs:
        :return:
        '''
        response_dic = {
            "code":RESPONSE_ERROR_CODE,
            "mode":RESPONSE_RECONNECT,
            "msg":msg
        }
        return response_dic

    @staticmethod
    def chat_dic(response_dic,*args,**kwargs):
        """
        聊天字典
        :param dic:
        :param args:
        :param kwargs:
        :return:
        """
        response_dic.pop("token")
        response_dic["code"] = RESPONSE_SUCCESS_CODE
        response_dic["time"] = get_utc_time()
        return response_dic

    @staticmethod
    def file_dic(response_dic,*args,**kwargs):
        '''
        文件字典
        :param response_dic:
        :param args:
        :param kwargs:
        :return:
        '''
        response_dic.pop("token")
        response_dic["code"] = RESPONSE_SUCCESS_CODE
        response_dic["time"] = get_utc_time()
        return response_dic



class MyConn:
    online_users = {}
    bcst_q = None
    q_list = None
    users_list = None
    offline_users = []

    def __init__(self,reader,writer):
        self.reader = reader
        self.writer = writer

        self.name = None
        self.token = None

    async def write(self,bytes_data):
        self.writer.write(bytes_data)
        await self.writer.drain()

    async def send(self,dic):
        dic_bytes = pickle.dumps(dic)
        len_bytes = len(dic_bytes).to_bytes(PROTOCOL_LENGTH,byteorder="big")
        await self.write(len_bytes)
        await self.write(dic_bytes)
        LOGGER.debug("发送响应字典完成")
        if dic.get("mode") != RESPONSE_FILE:
            return


    @classmethod
    async def send_file(cls,dic,file_path):
        async with aiofiles.open(file_path,"rb") as f:
            while True:
                temp = await f.read(4096)
                if not temp:
                    break
                for conn in cls.online_users.values():
                    if conn.name == dic.get("user"):
                        continue
                    await conn.write(temp)


    @classmethod
    async def send_all(cls):
        loop = asyncio.get_running_loop()
        while True:
            dic = await loop.run_in_executor(None,cls.bcst_q.get)
            file_path = dic.pop("file_path",0)
            for conn in cls.online_users.values():
                if conn.name == dic.get("user"):
                    continue
                await conn.send(dic)
            #发送文件
            if dic.get("mode") == RESPONSE_FILE:
                await cls.send_file(dic,file_path)
            for user in cls.offline_users:
                cls.online_users.pop(user)
            cls.offline_users.clear()

    async def put_q(self,dic):
        loop = asyncio.get_running_loop()
        for q in self.q_list:
            await loop.run_in_executor(None,q.put,dic)



    async def read(self,recv_len):
        return await self.reader.read(recv_len)

    async def recv(self):
        len_bytes = await self.read(PROTOCOL_LENGTH)
        if not len_bytes:
            raise ConnectionResetError
        stream_len = int.from_bytes(len_bytes,byteorder="big")
        dic_bytes = bytes()
        while stream_len > 0:
            if stream_len < 4096:
                temp = await self.read(stream_len)
            else:
                temp = await self.read(4096)
            if not temp:
                raise ConnectionResetError
            dic_bytes += temp
            stream_len -= len(temp)
        request_dic = pickle.loads(dic_bytes)
        if request_dic.get("mode") != RESPONSE_FILE:
            return request_dic
        #继续接收文件数据
        return await self.recv_file(request_dic)

    @staticmethod
    def rename(file_name):
        base , ext = os.path.splitext(file_name)
        pattern = re.compile(r"\((d+)\)$")
        res = pattern.search(base)
        if res:
            num = int(res.group(1)) + 1
            base = pattern.sub("({})".format(num),base)
        else:
            base = "{}{}".format(base,"(1)")
        return "{}{}".format(base,ext)


    async def recv_file(self,request_dic):
        file_size = request_dic.get("file_size")
        now_date = datetime.now().strftime("%Y-%m")
        file_dir = os.path.join(FILE_DIR,now_date)
        if not os.path.isdir(file_dir):
            os.mkdir(file_dir)

        file_name = request_dic.get("file_name")
        file_path = os.path.join(file_dir,file_name)
        while True:
            if os.path.exists(file_path):
                file_name = self.rename(file_name)
                file_path = os.path.join(file_dir, file_name)
            else:
                break
        async with aiofiles.open(file_path,"wb") as f:
            while file_size > 0:
                if file_size<4096:
                    temp = await self.read(file_size)
                else:
                    temp =await self.read(4096)
                if not temp:
                    raise ConnectionResetError
                await f.write(temp)
                file_size -= len(temp)
            request_dic["file_path"] = file_path
        return request_dic

    async def offline(self):
        self.users_list.pop(self.users_list.index(self.name))
        # self.online_users.pop(self.name)
        self.offline_users.append(self.name)
        LOGGER.info(f"【{self.name}】离开了")
        response_dic = ResponseData.offline_dic(self.name)
        await self.put_q(response_dic)

    def close(self):
        self.writer.close()

    async def __aenter__(self):
        return self
                            #退出时的报错信息，错误提示信息，定位信息
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.close()
        if self.name:
            await self.offline()
        if exc_type is ConnectionResetError:
            return True
        if (not exc_type is None) and LEVEL != "DEBUG":
            ERROR_LOGGER.error("{}: {} {}".format(
                exc_type.__name__, exc_val, exc_tb.tb_frame
            ))
            return True


