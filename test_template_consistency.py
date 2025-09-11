#!/usr/bin/env python3
"""
测试前端模板和ICS模板的一致性
Test consistency between frontend templates and ICS templates
"""

import sys
from pathlib import Path
from datetime import date, timedelta

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_cleaner import FocusedDataCleaner
from src.models import MinistryAssignment
from app_unified import generate_wednesday_template, generate_saturday_template
from src.calendar_generator import generate_unified_wednesday_template, generate_unified_saturday_template

def create_test_schedule():
    """创建测试用的排程数据"""
    test_date = date.today() + timedelta(days=7)  # 下周日
    
    schedule = MinistryAssignment(
        date=test_date,
        audio_tech="Jimmy",
        video_director="靖铮", 
        propresenter_play="张宇",
        propresenter_update="Daniel"
    )
    
    return schedule

def test_wednesday_template_consistency():
    """测试周三确认通知模板一致性"""
    print("🧪 测试周三确认通知模板一致性...")
    
    test_schedule = create_test_schedule()
    
    # 前端模板
    frontend_template = generate_wednesday_template(test_schedule.date, test_schedule)
    
    # ICS模板
    ics_template = generate_unified_wednesday_template(test_schedule.date, test_schedule)
    
    print("📋 前端模板:")
    print("-" * 40)
    print(frontend_template)
    print()
    
    print("📋 ICS模板:")
    print("-" * 40)
    print(ics_template)
    print()
    
    # 比较一致性
    if frontend_template.strip() == ics_template.strip():
        print("✅ 周三确认通知模板完全一致")
        return True
    else:
        print("❌ 周三确认通知模板不一致")
        print("\n🔍 差异分析:")
        frontend_lines = frontend_template.strip().split('\n')
        ics_lines = ics_template.strip().split('\n')
        
        max_lines = max(len(frontend_lines), len(ics_lines))
        for i in range(max_lines):
            f_line = frontend_lines[i] if i < len(frontend_lines) else ""
            i_line = ics_lines[i] if i < len(ics_lines) else ""
            
            if f_line != i_line:
                print(f"  行 {i+1}:")
                print(f"    前端: '{f_line}'")
                print(f"    ICS:  '{i_line}'")
        
        return False

def test_saturday_template_consistency():
    """测试周六提醒通知模板一致性"""
    print("🧪 测试周六提醒通知模板一致性...")
    
    test_schedule = create_test_schedule()
    
    # 前端模板
    frontend_template = generate_saturday_template(test_schedule.date, test_schedule)
    
    # ICS模板
    ics_template = generate_unified_saturday_template(test_schedule.date, test_schedule)
    
    print("📋 前端模板:")
    print("-" * 40)
    print(frontend_template)
    print()
    
    print("📋 ICS模板:")
    print("-" * 40)
    print(ics_template)
    print()
    
    # 比较一致性
    if frontend_template.strip() == ics_template.strip():
        print("✅ 周六提醒通知模板完全一致")
        return True
    else:
        print("❌ 周六提醒通知模板不一致")
        print("\n🔍 差异分析:")
        frontend_lines = frontend_template.strip().split('\n')
        ics_lines = ics_template.strip().split('\n')
        
        max_lines = max(len(frontend_lines), len(ics_lines))
        for i in range(max_lines):
            f_line = frontend_lines[i] if i < len(frontend_lines) else ""
            i_line = ics_lines[i] if i < len(ics_lines) else ""
            
            if f_line != i_line:
                print(f"  行 {i+1}:")
                print(f"    前端: '{f_line}'")
                print(f"    ICS:  '{i_line}'")
        
        return False

def test_ics_events_parsing():
    """测试ICS事件解析功能"""
    print("🧪 测试ICS事件解析功能...")
    
    calendar_dir = Path("calendars")
    coordinator_ics = calendar_dir / "grace_irvine_coordinator.ics"
    
    if not coordinator_ics.exists():
        print("❌ 负责人日历文件不存在")
        return False
    
    try:
        with open(coordinator_ics, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用app_unified中的解析函数
        from app_unified import parse_ics_events
        events = parse_ics_events(content)
        
        print(f"📊 解析到 {len(events)} 个事件")
        
        if events:
            # 显示第一个事件的详细信息
            first_event = events[0]
            print(f"\n📋 第一个事件示例:")
            print(f"  标题: {first_event.get('summary', 'N/A')}")
            print(f"  开始时间: {first_event.get('start_time', 'N/A')}")
            print(f"  地点: {first_event.get('location', 'N/A')}")
            print(f"  描述: {first_event.get('description', 'N/A')[:100]}...")
            
            # 检查是否包含模板内容
            description = first_event.get('description', '')
            print(f"🔍 实际描述内容: {description[:200]}...")
            
            if "【本周" in description and "主日事工安排提醒】" in description:
                print("✅ ICS事件包含正确的模板内容")
                return True
            elif "发送内容：" in description and "【本周" in description:
                print("✅ ICS事件包含正确的模板内容（包含发送前缀）")
                return True
            else:
                print("❌ ICS事件不包含预期的模板内容")
                return False
        else:
            print("❌ 未解析到任何事件")
            return False
            
    except Exception as e:
        print(f"❌ 解析ICS文件失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 Grace Irvine Ministry Scheduler - 模板一致性测试")
    print("=" * 60)
    
    tests = [
        ("周三确认通知模板一致性", test_wednesday_template_consistency),
        ("周六提醒通知模板一致性", test_saturday_template_consistency),
        ("ICS事件解析功能", test_ics_events_parsing),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if test_func():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！模板一致性修复成功")
        print("\n✅ 现在前端模板和ICS事件内容完全一致")
        print("✅ ICS事件内容查看功能正常工作")
        print("\n💡 您可以:")
        print("1. 在Web界面的'日历管理'页面点击'🔍 查看ICS事件内容'")
        print("2. 对比前端生成的模板和ICS事件描述")
        print("3. 确认两者内容完全一致")
    else:
        print("⚠️ 部分测试失败，需要进一步调整")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
