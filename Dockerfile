# 第一阶段：构建环境
FROM python:3.9-slim AS builder


ENV http_proxy=http://192.170.0.49:1087
ENV https_porxy=http://192.170.0.49:1087

# 安装必要的构建工具和依赖项，包括 objdump
RUN apt-get update && apt-get install -y --no-install-recommends build-essential binutils  && rm -rf /var/lib/apt/lists/*

# 设置临时环境变量 PIP_INDEX_URL 指向清华源
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# 设置工作目录
WORKDIR /app

# 将当前目录的内容复制到容器中的 /app 目录
COPY . .

# 安装 PyInstaller 和其他必要的依赖项
RUN pip install --no-cache-dir pyinstaller==5.0 && \
    pip install --no-cache-dir -r requirements.txt

# 使用 PyInstaller 编译 Python 项目为二进制文件
RUN  pyinstaller sse_demo.py -F -n main -p .

# 第二阶段：运行环境
FROM python:3.9-slim

# 设置工作目录
WORKDIR /opt/dbproxy

# 从构建阶段复制生成的二进制文件
COPY --from=builder /app/dist/* /opt/dbproxy 
COPY start.sh /opt/dbproxy

# 暴露应用监听的端口 (如果需要)
LABEL required_env="PROXY_PORT,TARGET_IP,TARGET_PORT"

# 定义启动命令
CMD ["/opt/dbproxy/start.sh"]
