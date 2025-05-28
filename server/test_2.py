import socket

client = socket.socket()

try:
    client.connect(("127.0.0.1",8080))
    print("开始发送数据")
    while True:
        client.send("hello".encode("utf-8"))
        recv_data = client.recv(1024)
        print(recv_data)
        if not recv_data:
            break
except Exception:
    client.close()