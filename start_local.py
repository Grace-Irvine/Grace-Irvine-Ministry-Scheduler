#!/usr/bin/env python3
"""
本地开发启动脚本
Local Development Startup Script
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """启动本地开发环境"""
    print("🚀 Grace Irvine Ministry Scheduler - 本地开发")
    print("=" * 60)
    
    # 设置本地环境
    print("1. 设置本地环境...")
    try:
        from local_dev_config import setup_local_environment
        setup_local_environment()
    except Exception as e:
        print(f"❌ 环境设置失败: {e}")
        return
    
    print()
    print("2. 启动Streamlit应用...")
    print("🌐 Web界面将在浏览器中打开")
    print("📝 使用 Ctrl+C 停止服务")
    print()
    
    try:
        # 启动Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app_unified.py",
            "--server.headless=false"
        ])
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"{chr(10)}❌ 启动失败: {e}")

if __name__ == "__main__":
    main()
