#!/usr/bin/env python3
"""
Grace Irvine Ministry Scheduler - 统一启动脚本
这是项目的唯一入口点

使用方法:
    python start.py               # 启动完整应用
    python start.py --port 8080   # 指定端口
    python start.py --help        # 显示帮助
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def setup_environment():
    """设置环境"""
    print("🔧 准备环境...")
    
    # 创建必要的目录
    directories = ['calendars', 'logs', 'data']
    for dir_name in directories:
        dir_path = Path(dir_name)
        dir_path.mkdir(exist_ok=True)
        print(f"📁 目录已准备: {dir_path}")
    
    return True

def check_dependencies():
    """检查依赖"""
    print("🔍 检查依赖...")
    
    required_packages = [
        'streamlit',
        'pandas',
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    print("✅ 所有依赖已安装")
    return True

def start_application(port=8501, host="0.0.0.0"):
    """启动统一应用"""
    print("🚀 启动Grace Irvine Ministry Scheduler")
    print("=" * 60)
    
    # 检查环境
    if 'K_SERVICE' in os.environ:
        print("✅ 运行在Cloud Run环境")
    else:
        print("ℹ️ 运行在本地环境")
    
    print(f"🌐 应用将启动在: http://{host}:{port}")
    print(f"📅 日历订阅将通过内置服务提供")
    print("=" * 60)
    print("按 Ctrl+C 停止服务")
    print()
    
    try:
        # 检查是否在Cloud Run环境中
        if 'K_SERVICE' in os.environ or os.getenv('PORT'):
            # Cloud Run环境：直接运行app_unified.py（包含FastAPI和Streamlit）
            print("🔧 启动统一应用（包含API端点）...")
            import sys
            sys.path.insert(0, '.')
            
            # 设置Streamlit环境变量
            os.environ['STREAMLIT_SERVER_PORT'] = str(port)
            os.environ['STREAMLIT_SERVER_ADDRESS'] = host
            os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
            os.environ['STREAMLIT_SERVER_ENABLE_CORS'] = 'false'
            os.environ['STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION'] = 'false'
            os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
            
            # 直接运行app_unified.py
            exec(open('app_unified.py').read())
        else:
            # 本地环境：使用Streamlit命令
            cmd = [
                'streamlit', 'run', 'app_unified.py',
                f'--server.port={port}',
                f'--server.address={host}',
                '--server.headless=true',
                '--server.fileWatcherType=none',
                '--browser.gatherUsageStats=false'
            ]
            
            subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 服务已停止")
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 意外错误: {e}")
        sys.exit(1)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Grace Irvine Ministry Scheduler - 统一启动脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python start.py                    # 使用默认设置启动
    python start.py --port 8080        # 指定端口
    python start.py --host 127.0.0.1   # 指定主机地址
        """
    )
    
    parser.add_argument(
        '--port', 
        type=int, 
        default=int(os.getenv('PORT', 8501)),
        help='指定端口号 (默认: 8501)'
    )
    
    parser.add_argument(
        '--host', 
        type=str, 
        default='0.0.0.0',
        help='指定主机地址 (默认: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--skip-checks', 
        action='store_true',
        help='跳过环境检查'
    )
    
    args = parser.parse_args()
    
    # 显示欢迎信息
    print("🎉 Grace Irvine Ministry Scheduler v2.0")
    print("恩典尔湾长老教会事工排程管理系统 - 简化版本")
    print("=" * 60)
    
    # 环境检查
    if not args.skip_checks:
        if not check_dependencies():
            sys.exit(1)
        
        if not setup_environment():
            sys.exit(1)
    
    # 启动应用
    start_application(port=args.port, host=args.host)

if __name__ == "__main__":
    main()
