#!/usr/bin/env python3
"""
获取模板内容工具
演示如何在ICS日历系统中获取和使用模板内容

用法:
  python scripts/get_template_content.py --type all           # 获取所有模板
  python scripts/get_template_content.py --type weekly       # 获取周三确认模板
  python scripts/get_template_content.py --type sunday       # 获取周六提醒模板
  python scripts/get_template_content.py --type monthly      # 获取月度总览模板
  python scripts/get_template_content.py --raw               # 获取原始模板（未渲染）
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime, date

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.template_manager import NotificationTemplateManager, get_default_template_manager
from src.scheduler import GoogleSheetsExtractor, NotificationGenerator
from dotenv import load_dotenv

def print_separator(title: str):
    """打印分隔符"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def get_raw_templates():
    """获取原始模板内容（未渲染）"""
    print_separator("原始模板内容")
    
    try:
        template_manager = NotificationTemplateManager()
        
        # 周三确认通知模板
        print("\n📅 【周三确认通知模板】")
        print("-" * 40)
        weekly_template = template_manager.get_template('weekly_confirmation', 'template')
        print(weekly_template)
        
        # 周六提醒通知模板
        print("\n🔔 【周六提醒通知模板】")
        print("-" * 40)
        sunday_template = template_manager.get_template('sunday_reminder', 'template')
        print(sunday_template)
        
        # 月度总览模板
        print("\n📊 【月度总览通知模板】")
        print("-" * 40)
        monthly_template = template_manager.get_template('monthly_overview', 'template')
        if monthly_template:
            print(monthly_template)
        else:
            print("⚠️  月度总览模板未找到")
        
        # 显示模板变量
        print_separator("模板变量说明")
        print("周三/周六模板变量:")
        print("  {month} - 月份")
        print("  {day} - 日期")
        print("  {audio_tech} - 音控同工")
        print("  {screen_operator} - 屏幕操作同工")
        print("  {camera_operator} - 摄像/导播同工")
        print("  {propresenter} - ProPresenter制作同工")
        print("  {video_editor} - 视频剪辑同工")
        
        print("\n月度模板变量:")
        print("  {year} - 年份")
        print("  {month} - 月份")
        print("  {sheet_url} - Google Sheets链接")
        print("  {schedule_text} - 排班详情文本")
        
    except Exception as e:
        print(f"❌ 获取原始模板时出错: {e}")

def get_rendered_templates(template_type: str = 'all'):
    """获取渲染后的模板内容"""
    print_separator("渲染后的模板内容")
    
    try:
        # 加载环境变量
        load_dotenv()
        spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
        
        if not spreadsheet_id:
            print("❌ 错误: 请在 .env 文件中设置 GOOGLE_SPREADSHEET_ID")
            return
        
        # 初始化组件
        print("🔗 正在连接 Google Sheets...")
        extractor = GoogleSheetsExtractor(spreadsheet_id)
        generator = NotificationGenerator(extractor)
        
        print("✅ 连接成功，正在生成模板内容...")
        
        if template_type in ['all', 'weekly']:
            print("\n📅 【周三确认通知 - 渲染后】")
            print("-" * 40)
            try:
                weekly_content = generator.generate_weekly_confirmation()
                print(weekly_content)
            except Exception as e:
                print(f"⚠️  生成周三通知时出错: {e}")
        
        if template_type in ['all', 'sunday']:
            print("\n🔔 【周六提醒通知 - 渲染后】")
            print("-" * 40)
            try:
                sunday_content = generator.generate_sunday_reminder()
                print(sunday_content)
            except Exception as e:
                print(f"⚠️  生成周六通知时出错: {e}")
        
        if template_type in ['all', 'monthly']:
            print("\n📊 【月度总览通知 - 渲染后】")
            print("-" * 40)
            try:
                monthly_content = generator.generate_monthly_overview()
                print(monthly_content)
            except Exception as e:
                print(f"⚠️  生成月度通知时出错: {e}")
        
    except Exception as e:
        print(f"❌ 获取渲染模板时出错: {e}")

