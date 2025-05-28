'''
核心逻辑
'''
import os
from lib.common import *
import socket
import datetime
import re
import pickle
import queue
from ui.login import Ui_Form as LoginUiMixin
from ui.chat import Ui_Form as ChatUiMixin
from PyQt6.QtGui import QDropEvent,QImage
from PyQt6.QtWidgets import QApplication,QWidget,QMessageBox,QLabel,QListWidgetItem,QTextEdit,QFileIconProvider
from PyQt6.QtCore import Qt,QCoreApplication,QThread,pyqtSignal,QTimer,QMargins,QFileInfo



class Mysocket:
    def __init__(self,host="127.0.0.1",port=9000):
        self.host = host
        self.port = port
        self.user = None
        self.token = None
        self.socket = None

    def recv(self,reve_len):
        return self.socket.recv(reve_len)

    def send(self,data):
        self.socket.send(data)

    def recv_data(self):
        len_bytes = self.recv(PROTOCOL_LENGTH)
        if not len_bytes:
            raise ConnectionResetError
        stream_len = int.from_bytes(len_bytes,byteorder="big")
        dic_bytes = bytes()
        while stream_len > 0:
            if stream_len <4096:
                temp = self.recv(stream_len)
            else:
                temp = self.recv(4096)
            if not temp:
                raise ConnectionResetError
            dic_bytes += temp
            stream_len -= len(temp)
        response_dic = pickle.loads(dic_bytes)
        if response_dic.get("mode") != REQUEST_FILE:
            LOGGER.debug("接收回复字典成功")
            return response_dic
        #接收文件数据
        return self.recv_file(response_dic)

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


    def recv_file(self,response_dic):
        LOGGER.debug("开始接收文件")
        file_size = response_dic.get("file_size")
        now_date = datetime.datetime.now().strftime("%Y-%m")
        file_dir = os.path.join(FILE_DIR, now_date)
        if not os.path.isdir(file_dir):
            os.mkdir(file_dir)
        file_name = response_dic.get("file_name")
        file_path = os.path.join(file_dir, file_name)
        while True:
            if os.path.exists(file_path):
                file_name = self.rename(file_name)
                file_path = os.path.join(file_dir, file_name)
            else:
                response_dic["file_name"] = file_name
                break
        with open(file_path, "wb") as f:
            while file_size > 0:
                if file_size < 4096:
                    temp = self.recv(file_size)
                else:
                    temp = self.recv(4096)
                if not temp:
                    raise ConnectionResetError
                f.write(temp)
                file_size -= len(temp)
            response_dic["file_path"] = file_path
        return response_dic

    def send_data(self,dic):
        file_path = dic.pop("file_path",0)
        #将dic转成二进制，并且将dic的长度转成固定8个自己的二进制
        dic_bytes = pickle.dumps(dic)
        len_bytes = len(dic_bytes).to_bytes(PROTOCOL_LENGTH,byteorder="big")
        self.send(len_bytes)
        self.send(dic_bytes)
        LOGGER.debug("发送请求字典完成")
        #如果请求模式不是发送文件则结束
        if dic.get("mode") != REQUEST_FILE:
            return
        #发送文件
        with open(file_path,"rb") as f :
            while True:
                temp = f.read(4096)
                if not temp:
                    break #文件读完则返回
                self.send(temp)


    def connect(self):
        for i in range(1,3):
            try:
                LOGGER.debug(f"开始第{i}次连接服务器")
                self.socket = socket.socket()
                self.socket.connect((self.host,self.port))
                return True
            except Exception as e:
                ERROR_LOGGER.error(f"第{i}次连接服务器失败:{e}")
                self.socket.close()


    def close(self):
        self.socket.close()

    def __enter__(self):
        if self.connect():
            LOGGER.debug("连接服务器成功")
            return self
        else:
            exit()
            # return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class LoginWindow(LoginUiMixin,QWidget):
    def __init__(self,client):
        super(LoginWindow, self).__init__()
        self.client = client
        self.setupUi(self)
        self.stackedWidget.setCurrentIndex(0)
        self.chat_window = None
        self.test()
        self.tip_label = QLabel()
        self.tip_label.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.tip_label.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.tip_label.setStyleSheet("background-color:gray")

    @reconnect
    def get(self,dic):
        self.client.send_data(dic)  #发送数据
        # 等待接收注册结果
        response_dic = self.client.recv_data() #接收数据
        return response_dic

    def login(self):
        LOGGER.debug("用户登录")
        user = self.lineEdit.text().strip()
        pwd = self.lineEdit_2.text().strip()
        if not user or not pwd :
            QMessageBox.warning(self, "警告", "用户名或密码不能为空")
            return
        if not self.checkBox.isChecked():
            QMessageBox.warning(self, "警告", "请勾选服务协议")
            return

        request_dic = RequestData.login_dic(user, pwd)
        response_dic = self.get(request_dic)
        if not response_dic:
            return  # 没有数据并且重连成功,重新点注册
        if response_dic.get("code") != 200:
            QMessageBox.about(self, "提示", response_dic.get("msg"))
            LOGGER.debug("用户登录失败")
            return  # 注册失败返回
        self.client.user = user
        self.client.token = response_dic.get("token")
        notice = response_dic.get("notice")
        users = response_dic.get("users")
        LOGGER.debug("用户登录成功")
        #打开聊天窗口，关闭登录窗口
        self.chat_window = ChatWindow(self,notice,users)
        self.chat_window.show()
        self.close()

    def register(self):
        LOGGER.debug("用户注册")
        user = self.lineEdit_3.text().strip()
        pwd = self.lineEdit_4.text().strip()
        re_pwd = self.lineEdit_5.text().strip()
        if not user or not pwd or not re_pwd:
            QMessageBox.warning(self,"警告","用户名或密码不能为空")
            return
        if pwd != re_pwd:
            QMessageBox.warning(self,"警告","两次密码不等")
            return
        request_dic = RequestData.register_dic(user,pwd)
        response_dic = self.get(request_dic)
        if not response_dic:
            return #没有数据并且重连成功,重新点注册
        QMessageBox.about(self,"提示",response_dic.get("msg"))
        if response_dic.get("code") != 200:
            return #注册失败返回
        self.lineEdit_3.clear()
        self.lineEdit_4.clear()
        self.lineEdit_5.clear()
        self.lineEdit.setText(user)
        self.label_2.setFocus()
        self.open_login_page()

    def open_login_page(self):
        LOGGER.debug("打开登录界面")
        self.stackedWidget.setCurrentIndex(0)

    def open_register_page(self):
        LOGGER.debug("打开注册界面")
        self.stackedWidget.setCurrentIndex(1)

    def protocol(self):
        LOGGER.debug("打开用户协议页面")
        QMessageBox.about(self,"服务协议","6666666666666666666666")

    def test(self):
        if LEVEL == "DEBUG":
            self.lineEdit.setText("tian")
            self.lineEdit_2.setText("123")
            self.checkBox.setChecked(True)
            self.lineEdit_2.setFocus()


