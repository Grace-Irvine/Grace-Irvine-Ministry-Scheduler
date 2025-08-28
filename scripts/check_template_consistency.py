#!/usr/bin/env python3
"""
检查模板一致性脚本
检查不同地方的模板定义是否一致
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.template_manager import NotificationTemplateManager
from src.scheduler import GoogleSheetsExtractor, NotificationGenerator
from datetime import date, timedelta

def check_template_consistency():
    """检查模板一致性"""
    print("🔍 检查模板一致性")
    print("=" * 60)
    
    # 1. 检查 src/template_manager.py 中的模板
    print("\n📋 1. src/template_manager.py 中的周六提醒模板")
    print("-" * 40)
    
    template_manager = NotificationTemplateManager()
    
    # 创建测试数据
    test_assignment = type('TestAssignment', (), {
        'date': date.today() + timedelta(days=1),
        'audio_tech': '张三',
        'screen_operator': '李四',
        'camera_operator': '王五',
        'propresenter': '赵六',
        'video_editor': '靖铮'
    })()
    
    # 渲染周六提醒模板
    saturday_content = template_manager.render_sunday_reminder(test_assignment)
    print("渲染结果:")
    print(saturday_content)
    
    # 2. 检查 streamlit_app.py 中的模板
    print("\n📋 2. streamlit_app.py 中的周六提醒模板")
    print("-" * 40)
    
    # 模拟 streamlit_app.py 中的 generate_saturday_template_focused 函数
    def generate_saturday_template_focused(sunday_date, schedule):
        """生成周六提醒通知模板 - 专注版"""
        template = f"""【主日服事提醒】✨
明天 8:30布置/ 9:00彩排 / 10:00 正式敬拜  
请各位同工提前到场：  

"""
        
        # 模拟 get_all_assignments 方法
        assignments = {
            '音控': '张三',
            '导播/摄影': '王五',
            'ProPresenter播放': '赵六',
            'ProPresenter更新': '靖铮'
        }
        
        if assignments.get('音控'):
            template += f"- 音控：{assignments['音控']} 9:00到，随敬拜团排练\n"
        else:
            template += "- 音控：待确认 9:00到，随敬拜团排练\n"
        
        if assignments.get('导播/摄影'):
            template += f"- 导播/摄影: {assignments['导播/摄影']} 9:30到，检查预设机位\n"
        else:
            template += "- 导播/摄影: 待确认 9:30到，检查预设机位\n"
        
        if assignments.get('ProPresenter播放'):
            template += f"- ProPresenter播放：{assignments['ProPresenter播放']} 9:00到，随敬拜团排练\n"
        else:
            template += "- ProPresenter播放：待确认 9:00到，随敬拜团排练\n"
        
        if assignments.get('ProPresenter更新'):
            template += f"- ProPresenter更新：{assignments['ProPresenter更新']} 提前准备内容\n"
        else:
            template += "- ProPresenter更新：待确认 提前准备内容\n"
        
        template += "\n愿主同在，出入平安。若临时不适请第一时间私信我。🙌"
        
        return template
    
    # 模拟 schedule 对象
    class MockSchedule:
        def get_all_assignments(self):
            return {
                '音控': '张三',
                '导播/摄影': '王五',
                'ProPresenter播放': '赵六',
                'ProPresenter更新': '靖铮'
            }
    
    mock_schedule = MockSchedule()
    streamlit_content = generate_saturday_template_focused(date.today() + timedelta(days=1), mock_schedule)
    print("渲染结果:")
    print(streamlit_content)
    
    # 3. 检查 templates/notification_templates.yaml 中的模板
    print("\n📋 3. templates/notification_templates.yaml 中的周六提醒模板")
    print("-" * 40)
    
    yaml_template = template_manager.get_template('sunday_reminder', 'template')
    print("原始模板:")
    print(yaml_template)
    
    # 4. 比较差异
    print("\n📋 4. 模板差异分析")
    print("-" * 40)
    
    print("🔍 主要差异:")
    print("1. src/template_manager.py:")
    print("   - 只显示3种事工: 音控、导播/摄影、ProPresenter播放")
    print("   - 不显示 ProPresenter更新")
    
    print("\n2. streamlit_app.py:")
    print("   - 显示4种事工: 音控、导播/摄影、ProPresenter播放、ProPresenter更新")
    print("   - 包含 ProPresenter更新")
    
    print("\n3. templates/notification_templates.yaml:")
    print("   - 显示5种事工: 音控、屏幕、摄像/导播、ProPresenter制作、视频剪辑")
    print("   - 使用不同的角色名称")
    
    # 5. 检查 NotificationGenerator 使用哪个模板
    print("\n📋 5. NotificationGenerator 使用的模板")
    print("-" * 40)
    
    try:
        # 模拟 GoogleSheetsExtractor
        class MockExtractor:
            def get_next_sunday_assignment(self):
                return test_assignment
        
        mock_extractor = MockExtractor()
        generator = NotificationGenerator(mock_extractor, template_manager)
        
        generated_content = generator.generate_sunday_reminder()
        print("NotificationGenerator.generate_sunday_reminder() 结果:")
        print(generated_content)
        
    except Exception as e:
        print(f"无法测试 NotificationGenerator: {e}")
    
    # 6. 建议修复方案
    print("\n📋 6. 修复建议")
    print("-" * 40)
    
    print("❌ 问题: 存在多个不同的模板定义，导致UI显示与实际模板内容不一致")
    print("\n✅ 解决方案:")
    print("1. 统一模板定义 - 所有地方使用相同的模板")
    print("2. 修改 src/template_manager.py 中的 render_sunday_reminder 方法")
    print("3. 确保 streamlit_app.py 使用 template_manager 而不是硬编码模板")
    print("4. 更新 templates/notification_templates.yaml 以匹配实际需求")

if __name__ == "__main__":
    check_template_consistency()
