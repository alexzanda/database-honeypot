# coding：utf-8
# forwarding test: l:80    r:10.20.129.189:80

# 本地开启socket监听指定端口
import os
import sys
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
#sys.path.append(os.getcwd())
import asyncio
import logging
from logging import handlers
from functools import wraps, partial
from inspect import isawaitable
from asyncio.streams import StreamReader, StreamWriter
from asyncio import ensure_future, Future, sleep
from netifaces import ifaddresses, AF_INET, AF_INET6
from argparse import ArgumentParser

from decoder.mongo_decoder import mongo_payload_decoder
from decoder.mssql_decoder import mssql_payload_decoder
from decoder.mysql_decoder import mysql_payload_decoder
from decoder.dameng_decoder import dameng_payload_decoder


def create_event_logger(name: str, log_level=logging.INFO):
    """创建事件日志记录器，此记录器仅会将原始内容记录到文件"""
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        th = handlers.RotatingFileHandler(f"{name}.log", maxBytes=5*1024*1024, backupCount=5)
        logger.addHandler(th)
        logger.setLevel(log_level)
    return logger


def launcher(func):
    """异步装饰器"""

    def coro_logger(func_name: str, future: Future):
        """协程异常捕获器"""
        try:
            future.set_result()
        except Exception as e:
            # create_logger("launcher_log").exception(f"uncaught exception in async function {func_name}, {e.__str__()}")
            pass

    @wraps(func)
    def wrapper(*args, **kwargs) -> object:
        result = func(*args, **kwargs)
        if isawaitable(result):
            task = ensure_future(result)
            task.add_done_callback(partial(coro_logger, func.__name__))
            result = task
        return result
    return wrapper


event_logger = create_event_logger("event")


payload_decoder_map = {
    1433: mssql_payload_decoder,  # mssql
    3306: mysql_payload_decoder,  # mysql
    4000: mysql_payload_decoder,  # tidb
    27017: mongo_payload_decoder,  # mongo
    5236: dameng_payload_decoder  # dameng
}


class Forwarder:
    """
    转发器
    """

    def __init__(self, proxy_port: int, target_ip: str, target_port: int):
        self.src_ip = None
        self.src_port = None
        self.ip = target_ip
        self.port = target_port
        self.proxy_port = proxy_port
        self.decoder = payload_decoder_map.get(self.proxy_port)

    async def handle_conn(self, cl_reader: StreamReader, cl_writer: StreamWriter):
        """
        客户端连接回调
        """
        # 开始建立到目标服务器的连接，并将流量发送到服务器
        ts_reader, ts_writer = await asyncio.open_connection(host=self.ip, port=self.port)
        print("***************  start handle connection...")
        src_ip, src_port = cl_writer.get_extra_info("peername")
        print(f"----src ip: {src_ip}, src port: {src_port}")
        # 在容器化环境中，docker的健康检查会从127.0.0.1发出，需要屏蔽掉
        if src_ip == "127.0.0.1":
            return

        # 循环接收服务器数据
        self._read_server_and_send_to_client(ts_reader, cl_writer)

        # 将客户端请求的数据转发给服务端
        await self._read_client_and_send_to_server(cl_reader, ts_writer)

    def get_bus_ip(self, iface: str, version: int = 4):
        """获取当前服务所在机器的业务ip，也即被代理钱的ip"""
        addresses = ifaddresses(iface)

        if version == 4:
            ipv4_infos = addresses.get(AF_INET, [])
            if ipv4_infos:
                return ipv4_infos[0]["addr"]
        else:
            ipv6_infos = addresses.get(AF_INET6, [])
            if ipv6_infos:
                return ipv6_infos[0]["addr"].partition("%")[0]

    def log_event(self, event_type: str, event_payload: str, dst_ip: str, dst_port: int):
        """将事件记录到事件日志
        格式
        src_ip src_port dst_ip dst_ip dst_port event_type event_data
        """
        if self.src_ip == "127.0.0.1":
            return
        event_logger.info(f"{self.src_ip} {self.src_port} {dst_ip} {dst_port} {event_type} {event_payload}")

    @launcher
    async def _read_client_and_send_to_server(self, cl_reader: StreamReader, ts_writer: StreamWriter):
        """读取客户端数据发送到服务端"""

        while True:
            try:
                cl_data = await cl_reader.read(len(cl_reader._buffer))
                if not cl_data:
                    await sleep(0.1)
                    continue
                data_type, data_decoded = self.decoder(cl_data)
                if data_type and data_decoded:
                    print(f"get type: {data_type}, data_decoded: {data_decoded}")
                    dst_ip, dst_port = cl_reader._transport.get_extra_info("sockname")
                    self.log_event(data_type, data_decoded, dst_ip, dst_port)
                ts_writer.write(cl_data)
                # print("send data to server")
            except Exception as e:
                print(f"_read_client_and_send_to_server error: {e}")
                break
        ts_writer.close()

    @launcher
    async def _read_server_and_send_to_client(self, ts_reader: StreamReader, cl_writer: StreamWriter):
        """读取服务端数据发送到客户端"""
        self.src_ip, self.src_port = cl_writer.get_extra_info("peername")
        print(f"get src ip: {self.src_ip}, src port: {self.src_port}")
        # 循环接收服务器数据
        while True:
            try:
                ts_data = await ts_reader.read(len(ts_reader._buffer))
                if not ts_data:
                    await sleep(0.1)
                    continue
                # print("------ ts_data: ", ts_data)
                cl_writer.write(ts_data)
                # print("send data to client")
            except Exception as e:
                print(f"_read_server_and_send_to_client error: {e}")
                break
        cl_writer.close()

    def signal_handle(self):
        pass


class TcpServer:

    def __init__(self, local_host: str, local_port: int):
        self.local_host = local_host
        self.local_port = local_port

    async def start(self, target_ip: str, target_port: int):
        """
        服务初始化
        """
        self.server = await asyncio.start_server(
            Forwarder(self.local_port, target_ip, target_port).handle_conn, self.local_host, self.local_port
        )

    async def stop(self):
        self.server.stop()


if __name__ == "__main__":
    parser = ArgumentParser(description="port forward proxy argument parser")
    parser.add_argument("--proxy_port", help="proxy port", required=True, type=int)
    parser.add_argument("--target_port", help="target port", required=True, type=int)
    parser.add_argument("--target_ip", help="target ip", required=True, type=str)

    args = parser.parse_args()
    proxy_port = args.proxy_port
    target_port = args.target_port
    target_ip = args.target_ip
    print(f"proxy_port: {proxy_port}, target_port: {target_port}, target_ip: {target_ip}")

    server = TcpServer("0.0.0.0", proxy_port)
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(server.start(target_ip, target_port))
    try:
        loop.run_forever()
    except:
        loop.close()
