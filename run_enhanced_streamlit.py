#!/usr/bin/env python3
"""
Grace Irvine Ministry Scheduler - 增强版 Streamlit 启动脚本
Enhanced Streamlit Launch Script with Weekly Overview
"""
import subprocess
import sys
import os
from pathlib import Path
from datetime import date, timedelta

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

def show_preview():
    """显示功能预览"""
    print("🎯 Grace Irvine Ministry Scheduler - 增强版")
    print("=" * 60)
    print("📅 新增功能: 周程安排概览")
    print()
    
    print("✨ 主要特性:")
    print("  📊 数据概览 - 实时统计和周程安排")
    print("  🔍 数据查看器 - 交互式数据浏览")
    print("  📝 模板生成器 - 自动生成通知模板")
    print("  ⚙️ 系统设置 - 配置管理")
    print()
    
    print("🆕 周程概览功能:")
    print("  • 显示前两周到未来7周的排程安排")
    print("  • 智能识别本周、下周等时间标签")
    print("  • 自动检测未安排和重复安排")
    print("  • 提供重要提醒和状态监控")
    print()
    
    # 显示当前周信息
    today = date.today()
    days_since_sunday = today.weekday() + 1
    if days_since_sunday == 7:
        days_since_sunday = 0
    current_sunday = today - timedelta(days=days_since_sunday)
    
    print("📅 时间信息:")
    print(f"  今天: {today.strftime('%Y年%m月%d日')} ({['周一','周二','周三','周四','周五','周六','周日'][today.weekday()]})")
    print(f"  本周主日: {current_sunday.strftime('%Y年%m月%d日')}")
    print(f"  下周主日: {(current_sunday + timedelta(weeks=1)).strftime('%Y年%m月%d日')}")
    print()

def check_dependencies():
    """检查依赖项"""
    print("🔍 检查依赖项...")
    
    required_modules = [
        ('streamlit', 'Streamlit Web框架'),
        ('pandas', '数据处理'),
        ('yaml', 'YAML配置文件'),
        ('src.data_cleaner', '专注数据清洗器')
    ]
    
    missing = []
    for module, description in required_modules:
        try:
            if module == 'src.data_cleaner':
                # 检查自定义模块
                from src.data_cleaner import FocusedDataCleaner
            else:
                __import__(module)
            print(f"  ✅ {description}")
        except ImportError:
            missing.append((module, description))
            print(f"  ❌ {description} (缺失)")
    
    if missing:
        print(f"\n⚠️  请安装缺失的依赖项:")
        for module, desc in missing:
            if module not in ['src.data_cleaner']:
                print(f"   pip3 install {module}")
        return False
    
    print("  ✅ 所有依赖项检查完成")
    return True

def test_data_connection():
    """测试数据连接"""
    print("\n🔗 测试数据连接...")
    
    try:
        from src.data_cleaner import FocusedDataCleaner
        cleaner = FocusedDataCleaner()
        
        # 快速测试连接
        print("  📊 正在连接 Google Sheets...")
        raw_df = cleaner.download_data()
        
        if not raw_df.empty:
            print(f"  ✅ 连接成功，找到 {len(raw_df)} 行数据")
            
            # 快速处理测试
            focused_df = cleaner.extract_focused_columns(raw_df)
            schedules = cleaner.clean_focused_data(focused_df)
            print(f"  ✅ 数据处理成功，生成 {len(schedules)} 个排程记录")
            
            return True
        else:
            print("  ⚠️  连接成功但数据为空")
            return False
            
    except Exception as e:
        print(f"  ❌ 连接测试失败: {str(e)[:100]}...")
        print("  💡 这不会影响应用启动，可以在Web界面中重试")
        return False

def launch_streamlit():
    """启动 Streamlit 应用"""
    print("\n🚀 启动 Web 应用...")
    
    project_root = Path(__file__).parent
    streamlit_app = project_root / "streamlit_app.py"
    
    if not streamlit_app.exists():
        print("❌ 找不到 streamlit_app.py 文件")
        return False
    
    print("  📍 本地地址: http://localhost:8501")
    print("  🔄 应用会自动在浏览器中打开")
    print("  ⏹️  按 Ctrl+C 停止应用")
    print()
    print("🎯 主要功能页面:")
    print("  • 📊 数据概览 - 查看周程安排和统计信息")
    print("  • 🔍 数据查看器 - 浏览和导出数据")
    print("  • 📝 模板生成器 - 生成微信群通知")
    print("  • ⚙️ 系统设置 - 配置和测试")
    print()
    print("=" * 60)
    
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
        return True
        
    except KeyboardInterrupt:
        print("\n👋 应用已停止，感谢使用！")
        return True
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        return False

def main():
    """主函数"""
    show_preview()
    
    # 检查依赖项
    if not check_dependencies():
        print("\n❌ 请先安装缺失的依赖项，然后重新运行")
        return 1
    
    # 测试数据连接
    connection_ok = test_data_connection()
    
    if connection_ok:
        print("\n✅ 所有检查通过，准备启动应用...")
    else:
        print("\n⚠️  数据连接测试未通过，但仍可启动应用")
        user_input = input("是否继续启动？(y/N): ").lower().strip()
        if user_input not in ['y', 'yes']:
            print("👋 已取消启动")
            return 0
    
    # 启动应用
    success = launch_streamlit()
    
    if success:
        print("\n🎉 应用运行完成")
    else:
        print("\n❌ 应用启动失败")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
