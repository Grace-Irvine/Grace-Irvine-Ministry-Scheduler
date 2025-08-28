#!/usr/bin/env python3
"""
ICS Calendar Management Tool - ICS日历管理工具
命令行工具，用于管理ICS日历系统

用法:
  python manage_ics_calendar.py sync              # 手动同步日历
  python manage_ics_calendar.py start             # 启动自动同步
  python manage_ics_calendar.py stop              # 停止自动同步
  python manage_ics_calendar.py status            # 查看同步状态
  python manage_ics_calendar.py generate          # 生成日历文件
  python manage_ics_calendar.py cleanup           # 清理旧文件
  python manage_ics_calendar.py subscribers       # 管理订阅者
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.ics_manager import ICSManager
from src.calendar_scheduler import CalendarScheduler
from src.scheduler import GoogleSheetsExtractor
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

def cmd_sync(args):
    """手动同步日历"""
    print("🔄 开始手动同步日历...")
    
    try:
        scheduler = CalendarScheduler()
        success = scheduler.force_sync()
        
        if success:
            print("✅ 日历同步成功！")
            status = scheduler.get_sync_status()
            print(f"📅 同步时间: {status['last_sync_time']}")
        else:
            print("❌ 日历同步失败")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ 同步过程中出现错误: {e}")
        sys.exit(1)

def cmd_start(args):
    """启动自动同步"""
    print("🚀 启动自动同步服务...")
    
    try:
        scheduler = CalendarScheduler()
        success = scheduler.start_auto_sync()
        
        if success:
            print("✅ 自动同步服务已启动！")
            status = scheduler.get_sync_status()
            print(f"⏰ 同步频率: 每 {status['sync_frequency_hours']} 小时")
            print("📝 服务将在后台运行，按 Ctrl+C 停止")
            
            # 保持程序运行
            try:
                while True:
                    import time
                    time.sleep(60)
            except KeyboardInterrupt:
                print("\n🛑 正在停止自动同步...")
                scheduler.stop_auto_sync()
                print("✅ 自动同步已停止")
        else:
            print("❌ 启动自动同步失败")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ 启动过程中出现错误: {e}")
        sys.exit(1)

def cmd_stop(args):
    """停止自动同步"""
    print("🛑 停止自动同步服务...")
    
    try:
        scheduler = CalendarScheduler()
        success = scheduler.stop_auto_sync()
        
        if success:
            print("✅ 自动同步服务已停止")
        else:
            print("⚠️  自动同步服务未在运行")
    
    except Exception as e:
        print(f"❌ 停止过程中出现错误: {e}")
        sys.exit(1)

def cmd_status(args):
    """查看同步状态"""
    print("📊 ICS日历系统状态")
    print("=" * 50)
    
    try:
        scheduler = CalendarScheduler()
        status = scheduler.get_sync_status()
        
        print(f"🔄 自动同步状态: {'运行中' if status['is_running'] else '已停止'}")
        print(f"⏰ 同步频率: 每 {status['sync_frequency_hours']} 小时")
        print(f"📅 上次同步: {status['last_sync_time'] or '从未同步'}")
        print(f"🎯 下次同步: {status['next_sync_time'] or '未计划'}")
        print(f"📝 同步状态: {status['sync_status']}")
        print(f"🔧 自动同步: {'启用' if status['auto_sync_enabled'] else '禁用'}")
        
        # 检查输出目录
        ics_manager = ICSManager()
        output_dir = Path(ics_manager.config['output_directory'])
        if output_dir.exists():
            ics_files = list(output_dir.glob('*.ics'))
            print(f"📁 日历文件: {len(ics_files)} 个")
            
            if ics_files:
                print("   最新文件:")
                for file_path in sorted(ics_files, key=lambda x: x.stat().st_mtime, reverse=True)[:3]:
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    print(f"   - {file_path.name} ({mtime.strftime('%Y-%m-%d %H:%M:%S')})")
        else:
            print("📁 日历文件: 输出目录不存在")
        
    except Exception as e:
        print(f"❌ 获取状态时出现错误: {e}")
        sys.exit(1)

def cmd_generate(args):
    """生成日历文件"""
    print("📅 生成ICS日历文件...")
    
    try:
        # 获取数据
        spreadsheet_id = setup_environment()
        extractor = GoogleSheetsExtractor(spreadsheet_id)
        assignments = extractor.parse_ministry_data()
        
        if not assignments:
            print("⚠️  未找到事工安排数据")
            return
        
        print(f"📋 获取到 {len(assignments)} 条事工安排")
        
        # 生成日历
        ics_manager = ICSManager()
        
        if args.type in ['all', 'coordinator']:
            print("👨‍💼 生成负责人日历...")
            coordinator_path = ics_manager.generate_coordinator_calendar(assignments)
            print(f"✅ 负责人日历: {coordinator_path}")
        
        if args.type in ['all', 'worker']:
            print("👥 生成同工日历...")
            worker_path = ics_manager.generate_worker_calendar(assignments)
            print(f"✅ 同工日历: {worker_path}")
        
        if args.worker_name:
            print(f"👤 生成 {args.worker_name} 的个人日历...")
            personal_path = ics_manager.generate_worker_calendar(assignments, args.worker_name)
            print(f"✅ 个人日历: {personal_path}")
        
        print("🎉 日历生成完成！")
        
    except Exception as e:
        print(f"❌ 生成过程中出现错误: {e}")
        sys.exit(1)

def cmd_cleanup(args):
    """清理旧文件"""
    print(f"🧹 清理 {args.days} 天前的旧日历文件...")
    
    try:
        scheduler = CalendarScheduler()
        cleaned_count = scheduler.cleanup_old_calendars(args.days)
        
        if cleaned_count > 0:
            print(f"✅ 已清理 {cleaned_count} 个旧文件")
        else:
            print("📁 没有需要清理的文件")
        
    except Exception as e:
        print(f"❌ 清理过程中出现错误: {e}")
        sys.exit(1)

def cmd_subscribers(args):
    """管理订阅者"""
    try:
        ics_manager = ICSManager()
        
        if args.action == 'list':
            print("📧 订阅者列表")
            print("=" * 30)
            
            coordinator_subs = ics_manager.get_subscribers('coordinator')
            worker_subs = ics_manager.get_subscribers('worker')
            
            print("👨‍💼 负责人日历订阅者:")
            for email in coordinator_subs:
                print(f"  - {email}")
            
            print("\n👥 同工日历订阅者:")
            for email in worker_subs:
                print(f"  - {email}")
        
        elif args.action == 'add':
            success = ics_manager.add_subscriber(args.calendar_type, args.email)
            if success:
                print(f"✅ 已添加订阅者 {args.email} 到 {args.calendar_type} 日历")
            else:
                print(f"❌ 添加订阅者失败")
        
        elif args.action == 'remove':
            success = ics_manager.remove_subscriber(args.calendar_type, args.email)
            if success:
                print(f"✅ 已移除订阅者 {args.email} 从 {args.calendar_type} 日历")
            else:
                print(f"❌ 移除订阅者失败")
        
    except Exception as e:
        print(f"❌ 管理订阅者时出现错误: {e}")
        sys.exit(1)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Grace Irvine ICS Calendar Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # sync 命令
    parser_sync = subparsers.add_parser('sync', help='手动同步日历')
    parser_sync.set_defaults(func=cmd_sync)
    
    # start 命令
    parser_start = subparsers.add_parser('start', help='启动自动同步')
    parser_start.set_defaults(func=cmd_start)
    
    # stop 命令
    parser_stop = subparsers.add_parser('stop', help='停止自动同步')
    parser_stop.set_defaults(func=cmd_stop)
    
    # status 命令
    parser_status = subparsers.add_parser('status', help='查看同步状态')
    parser_status.set_defaults(func=cmd_status)
    
    # generate 命令
    parser_generate = subparsers.add_parser('generate', help='生成日历文件')
    parser_generate.add_argument('--type', choices=['all', 'coordinator', 'worker'], 
                                default='all', help='生成的日历类型')
    parser_generate.add_argument('--worker-name', help='生成特定同工的个人日历')
    parser_generate.set_defaults(func=cmd_generate)
    
    # cleanup 命令
    parser_cleanup = subparsers.add_parser('cleanup', help='清理旧文件')
    parser_cleanup.add_argument('--days', type=int, default=7, 
                               help='保留最近N天的文件 (默认: 7)')
    parser_cleanup.set_defaults(func=cmd_cleanup)
    
    # subscribers 命令
    parser_subs = subparsers.add_parser('subscribers', help='管理订阅者')
    parser_subs.add_argument('action', choices=['list', 'add', 'remove'], 
                            help='操作类型')
    parser_subs.add_argument('--calendar-type', choices=['coordinator', 'worker'],
                            help='日历类型 (add/remove时必需)')
    parser_subs.add_argument('--email', help='邮箱地址 (add/remove时必需)')
    parser_subs.set_defaults(func=cmd_subscribers)
    
    # 解析参数
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 执行命令
    args.func(args)

if __name__ == "__main__":
    main()
