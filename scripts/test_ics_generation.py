#!/usr/bin/env python3
"""
测试 ICS 文件生成
Test ICS file generation

测试新系统的 ICS 日历生成功能
"""

import os
import sys
import json
from pathlib import Path
from datetime import date, datetime

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.json_data_reader import get_json_data_reader
from src.multi_calendar_generator import generate_all_calendars, generate_media_team_calendar, generate_children_team_calendar, generate_weekly_overview_calendar
from src.ics_notification_config import get_config_manager
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_json_data_reader():
    """测试 JSON 数据读取器"""
    print("=" * 60)
    print("📊 测试 JSON 数据读取器")
    print("=" * 60)
    
    try:
        reader = get_json_data_reader()
        
        # 测试读取最新数据
        print("\n1. 测试读取最新数据...")
        latest_data = reader.get_latest_data()
        if latest_data:
            print(f"   ✅ 成功读取数据")
            print(f"   📊 数据键: {list(latest_data.keys())}")
        else:
            print(f"   ❌ 未读取到数据")
            return False
        
        # 测试读取服事安排
        print("\n2. 测试读取服事安排...")
        schedules = reader.get_service_schedule()
        print(f"   ✅ 找到 {len(schedules)} 条服事安排")
        if schedules:
            print(f"   📅 第一条日期: {schedules[0].get('date')}")
        
        # 测试读取媒体部数据
        print("\n3. 测试读取媒体部数据...")
        media_data = reader.get_media_team_volunteers()
        print(f"   ✅ 找到 {len(media_data)} 条媒体部安排")
        if media_data:
            print(f"   📅 第一条日期: {media_data[0].get('date')}")
            print(f"   👤 音控: {media_data[0].get('audio_tech')}")
        
        # 测试读取儿童部数据
        print("\n4. 测试读取儿童部数据...")
        children_data = reader.get_children_team_volunteers()
        print(f"   ✅ 找到 {len(children_data)} 条儿童部安排")
        if children_data:
            print(f"   📅 第一条日期: {children_data[0].get('date')}")
            print(f"   👤 老师: {children_data[0].get('teacher')}")
        
        # 测试读取每周概览
        print("\n5. 测试读取每周概览...")
        overview_data = reader.get_weekly_overview()
        print(f"   ✅ 找到 {len(overview_data)} 条每周概览")
        if overview_data:
            print(f"   📅 第一条日期: {overview_data[0].get('date')}")
            print(f"   📖 证道主题: {overview_data[0].get('sermon', {}).get('title', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ics_config():
    """测试 ICS 配置"""
    print("\n" + "=" * 60)
    print("⚙️  测试 ICS 配置")
    print("=" * 60)
    
    try:
        config_manager = get_config_manager()
        
        # 测试读取配置
        print("\n1. 测试读取配置...")
        if config_manager.config:
            print(f"   ✅ 配置加载成功")
            print(f"   📋 日历类型: {list(config_manager.config.calendars.keys())}")
        else:
            print(f"   ❌ 配置未加载")
            return False
        
        # 测试获取媒体部配置
        print("\n2. 测试获取媒体部配置...")
        media_config = config_manager.get_notification_timing('media-team', 'wednesday_confirmation')
        if media_config:
            print(f"   ✅ 周三确认通知配置:")
            print(f"      - 相对主日: {media_config.relative_to_sunday} 天")
            print(f"      - 时间: {media_config.time_str}")
            print(f"      - 持续时间: {media_config.duration_minutes} 分钟")
            print(f"      - 提醒提前: {media_config.reminder_minutes} 分钟")
        else:
            print(f"   ⚠️  未找到配置")
        
        # 测试获取每周概览配置
        print("\n3. 测试获取每周概览配置...")
        overview_config = config_manager.get_notification_timing('weekly-overview', 'monday_overview')
        if overview_config:
            print(f"   ✅ 周一概览通知配置:")
            print(f"      - 相对主日: {overview_config.relative_to_sunday} 天")
            print(f"      - 时间: {overview_config.time_str}")
            print(f"      - 持续时间: {overview_config.duration_minutes} 分钟")
            print(f"      - 提醒提前: {overview_config.reminder_minutes} 分钟")
        else:
            print(f"   ⚠️  未找到配置")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ics_generation():
    """测试 ICS 生成"""
    print("\n" + "=" * 60)
    print("📅 测试 ICS 生成")
    print("=" * 60)
    
    try:
        # 测试生成媒体部日历
        print("\n1. 测试生成媒体部日历...")
        media_ics = generate_media_team_calendar()
        if media_ics:
            event_count = media_ics.count('BEGIN:VEVENT')
            print(f"   ✅ 生成成功")
            print(f"   📊 事件数量: {event_count}")
            print(f"   📏 文件大小: {len(media_ics)} 字节")
            
            # 保存测试文件
            test_file = Path("calendars/test_media-team.ics")
            test_file.parent.mkdir(exist_ok=True)
            test_file.write_text(media_ics, encoding='utf-8')
            print(f"   💾 已保存到: {test_file}")
        else:
            print(f"   ❌ 生成失败")
        
        # 测试生成儿童部日历
        print("\n2. 测试生成儿童部日历...")
        children_ics = generate_children_team_calendar()
        if children_ics:
            event_count = children_ics.count('BEGIN:VEVENT')
            print(f"   ✅ 生成成功")
            print(f"   📊 事件数量: {event_count}")
            print(f"   📏 文件大小: {len(children_ics)} 字节")
            
            # 保存测试文件
            test_file = Path("calendars/test_children-team.ics")
            test_file.write_text(children_ics, encoding='utf-8')
            print(f"   💾 已保存到: {test_file}")
        else:
            print(f"   ❌ 生成失败")
        
        # 测试生成每周概览日历
        print("\n3. 测试生成每周概览日历...")
        overview_ics = generate_weekly_overview_calendar()
        if overview_ics:
            event_count = overview_ics.count('BEGIN:VEVENT')
            print(f"   ✅ 生成成功")
            print(f"   📊 事件数量: {event_count}")
            print(f"   📏 文件大小: {len(overview_ics)} 字节")
            
            # 保存测试文件
            test_file = Path("calendars/test_weekly-overview.ics")
            test_file.write_text(overview_ics, encoding='utf-8')
            print(f"   💾 已保存到: {test_file}")
        else:
            print(f"   ❌ 生成失败")
        
        # 测试生成所有日历
        print("\n4. 测试生成所有日历...")
        results = generate_all_calendars()
        if results['success']:
            print(f"   ✅ 生成成功")
            for calendar_type, calendar_result in results['calendars'].items():
                status = "✅" if calendar_result['success'] else "❌"
                events = calendar_result['events']
                print(f"   {status} {calendar_type}: {events} 个事件")
        else:
            print(f"   ⚠️  部分生成失败")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_ics_format(ics_content: str) -> bool:
    """验证 ICS 文件格式"""
    if not ics_content:
        return False
    
    # 检查必需的 ICS 元素
    required_elements = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'END:VCALENDAR'
    ]
    
    for element in required_elements:
        if element not in ics_content:
            print(f"   ❌ 缺少必需元素: {element}")
            return False
    
    # 检查事件格式
    if 'BEGIN:VEVENT' in ics_content:
        event_count = ics_content.count('BEGIN:VEVENT')
        end_count = ics_content.count('END:VEVENT')
        if event_count != end_count:
            print(f"   ❌ 事件未正确闭合: BEGIN={event_count}, END={end_count}")
            return False
        
        # 检查每个事件的基本字段
        events = ics_content.split('BEGIN:VEVENT')
        for i, event in enumerate(events[1:], 1):
            required_fields = ['UID', 'DTSTART', 'DTEND', 'SUMMARY']
            for field in required_fields:
                if field not in event:
                    print(f"   ❌ 事件 {i} 缺少字段: {field}")
                    return False
    
    return True


