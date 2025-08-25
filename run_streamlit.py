#!/usr/bin/env python3
"""
Grace Irvine Ministry Scheduler - Streamlit 启动脚本
启动 Web 应用的便捷脚本
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """启动 Streamlit 应用"""
    print("=" * 60)
    print("  Grace Irvine Ministry Scheduler - Web 应用")
    print("  恩典尔湾教会事工排程管理系统")
    print("=" * 60)
    print()
    
    # 检查依赖
    print("🔍 检查依赖项...")
    
    try:
        import streamlit
        import pandas
        import gspread
        print("  ✅ 所有依赖项已安装")
    except ImportError as e:
        print(f"  ❌ 缺少依赖项: {e}")
        print("\n请运行以下命令安装依赖:")
        print("  pip3 install -r requirements.txt")
        sys.exit(1)
    
    # 检查必要文件
    project_root = Path(__file__).parent
    streamlit_app = project_root / "streamlit_app.py"
    
    if not streamlit_app.exists():
        print("❌ 找不到 streamlit_app.py 文件")
        sys.exit(1)
    
    print("  ✅ 应用文件检查完成")
    print()
    
    # 启动信息
    print("🚀 启动 Web 应用...")
    print("  📍 本地地址: http://localhost:8501")
    print("  🔄 应用会自动在浏览器中打开")
    print("  ⏹️  按 Ctrl+C 停止应用")
    print()
    print("⚡ 功能特性:")
    print("  • 📊 实时数据查看和分析")
    print("  • 📝 自动生成通知模板")
    print("  • 📥 数据导出功能")
    print("  • ⚙️ 系统设置和配置")
    print()
    
    try:
        # 启动 Streamlit
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            str(streamlit_app),
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ]
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n👋 应用已停止，感谢使用！")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
