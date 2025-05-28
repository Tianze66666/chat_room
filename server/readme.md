#
协议格式   
##
注册请求格式
{
    "mode":"register",
    "user":"tian",
    "pwd":123
}
##
登录请求格式
{
    "mode":"login",
    "user":"tian",
    "pwd":123
}
##
聊天请求格式
{
    "mode":"chat",
    "user":"fei",
    "msg":"hello",
    "time":"2025-5-1 12:00:00",
    "token":"asdasd"
}

##
文件请求格式
{
    'mode':'file',
    'user':'tian',
    'flie_name':'adb.txt',
    'file_size':5255,
    'file_md5':'sfasadasdas'
    "time":"2025-5-1 12:00:00",
    "token":"asdasd"
}

##
重连请求
{
    'mode':'reconnect',
    "user":"fei",
    "token":"asdasd"
}

##
注册响应格式
{
    "code":200,
    "mode":"register",
    "msg":"注册成功"
}
{
    "code":400,
    "mode":"register",
    "msg":"注册失败"
}
##
登录响应格式
{
    "code":200,
    "mode":"login",
    "user":"tian",
    "msg":"登录成功"
    "token":"adsaasfasd",
    "notice":"群公告",
    "users":("1","2","3")
}
{
    "code":400,
    "mode":"login",
    "user":"tian",
    "msg":"登录失败"
}
##
广播响应格式
{
    "code":200
    "mode":"broadcast",
    "status":"online",
    "user":"tian"
}
{
    "code":200
    "mode":"broadcast",
    "status":"offline",
    "user":"tian"
}
##
聊天响应格式
{
    "code":200,
    "mode":"chat",
    "user":"fei",
    "msg":"hello",
    "time":"2025-5-1 12:00:00",#世界标准时间
}

##
文件响应格式
{
    'code':200,
    'mode':'file',
    'user':'tian',
    'flie_name':'adb.txt',
    'file_size':5255,
    'file_md5':'sfasadasdas'
    "time":"2025-5-1 12:00:00",
}

##重连响应格式
重连请求
{
    'code':200,
    'mode':'reconnect',
    "users":("1","2","3")
}




