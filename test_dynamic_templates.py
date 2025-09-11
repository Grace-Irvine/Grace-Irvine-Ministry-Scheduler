#!/usr/bin/env python3
"""
测试动态模板系统
Test Dynamic Template System
"""

import sys
from pathlib import Path
from datetime import date, timedelta

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_template_loading():
    """测试模板加载"""
    print("🧪 测试模板加载...")
    
    try:
        from src.dynamic_template_manager import DynamicTemplateManager
        
        manager = DynamicTemplateManager()
        templates = manager.get_all_templates()
        
        if templates and 'templates' in templates:
            template_count = len(templates['templates'])
            print(f"✅ 成功加载 {template_count} 个模板")
            
            # 检查必需的模板
            required_templates = ['weekly_confirmation', 'saturday_reminder', 'monthly_overview']
            missing_templates = []
            
            for template_type in required_templates:
                if template_type not in templates['templates']:
                    missing_templates.append(template_type)
            
            if missing_templates:
                print(f"❌ 缺少模板: {', '.join(missing_templates)}")
                return False
            else:
                print("✅ 所有必需模板都存在")
                return True
        else:
            print("❌ 模板加载失败")
            return False
            
    except Exception as e:
        print(f"❌ 模板加载测试失败: {e}")
        return False

def test_template_rendering():
    """测试模板渲染"""
    print("🧪 测试模板渲染...")
    
    try:
        from src.dynamic_template_manager import DynamicTemplateManager
        from src.models import MinistryAssignment
        
        manager = DynamicTemplateManager()
        
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
        wed_result = manager.render_weekly_confirmation(test_date, test_schedule)
        if "【本周" in wed_result and "事工安排提醒】" in wed_result:
            print("✅ 周三确认通知渲染正常")
        else:
            print("❌ 周三确认通知渲染失败")
            return False
        
        # 测试周六模板
        sat_result = manager.render_saturday_reminder(test_date, test_schedule)
        if "【主日服事提醒】" in sat_result:
            print("✅ 周六提醒通知渲染正常")
        else:
            print("❌ 周六提醒通知渲染失败")
            return False
        
        # 测试月度模板
        monthly_result = manager.render_monthly_overview([test_schedule], test_date.year, test_date.month)
        if "月事工排班一览" in monthly_result:
            print("✅ 月度总览通知渲染正常")
        else:
            print("❌ 月度总览通知渲染失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 模板渲染测试失败: {e}")
        return False

def test_frontend_integration():
    """测试前端集成"""
    print("🧪 测试前端集成...")
    
    try:
        from app_unified import generate_wednesday_template, generate_saturday_template, generate_monthly_template
        from src.models import MinistryAssignment
        
        # 创建测试数据
        test_date = date.today() + timedelta(days=7)
        test_schedule = MinistryAssignment(
            date=test_date,
            audio_tech="Jimmy",
            video_director="靖铮",
            propresenter_play="张宇",
            propresenter_update="Daniel"
        )
        
        # 测试前端模板生成
        wed_template = generate_wednesday_template(test_date, test_schedule)
        if "【本周" in wed_template:
            print("✅ 前端周三模板生成正常")
        else:
            print("❌ 前端周三模板生成失败")
            return False
        
        sat_template = generate_saturday_template(test_date, test_schedule)
        if "【主日服事提醒】" in sat_template:
            print("✅ 前端周六模板生成正常")
        else:
            print("❌ 前端周六模板生成失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 前端集成测试失败: {e}")
        return False

def test_calendar_integration():
    """测试日历生成集成"""
    print("🧪 测试日历生成集成...")
    
    try:
        from src.calendar_generator import generate_unified_wednesday_template, generate_unified_saturday_template
        from src.models import MinistryAssignment
        
        # 创建测试数据
        test_date = date.today() + timedelta(days=7)
        test_schedule = MinistryAssignment(
            date=test_date,
            audio_tech="Jimmy",
            video_director="靖铮",
            propresenter_play="张宇",
            propresenter_update="Daniel"
        )
        
        # 测试日历模板生成
        wed_ics = generate_unified_wednesday_template(test_date, test_schedule)
        if "【本周" in wed_ics:
            print("✅ 日历周三模板生成正常")
        else:
            print("❌ 日历周三模板生成失败")
            return False
        
        sat_ics = generate_unified_saturday_template(test_date, test_schedule)
        if "【主日服事提醒】" in sat_ics:
            print("✅ 日历周六模板生成正常")
        else:
            print("❌ 日历周六模板生成失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 日历集成测试失败: {e}")
        return False

def test_template_consistency():
    """测试模板一致性"""
    print("🧪 测试动态模板一致性...")
    
    try:
        from app_unified import generate_wednesday_template, generate_saturday_template
        from src.calendar_generator import generate_unified_wednesday_template, generate_unified_saturday_template
        from src.models import MinistryAssignment
        
        # 创建测试数据
        test_date = date.today() + timedelta(days=7)
        test_schedule = MinistryAssignment(
            date=test_date,
            audio_tech="Jimmy",
            video_director="靖铮",
            propresenter_play="张宇",
            propresenter_update="Daniel"
        )
        
        # 比较周三模板
        frontend_wed = generate_wednesday_template(test_date, test_schedule)
        calendar_wed = generate_unified_wednesday_template(test_date, test_schedule)
        
        if frontend_wed.strip() == calendar_wed.strip():
            print("✅ 周三模板完全一致")
        else:
            print("❌ 周三模板不一致")
            return False
        
        # 比较周六模板
        frontend_sat = generate_saturday_template(test_date, test_schedule)
        calendar_sat = generate_unified_saturday_template(test_date, test_schedule)
        
        if frontend_sat.strip() == calendar_sat.strip():
            print("✅ 周六模板完全一致")
        else:
            print("❌ 周六模板不一致")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 模板一致性测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 Grace Irvine Ministry Scheduler - 动态模板系统测试")
    print("=" * 60)
    
    tests = [
        ("模板加载", test_template_loading),
        ("模板渲染", test_template_rendering),
        ("前端集成", test_frontend_integration),
        ("日历集成", test_calendar_integration),
        ("模板一致性", test_template_consistency),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！动态模板系统工作正常")
        
        print("\n✅ 新功能:")
        print("  • 模板存储在JSON文件中，可以随时编辑")
        print("  • 支持GCP Storage云端存储")
        print("  • Web界面可在线编辑模板")
        print("  • 自动备份和版本控制")
        print("  • 本地和云端模板完全一致")
        
        print("\n🚀 使用方法:")
        print("  1. python3 start.py  # 启动应用")
        print("  2. 访问'🛠️ 模板编辑器'页面")
        print("  3. 在线编辑和保存模板")
        print("  4. 部署到GCP时自动使用云端存储")
        
    else:
        print("⚠️ 部分测试失败，需要进一步调整")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
