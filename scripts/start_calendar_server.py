#!/usr/bin/env python3
"""
ICS日历订阅服务器启动脚本
提供HTTP服务，支持日历应用通过URL自动订阅和更新

用法:
  python start_calendar_server.py                # 启动服务器 (端口 8080)
  python start_calendar_server.py --port 9000    # 指定端口
  python start_calendar_server.py --test         # 测试模式
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.calendar_subscription_server import start_subscription_server, CalendarSubscriptionManager
from dotenv import load_dotenv

def test_subscription_manager():
    """测试订阅管理器"""
    print("🧪 测试订阅管理器")
    print("=" * 50)
    
    try:
        manager = CalendarSubscriptionManager()
        
        # 测试状态
        status = manager.get_status()
        print("📊 系统状态:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        # 测试负责人日历生成
        print("\n📅 测试负责人日历生成...")
        coordinator_ics = manager.get_fresh_coordinator_calendar()
        
        if coordinator_ics and "BEGIN:VCALENDAR" in coordinator_ics:
            event_count = coordinator_ics.count("BEGIN:VEVENT")
            print(f"✅ 负责人日历生成成功 ({event_count} 个事件)")
            
            # 显示前几行
            lines = coordinator_ics.split('\n')[:15]
            print("📋 日历头部:")
            for line in lines:
                if line.strip():
                    print(f"  {line}")
            print("  ...")
        else:
            print("❌ 负责人日历生成失败")
        
        # 测试同工日历生成
        print("\n👥 测试同工日历生成...")
        workers_ics = manager.get_fresh_workers_calendar()
        
        if workers_ics and "BEGIN:VCALENDAR" in workers_ics:
            event_count = workers_ics.count("BEGIN:VEVENT")
            print(f"✅ 同工日历生成成功 ({event_count} 个事件)")
        else:
            print("❌ 同工日历生成失败")
        
        print("\n✅ 订阅管理器测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Grace Irvine ICS日历订阅服务器",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--port', type=int, default=8080, help='服务器端口 (默认: 8080)')
    parser.add_argument('--test', action='store_true', help='测试模式，不启动服务器')
    
    args = parser.parse_args()
    
    # 设置环境
    load_dotenv()
    
    if not os.getenv('GOOGLE_SPREADSHEET_ID'):
        print("❌ 错误: 请在 .env 文件中设置 GOOGLE_SPREADSHEET_ID")
        sys.exit(1)
    
    print("🎯 Grace Irvine ICS日历订阅服务")
    print(f"⏰ 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if args.test:
        # 测试模式
        success = test_subscription_manager()
        if success:
            print("\n🎉 测试成功！可以启动服务器")
        else:
            print("\n❌ 测试失败！请检查配置")
            sys.exit(1)
    else:
        # 启动服务器
        print("🔧 正在初始化组件...")
        
        # 先测试一下
        if not test_subscription_manager():
            print("❌ 初始化测试失败，无法启动服务器")
            sys.exit(1)
        
        print(f"\n🚀 启动ICS订阅服务器 (端口 {args.port})...")
        start_subscription_server(args.port)

if __name__ == "__main__":
    main()
