# Grace Irvine Ministry Scheduler - Cloud Run Dockerfile
# 支持 Streamlit + 静态文件服务

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p /app/calendars

# 设置环境变量
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLE_CORS=false
ENV STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false

# 暴露端口
EXPOSE 8080

# 启动命令 - 使用统一应用
CMD ["python3", "start.py", "--host", "0.0.0.0", "--port", "8080"]
