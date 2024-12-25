# coding：utf-8
def mssql_payload_decoder(data: bytes):
    """mssql payload解码"""
    data_type, data_decoded = "", ""
    try:
        # print(f"----- cl data: {data}")
        bytes_data = list(data)
        # print(f"----- cl_data bytes list: {list(data)}")
        data = data.replace(b'\x00', b'')
        data = data.replace(b'\x01', b'')
        int_ascii_list = list(data)
        decoded_data = ""
        for i in int_ascii_list:
            if i < 32 or i >= 127:
                continue
            decoded_data += chr(i)
        # print(f"----- cl_data decoded {decoded_data}")

        # 去掉首部的引号和逗号
        decoded_data = decoded_data.strip('"')
        decoded_data = decoded_data.strip(',')
        if bytes_data and bytes_data[0] == 18 and decoded_data and 'UMSSQLServerK' in decoded_data:
            return "auth", decoded_data

        if bytes_data and bytes_data[0] == 1 and decoded_data:
            return "sql", decoded_data
        return data_type, data_decoded
    except Exception as e:
        return data_type, data_decoded
