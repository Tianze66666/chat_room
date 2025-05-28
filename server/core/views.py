
from db.models import User
from lib.common import *

async def register(conn,request_dic,*args,**kwargs):
    '''
    注册接口
    :param conn:
    :param request_dic:
    :param args:
    :param kwargs:
    :return:
    '''
    LOGGER.debug("开始注册")
    user = request_dic.get("user")
    pwd = request_dic.get("pwd")
    if await User.select(user):
        #组织注册失败响应字典并发送
        response_dic = ResponseData.register_error_dic(f"用户:{user}已存在，请更换用户名")
        await conn.send(response_dic)
        return
    user_obj = User(user,pwd)
    await user_obj.save()
    #组织注册成功字典并发送
    response_dic = ResponseData.register_success_dic(f"用户:{user}注册成功")
    await conn.send(response_dic)


async def login(conn,request_dic,*args,**kwargs):

    '''
    登录接口
    :param conn:
    :param request_dic:
    :param args:
    :param kwargs:
    :return:
    '''
    user = request_dic.get("user")
    pwd = request_dic.get("pwd")
    LOGGER.debug(f"用户{user}开始登录")
    user_obj = await User.select(user)
    if not user_obj or user_obj.pwd != pwd:
        LOGGER.debug(f"用户{user}登录失败,用户名或密码错误")
        response_dic = ResponseData.login_error_dic(user,"登录失败,用户名或密码错误")
        await conn.send(response_dic)
        return
    if user in conn.users_list:
        LOGGER.debug(f"用户{user}登录失败,已经在线")
        response_dic = ResponseData.login_error_dic(user,"请不要重复登录")
        await conn.send(response_dic)
        return

    LOGGER.debug(f"用户{user}登录成功")
    #保存当前的sonn对象
    conn.users_list.append(user)
    conn.online_users[user] = conn
    conn.name = user
    conn.token = generate_token(user)
    LOGGER.info(f"【{user}】进入了")
    response_dic = ResponseData.login_success_dic(user,"登录成功",conn.token)
    await conn.send(response_dic)
    #广播消息
    broadcast_dic = ResponseData.online_dic(user)

    await conn.put_q(broadcast_dic)


async def reconnect(conn,request_dic,*args,**kwargs):
    """
    重连接口
    :param conn:
    :param request_dic:
    :return:
    """
    LOGGER.debug(f"用户{request_dic.get('user')}开始重连")
    token = request_dic.get("token")
    user = request_dic.get("user")
    if generate_token(user) != token:
        response_dic = ResponseData.reconnect_error_dic("token无效")
        await conn.send(response_dic)
        return
    if user in conn.online_users:
        LOGGER.debug(f"用户{user}登录失败,已经在线")
        response_dic = ResponseData.reconnect_error_dic("已经在其他地方登录")
        await conn.send(response_dic)
        return

    conn.users_list.append(user)
    conn.online_users[user] = conn
    conn.name = user
    conn.token = token
    LOGGER.info(f"【{user}】进入聊天室")
    response_dic = ResponseData.reconnect_success_dic()
    await conn.send(response_dic)

    #广播消息
    broadcast_dic = ResponseData.online_dic(user)

    await conn.put_q(broadcast_dic)


async def chat(conn,request_dic,*args,**kwargs):
    '''
    聊天接口
    :param conn:
    :param request_dic:
    :param args:
    :param kwargs:
    :return:
    '''

    token = request_dic.get("token")
    user = request_dic.get("user")
    msg = request_dic.get("msg")
    if token != conn.token:
        conn.close()
        return
    MSG_LOGGER.debug(f"{user}说:{msg}")
    response_dic = ResponseData.chat_dic(request_dic)
    await conn.put_q(response_dic)


async def file(conn,request_dic,*args,**kwargs):
    '''
    文件接口
    :param conn:
    :param request_dic:
    :param args:
    :param kwargs:
    :return:
    '''
    token = request_dic.get("token")
    if token != conn.token:
        conn.close()
        return
    user = request_dic.get("user")
    file_name = request_dic.get("file_name")
    MSG_LOGGER.info("{}发了文件{}".format(user,file_name))
    response_dic = ResponseData.file_dic(request_dic)
    await conn.put_q(response_dic)




