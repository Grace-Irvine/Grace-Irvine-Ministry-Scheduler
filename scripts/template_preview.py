#!/usr/bin/env python3
"""
模板预览和管理工具
提供直观的模板查看、修改和测试功能

用法:
  python template_preview.py preview         # 预览所有模板
  python template_preview.py test            # 测试模板渲染
  python template_preview.py structure       # 查看模板结构
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import date

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.template_manager import get_default_template_manager
from src.scheduler import GoogleSheetsExtractor
from dotenv import load_dotenv

def print_section(title: str, content: str = None):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)
    if content:
        print(content)

def print_subsection(title: str):
    """打印子节标题"""
    print(f"\n📋 {title}")
    print('-'*40)

def cmd_preview(args):
    """预览所有模板"""
    print("🎯 Grace Irvine 模板预览工具")
    
    try:
        # 获取测试数据
        load_dotenv()
        spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
        
        if spreadsheet_id:
            extractor = GoogleSheetsExtractor(spreadsheet_id)
            assignments = extractor.parse_ministry_data()
            future_assignments = [a for a in assignments if a.date >= date.today()]
            test_assignment = future_assignments[0] if future_assignments else None
        else:
            test_assignment = None
            print("⚠️  未设置Google Sheets ID，将显示模板结构")
        
        template_manager = get_default_template_manager()
        
        # 预览周三确认通知
        print_section("周三确认通知模板")
        weekly_preview = template_manager.preview_weekly_confirmation(test_assignment)
        
        print(f"📝 描述: {weekly_preview['description']}")
        print(f"⏰ 发送时间: {weekly_preview['send_time']}")
        print(f"🎯 目的: {weekly_preview['purpose']}")
        
        print_subsection("包含的事工角色")
        for role in weekly_preview['included_roles']:
            print(f"  ✅ {role}")
        
        print_subsection("排除的事工角色")
        for role in weekly_preview['excluded_roles']:
            print(f"  ❌ {role}")
        
        if 'sample_content' in weekly_preview:
            print_subsection("示例内容")
            print(weekly_preview['sample_content'])
            
            print_subsection("数据映射")
            for role, person in weekly_preview['data_mapping'].items():
                status = "✅" if person and person.strip() else "❌"
                print(f"  {status} {role}: {person or '(空)'}")
        
        # 预览周六提醒通知
        print_section("周六提醒通知模板")
        sunday_preview = template_manager.preview_sunday_reminder(test_assignment)
        
        print(f"📝 描述: {sunday_preview['description']}")
        print(f"⏰ 发送时间: {sunday_preview['send_time']}")
        print(f"🎯 目的: {sunday_preview['purpose']}")
        
        print_subsection("包含的事工角色")
        for role in sunday_preview['included_roles']:
            print(f"  ✅ {role}")
        
        print_subsection("排除的事工角色")
        for role in sunday_preview['excluded_roles']:
            print(f"  ❌ {role}")
        
        print_subsection("到场时间安排")
        for role, instruction in sunday_preview['arrival_times'].items():
            print(f"  🕘 {role}: {instruction}")
        
        if 'sample_content' in sunday_preview:
            print_subsection("示例内容")
            print(sunday_preview['sample_content'])
            
            print_subsection("数据映射")
            for role, person in sunday_preview['data_mapping'].items():
                status = "✅" if person and person.strip() else "❌"
                print(f"  {status} {role}: {person or '(空)'}")
        
        print_section("预览完成")
        print("💡 使用 'python template_preview.py test' 来测试实际渲染效果")
        
    except Exception as e:
        print(f"❌ 预览过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

def cmd_test(args):
    """测试模板渲染"""
    print("🧪 模板渲染测试")
    
    try:
        # 获取实际数据
        load_dotenv()
        spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
        
        if not spreadsheet_id:
            print("❌ 错误: 请在 .env 文件中设置 GOOGLE_SPREADSHEET_ID")
            return
        
        print("📊 正在获取Google Sheets数据...")
        extractor = GoogleSheetsExtractor(spreadsheet_id)
        assignments = extractor.parse_ministry_data()
        
        future_assignments = [a for a in assignments if a.date >= date.today()]
        if not future_assignments:
            print("❌ 未找到未来的事工安排数据")
            return
        
        template_manager = get_default_template_manager()
        
        print(f"✅ 成功获取 {len(assignments)} 条事工安排")
        print(f"📅 测试最近的安排: {future_assignments[0].date}")
        
        # 测试周三确认通知
        print_section("周三确认通知测试")
        assignment = future_assignments[0]
        
        print(f"📊 测试数据 ({assignment.date}):")
        print(f"  音控: {assignment.audio_tech or '(空)'}")
        print(f"  导播/摄影: {assignment.camera_operator or '(空)'}")
        print(f"  ProPresenter播放: {assignment.propresenter or '(空)'}")
        print(f"  ProPresenter更新: {assignment.video_editor or '(空)'}")
        
        weekly_content = template_manager.render_weekly_confirmation(assignment)
        print_subsection("渲染结果")
        print(weekly_content)
        
        # 测试周六提醒通知
        print_section("周六提醒通知测试")
        
        sunday_content = template_manager.render_sunday_reminder(assignment)
        print_subsection("渲染结果")
        print(sunday_content)
        
        # 对比测试多个数据
        if len(future_assignments) > 1:
            print_section("多数据对比测试")
            
            for i, assignment in enumerate(future_assignments[:3], 1):
                print_subsection(f"测试数据 {i} ({assignment.date})")
                
                # 显示原始数据
                print("原始数据:")
                print(f"  音控: {assignment.audio_tech or '(空)'}")
                print(f"  导播/摄影: {assignment.camera_operator or '(空)'}")
                print(f"  ProPresenter播放: {assignment.propresenter or '(空)'}")
                
                # 显示渲染结果
                weekly_result = template_manager.render_weekly_confirmation(assignment)
                print("\n周三通知:")
                for line in weekly_result.split('\n')[:6]:  # 只显示前6行
                    if line.strip():
                        print(f"  {line}")
                print("  ...")
        
        print_section("测试完成")
        print("✅ 所有模板渲染正常")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

def cmd_structure(args):
    """查看模板结构"""
    print("🏗️ 模板结构概览")
    
    try:
        template_manager = get_default_template_manager()
        structure = template_manager.get_template_structure()
        
        print_section("模板类型")
        for template_key, template_info in structure['template_types'].items():
            print(f"\n📋 {template_info['name']} ({template_key})")
            print(f"   方法: {template_info['method']}")
            print(f"   发送时间: {template_info['send_time']}")
            print(f"   包含角色: {', '.join(template_info['roles'])}")
        
        print_section("数据源配置")
        print(f"📊 数据来源: {structure['data_source']}")
        
        print_subsection("Google Sheets 列映射")
        for field, description in structure['configuration'].items():
            print(f"  {field}: {description}")
        
        print_section("模板渲染逻辑")
        print("🔧 周三确认通知 (render_weekly_confirmation):")
        print("   1. 检查事工安排数据")
        print("   2. 只显示4种事工: 音控、导播/摄影、ProPresenter播放、ProPresenter更新")
        print("   3. 隐藏空角色（无人员分配的角色）")
        print("   4. 生成确认格式的通知")
        
        print("\n🔧 周六提醒通知 (render_sunday_reminder):")
        print("   1. 检查事工安排数据")
        print("   2. 只显示3种事工: 音控、导播/摄影、ProPresenter播放")
        print("   3. 包含具体的到场时间和注意事项")
        print("   4. 生成提醒格式的通知")
        
        print_section("修改指南")
        print("💡 如需修改模板:")
        print("   1. 编辑 src/template_manager.py 中的渲染方法")
        print("   2. 修改 ministry_roles 列表来调整显示的角色")
        print("   3. 修改 content 字符串来调整通知格式")
        print("   4. 使用 'python template_preview.py test' 测试修改结果")
        
        print("\n🔧 常见修改:")
        print("   - 添加新角色: 在 ministry_roles 列表中添加")
        print("   - 修改到场时间: 在 arrival_instruction 中修改")
        print("   - 调整通知格式: 修改 content 构建逻辑")
        print("   - 修改表情符号: 直接在字符串中修改")
        
    except Exception as e:
        print(f"❌ 查看结构时出现错误: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Grace Irvine 模板预览和管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # preview 命令
    parser_preview = subparsers.add_parser('preview', help='预览所有模板')
    parser_preview.set_defaults(func=cmd_preview)
    
    # test 命令
    parser_test = subparsers.add_parser('test', help='测试模板渲染')
    parser_test.set_defaults(func=cmd_test)
    
    # structure 命令
    parser_structure = subparsers.add_parser('structure', help='查看模板结构')
    parser_structure.set_defaults(func=cmd_structure)
    
    # 解析参数
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        print("\n💡 建议:")
        print("  python template_preview.py preview   # 查看模板预览")
        print("  python template_preview.py test      # 测试实际渲染")
        print("  python template_preview.py structure # 了解模板结构")
        sys.exit(1)
    
    # 执行命令
    args.func(args)

if __name__ == "__main__":
    main()
