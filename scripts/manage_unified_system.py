#!/usr/bin/env python3
"""
统一系统管理工具 - Unified System Management Tool
管理集成的数据流：Google Sheets → 数据清洗 → 模板生成 → ICS更新 + 邮件发送

用法:
  python manage_unified_system.py start              # 启动统一调度器
  python manage_unified_system.py stop               # 停止统一调度器
  python manage_unified_system.py status             # 查看系统状态
  python manage_unified_system.py sync               # 手动同步数据和日历
  python manage_unified_system.py send weekly        # 手动发送周三通知
  python manage_unified_system.py send sunday        # 手动发送周六通知
  python manage_unified_system.py send monthly       # 手动发送月度通知
  python manage_unified_system.py test               # 测试系统组件
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime
import time

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.unified_scheduler import UnifiedScheduler
from dotenv import load_dotenv

def setup_environment():
    """设置环境"""
    load_dotenv()
    
    # 检查必要的环境变量
    spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
    if not spreadsheet_id:
        print("❌ 错误: 请在 .env 文件中设置 GOOGLE_SPREADSHEET_ID")
        sys.exit(1)
    
    # 检查服务账户文件
    service_account_path = Path("configs/service_account.json")
    if not service_account_path.exists():
        print("❌ 错误: 服务账户文件不存在 configs/service_account.json")
        sys.exit(1)
    
    return spreadsheet_id

def print_status(status: dict):
    """格式化打印系统状态"""
    print("📊 统一系统状态")
    print("=" * 50)
    
    # 基本状态
    print(f"🔄 运行状态: {'✅ 运行中' if status['is_running'] else '⏹️  已停止'}")
    print(f"⏰ 同步频率: 每 {status['sync_frequency_hours']} 小时")
    print(f"🔧 自动同步: {'✅ 启用' if status['auto_sync_enabled'] else '❌ 禁用'}")
    print(f"📋 计划任务: {status['scheduled_tasks']} 个")
    
    # 时间信息
    last_sync = status['last_sync_time']
    last_notification = status['last_notification_time']
    
    print(f"\n⏱️  时间信息:")
    print(f"  📅 最后同步: {last_sync or '从未同步'}")
    print(f"  📧 最后通知: {last_notification or '从未发送'}")
    
    # 组件状态
    print(f"\n🔧 组件状态:")
    components = status['components_status']
    for component, is_ok in components.items():
        status_icon = "✅" if is_ok else "❌"
        component_name = {
            'sheets_extractor': 'Google Sheets提取器',
            'template_manager': '模板管理器',
            'ics_manager': 'ICS日历管理器',
            'email_sender': '邮件发送器',
            'notification_generator': '通知生成器'
        }.get(component, component)
        print(f"  {status_icon} {component_name}")
    
    # 同步状态
    sync_status = status.get('sync_status', '未知')
    print(f"\n📝 同步状态: {sync_status}")

def cmd_start(args):
    """启动统一调度器"""
    print("🚀 启动统一调度器...")
    
    try:
        scheduler = UnifiedScheduler()
        success = scheduler.start()
        
        if success:
            print("✅ 统一调度器已启动！")
            print("\n📋 系统功能:")
            print("  • 🔄 每12小时自动同步Google Sheets数据")
            print("  • 📅 自动更新ICS日历文件")
            print("  • 📧 按时发送邮件通知:")
            print("    - 周三晚上: 发送周末确认通知")
            print("    - 周六晚上: 发送主日提醒通知")
            print("    - 每月1日: 发送月度总览通知")
            
            print("\n🎯 服务将持续运行，按 Ctrl+C 停止...")
            
            # 显示当前状态
            status = scheduler.get_status()
            print_status(status)
            
            # 保持程序运行
            try:
                while True:
                    time.sleep(60)
                    # 可以在这里添加状态监控逻辑
            except KeyboardInterrupt:
                print("\n🛑 正在停止统一调度器...")
                scheduler.stop()
                print("✅ 统一调度器已停止")
        else:
            print("❌ 启动统一调度器失败")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ 启动过程中出现错误: {e}")
        sys.exit(1)

def cmd_stop(args):
    """停止统一调度器"""
    print("🛑 停止统一调度器...")
    
    try:
        scheduler = UnifiedScheduler()
        success = scheduler.stop()
        
        if success:
            print("✅ 统一调度器已停止")
        else:
            print("⚠️  统一调度器未在运行")
    
    except Exception as e:
        print(f"❌ 停止过程中出现错误: {e}")
        sys.exit(1)

def cmd_status(args):
    """查看系统状态"""
    try:
        scheduler = UnifiedScheduler()
        status = scheduler.get_status()
        print_status(status)
        
        # 额外的系统信息
        print(f"\n💾 输出目录信息:")
        output_dir = Path("calendars/")
        if output_dir.exists():
            ics_files = list(output_dir.glob('*.ics'))
            print(f"  📁 ICS文件: {len(ics_files)} 个")
            
            if ics_files:
                print("  📋 最新文件:")
                for file_path in sorted(ics_files, key=lambda x: x.stat().st_mtime, reverse=True)[:3]:
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    print(f"    - {file_path.name} ({mtime.strftime('%Y-%m-%d %H:%M:%S')})")
        else:
            print("  📁 输出目录不存在")
        
    except Exception as e:
        print(f"❌ 获取状态时出现错误: {e}")
        sys.exit(1)

def cmd_sync(args):
    """手动同步数据和日历"""
    print("🔄 开始手动同步...")
    
    try:
        scheduler = UnifiedScheduler()
        success = scheduler.force_sync()
        
        if success:
            print("✅ 数据同步成功！")
            
            # 显示同步后的状态
            status = scheduler.get_status()
            print(f"📅 同步时间: {status['last_sync_time']}")
            print(f"📝 同步状态: {status['sync_status']}")
        else:
            print("❌ 数据同步失败")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ 同步过程中出现错误: {e}")
        sys.exit(1)

def cmd_send(args):
    """手动发送通知"""
    notification_type = args.notification_type
    
    type_names = {
        'weekly': '周三确认通知',
        'sunday': '周六提醒通知',
        'monthly': '月度总览通知'
    }
    
    type_name = type_names.get(notification_type, notification_type)
    print(f"📧 开始发送{type_name}...")
    
    try:
        scheduler = UnifiedScheduler()
        success = scheduler.force_send_notification(notification_type)
        
        if success:
            print(f"✅ {type_name}发送成功！")
            
            # 显示发送后的状态
            status = scheduler.get_status()
            print(f"📧 发送时间: {status['last_notification_time']}")
        else:
            print(f"❌ {type_name}发送失败")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ 发送过程中出现错误: {e}")
        sys.exit(1)

def cmd_test(args):
    """测试系统组件"""
    print("🧪 开始系统组件测试...")
    print("=" * 50)
    
    try:
        scheduler = UnifiedScheduler()
        
        # 测试各个组件
        status = scheduler.get_status()
        components = status['components_status']
        
        print("🔧 组件测试结果:")
        all_ok = True
        
        for component, is_ok in components.items():
            status_icon = "✅" if is_ok else "❌"
            component_name = {
                'sheets_extractor': 'Google Sheets提取器',
                'template_manager': '模板管理器', 
                'ics_manager': 'ICS日历管理器',
                'email_sender': '邮件发送器',
                'notification_generator': '通知生成器'
            }.get(component, component)
            
            print(f"  {status_icon} {component_name}")
            if not is_ok:
                all_ok = False
        
        print(f"\n🔄 测试数据同步功能...")
        sync_success = scheduler.force_sync()
        print(f"  数据同步: {'✅ 成功' if sync_success else '❌ 失败'}")
        
        if not sync_success:
            all_ok = False
        
        print(f"\n📋 系统整体状态: {'✅ 正常' if all_ok else '❌ 存在问题'}")
        
        if all_ok:
            print("\n🎉 系统测试完成，所有组件正常！")
        else:
            print("\n⚠️  系统测试发现问题，请检查配置和环境")
            sys.exit(1)
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Grace Irvine 统一系统管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # start 命令
    parser_start = subparsers.add_parser('start', help='启动统一调度器')
    parser_start.set_defaults(func=cmd_start)
    
    # stop 命令
    parser_stop = subparsers.add_parser('stop', help='停止统一调度器')
    parser_stop.set_defaults(func=cmd_stop)
    
    # status 命令
    parser_status = subparsers.add_parser('status', help='查看系统状态')
    parser_status.set_defaults(func=cmd_status)
    
    # sync 命令
    parser_sync = subparsers.add_parser('sync', help='手动同步数据和日历')
    parser_sync.set_defaults(func=cmd_sync)
    
    # send 命令
    parser_send = subparsers.add_parser('send', help='手动发送通知')
    parser_send.add_argument('notification_type', choices=['weekly', 'sunday', 'monthly'],
                            help='通知类型')
    parser_send.set_defaults(func=cmd_send)
    
    # test 命令
    parser_test = subparsers.add_parser('test', help='测试系统组件')
    parser_test.set_defaults(func=cmd_test)
    
    # 解析参数
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 设置环境
    setup_environment()
    
    # 显示标题
    print("🎯 Grace Irvine 统一系统管理工具")
    print(f"⏰ 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 执行命令
    args.func(args)

if __name__ == "__main__":
    main()
