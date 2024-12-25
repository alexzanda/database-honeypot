# coding：utf-8
import bson

# 在arm环境下，没有bson.decode_all方法，只有bson.loads

OP_REPLY = 1
OP_MESSAGE = 1000
OP_UPDATE = 2001
OP_INSERT = 2002
OP_RESERVED = 2003
OP_QUERY = 2004
OP_GET_MORE = 2005
OP_DELETE = 2006
OP_KILL_CURSORS = 2007
OP_COMMAND = 2010
OP_COMMANDREPLY = 2011
OP_COMPRESSED = 2012
OP_MSG = 2013

OPCODE_MAP = {
    OP_REPLY:  "Reply",
    OP_MESSAGE: "Message",
    OP_UPDATE:  "Update document",
    OP_INSERT:  "Insert document",
    OP_RESERVED: "Reserved",
    OP_QUERY:  "Query",
    OP_GET_MORE:  "Get More",
    OP_DELETE:  "Delete document",
    OP_KILL_CURSORS:  "Kill Cursors",
    OP_COMMAND:  "Command Request",
    OP_COMMANDREPLY:  "Command Reply",
    OP_COMPRESSED:  "Compressed Data",
    OP_MSG:  "Extensible Message Format"
}

init_bytes = [
    # b"MongoDB Internal Client",
    b"whatsmyuri",
    b"buildinfo",
    b"buildInfo",
    # b"serverStatus",
    # b"startupWarnings",
    # b"isMaster",
    b"replSetGetStatus"
]

def bson_decode(data):
    try:
        return bson.decode_all(data)
    except:
        return bson.loads(data)


def mongo_payload_decoder(data: bytes):
    """mysql payload解码
    客户端到服务端的消息类型有两类，认证和命令执行，格式为：3字节包长度+1字节包序号+内容
    客户端认证类型，由于是回复服务端的greeting，packet为1，辅以包内容进行判断
    客户端命令类型：1
    """
    # print(f"length: {len(data)}, origin data: ", data)
    data_type, data_decoded = "", ""
    if len(data) < 16:
        return "", ""

    # 过滤掉客户端初次连接时生成的一些内部查询信息

    for item in init_bytes:
        if item in data:
            print("filter init query")
            return "", ""

    try:
        # 读取消息长度、request id、response to、opcode
        message_length = int.from_bytes(data[0:4], "little")
        request_id = data[4:8]
        response_to = data[8:12]
        op_code = int.from_bytes(data[12:16], "little")

        print(f"message length: {message_length}, op_code: {op_code}")

        # 根据opcode来进一步处理
        if op_code == OP_QUERY:
            return handle_op_query(data)
        if op_code == OP_MSG:
            return handle_op_msg(data[20:])

        # 切换数据库的操作，手动补上use
        return data_type, data_decoded
    except Exception as e:
        print(f"decode error: {e}")
        return data_type, data_decoded


def handle_op_query(data: bytes):
    """2004"""
    # 读取query flag
    query_flags = data[16:20]

    # 读取full collection name，读到\x00为止
    left_data_len = len(data[20:])
    start_index = 20
    full_col_bytes = b""
    for index in range(left_data_len):
        item = data[start_index + index:start_index + index + 1]
        if item != b"\x00":
            full_col_bytes += item
        else:
            break
    # print(f"---- get full collection name: ", str(full_col_bytes))

    # number to skip, 4 bytes
    number_to_skip_start = 20 + len(full_col_bytes) + 1
    number_to_skip_end = 20 + len(full_col_bytes) + 5

    # number to return, 4 bytes
    number_to_return_start = number_to_skip_end
    number_to_return_end = number_to_return_start + 4

    # query data
    query_data = data[number_to_return_end:]
    query_data_dict = bson_decode(query_data)
    # print(f"get query data: {query_data_dict}")

    return "cmd", str(query_data_dict)


def handle_op_msg(data: bytes):
    """2013 section kind 有0 1 2三种"""
    # 记录当前命令的行为，包括执行命令的类型（对应到seqid，有documents,updates,deletes三种）、命令参数、目标数据库
    ops = []
    readed_data_len = 0
    while True:
        if readed_data_len == len(data):
            break
        # 剩余数据，可能由多个section组成

        # 分析sections，先读一个字节，判断当前位置section kind
        section_kind = data[:1]
        # print(f"---- get section kind: {section_kind}")

        # 这种section类型为document sequence 类型，这种类型里会有多个文档序列
        # 其结构组成为Kind（1字节）+ Size（4字节）+ Seqid（若干字节，读到\x00即可）+ DocumentSequence
        # DocumentSequence中就是多个可直接被bson解码的document
        # document的组成为Document length(4字节) + Elements
        if section_kind == b"\x01":
            size = int.from_bytes(data[1:5], "little")
            # print(f"get document sequence section size: {size}")

            # 读取SeqID(只需要按顺序读到\x00即可)
            seqid = b""
            i = 0
            while True:
                cur_byte = data[5+i: 5+i+1]
                if cur_byte == b"\x00":
                    break
                seqid += cur_byte
                i += 1
            # print(f"get document sequence seqid: {seqid}")
            ops.append(f"action type: {seqid.decode()}")

            # 获取此section的document sequences，一个序列里可能有多个document，每个document都由4字节length+主体elements+一个字节的\x00
            current_section_data = data[:size+1]
            document_sequences = current_section_data[1+4+len(seqid)+1:]
            # print(f"get current document sequence: {document_sequences}")

            readed_document_len = 0
            while True:
                if readed_document_len == len(document_sequences):
                    break
                document_len = int.from_bytes(document_sequences[readed_document_len:4], "little")
                document = document_sequences[readed_document_len:document_len]
                element_dict = {}
                try:
                    # TODO 如果客户端在插入一条记录时，并没有指定_id而是使用默认的ObjectId, bson解码会出错
                    element_dict = bson_decode(document)
                except Exception as e:
                    print(f">>>> decode kind 1 element error: {e}")
                ops.append(element_dict)
                # print(f"get kind 1 document element: {element_dict}")
                readed_document_len += document_len

            # 读完一个section，统计当前section的长度，偏移读取的下标
            readed_data_len = readed_data_len +1 + size
            data = data[readed_data_len:]

        # 这种section类型里面就只有一个简单的文档序列
        # 其结构组成为Kind(1字节)+BodyDocument(可直接被bson解析)
        elif section_kind == b"\x00":
            # 读取4个字节，获取文档长度
            document_len = int.from_bytes(data[:4], "little")
            element_dict = {}
            try:
                element_dict = bson_decode(data[1:document_len])
            except Exception as e:
                print(f">>>> decode kind 0 element error: {e}")
            ops.append(element_dict)
            # print(f"get kind 0 document element: {element_dict}")
            readed_data_len = readed_data_len + 1 + document_len
            data = data[readed_data_len:]
        else:
            break

    # 由于更新一个集合时，实际产生了多个文档，而数据中的更新element在前，所属数据库element在后，为了便于理解，将elements反转
    ops.reverse()
    # print(f"get op msg: {str(ops)}")

    return "cmd", str(ops)