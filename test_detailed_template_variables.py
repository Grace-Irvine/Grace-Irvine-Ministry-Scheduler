#!/usr/bin/env python3
"""
测试细化的模板变量
Test Detailed Template Variables
"""

import sys
from pathlib import Path
from datetime import date, timedelta

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_detailed_variables():
    """测试细化的模板变量"""
    print("🧪 测试细化的模板变量...")
    
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
            propresenter_update="Daniel",
            video_editor="靖铮"
        )
        
        # 测试周三模板
        wed_result = manager.render_weekly_confirmation(test_date, test_schedule)
        
        print("📋 周三确认通知模板结果:")
        print("-" * 50)
        print(wed_result)
        print("-" * 50)
        
        # 验证各个变量是否正确替换
        checks = [
            ("月份", f"{test_date.month}月", wed_result),
            ("日期", f"{test_date.day}日", wed_result),
            ("音控", "Jimmy", wed_result),
            ("导播/摄影", "靖铮", wed_result),
            ("ProPresenter播放", "张宇", wed_result),
            ("ProPresenter更新", "Daniel", wed_result),
            ("视频剪辑", "靖铮", wed_result)
        ]
        
        all_passed = True
        for var_name, expected_value, content in checks:
            if expected_value in content:
                print(f"✅ {var_name} 变量替换正确: {expected_value}")
            else:
                print(f"❌ {var_name} 变量替换失败: 期望 {expected_value}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 细化变量测试失败: {e}")
        return False

def test_template_editing_flexibility():
    """测试模板编辑灵活性"""
    print("🧪 测试模板编辑灵活性...")
    
    try:
        from src.dynamic_template_manager import DynamicTemplateManager
        from src.models import MinistryAssignment
        
        manager = DynamicTemplateManager()
        
        # 获取周三模板配置
        template_config = manager.get_template('weekly_confirmation')
        if not template_config:
            print("❌ 无法获取周三模板配置")
            return False
        
        # 测试自定义模板格式
        custom_templates = [
            # 格式1：简洁版
            "【{month}月{day}日事工安排】\n音控：{audio_tech}\n导播：{video_director}\n播放：{propresenter_play}",
            
            # 格式2：详细版  
            "🕊️ 本周{month}月{day}日主日安排：\n\n🎤 音控同工：{audio_tech}\n📹 导播摄影：{video_director}\n🖥️ ProPresenter播放：{propresenter_play}\n🔄 ProPresenter更新：{propresenter_update}\n🎬 视频剪辑：{video_editor}\n\n请确认时间 🙏",
            
            # 格式3：表格版
            "【主日事工安排】\n┌─────────────┬─────────────┐\n│ 音控        │ {audio_tech}  │\n│ 导播/摄影   │ {video_director} │\n│ PP播放      │ {propresenter_play} │\n└─────────────┴─────────────┘"
        ]
        
        test_date = date.today() + timedelta(days=7)
        test_schedule = MinistryAssignment(
            date=test_date,
            audio_tech="Jimmy",
            video_director="靖铮",
            propresenter_play="张宇",
            propresenter_update="Daniel"
        )
        
        for i, custom_template in enumerate(custom_templates, 1):
            print(f"\n📝 测试自定义格式 {i}:")
            
            # 临时更新模板
            original_template = template_config['template']
            template_config['template'] = custom_template
            manager.update_template('weekly_confirmation', template_config)
            
            # 渲染测试
            result = manager.render_weekly_confirmation(test_date, test_schedule)
            
            # 检查是否包含人员信息
            if "Jimmy" in result and "靖铮" in result:
                print(f"✅ 格式 {i} 渲染正常")
                print(f"   结果: {result[:100]}...")
            else:
                print(f"❌ 格式 {i} 渲染失败")
                return False
            
            # 恢复原模板
            template_config['template'] = original_template
            manager.update_template('weekly_confirmation', template_config)
        
        return True
        
    except Exception as e:
        print(f"❌ 模板编辑灵活性测试失败: {e}")
        return False

def test_variable_documentation():
    """测试变量文档"""
    print("🧪 测试变量文档...")
    
    try:
        from src.dynamic_template_manager import DynamicTemplateManager
        
        manager = DynamicTemplateManager()
        
        # 测试获取变量文档
        variables = manager.get_template_variables('weekly_confirmation')
        
        expected_variables = [
            'month', 'day', 'audio_tech', 'video_director', 
            'propresenter_play', 'propresenter_update', 'video_editor'
        ]
        
        missing_vars = []
        for var in expected_variables:
            if var not in variables:
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ 缺少变量文档: {', '.join(missing_vars)}")
            return False
        
        print(f"✅ 变量文档完整，包含 {len(variables)} 个变量:")
        for var, desc in variables.items():
            print(f"   • {{{var}}}: {desc}")
        
        return True
        
    except Exception as e:
        print(f"❌ 变量文档测试失败: {e}")
        return False

def test_template_validation():
    """测试模板验证"""
    print("🧪 测试模板验证...")
    
    try:
        from src.dynamic_template_manager import DynamicTemplateManager
        
        manager = DynamicTemplateManager()
        
        # 测试有效模板
        valid_template = "【{month}月{day}日安排】\n音控：{audio_tech}\n导播：{video_director}"
        is_valid, msg = manager.validate_template('weekly_confirmation', valid_template)
        
        if is_valid:
            print(f"✅ 有效模板验证通过: {msg}")
        else:
            print(f"❌ 有效模板验证失败: {msg}")
            return False
        
        # 测试无效模板（缺少必需变量）
        invalid_template = "简单的通知内容，没有变量"
        is_valid, msg = manager.validate_template('weekly_confirmation', invalid_template)
        
        if not is_valid:
            print(f"✅ 无效模板正确被拒绝: {msg}")
        else:
            print(f"❌ 无效模板错误通过验证")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 模板验证测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 Grace Irvine Ministry Scheduler - 细化模板变量测试")
    print("=" * 60)
    
    tests = [
        ("细化模板变量", test_detailed_variables),
        ("模板编辑灵活性", test_template_editing_flexibility),
        ("变量文档", test_variable_documentation),
        ("模板验证", test_template_validation),
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
        print("🎉 所有测试通过！细化模板变量功能正常")
        
        print("\n✅ 细化改进:")
        print("  • {assignments_text} → 细化为各个角色变量")
        print("  • {audio_tech} - 音控人员")
        print("  • {video_director} - 导播/摄影人员")
        print("  • {propresenter_play} - ProPresenter播放人员")
        print("  • {propresenter_update} - ProPresenter更新人员")
        print("  • {video_editor} - 视频剪辑人员")
        
        print("\n🛠️ 编辑优势:")
        print("  • 可以自由调整各角色的显示格式")
        print("  • 可以选择显示或隐藏某些角色")
        print("  • 可以添加自定义的角色描述")
        print("  • 支持完全自定义的布局")
        
        print("\n💡 示例模板格式:")
        print("  简洁版: 音控：{audio_tech}，导播：{video_director}")
        print("  详细版: 🎤 音控同工：{audio_tech}")
        print("  表格版: │ 音控 │ {audio_tech} │")
        
    else:
        print("⚠️ 部分测试失败，需要进一步调整")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
