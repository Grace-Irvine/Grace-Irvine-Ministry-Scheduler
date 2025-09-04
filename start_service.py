#!/usr/bin/env python3
"""
启动Grace Irvine Ministry Scheduler服务
Start Grace Irvine Ministry Scheduler service
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path

def check_dependencies():
    """检查依赖"""
    print("🔍 检查依赖...")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'streamlit',
        'pandas',
        'gspread'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    print("✅ 所有依赖已安装")
    return True

def prepare_environment():
    """准备环境"""
    print("🔧 准备环境...")
    
    # 创建必要的目录
    directories = ['calendars', 'logs', 'data']
    for dir_name in directories:
        dir_path = Path(dir_name)
        dir_path.mkdir(exist_ok=True)
        print(f"📁 目录已准备: {dir_path}")
    
    # 检查环境变量
    if not os.getenv('GOOGLE_SPREADSHEET_ID'):
        print("⚠️ 未设置GOOGLE_SPREADSHEET_ID环境变量")
        print("💡 请在.env文件中设置或使用默认值")
    
    return True

def generate_initial_calendars():
    """生成初始日历文件"""
    print("📅 生成初始日历文件...")
    
    try:
        result = subprocess.run([
            'python3', 'generate_real_calendars.py'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ 初始日历文件生成成功")
            return True
        else:
            print(f"⚠️ 日历文件生成失败: {result.stderr}")
            print("💡 将使用测试日历文件")
            
            # 生成简单的测试文件
            calendar_dir = Path("calendars")
            test_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Grace Irvine Ministry Scheduler//Test Calendar//CN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Grace Irvine 测试日历
X-WR-CALDESC:测试用日历文件
X-WR-TIMEZONE:America/Los_Angeles
BEGIN:VEVENT
UID:test_event@graceirvine.org
DTSTAMP:{time.strftime('%Y%m%dT%H%M%S')}
DTSTART:{time.strftime('%Y%m%dT%H%M%S')}
DTEND:{time.strftime('%Y%m%dT%H%M%S')}
SUMMARY:测试事件
DESCRIPTION:这是一个测试事件
LOCATION:Grace Irvine 教会
END:VEVENT
END:VCALENDAR"""
            
            for filename in ['grace_irvine_coordinator.ics', 'grace_irvine_workers.ics']:
                with open(calendar_dir / filename, 'w', encoding='utf-8') as f:
                    f.write(test_content)
            
            print("✅ 测试日历文件已生成")
            return True
            
    except Exception as e:
        print(f"❌ 生成日历文件失败: {e}")
        return False

def start_fastapi_service():
    """启动FastAPI服务"""
    print("🚀 启动FastAPI服务...")
    
    try:
        # 确定端口
        port = int(os.getenv('PORT', 8080))
        
        print(f"🌐 服务将启动在端口 {port}")
        print(f"📅 负责人日历: http://localhost:{port}/calendars/grace_irvine_coordinator.ics")
        print(f"📅 同工日历: http://localhost:{port}/calendars/grace_irvine_workers.ics")
        print(f"📊 系统状态: http://localhost:{port}/api/status")
        print(f"❤️ 健康检查: http://localhost:{port}/health")
        print(f"🔍 调试信息: http://localhost:{port}/debug")
        print("=" * 60)
        print("按 Ctrl+C 停止服务")
        
        # 启动服务
        import uvicorn
        from app_with_static_routes import app
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n🛑 服务已停止")
    except Exception as e:
        print(f"❌ 启动服务失败: {e}")
        sys.exit(1)

def main():
    """主函数"""
    print("🚀 Grace Irvine Ministry Scheduler 启动器")
    print("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 准备环境
    if not prepare_environment():
        sys.exit(1)
    
    # 生成初始日历文件
    if not generate_initial_calendars():
        print("⚠️ 继续启动服务，但日历文件可能为空")
    
    # 启动FastAPI服务
    start_fastapi_service()

if __name__ == "__main__":
    main()
