'''
配置文件
'''
import logging.config
import os

#服务器地址配置
HOST = "120.26.129.26"
PORT = 9000


#协议配置
REQUEST_REGISTER = "register"
REQUEST_LOGIN = "login"
REQUEST_CHAT = "chat"
REQUEST_FILE = "file"
REQUEST_RECONNECT = "reconnect"
REQUEST_ONLINE = "online"
REQUEST_OFFLINE = "offline"
PROTOCOL_LENGTH = 8


#颜色配置
USER_COLOR = "green"
OTHER_USER_COLOR = "gray"
MSG_COLOR = "black"
TIME_COLOR = "gray"

#图片后缀名
IMG_TYPES = ["jpg","gpeg","png","gif","bmp"]

#隔多少秒刷新
INTERVAL = 5

#路径配置
BASE_DIR =os.path.dirname(
    os.path.dirname(__file__)
)
INFO_LOG_DIR = os.path.join(
    BASE_DIR,"log","info.log"
)
ERROR_LOG_DIR = os.path.join(
    BASE_DIR,"log","error.log"
)
MSG_LOG_DIR = os.path.join(
    BASE_DIR,"log","msg.log"
)
IGM_DIR = os.path.join(
    BASE_DIR,"imgs"
)
FILE_DIR = os.path.join(
    BASE_DIR,"datas"
)


LEVEL = "DEBUG"
LOGGING_DIC = {
    'version': 1.0,
    'disable_existing_loggers': False,
    # 日志格式
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(threadName)s:%(thread)d [%(name)s] %(levelname)s [%(pathname)s:%(lineno)d] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '%(asctime)s [%(name)s] %(levelname)s  %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'test': {
            'format': '%(asctime)s %(message)s',
        },
        'test1': {
            'format': '%(asctime)s %(message)s',
        },
    },
    'filters': {},
    # 日志处理器
    'handlers': {
        'console_debug_handler': {
            'level': LEVEL,  # 日志处理的级别限制
            'class': 'logging.StreamHandler',  # 输出到终端
            'formatter': 'simple'  # 日志格式
        },
        'file_info_handler': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',  # 保存到文件,日志轮转
            'filename': INFO_LOG_DIR,
            'maxBytes': 1024*1024*10,  # 日志大小 10M
            'backupCount': 10,  # 日志文件保存数量限制
            'encoding': 'utf-8',
            'formatter': 'standard',
        },
        'file_error_handler': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',  # 保存到文件,日志轮转
            'filename': ERROR_LOG_DIR,
            'maxBytes': 1024*1024*10,  # 日志大小 10M
            'backupCount': 10,  # 日志文件保存数量限制
            'encoding': 'utf-8',
            'formatter': 'standard',
        },
        'file_msg_handler': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',  # 保存到文件,日志轮转
            'filename': MSG_LOG_DIR,
            'maxBytes': 1024*1024*10,  # 日志大小 10M
            'backupCount': 10,  # 日志文件保存数量限制
            'encoding': 'utf-8',
            'formatter': 'standard',
        },

        'file_deal_handler': {
            'level': 'INFO',
            'class': 'logging.FileHandler',  # 保存到文件
            'filename': 'deal.log',  # 日志存放的路径
            'encoding': 'utf-8',  # 日志文件的编码
            'formatter': 'standard',
        },
        'file_operate_handler': {
            'level': 'INFO',
            'class': 'logging.FileHandler',  # 保存到文件
            'filename': 'operate.log',  # 日志存放的路径
            'encoding': 'utf-8',  # 日志文件的编码
            'formatter': 'standard',
        },
    },
    # 日志记录器
    'loggers': {
        '': {  # 导入时logging.getLogger时使用的app_name
            'handlers': ['console_debug_handler','file_info_handler'],  # 日志分配到哪个handlers中
            'level': 'DEBUG',  # 日志记录的级别限制
            'propagate': False,  # 默认为True，向上（更高级别的logger）传递，设置为False即可，否则会一份日志向上层层传递
        },
        'error_logger': {  # 导入时logging.getLogger时使用的app_name
            'handlers': ['file_error_handler','console_debug_handler'],  # 日志分配到哪个handlers中
            'level': 'ERROR',  # 日志记录的级别限制
            'propagate': False,  # 默认为True，向上（更高级别的logger）传递，设置为False即可，否则会一份日志向上层层传递
        },
        'msg_logger': {  # 导入时logging.getLogger时使用的app_name
            'handlers': ['file_msg_handler','console_debug_handler'],  # 日志分配到哪个handlers中
            'level': 'INFO',  # 日志记录的级别限制
            'propagate': False,  # 默认为True，向上（更高级别的logger）传递，设置为False即可，否则会一份日志向上层层传递
        },
    }
}

logging.config.dictConfig(LOGGING_DIC)
LOGGER = logging.getLogger("client")
ERROR_LOGGER = logging.getLogger("error_logger")
MSG_LOGGER = logging.getLogger("msg_logger")