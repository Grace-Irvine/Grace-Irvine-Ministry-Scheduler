#!/usr/bin/env python3
"""
本地 ICS 日历生成脚本
生成所有类型的 ICS 日历文件并保存到本地 calendars/ 目录（媒体部、儿童部）
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.multi_calendar_generator import generate_all_calendars

def main():
    """生成所有 ICS 日历文件并保存到本地"""
    print("=" * 60)
    print("📅 Grace Irvine 事工排程 - ICS 日历生成器")
    print("=" * 60)
    print()
    
    # 确保 calendars 目录存在
    calendar_dir = PROJECT_ROOT / "calendars"
    calendar_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 输出目录: {calendar_dir}")
    print()
    
    # 生成所有日历
    print("🔄 正在生成 ICS 日历文件...")
    print()
    
    try:
        results = generate_all_calendars()
        
        if not results['success']:
            print("❌ 生成过程中出现错误")
            return 1
        
        # 保存文件
        filename_map = {
            'media-team': 'media-team.ics',
            'children-team': 'children-team.ics'
        }
        
        saved_files = []
        
        for calendar_type, calendar_result in results['calendars'].items():
            if calendar_result['success'] and calendar_result['content']:
                filename = filename_map.get(calendar_type, f"{calendar_type}.ics")
                file_path = calendar_dir / filename
                
                # 保存文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(calendar_result['content'])
                
                event_count = calendar_result['events']
                file_size = len(calendar_result['content'].encode('utf-8'))
                file_size_kb = file_size / 1024
                
                saved_files.append({
                    'filename': filename,
                    'path': file_path,
                    'events': event_count,
                    'size_kb': file_size_kb
                })
                
                print(f"✅ {filename}")
                print(f"   事件数: {event_count}")
                print(f"   文件大小: {file_size_kb:.1f} KB")
                print(f"   保存路径: {file_path}")
                print()
            else:
                print(f"❌ {calendar_type}: 生成失败")
                print()
        
        # 总结
        print("=" * 60)
        print(f"✅ 生成完成！共生成 {len(saved_files)} 个文件")
        print("=" * 60)
        print()
        
        if saved_files:
            print("📋 生成的文件列表:")
            for file_info in saved_files:
                print(f"   • {file_info['filename']}")
                print(f"     事件数: {file_info['events']} | 大小: {file_info['size_kb']:.1f} KB")
            print()
            
            print("💡 使用说明:")
            print("   1. 启动前端应用: streamlit run app_unified.py")
            print("   2. 进入 '📅 ICS日历管理' 页面")
            print("   3. 在 '🆕 多类型 ICS 日历查看器' 中选择 '💻 本地文件'")
            print("   4. 选择要查看的 ICS 类型")
            print()
            
            print("📁 文件位置:")
            for file_info in saved_files:
                print(f"   • {file_info['path']}")
            print()
        
        return 0
        
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())

