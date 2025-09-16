# Grace Irvine Ministry Scheduler - Cloud Run Dockerfile
# 支持 Streamlit + 静态文件服务

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录和权限
RUN mkdir -p /app/calendars /app/logs /app/data /app/templates && \
    chmod +x /app/start.py

# 确保经文分享配置文件存在
RUN if [ ! -f /app/templates/scripture_sharing.json ]; then \
        echo '{"metadata":{"version":"1.0","current_index":0,"total_count":0},"scriptures":[]}' > /app/templates/scripture_sharing.json; \
    fi

# 设置环境变量
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLE_CORS=false
ENV STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV PORT=8080
ENV API_PORT=8000

# 暴露端口
EXPOSE 8080 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/_stcore/health || exit 1

# 启动命令 - 运行统一启动脚本
CMD ["python3", "start.py", "--skip-checks"]
