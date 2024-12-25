# coding：utf-8

def mysql_payload_decoder(data: bytes):
    """mysql payload解码
    客户端到服务端的消息类型有两类，认证和命令执行，格式为：3字节包长度+1字节包序号+内容
    客户端认证类型，由于是回复服务端的greeting，packet为1，辅以包内容进行判断
    客户端命令类型：1
    """
    print(f"origin data: ", data)
    data_type, data_decoded = "", ""
    try:
        if len(data) <= 4:
            return "", ""

        # 判断是否为认证数据包
        if data[3:4] == b"\x01" and b"mysql_native_password" in data:
            data_type = "auth"
            # 从第36个字节开始读，读到第一次遇到的\x00，中间的就是用户名
            auth_datas = data[36:]
            auth_datas_len = len(auth_datas)
            bytes_username = b""
            for i in range(auth_datas_len):
                if auth_datas[i:i+1] == b"\x00":
                    break
                bytes_username += auth_datas[i:i+1]
            return "auth", bytes_username.decode()

        # 是命令执行的情况
        data_type = "sql"
        # 获取命令的类型
        com_type = data[4:5]

        # 退出mysql
        if com_type == b"\x01":
            return data_type, "exit"

        # 获取命令的主体数据，过滤掉不可打印字符
        data = data[5:]
        int_ascii_list = list(data)
        data_decoded = ""
        for i in int_ascii_list:
            if i < 32 or i >= 127:
                continue
            data_decoded += chr(i)

        # 切换数据库的操作，手动补上use
        if com_type == b"\x02":
            data_decoded = "use " + data_decoded
        return data_type, data_decoded
    except Exception as e:
        return data_type, data_decoded
