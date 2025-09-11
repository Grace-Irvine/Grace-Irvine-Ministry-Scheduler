#!/usr/bin/env python3
"""
测试统一数据模型
Test Unified Data Models
"""

import sys
from pathlib import Path
from datetime import date, timedelta

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_unified_model_import():
    """测试统一模型导入"""
    print("🧪 测试统一模型导入...")
    
    try:
        from src.models import MinistryAssignment, ServiceRole, validate_ministry_assignment
        print("✅ 统一数据模型导入成功")
        
        # 测试枚举
        roles = list(ServiceRole)
        print(f"✅ 服事角色枚举包含 {len(roles)} 个角色")
        
        return True
        
    except Exception as e:
        print(f"❌ 统一模型导入失败: {e}")
        return False

def test_model_functionality():
    """测试模型功能"""
    print("🧪 测试模型功能...")
    
    try:
        from src.models import MinistryAssignment, ServiceRole
        
        # 创建测试实例
        test_date = date.today() + timedelta(days=7)
        assignment = MinistryAssignment(
            date=test_date,
            audio_tech="Jimmy",
            video_director="靖铮",
            propresenter_play="张宇",
            propresenter_update="Daniel"
        )
        
        # 测试基本功能
        assignments_dict = assignment.get_all_assignments()
        if len(assignments_dict) >= 4:  # 至少4个角色
            print(f"✅ get_all_assignments() 返回 {len(assignments_dict)} 个安排")
        else:
            print("❌ get_all_assignments() 返回的安排数量不正确")
            return False
        
        # 测试向后兼容性
        if assignment.camera_operator == assignment.video_director:
            print("✅ 向后兼容字段映射正确")
        else:
            print("❌ 向后兼容字段映射失败")
            return False
        
        # 测试完整性检查
        if assignment.is_complete():
            print("✅ 完整性检查正常")
        else:
            print("❌ 完整性检查失败")
            return False
        
        # 测试字典转换
        dict_data = assignment.to_dict()
        if 'date' in dict_data and 'audio_tech' in dict_data:
            print("✅ 字典转换正常")
        else:
            print("❌ 字典转换失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 模型功能测试失败: {e}")
        return False

def test_cross_module_compatibility():
    """测试跨模块兼容性"""
    print("🧪 测试跨模块兼容性...")
    
    try:
        # 测试数据清洗模块
        from src.data_cleaner import FocusedDataCleaner
        print("✅ 数据清洗模块导入成功")
        
        # 测试调度模块
        from src.scheduler import GoogleSheetsExtractor
        print("✅ 调度模块导入成功")
        
        # 测试模板管理模块
        from src.template_manager import NotificationTemplateManager
        print("✅ 模板管理模块导入成功")
        
        # 测试动态模板管理模块
        from src.dynamic_template_manager import DynamicTemplateManager
        print("✅ 动态模板管理模块导入成功")
        
        # 测试日历生成模块
        from src.calendar_generator import generate_unified_wednesday_template
        print("✅ 日历生成模块导入成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 跨模块兼容性测试失败: {e}")
        return False

def test_data_flow():
    """测试数据流"""
    print("🧪 测试数据流...")
    
    try:
        from src.models import MinistryAssignment
        from src.dynamic_template_manager import DynamicTemplateManager
        
        # 创建测试数据
        test_date = date.today() + timedelta(days=7)
        assignment = MinistryAssignment(
            date=test_date,
            audio_tech="Jimmy",
            video_director="靖铮",
            propresenter_play="张宇"
        )
        
        # 测试模板渲染
        manager = DynamicTemplateManager()
        
        # 测试周三模板
        wed_result = manager.render_weekly_confirmation(test_date, assignment)
        if "Jimmy" in wed_result and "靖铮" in wed_result:
            print("✅ 数据流到周三模板正常")
        else:
            print("❌ 数据流到周三模板失败")
            return False
        
        # 测试周六模板
        sat_result = manager.render_saturday_reminder(test_date, assignment)
        if "Jimmy" in sat_result and "靖铮" in sat_result:
            print("✅ 数据流到周六模板正常")
        else:
            print("❌ 数据流到周六模板失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 数据流测试失败: {e}")
        return False

def test_legacy_compatibility():
    """测试向后兼容性"""
    print("🧪 测试向后兼容性...")
    
    try:
        from src.models import MinistryAssignment
        from src.data_cleaner import MinistrySchedule  # 应该是别名
        
        # 测试别名
        if MinistrySchedule == MinistryAssignment:
            print("✅ 向后兼容别名正确")
        else:
            print("❌ 向后兼容别名失败")
            return False
        
        # 测试创建实例
        test_date = date.today() + timedelta(days=7)
        
        # 使用新模型
        new_assignment = MinistryAssignment(
            date=test_date,
            audio_tech="Jimmy",
            video_director="靖铮"
        )
        
        # 使用别名（向后兼容）
        legacy_assignment = MinistrySchedule(
            date=test_date,
            audio_tech="Jimmy",
            video_director="靖铮"
        )
        
        if type(new_assignment) == type(legacy_assignment):
            print("✅ 新旧模型类型一致")
        else:
            print("❌ 新旧模型类型不一致")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 向后兼容性测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 Grace Irvine Ministry Scheduler - 统一数据模型测试")
    print("=" * 60)
    
    tests = [
        ("统一模型导入", test_unified_model_import),
        ("模型功能", test_model_functionality),
        ("跨模块兼容性", test_cross_module_compatibility),
        ("数据流", test_data_flow),
        ("向后兼容性", test_legacy_compatibility),
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
        print("🎉 所有测试通过！数据模型统一化成功")
        
        print("\n✅ 统一化成果:")
        print("  • 创建了统一的MinistryAssignment数据模型")
        print("  • 所有模块使用相同的数据结构")
        print("  • 保持了向后兼容性")
        print("  • 添加了数据验证功能")
        print("  • 支持角色枚举和类型安全")
        
        print("\n🔧 改进:")
        print("  • 字段名称统一化")
        print("  • 数据类型一致化")
        print("  • 功能方法标准化")
        print("  • 向后兼容性保证")
        
    else:
        print("⚠️ 部分测试失败，需要进一步调整")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