def test_ics_validation():
    """测试 ICS 文件验证"""
    print("\n" + "=" * 60)
    print("✅ 测试 ICS 文件验证")
    print("=" * 60)
    
    test_files = [
        "calendars/test_media-team.ics",
        "calendars/test_children-team.ics",
        "calendars/test_weekly-overview.ics"
    ]
    
    for test_file in test_files:
        file_path = Path(test_file)
        if file_path.exists():
            print(f"\n📄 验证文件: {test_file}")
            content = file_path.read_text(encoding='utf-8')
            if validate_ics_format(content):
                print(f"   ✅ 格式验证通过")
            else:
                print(f"   ❌ 格式验证失败")
        else:
            print(f"\n⚠️  文件不存在: {test_file}")


def main():
    """主函数"""
    print("🧪 ICS 文件生成测试")
    print("=" * 60)
    
    # 检查环境变量
    print("\n📋 环境检查:")
    print(f"   DATA_SOURCE_BUCKET: {os.getenv('DATA_SOURCE_BUCKET', '未设置')}")
    print(f"   GCP_STORAGE_BUCKET: {os.getenv('GCP_STORAGE_BUCKET', '未设置')}")
    print(f"   GOOGLE_CLOUD_PROJECT: {os.getenv('GOOGLE_CLOUD_PROJECT', '未设置')}")
    
    # 运行测试
    results = []
    
    results.append(("JSON 数据读取器", test_json_data_reader()))
    results.append(("ICS 配置", test_ics_config()))
    results.append(("ICS 生成", test_ics_generation()))
    test_ics_validation()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print("\n💡 提示:")
    print("   - 测试文件已保存到 calendars/ 目录")
    print("   - 可以在日历应用中导入这些文件进行测试")
    print("   - 使用 'python start_api.py' 启动 API 服务进行 API 测试")


if __name__ == "__main__":
    main()

