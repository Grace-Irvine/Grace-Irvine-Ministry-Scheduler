#!/usr/bin/env python3
"""
最终架构测试
Final Architecture Test

验证简化和重构后的完整功能
"""

import sys
import os
from pathlib import Path
from datetime import date, timedelta

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_file_organization():
    """测试文件组织结构"""
    print("🧪 测试文件组织结构...")
    
    expected_files = {
        "start.py": "统一启动入口",
        "app_unified.py": "统一Web应用", 
        "generate_calendars.py": "日历生成启动器",
        "src/calendar_generator.py": "ICS日历生成器"
    }
    
    removed_files = [
        "start_service.py",
        "run_enhanced_streamlit.py", 
        "app_with_static_routes.py",
        "generate_real_calendars.py"
    ]
    
    # 检查预期文件
    missing_files = []
    for file, desc in expected_files.items():
        if not Path(file).exists():
            missing_files.append(f"{file} ({desc})")
    
    # 检查已删除的文件
    still_exists = []
    for file in removed_files:
        if Path(file).exists():
            still_exists.append(file)
    
    if missing_files:
        print(f"❌ 缺少文件: {', '.join(missing_files)}")
        return False
    
    if still_exists:
        print(f"❌ 应删除但仍存在的文件: {', '.join(still_exists)}")
        return False
    
    print("✅ 文件组织结构正确")
    return True

def test_calendar_generation():
    """测试日历生成功能"""
    print("🧪 测试日历生成功能...")
    
    try:
        from src.calendar_generator import generate_coordinator_calendar
        
        # 检查是否能成功导入
        print("✅ 日历生成器模块导入成功")
        
        # 检查生成的日历文件
        coordinator_ics = Path("calendars/grace_irvine_coordinator.ics")
        if coordinator_ics.exists():
            with open(coordinator_ics, 'r', encoding='utf-8') as f:
                content = f.read()
            
            event_count = content.count("BEGIN:VEVENT")
            if event_count > 0:
                print(f"✅ 负责人日历包含 {event_count} 个事件")
            else:
                print("❌ 负责人日历没有事件")
                return False
        else:
            print("❌ 负责人日历文件不存在")
            return False
        
        # 检查同工日历文件是否被正确移除
        workers_ics = Path("calendars/grace_irvine_workers.ics")
        if workers_ics.exists():
            print("❌ 同工日历文件仍然存在，应该被移除")
            return False
        else:
            print("✅ 同工日历文件已正确移除")
        
        return True
        
    except Exception as e:
        print(f"❌ 日历生成功能测试失败: {e}")
        return False

def test_template_consistency():
    """测试模板一致性"""
    print("🧪 测试模板一致性...")
    
    try:
        from src.models import MinistryAssignment
        from app_unified import generate_wednesday_template, generate_saturday_template
        from src.calendar_generator import generate_unified_wednesday_template, generate_unified_saturday_template
        
        # 创建测试数据
        test_date = date.today() + timedelta(days=7)
        test_schedule = MinistryAssignment(
            date=test_date,
            audio_tech="Jimmy",
            video_director="靖铮",
            propresenter_play="张宇",
            propresenter_update="Daniel"
        )
        
        # 测试周三模板
        frontend_wed = generate_wednesday_template(test_date, test_schedule)
        ics_wed = generate_unified_wednesday_template(test_date, test_schedule)
        
        if frontend_wed.strip() == ics_wed.strip():
            print("✅ 周三确认通知模板一致")
        else:
            print("❌ 周三确认通知模板不一致")
            return False
        
        # 测试周六模板
        frontend_sat = generate_saturday_template(test_date, test_schedule)
        ics_sat = generate_unified_saturday_template(test_date, test_schedule)
        
        if frontend_sat.strip() == ics_sat.strip():
            print("✅ 周六提醒通知模板一致")
        else:
            print("❌ 周六提醒通知模板不一致")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 模板一致性测试失败: {e}")
        return False

def test_ics_event_parsing():
    """测试ICS事件解析"""
    print("🧪 测试ICS事件解析...")
    
    try:
        from app_unified import parse_ics_events
        
        coordinator_ics = Path("calendars/grace_irvine_coordinator.ics")
        if not coordinator_ics.exists():
            print("❌ 负责人日历文件不存在")
            return False
        
        with open(coordinator_ics, 'r', encoding='utf-8') as f:
            content = f.read()
        
        events = parse_ics_events(content)
        
        if len(events) > 0:
            print(f"✅ 成功解析 {len(events)} 个事件")
            
            # 检查第一个事件的内容
            first_event = events[0]
            description = first_event.get('description', '')
            
            if "【本周" in description or "【主日服事提醒】" in description:
                print("✅ 事件描述包含正确的模板内容")
                return True
            else:
                print("❌ 事件描述不包含预期的模板内容")
                return False
        else:
            print("❌ 未解析到任何事件")
            return False
            
    except Exception as e:
        print(f"❌ ICS事件解析测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 Grace Irvine Ministry Scheduler - 最终架构测试")
    print("=" * 60)
    
    tests = [
        ("文件组织结构", test_file_organization),
        ("日历生成功能", test_calendar_generation),
        ("模板一致性", test_template_consistency),
        ("ICS事件解析", test_ics_event_parsing),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 最终测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！架构重构完全成功")
        print("\n✅ 重构成果:")
        print("  • 统一了入口点 (start.py)")
        print("  • 规范了文件组织 (src/calendar_generator.py)")
        print("  • 修复了模板一致性")
        print("  • 添加了ICS事件查看功能") 
        print("  • 简化了同工日历功能（留到下阶段）")
        
        print("\n🚀 现在可以使用:")
        print("  python3 start.py               # 启动完整应用")
        print("  python3 generate_calendars.py  # 生成ICS日历")
        
    else:
        print("⚠️ 部分测试失败，需要进一步调整")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
