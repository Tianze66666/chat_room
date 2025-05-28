'''
公共方法
'''
from conf.settings import *
import hashlib
import datetime

import os
from PyQt6.QtWidgets import QMessageBox

#密码加密
def hash_pwd(pwd):
    hash = hashlib.sha256()
    hash.update(pwd.encode("utf-8"))
    #密码加盐
    hash.update("12345679".encode("utf-8"))
    return hash.hexdigest()

# 获取当前时间
def get_time():
    return datetime.datetime.now().replace(microsecond=0)

#获取文件信息
def get_file_info(file_path):
    file_name = os.path.basename(file_path)

    hash_obj = hashlib.md5()
    with open(file_path,"rb") as f:
        f.seek(0,2)
        file_size = f.tell()
        one_tenth = file_size // 10
        for i in range(10):
            f.seek(i*one_tenth)
            res = f.read(100)
            hash_obj.update(res)
        return file_name,file_size,hash_obj.hexdigest()

#字节进制转换
def byte_to_human(size):
    units = ["B","KB","MB","GB","TB","PB"]
    for unit in units:
        if size < 1024 or unit == "PB":
            return f"{size:.2f} {unit}"
        size /= 1024

#组织请求格式类
class RequestData:
    @staticmethod
    def register_dic(user,pwd,*args,**kwargs):
        """
        组织注册字典
        :param user:
        :param pwd:
        :param args:
        :param kwargs:
        :return:
        """
        request_dic = {
            "mode": REQUEST_REGISTER,
            "user": user,
            "pwd": hash_pwd(pwd)
        }
        return request_dic

    @staticmethod
    def login_dic(user, pwd, *args, **kwargs):
        """
        组织登录请求字典
        :param user:
        :param pwd:
        :param args:
        :param kwargs:
        :return:
        """
        request_dic = {
            "mode": REQUEST_LOGIN,
            "user": user,
            "pwd": hash_pwd(pwd)
        }
        return request_dic

    @staticmethod
    def chat_dic(user,msg,token,*args,**kwargs):
        """
        组织聊天字典
        :param user:
        :param msg:
        :param token:
        :param args:
        :param kwargs:
        :return:
        """
        requset_dic = {
            "mode": REQUEST_CHAT,
            "user": user,
            "msg": msg,
            "time": get_time(),
            "token": token,
        }
        return requset_dic

    @staticmethod
    def file_dic(user,file_path,token,*args,**kwargs):
        '''
        组织文件字典
        :return:
        '''
        file_name , file_size, file_md5 = get_file_info(file_path)
        requset_dic = {
            'mode': REQUEST_FILE,
            'user': user,
            'file_name': file_name,
            'file_size': file_size,
            'file_md5': file_md5,
            "time": get_time(),
            "token": token,
            "file_path":file_path
        }
        return requset_dic

    @staticmethod
    def reconnect_dic(user,token,*args,**kwargs):
        '''
        组织重连字典
        :param user:
        :param token:
        :param args:
        :param kwargs:
        :return:
        '''
        request_dic = {
            'mode': REQUEST_RECONNECT,
            "user": user,
            "token": token
        }
        return request_dic


#重连处理装饰器
def reconnect(fn):
    def wrapper(*args,**kwargs):
        self = args[0]

        try:
            res = fn(*args,**kwargs)
        except Exception as e:
            LOGGER.error("连接断开，正在重连......{}".format(e))


            self.tip_label.setText("连接断开，正在重连.....")
            self.tip_label.adjustSize()
            self.tip_label.setFixedSize(self.tip_label.size())

            self.tip_label.show()

            x = self.geometry().center().x()
            y = self.geometry().center().y()

            self.tip_label.move(int(x - (self.tip_label.width() / 2)),
                                int((y - self.tip_label.height() / 2)))  # 要传入int类型参数
            self.client.close()
            res = self.client.connect()
            if res:
                LOGGER.debug("重连成功")
                self.tip_label.close()
                return
            QMessageBox.warning(self,"提示","连接服务器失败，即将关闭程序")
            exit()
        return res
    return wrapper


def reconnect_t(fn):
    def wrapper(*args,**kwargs):
        self = args[0]
        try:
            res = fn(*args,**kwargs)
        except Exception as e:
            LOGGER.error("连接断开，正在重连......_ttt{}".format(e))
            #给主线程发信号

            self.reconnected.emit("show_tip")

            self.client.close()

            res = self.client.connect()

            if res:

                LOGGER.debug("重连成功")
                self.reconnected.emit("close_tip")
                return
            self.reconnected.emit("over")

            # time.sleep(0.5)
            self.terminate()
            # exit()
        return res
    return wrapper