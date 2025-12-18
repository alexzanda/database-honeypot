from typing import Tuple


def dameng_payload_decoder(data: bytes) -> Tuple[str, str]:
    """
    达梦数据库的payload解码器
    """
    data_type, data_decoded = "", ""
    offset = 0
    try:
        # 1、偏移4字节，读取两字节
        offset += 4
        # 协议版本号，占用两个字节
        protocol_version = data[offset:offset+2]
        offset += 2
        # 数据体长度，占用两个字节
        data_length_data = data[offset:offset+2]
        data_length = int.from_bytes(data_length_data, byteorder="little", signed=False)
        offset += 2
        # 认证类型
        if protocol_version == b"\x01\x00":
            offset += 56
            # 解出username
            username_length_data = data[offset:offset + 4]
            username_length = int.from_bytes(username_length_data, byteorder='little')
            offset += 4
            username = data[offset:offset+username_length]
            offset += username_length
            # 解出password
            password_length_data = data[offset:offset+4]
            password_length = int.from_bytes(password_length_data, byteorder='little')
            offset += 4
            password = data[offset:offset+password_length]
            offset += password_length
            # 解出客户端名称
            client_name_length_data = data[offset:offset+4]
            client_name_length = int.from_bytes(client_name_length_data, byteorder='little')
            offset += 4
            client_name = data[offset:offset+client_name_length]
            offset += client_name_length
            # 解出系统名称
            system_name_length_data = data[offset:offset+4]
            system_name_length = int.from_bytes(system_name_length_data, byteorder='little')
            offset += 4
            system_name = data[offset:offset+system_name_length]
            offset += system_name_length
            # 解出主机名称
            host_name_length_data = data[offset:offset+4]
            host_name_length = int.from_bytes(host_name_length_data, byteorder='little')
            offset += 4
            host_name = data[offset:offset+host_name_length]
            offset += host_name_length

            # 拼接认证信息
            # print(f"username: {username}")
            # print(f"password: {password}")
            # print(f"client_name: {client_name}")
            # print(f"system_name: {system_name}")
            # print(f"host_name: {host_name}")
            # data_decoded = f"{username.decode()}/{password.decode()}/{client_name.decode()}/{system_name.decode()}/{host_name.decode()}"
            # 用户名和密码是加密的，暂时解不出来
            data_decoded = f"client_name: {client_name.decode()}, system_name: {system_name.decode()}, host_name: {host_name.decode()}"
            data_type = "auth"
            # 解除认证的信息
            return data_type, data_decoded
        # sql查询类型
        elif protocol_version == b"\x05\x00":
            offset += 56
            # 解出sql语句
            sql = data[offset:offset+data_length]
            sql = sql.rstrip(b"\x00")
            data_type = "sql"
            return data_type, sql.decode()

        # 其他事件类型暂时忽略
        return "", ""
    except Exception as e:
        return data_type, data_decoded
