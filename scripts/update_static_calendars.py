#!/usr/bin/env python3
"""
静态日历文件更新器
生成固定文件名的ICS日历，支持用户订阅固定URL进行自动更新

用法:
  python update_static_calendars.py           # 更新所有静态日历文件
  python update_static_calendars.py --watch   # 持续监控并更新
"""

import sys
import argparse
import time
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.multi_calendar_generator import generate_all_calendars

def update_static_calendars() -> list:
    """更新静态日历文件（媒体部、儿童部）"""
    results = generate_all_calendars()
    if not results or not results.get('calendars'):
        print("❌ 未生成任何日历内容")
        return []
    
    output_dir = Path("calendars/")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename_map = {
        'media-team': 'media-team.ics',
        'children-team': 'children-team.ics'
    }
    
    saved_files = []
    for calendar_type, calendar_result in results['calendars'].items():
        if not calendar_result.get('success') or not calendar_result.get('content'):
            print(f"⚠️  跳过 {calendar_type}：生成失败")
            continue
        
        filename = filename_map.get(calendar_type, f"{calendar_type}.ics")
        file_path = output_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(calendar_result['content'])
        
        event_count = calendar_result.get('events', 0)
        saved_files.append((filename, event_count))
        print(f"✅ 已更新: {filename} (事件数: {event_count})")
    
    return saved_files

def cmd_update():
    """更新所有静态日历文件"""
    print("🔄 更新静态日历文件")
    print("=" * 50)
    
    saved_files = update_static_calendars()
    success_count = len(saved_files)
    total_count = 2
    
    print(f"\n📊 更新结果: {success_count}/{total_count} 个日历文件更新成功")
    
    if success_count == total_count:
        print("✅ 所有日历文件更新完成！")
        
        # 显示订阅信息
        print("\n🔗 日历订阅信息:")
        print("=" * 50)
        print("📋 固定文件名日历（推荐用于订阅）:")
        print("  媒体部日历: calendars/media-team.ics")
        print("  儿童部日历: calendars/children-team.ics")
        
        print("\n💡 使用方法:")
        print("1. 将文件上传到Web服务器")
        print("2. 在日历应用中订阅URL（如 https://your-server.com/calendars/media-team.ics）")
        print("3. 定期运行此脚本更新文件内容")
        print("4. 日历应用会自动检测文件变化并更新")
        
    else:
        print("⚠️  部分日历文件更新失败")

def cmd_watch():
    """持续监控并更新日历文件"""
    print("👁️ 启动日历文件监控模式")
    print("=" * 50)
    print("🔄 每30分钟自动更新一次日历文件")
    print("按 Ctrl+C 停止监控")
    
    try:
        while True:
            print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 开始更新...")
            cmd_update()
            
            print(f"😴 等待30分钟后下次更新...")
            time.sleep(1800)  # 30分钟 = 1800秒
            
    except KeyboardInterrupt:
        print("\n🛑 监控已停止")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Grace Irvine 静态日历文件更新器",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--watch', action='store_true', help='持续监控模式（每30分钟更新）')
    
    args = parser.parse_args()
    
    print("🎯 Grace Irvine 静态日历更新器")
    print(f"⏰ 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if args.watch:
        cmd_watch()
    else:
        cmd_update()

if __name__ == "__main__":
    main()
