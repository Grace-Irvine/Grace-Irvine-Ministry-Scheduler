#!/usr/bin/env python3
"""
测试并打印 ICS 文件内容
Test and print ICS file content

在本地测试 ICS 生成，并打印各个 ICS 的例子
"""

import os
import sys
from pathlib import Path
from datetime import date, datetime

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.json_data_reader import get_json_data_reader
from src.multi_calendar_generator import (
    generate_media_team_calendar,
    generate_children_team_calendar,
    generate_weekly_overview_calendar
)
from src.ics_notification_config import get_config_manager
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def print_separator(title: str = ""):
    """打印分隔线"""
    if title:
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80)
    else:
        print("\n" + "-" * 80)


def test_data_source():
    """测试数据源"""
    print_separator("📊 测试数据源")
    
    try:
        reader = get_json_data_reader()
        
        # 测试读取最新数据
        print("\n1. 读取最新数据...")
        latest_data = reader.get_latest_data()
        if latest_data:
            print(f"   ✅ 成功读取数据")
            print(f"   📋 数据键: {list(latest_data.keys())}")
            
            # 显示第一个条目示例
            if 'service_schedule' in latest_data and latest_data['service_schedule']:
                first_item = latest_data['service_schedule'][0]
                print(f"\n   📅 第一条数据示例:")
                print(f"      日期: {first_item.get('date')}")
                if 'sermon' in first_item:
                    sermon = first_item['sermon']
                    print(f"      证道主题: {sermon.get('title', 'N/A')}")
                    print(f"      讲员: {sermon.get('speaker', 'N/A')}")
                if 'volunteers' in first_item:
                    volunteers = first_item['volunteers']
                    print(f"      媒体部: {bool(volunteers.get('media'))}")
                    print(f"      儿童部: {bool(volunteers.get('children'))}")
        else:
            print(f"   ❌ 未读取到数据")
            return False
        
        # 测试读取媒体部数据
        print("\n2. 读取媒体部数据...")
        media_data = reader.get_media_team_volunteers()
        print(f"   ✅ 找到 {len(media_data)} 条媒体部安排")
        if media_data:
            print(f"   📅 第一条:")
            print(f"      日期: {media_data[0].get('date')}")
            print(f"      音控: {media_data[0].get('audio_tech', 'N/A')}")
            print(f"      导播/摄影: {media_data[0].get('video_director', 'N/A')}")
        
        # 测试读取儿童部数据
        print("\n3. 读取儿童部数据...")
        children_data = reader.get_children_team_volunteers()
        print(f"   ✅ 找到 {len(children_data)} 条儿童部安排")
        if children_data:
            print(f"   📅 第一条:")
            print(f"      日期: {children_data[0].get('date')}")
            print(f"      老师: {children_data[0].get('teacher', 'N/A')}")
            print(f"      助教: {children_data[0].get('assistant', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    """测试配置"""
    print_separator("⚙️  测试配置")
    
    try:
        config_manager = get_config_manager()
        
        if not config_manager.config:
            print("   ❌ 配置未加载")
            return False
        
        print(f"   ✅ 配置加载成功")
        print(f"   📋 日历类型: {list(config_manager.config.calendars.keys())}")
        
        # 显示媒体部配置
        print("\n   📅 媒体部配置:")
        media_config = config_manager.get_notification_timing('media-team', 'wednesday_confirmation')
        if media_config:
            print(f"      周三确认: {media_config.time_str}, 相对主日 {media_config.relative_to_sunday} 天")
        saturday_config = config_manager.get_notification_timing('media-team', 'saturday_reminder')
        if saturday_config:
            print(f"      周六提醒: {saturday_config.time_str}, 相对主日 {saturday_config.relative_to_sunday} 天")
        
        # 显示每周概览配置
        print("\n   📅 每周概览配置:")
        overview_config = config_manager.get_notification_timing('weekly-overview', 'monday_overview')
        if overview_config:
            print(f"      周一概览: {overview_config.time_str}, 相对主日 {overview_config.relative_to_sunday} 天")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_ics_example(ics_content: str, title: str, max_lines: int = 50):
    """打印 ICS 文件示例"""
    if not ics_content:
        print(f"   ❌ {title} 生成失败")
        return
    
    lines = ics_content.split('\n')
    event_count = ics_content.count('BEGIN:VEVENT')
    
    print(f"\n   ✅ {title} 生成成功")
    print(f"   📊 事件数量: {event_count}")
    print(f"   📏 文件大小: {len(ics_content)} 字节")
    print(f"   📄 总行数: {len(lines)}")
    
    print(f"\n   📋 ICS 文件内容预览（前 {min(max_lines, len(lines))} 行）:")
    print("   " + "-" * 76)
    
    # 打印前 N 行
    for i, line in enumerate(lines[:max_lines], 1):
        # 限制每行长度
        if len(line) > 76:
            line = line[:73] + "..."
        print(f"   {line}")
    
    if len(lines) > max_lines:
        print(f"\n   ... (还有 {len(lines) - max_lines} 行)")
    
    print("   " + "-" * 76)
    
    # 显示第一个事件的详细信息
    if 'BEGIN:VEVENT' in ics_content:
        print(f"\n   📅 第一个事件详情:")
        event_start = ics_content.find('BEGIN:VEVENT')
        event_end = ics_content.find('END:VEVENT', event_start) + len('END:VEVENT')
        first_event = ics_content[event_start:event_end]
        
        event_lines = first_event.split('\n')
        for line in event_lines[:20]:  # 显示前20行
            if line.strip():
                if len(line) > 76:
                    line = line[:73] + "..."
                print(f"      {line}")
        
        if len(event_lines) > 20:
            print(f"      ... (还有 {len(event_lines) - 20} 行)")


def test_media_team_ics():
    """测试并打印媒体部 ICS"""
    print_separator("📅 媒体部服事日历 (media-team.ics)")
    
    try:
        ics_content = generate_media_team_calendar()
        print_ics_example(ics_content, "媒体部服事日历", max_lines=60)
        
        # 保存到文件
        if ics_content:
            test_file = Path("calendars/test_media-team.ics")
            test_file.parent.mkdir(exist_ok=True)
            test_file.write_text(ics_content, encoding='utf-8')
            print(f"\n   💾 已保存到: {test_file.absolute()}")
        
        return ics_content is not None
        
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_children_team_ics():
    """测试并打印儿童部 ICS"""
    print_separator("📅 儿童部服事日历 (children-team.ics)")
    
    try:
        ics_content = generate_children_team_calendar()
        print_ics_example(ics_content, "儿童部服事日历", max_lines=60)
        
        # 保存到文件
        if ics_content:
            test_file = Path("calendars/test_children-team.ics")
            test_file.parent.mkdir(exist_ok=True)
            test_file.write_text(ics_content, encoding='utf-8')
            print(f"\n   💾 已保存到: {test_file.absolute()}")
        
        return ics_content is not None
        
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_weekly_overview_ics():
    """测试并打印每周概览 ICS"""
    print_separator("📅 每周全部事工概览日历 (weekly-overview.ics)")
    
    try:
        ics_content = generate_weekly_overview_calendar()
        print_ics_example(ics_content, "每周全部事工概览日历", max_lines=80)
        
        # 保存到文件
        if ics_content:
            test_file = Path("calendars/test_weekly-overview.ics")
            test_file.parent.mkdir(exist_ok=True)
            test_file.write_text(ics_content, encoding='utf-8')
            print(f"\n   💾 已保存到: {test_file.absolute()}")
        
        return ics_content is not None
        
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("🧪 ICS 文件生成测试 - 打印示例")
    print("=" * 80)
    
    # 检查环境变量
    print("\n📋 环境检查:")
    print(f"   DATA_SOURCE_BUCKET: {os.getenv('DATA_SOURCE_BUCKET', '未设置')}")
    print(f"   GCP_STORAGE_BUCKET: {os.getenv('GCP_STORAGE_BUCKET', '未设置')}")
    print(f"   GOOGLE_CLOUD_PROJECT: {os.getenv('GOOGLE_CLOUD_PROJECT', '未设置')}")
    
    # 运行测试
    results = []
    
    print_separator()
    results.append(("数据源", test_data_source()))
    results.append(("配置", test_config()))
    
    # 测试 ICS 生成
    results.append(("媒体部 ICS", test_media_team_ics()))
    results.append(("儿童部 ICS", test_children_team_ics()))
    results.append(("每周概览 ICS", test_weekly_overview_ics()))
    
    # 总结
    print_separator("📊 测试总结")
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
    
    print_separator()
    print("💡 提示:")
    print("   - 测试文件已保存到 calendars/ 目录")
    print("   - 可以在日历应用中导入这些文件进行测试")
    print("   - 使用 'python start_api.py' 启动 API 服务")


if __name__ == "__main__":
    main()

