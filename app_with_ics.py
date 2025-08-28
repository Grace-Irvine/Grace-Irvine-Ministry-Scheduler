#!/usr/bin/env python3
"""
集成应用启动器
同时运行Streamlit Web界面和ICS API端点

用于Cloud Run部署，提供：
1. Streamlit Web界面 (主端口 8080)
2. ICS API端点 (/api/* 路由)
3. 静态日历文件服务 (/calendars/* 路由)
"""

import os
import sys
import threading
import time
from pathlib import Path

# 设置项目路径
sys.path.append(str(Path(__file__).parent))

def start_ics_api():
    """启动ICS API服务"""
    try:
        from ics_api import app
        import logging
        
        # 配置日志
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        
        # 在子线程中运行Flask API
        app.run(
            host='0.0.0.0', 
            port=5000, 
            debug=False,
            use_reloader=False,
            threaded=True
        )
        
    except Exception as e:
        print(f"❌ 启动ICS API失败: {e}")

def start_streamlit():
    """启动Streamlit应用"""
    try:
        import subprocess
        
        # 启动Streamlit
        cmd = [
            'streamlit', 'run', 'streamlit_app.py',
            '--server.port=8080',
            '--server.address=0.0.0.0',
            '--server.headless=true',
            '--server.enableCORS=false',
            '--server.enableXsrfProtection=false',
            '--server.fileWatcherType=none',
            '--browser.gatherUsageStats=false'
        ]
        
        subprocess.run(cmd)
        
    except Exception as e:
        print(f"❌ 启动Streamlit失败: {e}")

def main():
    """主函数"""
    print("🚀 启动Grace Irvine集成应用")
    print("=" * 50)
    print("📱 Streamlit界面: http://localhost:8080")
    print("🔗 ICS API: http://localhost:5000/api/")
    print("📅 日历文件: http://localhost:8080/calendars/")
    print()
    
    # 启动ICS API服务（后台线程）
    print("🔧 启动ICS API服务...")
    api_thread = threading.Thread(target=start_ics_api, daemon=True)
    api_thread.start()
    
    # 等待API服务启动
    time.sleep(3)
    
    # 启动Streamlit应用（主线程）
    print("🖥️ 启动Streamlit应用...")
    start_streamlit()

if __name__ == "__main__":
    main()