def get_template_for_ics():
    """演示如何在ICS系统中获取模板内容"""
    print_separator("ICS系统中的模板获取")
    
    try:
        # 加载环境变量
        load_dotenv()
        spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
        
        if not spreadsheet_id:
            print("❌ 错误: 请在 .env 文件中设置 GOOGLE_SPREADSHEET_ID")
            return
        
        # 模拟ICS管理器中的模板获取过程
        from src.scheduler import MinistryAssignment
        from datetime import date, timedelta
        
        print("🔧 模拟ICS管理器中的模板获取过程...")
        
        # 创建模拟数据
        today = date.today()
        next_sunday = today + timedelta(days=(6-today.weekday()))
        
        test_assignment = MinistryAssignment(
            date=next_sunday,
            audio_tech="张三",
            screen_operator="李四",
            camera_operator="王五",
            propresenter="赵六",
            video_editor="靖铮"
        )
        
        # 获取模板管理器
        template_manager = get_default_template_manager()
        
        # 渲染模板内容（这就是ICS管理器中使用的方法）
        weekly_content = template_manager.render_weekly_confirmation(test_assignment)
        sunday_content = template_manager.render_sunday_reminder(test_assignment)
        
        print("\n📋 ICS事件中的模板内容示例:")
        print("\n【周三确认事件描述】")
        print(f"发送内容：\n\n{weekly_content}")
        
        print("\n【周六提醒事件描述】")
        print(f"发送内容：\n\n{sunday_content}")
        
        # 显示如何在代码中使用
        print_separator("代码使用示例")
        print("""
# 在ICS管理器中获取模板内容的方法:

from src.template_manager import get_default_template_manager

# 1. 获取模板管理器
template_manager = get_default_template_manager()

# 2. 渲染模板内容
notification_content = template_manager.render_weekly_confirmation(assignment)

# 3. 在ICS事件中使用
event = CalendarEvent(
    title="发送周末确认通知",
    description=f"发送内容：\\n\\n{notification_content}",
    # ... 其他属性
)
        """)
        
    except Exception as e:
        print(f"❌ 演示过程中出错: {e}")

def show_template_structure():
    """显示模板文件结构"""
    print_separator("模板文件结构")
    
    try:
        template_manager = NotificationTemplateManager()
        all_templates = template_manager.get_all_templates()
        
        print("📁 模板文件: templates/notification_templates.yaml")
        print("\n🏗️  模板结构:")
        
        for template_type, config in all_templates.items():
            print(f"\n📋 {template_type}:")
            for key, value in config.items():
                if key == 'template':
                    print(f"  ├── {key}: (主模板内容)")
                elif key == 'defaults':
                    print(f"  ├── {key}: (默认值配置)")
                    for default_key, default_value in value.items():
                        print(f"  │   ├── {default_key}: {default_value}")
                else:
                    print(f"  ├── {key}: {type(value).__name__}")
        
        print("\n💡 获取模板的方法:")
        print("  template_manager.get_template('weekly_confirmation', 'template')")
        print("  template_manager.render_weekly_confirmation(assignment)")
        
    except Exception as e:
        print(f"❌ 显示模板结构时出错: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Grace Irvine 模板内容获取工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--type', choices=['all', 'weekly', 'sunday', 'monthly'], 
                       default='all', help='获取的模板类型')
    parser.add_argument('--raw', action='store_true', 
                       help='获取原始模板（未渲染）')
    parser.add_argument('--structure', action='store_true',
                       help='显示模板文件结构')
    parser.add_argument('--ics-demo', action='store_true',
                       help='演示ICS系统中的模板使用')
    
    args = parser.parse_args()
    
    print("🎯 Grace Irvine 模板内容获取工具")
    print(f"⏰ 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.structure:
        show_template_structure()
    elif args.ics_demo:
        get_template_for_ics()
    elif args.raw:
        get_raw_templates()
    else:
        get_rendered_templates(args.type)
    
    print_separator("完成")
    print("✅ 模板内容获取完成！")
    
    if not args.raw:
        print("\n💡 提示:")
        print("- 使用 --raw 参数查看原始模板格式")
        print("- 使用 --structure 参数查看模板文件结构")
        print("- 使用 --ics-demo 参数查看ICS系统使用示例")

if __name__ == "__main__":
    main()
