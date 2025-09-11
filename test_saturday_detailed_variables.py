#!/usr/bin/env python3
"""
测试周六模板细化变量
Test Saturday Template Detailed Variables
"""

import sys
from pathlib import Path
from datetime import date, timedelta

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_saturday_detailed_variables():
    """测试周六模板细化变量"""
    print("🧪 测试周六模板细化变量...")
    
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
        
        # 测试周六模板
        sat_result = manager.render_saturday_reminder(test_date, test_schedule)
        
        print("📋 周六提醒通知模板结果:")
        print("-" * 50)
        print(sat_result)
        print("-" * 50)
        
        # 验证各个详细变量是否正确生成
        expected_details = [
            ("Jimmy 9:00到，随敬拜团排练", "音控详情"),
            ("靖铮 9:30到，检查预设机位", "导播详情"),
            ("张宇 9:00到，随敬拜团排练", "ProPresenter播放详情")
        ]
        
        all_passed = True
        for expected_detail, desc in expected_details:
            if expected_detail in sat_result:
                print(f"✅ {desc} 正确: {expected_detail}")
            else:
                print(f"❌ {desc} 失败: 期望包含 '{expected_detail}'")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 周六细化变量测试失败: {e}")
        return False

def test_saturday_template_flexibility():
    """测试周六模板编辑灵活性"""
    print("🧪 测试周六模板编辑灵活性...")
    
    try:
        from src.dynamic_template_manager import DynamicTemplateManager
        from src.models import MinistryAssignment
        
        manager = DynamicTemplateManager()
        
        # 获取周六模板配置
        template_config = manager.get_template('saturday_reminder')
        if not template_config:
            print("❌ 无法获取周六模板配置")
            return False
        
        # 测试自定义模板格式
        custom_templates = [
            # 格式1：简洁版
            "【明日主日】✨\n音控：{audio_tech_detail}\n导播：{video_director_detail}\n播放：{propresenter_play_detail}",
            
            # 格式2：时间重点版  
            "🔔 明日服事提醒：\n\n⏰ 9:00 到场：{audio_tech_detail}\n⏰ 9:30 到场：{video_director_detail}\n⏰ 9:00 到场：{propresenter_play_detail}\n\n愿主同在！",
            
            # 格式3：emoji版
            "✨ 明日主日 ✨\n🎤 {audio_tech_detail}\n📹 {video_director_detail}\n🖥️ {propresenter_play_detail}\n\n🙏 请提前到场"
        ]
        
        test_date = date.today() + timedelta(days=7)
        test_schedule = MinistryAssignment(
            date=test_date,
            audio_tech="Jimmy",
            video_director="靖铮",
            propresenter_play="张宇"
        )
        
        for i, custom_template in enumerate(custom_templates, 1):
            print(f"\n📝 测试自定义周六格式 {i}:")
            
            # 临时更新模板
            original_template = template_config['template']
            template_config['template'] = custom_template
            manager.update_template('saturday_reminder', template_config)
            
            # 渲染测试
            result = manager.render_saturday_reminder(test_date, test_schedule)
            
            # 检查是否包含人员信息和时间信息
            if "Jimmy" in result and "9:00" in result:
                print(f"✅ 格式 {i} 渲染正常")
                print(f"   结果: {result[:100]}...")
            else:
                print(f"❌ 格式 {i} 渲染失败")
                print(f"   实际结果: {result}")
                return False
            
            # 恢复原模板
            template_config['template'] = original_template
            manager.update_template('saturday_reminder', template_config)
        
        return True
        
    except Exception as e:
        print(f"❌ 周六模板编辑灵活性测试失败: {e}")
        return False

def test_saturday_variables_documentation():
    """测试周六模板变量文档"""
    print("🧪 测试周六模板变量文档...")
    
    try:
        from src.dynamic_template_manager import DynamicTemplateManager
        
        manager = DynamicTemplateManager()
        
        # 测试获取变量文档
        variables = manager.get_template_variables('saturday_reminder')
        
        expected_variables = [
            'audio_tech_detail', 'video_director_detail', 
            'propresenter_play_detail', 'propresenter_update_detail'
        ]
        
        missing_vars = []
        for var in expected_variables:
            if var not in variables:
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ 缺少变量文档: {', '.join(missing_vars)}")
            return False
        
        print(f"✅ 周六模板变量文档完整，包含 {len(variables)} 个变量:")
        for var, desc in variables.items():
            print(f"   • {{{var}}}: {desc}")
        
        return True
        
    except Exception as e:
        print(f"❌ 周六变量文档测试失败: {e}")
        return False

def test_no_assignment_handling():
    """测试无安排情况处理"""
    print("🧪 测试无安排情况处理...")
    
    try:
        from src.dynamic_template_manager import DynamicTemplateManager
        
        manager = DynamicTemplateManager()
        test_date = date.today() + timedelta(days=7)
        
        # 测试完全无安排
        result_no_schedule = manager.render_saturday_reminder(test_date, None)
        
        if "暂无明日事工安排" in result_no_schedule:
            print("✅ 无安排模板正确")
        else:
            print("❌ 无安排模板失败")
            return False
        
        # 测试部分安排
        from src.models import MinistryAssignment
        partial_schedule = MinistryAssignment(
            date=test_date,
            audio_tech="Jimmy"  # 只有音控安排
        )
        
        result_partial = manager.render_saturday_reminder(test_date, partial_schedule)
        
        if "Jimmy" in result_partial and "待确认" in result_partial:
            print("✅ 部分安排处理正确（有人员和待确认）")
        else:
            print("❌ 部分安排处理失败")
            print(f"   结果: {result_partial}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 无安排情况处理测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 Grace Irvine Ministry Scheduler - 周六模板细化变量测试")
    print("=" * 60)
    
    tests = [
        ("周六细化变量", test_saturday_detailed_variables),
        ("周六模板灵活性", test_saturday_template_flexibility),
        ("周六变量文档", test_saturday_variables_documentation),
        ("无安排情况处理", test_no_assignment_handling),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if test_func():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！周六模板细化变量功能正常")
        
        print("\n✅ 周六模板细化改进:")
        print("  • {service_details} → 细化为各角色详细变量")
        print("  • {audio_tech_detail} - 音控详细安排")
        print("  • {video_director_detail} - 导播/摄影详细安排")
        print("  • {propresenter_play_detail} - ProPresenter播放详细安排")
        print("  • {propresenter_update_detail} - ProPresenter更新详细安排")
        
        print("\n🛠️ 编辑优势:")
        print("  • 可以自定义每个角色的显示格式")
        print("  • 可以调整到场时间和说明")
        print("  • 可以选择显示哪些角色")
        print("  • 支持完全自定义布局")
        
        print("\n💡 示例编辑格式:")
        print("  简洁版: 音控：{audio_tech_detail}")
        print("  时间版: ⏰ 9:00 {audio_tech_detail}")
        print("  emoji版: 🎤 {audio_tech_detail}")
        
    else:
        print("⚠️ 部分测试失败，需要进一步调整")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