class ChatWindow(ChatUiMixin,QWidget):
    _translate = QCoreApplication.translate

    def __init__(self,login_window,notice,users):
        super(ChatWindow, self).__init__()
        self.client = login_window.client
        self.users = users
        self.login_window = login_window
        self.setupUi(self)
        self.label.close()
        self.textEdit_2.setText(notice)
        self.textBrowser.clear()
        self.textEdit.clear()
        self.set_online_users(users)
        self.tip_label = QLabel()
        self.tip_label.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.tip_label.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.tip_label.setStyleSheet("background-color:gray")

        #拿到71年的本地时间
        self.last_time = datetime.datetime.utcfromtimestamp(0).replace(tzinfo=datetime.timezone.utc).astimezone().replace(tzinfo=None)

        self.route_mode = {
            "reconnect":self.reconnect_res,
            "broadcast":self.broadcast_res,
            "chat":self.chat_res,
            "file":self.file_res
        }
        self.signal_route = {
            "show_tip":self.show_tip,
            "close_tip":self.tip_label.close,
            "over":self.over
        }
        self.my_thread = MyThread(self.client)
        self.my_thread.reconnected.connect(self.t_signal)
        self.my_thread.received.connect(self.dic_handle)
        self.my_thread.start()

        #设置计时器并给计时器连接槽函数
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.close_broadcast)
        self.textEdit.returnPressed.connect(self.send_msg)

        #新建一个发消息的线程
        self.request_q  = queue.Queue()
        self.send_thread = MyThread(self.client,self.request_q)
        self.send_thread.send_success.connect(self.send_success)
        self.send_thread.start()

        self.textBrowser.setViewportMargins(QMargins(0,0,8,0))
        self.textBrowser.anchorClicked.connect(self.open_url)
        self.textEdit.drop_event.connect(self.confirm_send)

    # 消息发送成功，渲染消息
    def send_success(self,request_dic):
        self.append_time(request_dic.get("time"))
        if request_dic.get("mode") == REQUEST_FILE:
            self.show_file(request_dic, "right", USER_COLOR)
            return

        msg = request_dic.get("msg")
        self.textEdit.setText("")
        self.show_msg("我",msg,"right",USER_COLOR)


    @reconnect
    def put(self,request_dic):
        self.client.send_data(request_dic)
        return True

    @staticmethod
    def open_url(q_url):
        system_name = os.name
        if system_name == "posix":#如果是mac或者linx系统
            os.system("open '{}'".format(q_url.toLocalFile()))
        elif system_name == "nt":
            fixed_path = q_url.toLocalFile().replace("//d", "D:").replace("/", "\\")
            os.system('start "" "{}"'.format(fixed_path))

    @staticmethod
    def get_icon(url):
        icon_path = os.path.join(IGM_DIR,"{}.png".format(url.split(".")[-1]))
        if os.path.isfile(icon_path):
            return icon_path
        file_info = QFileInfo(url)
        file_icon = QFileIconProvider().icon(file_info)

        file_icon.pixmap(200).save(icon_path)
        return icon_path

    def confirm_send(self,urls):
        files_info = "\n"
        for url in urls:
            file_name = os.path.basename(url)
            file_size = byte_to_human(os.path.getsize(url))
            files_info = "{}{} {}\n".format(files_info,file_name,file_size)
        files_info = "{}\n是否发送".format(files_info)
        res = QMessageBox.question(self,"发送文件",files_info,QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if res == QMessageBox.StandardButton.No:
            return
        #开始发送文件
        self.send_files(urls)

    def send_files(self,urls):
        for url in urls:
            request_dic = RequestData.file_dic(self.client.user,url,self.client.token)
            self.request_q.put(request_dic)

    def show_msg(self,user,msg,align,color):
        self.cursor_end()
        self.textBrowser.insertHtml(f'''
                <tr style="text-align:{align}">
                <p>
                <a style="color:{color}">{user}</a>
                <br>
                <a style="{MSG_COLOR}">{msg}</a>
                </p>
                </tr>
                ''')
        self.cursor_end()
        MSG_LOGGER.info(f"{user}说:{msg}")

    def send_msg(self):
        msg = self.textEdit.toPlainText().strip()
        if not msg:
            QMessageBox.warning(self,"警告","不能发空")
            return
        request_dic = RequestData.chat_dic(self.client.user,msg,self.client.token)
        # 将消息放入队列中准备发送
        self.request_q.put(request_dic)

    def dic_handle(self,response_dic):
        LOGGER.debug("收到响应字典，进入处理")
        code = response_dic.get("code")
        if code != 200:
            QMessageBox.warning(self,"提示",f"{response_dic.get('msg')}\n状态码：{code}")

        fn = self.route_mode.get(response_dic.get("mode"))
        fn(response_dic)

    def append_time(self,local_time):
        if (local_time - self.last_time).total_seconds()>INTERVAL:
            cursor = self.textBrowser.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.textBrowser.setTextCursor(cursor)
            self.textBrowser.insertHtml(f'''
            <tr style="text-align:center">
            <p>
            <a style="color:{TIME_COLOR}">{local_time}</a>
            </p>
            </tr>
            ''')
        self.last_time = local_time

    def cursor_end(self):
        cursor = self.textBrowser.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.textBrowser.setTextCursor(cursor)

    # D:\\pythonProject\\chat_room\\client\\datas\\2025 - 03\\身份证(1).docx
    # D: / desk / 身份证.docx
    def show_file(self,response_dic,align,color):
        self.cursor_end()
        user = response_dic.get("user")
        url = response_dic.get("file_path")
        html = '''
                                    <tr style="text-align:{}">
                                    <p>
                                    <a style="color:{}">{}</a>
                                    <br>
                                    <a href="file://{}">
                                    <img src="{}" width={}>
                                    </a>
                                    {}
                                    </p>
                                    </tr>
                                    '''
        if url.split(".")[-1] in IMG_TYPES:
            img_width = QImage(url).width()
            if img_width > 200:
                img_width = 200
            self.textBrowser.insertHtml(html.format(align,color, user, url, url, img_width, ""))
        else:
            # 进行文件的展示
            icon_path = self.get_icon(url)
            file_info_html = """
                        <br>
                        <a href="file:{}">[打开文件夹]</a>
                        <a href="file:{}">{} ({})</a>
                    """
            file_dir = os.path.dirname(url)
            file_name = response_dic.get("file_name")
            file_size = byte_to_human(response_dic.get("file_size"))
            self.textBrowser.insertHtml(html.format(align,color, user, url, icon_path, 100,
                                                    file_info_html.format(file_dir, url, file_name, file_size)))
        self.cursor_end()
        MSG_LOGGER.info(f"{user}发送了文件了文件:{response_dic.get('file_name')}")

    def file_res(self,response_dic,*args,**kwargs):
        url = response_dic["file_path"]
        url = url.replace("\\","/")
        response_dic["file_path"] = url
        utc_time = response_dic.get("time")
        local_time = utc_time.astimezone().replace(tzinfo=None)
        self.append_time(local_time)
        self.show_file(response_dic,"left",OTHER_USER_COLOR)

    def chat_res(self,response_dic,*args,**kwargs):
        user = response_dic.get("user")
        msg = response_dic.get("msg")
        utc_time = response_dic.get("time")
        local_time = utc_time.astimezone().replace(tzinfo=None)
        self.append_time(local_time)
        self.show_msg(user,msg,"left",OTHER_USER_COLOR)

    def reconnect_res(self,response_dic,*args,**kwargs):
        code = response_dic.get("code")
        if code != 200:
            QMessageBox.warning(self,"提示",f"{response_dic.get('msg')}\n状态码：{code}")
            self.login_window.show()
            self.close()
            return
        users = response_dic.get("users")
        self.set_online_users(users)

    def close_broadcast(self):
        self.label.close()
        self.timer.stop()

    def broadcast_res(self,response_dic,*args,**kwargs):
        print("--------",response_dic)
        user = response_dic.get("user")
        if response_dic.get("status") == REQUEST_ONLINE:
            if self.listWidget.findItems(user,Qt.MatchFlag.MatchExactly):
                return
            item = QListWidgetItem()
            self.listWidget.addItem(item)
            if user == self.client.user:
                user = "我"
            item.setText(self._translate("Form", user))
            self.label_3.setText(f"在线用户数:{self.listWidget.count()}")
            self.label.show()
            self.label.setText(f"{user}进入了聊天室")
        else:
            item = self.listWidget.findItems(user,Qt.MatchFlag.MatchExactly)[0]
            self.listWidget.takeItem(self.listWidget.row(item))
            self.label_3.setText(f"在线用户数:{self.listWidget.count()}")
            self.label.show()
            self.label.setText(f"{user}离开了聊天室")
        #启动计时器
        self.timer.start(5000)

    def set_online_users(self,users):
        self.listWidget.clear()
        self.label_3.setText(f"在线用户数:{str(len(users))}")
        for user in users:
            item = QListWidgetItem()
            self.listWidget.addItem(item)
            if user == self.client.user:
                user = "我"
            item.setText(self._translate("Form",user))

    def t_signal(self,s):
        self.signal_route.get(s)()

    def show_tip(self):

        self.tip_label.setText("连接断开，正在重连.....")
        self.tip_label.adjustSize()
        self.tip_label.setFixedSize(self.tip_label.size())
        x = self.geometry().center().x()
        y = self.geometry().center().y()
        self.tip_label.move(int(x-(self.tip_label.width()/2)),int((y-self.tip_label.height()/2))) #要传入int类型参数
        self.tip_label.show()

    def over(self):

        self.tip_label.close()
        QMessageBox.warning(self,"提示","连接服务器失败，即将关闭程序")
        self.close()

    def closeEvent(self, a0) -> None:
        self.my_thread.terminate()
        self.send_thread.terminate()
        super(ChatWindow, self).closeEvent(a0)


class MyThread(QThread):
    reconnected = pyqtSignal(str)
    received = pyqtSignal(dict)
    send_success = pyqtSignal(dict)

    def __init__(self,client,request_q=None):
        self.client = client
        self.request_q = request_q
        super(MyThread, self).__init__()

    def run(self):
        if self.request_q:
            self.loop_send()
            return
        self.loop_recv()

    @reconnect_t
    def put(self, dic):
        self.client.send_data(dic)
        return True

    def loop_recv(self):
        num = 0
        while True:
            response_dic = self.get()  # 如果收到的是空，说明连接断开重连成功了
            if not response_dic:
                while True:
                    request_dic = RequestData.reconnect_dic(self.client.user, self.client.token)
                    if not self.put(request_dic):  # 如果发送失败重连成功
                        continue
                    LOGGER.info("重连字典发送成功")
                    num += 1
                    if num > 3:
                        self.reconnected.emit("over")
                    break
                continue  # 处理重连问题
            num = 0
            self.received.emit(response_dic)

    def loop_send(self):
        num = 0
        while True:
            request_dic = self.request_q.get()
            url = request_dic.get("file_path")
            if not self.put(request_dic):#发送失败重连成功
                while True:
                    request_dic = RequestData.reconnect_dic(self.client.user, self.client.token)
                    if not self.put(request_dic):  # 如果发送失败重连成功
                        continue
                    LOGGER.info("重连字典发送成功")
                    num += 1
                    if num > 3:
                        self.reconnected.emit("over")
                    break
                continue
            num = 0
            request_dic["file_path"] = url
            self.send_success.emit(request_dic)

    @reconnect_t
    def get(self):
        return self.client.recv_data()


class MyTextEdit(QTextEdit):
    returnPressed = pyqtSignal()
    drop_event = pyqtSignal(list)
    def keyPressEvent(self, e) -> None:
        if e.key() == Qt.Key.Key_Return and not e.modifiers():
            self.returnPressed.emit()
            return
        super(MyTextEdit, self).keyPressEvent(e)

    def dropEvent(self, e: QDropEvent) -> None:
        urls = []
        q_urls = e.mimeData().urls()
        for q_url in q_urls:
            url = q_url.toLocalFile()
            if os.path.isfile(url):
                urls.append(url)
        if not urls:
            return
        self.drop_event.emit(urls)




def run():
    import sys
    #连接服务器
    with Mysocket(HOST,PORT) as client:
        #展示登录界面
        app = QApplication(sys.argv)
        loginwindow = LoginWindow(client)
        loginwindow.show()
        sys.exit(app.exec())