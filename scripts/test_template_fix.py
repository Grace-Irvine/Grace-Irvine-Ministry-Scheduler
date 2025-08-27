#!/usr/bin/env python3
"""
测试模板修复脚本
验证修复后的模板一致性
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.template_manager import NotificationTemplateManager
from src.scheduler import NotificationGenerator
from datetime import date, timedelta

def test_template_fix():
    """测试模板修复"""
    print("🧪 测试模板修复效果")
    print("=" * 60)
    
    # 创建测试数据
    test_assignment = type('TestAssignment', (), {
        'date': date.today() + timedelta(days=1),
        'audio_tech': '张三',
        'screen_operator': '李四',
        'camera_operator': '王五',
        'propresenter': '赵六',
        'video_editor': '靖铮'
    })()
    
    # 1. 测试 template_manager
    print("\n📋 1. 测试 src/template_manager.py")
    print("-" * 40)
    
    template_manager = NotificationTemplateManager()
    saturday_content = template_manager.render_sunday_reminder(test_assignment)
    print("周六提醒模板内容:")
    print(saturday_content)
    
    # 检查是否包含 ProPresenter更新
    if "ProPresenter更新" in saturday_content:
        print("✅ 包含 ProPresenter更新")
    else:
        print("❌ 不包含 ProPresenter更新")
    
    # 2. 测试 NotificationGenerator
    print("\n📋 2. 测试 NotificationGenerator")
    print("-" * 40)
    
    class MockExtractor:
        def get_next_sunday_assignment(self):
            return test_assignment
    
    mock_extractor = MockExtractor()
    generator = NotificationGenerator(mock_extractor, template_manager)
    
    generated_content = generator.generate_sunday_reminder()
    print("NotificationGenerator 生成的周六提醒:")
    print(generated_content)
    
    # 检查是否包含 ProPresenter更新
    if "ProPresenter更新" in generated_content:
        print("✅ 包含 ProPresenter更新")
    else:
        print("❌ 不包含 ProPresenter更新")
    
    # 3. 测试模板结构
    print("\n📋 3. 测试模板结构")
    print("-" * 40)
    
    structure = template_manager.get_template_structure()
    sunday_roles = structure['template_types']['sunday_reminder']['roles']
    print(f"周六提醒模板包含的角色: {sunday_roles}")
    
    if 'ProPresenter更新' in sunday_roles:
        print("✅ 模板结构中包含 ProPresenter更新")
    else:
        print("❌ 模板结构中不包含 ProPresenter更新")
    
    # 4. 测试预览功能
    print("\n📋 4. 测试预览功能")
    print("-" * 40)
    
    preview = template_manager.preview_sunday_reminder(test_assignment)
    included_roles = preview['included_roles']
    print(f"预览中包含的角色: {included_roles}")
    
    if 'ProPresenter更新' in included_roles:
        print("✅ 预览中包含 ProPresenter更新")
    else:
        print("❌ 预览中不包含 ProPresenter更新")
    
    # 5. 总结
    print("\n📋 5. 修复总结")
    print("-" * 40)
    
    all_tests_passed = (
        "ProPresenter更新" in saturday_content and
        "ProPresenter更新" in generated_content and
        'ProPresenter更新' in sunday_roles and
        'ProPresenter更新' in included_roles
    )
    
    if all_tests_passed:
        print("🎉 所有测试通过！模板修复成功！")
        print("✅ src/template_manager.py 已更新")
        print("✅ NotificationGenerator 使用统一模板")
        print("✅ 模板结构已更新")
        print("✅ 预览功能已更新")
    else:
        print("❌ 部分测试失败，需要进一步检查")

if __name__ == "__main__":
    test_template_fix()
