#!/usr/bin/env python3
"""
负责人日历测试脚本
生成负责人ICS日历并显示最近的日历事件内容

用法:
  python test_coordinator_calendar.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
import re

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.scheduler import GoogleSheetsExtractor
from src.ics_manager import ICSManager
from src.template_manager import get_default_template_manager
from dotenv import load_dotenv

def setup_environment():
    """设置环境"""
    load_dotenv()
    
    spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
    if not spreadsheet_id:
        print("❌ 错误: 请在 .env 文件中设置 GOOGLE_SPREADSHEET_ID")
        sys.exit(1)
    
    service_account_path = Path("configs/service_account.json")
    if not service_account_path.exists():
        print("❌ 错误: 服务账户文件不存在 configs/service_account.json")
        sys.exit(1)
    
    return spreadsheet_id

def parse_ics_file(ics_path: str) -> List[Dict[str, Any]]:
    """解析ICS文件并提取事件信息"""
    events = []
    
    try:
        with open(ics_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用正则表达式提取事件
        event_pattern = r'BEGIN:VEVENT(.*?)END:VEVENT'
        event_matches = re.findall(event_pattern, content, re.DOTALL)
        
        for event_content in event_matches:
            event = {}
            
            # 提取标题
            summary_match = re.search(r'SUMMARY:(.*?)(?:\r?\n|\r)', event_content)
            if summary_match:
                event['title'] = summary_match.group(1).strip()
            
            # 提取描述
            description_match = re.search(r'DESCRIPTION:(.*?)(?:\r?\n[A-Z]|\r?\n$)', event_content, re.DOTALL)
            if description_match:
                description = description_match.group(1).strip()
                # 处理换行符
                description = description.replace('\\n', '\n').replace('\\,', ',').replace('\\;', ';')
                event['description'] = description
            
            # 提取开始时间
            dtstart_match = re.search(r'DTSTART[^:]*:(.*?)(?:\r?\n|\r)', event_content)
            if dtstart_match:
                event['start_time'] = dtstart_match.group(1).strip()
            
            # 提取UID
            uid_match = re.search(r'UID:(.*?)(?:\r?\n|\r)', event_content)
            if uid_match:
                event['uid'] = uid_match.group(1).strip()
            
            events.append(event)
        
        # 按开始时间排序
        events.sort(key=lambda x: x.get('start_time', ''))
        
        return events
        
    except Exception as e:
        print(f"❌ 解析ICS文件时出错: {e}")
        return []

def format_datetime(dt_string: str) -> str:
    """格式化日期时间字符串"""
    try:
        # 处理不同的日期格式
        if 'T' in dt_string:
            if dt_string.endswith('Z'):
                dt = datetime.strptime(dt_string, '%Y%m%dT%H%M%SZ')
            else:
                dt = datetime.strptime(dt_string, '%Y%m%dT%H%M%S')
        else:
            dt = datetime.strptime(dt_string, '%Y%m%d')
        
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return dt_string

def main():
    """主函数"""
    print("🎯 负责人日历测试")
    print("=" * 60)
    
    try:
        # 设置环境
        spreadsheet_id = setup_environment()
        
        # 初始化组件
        print("🔗 正在初始化组件...")
        extractor = GoogleSheetsExtractor(spreadsheet_id)
        ics_manager = ICSManager()
        template_manager = get_default_template_manager()
        
        print("✅ 组件初始化完成")
        
        # 获取事工安排数据
        print("📊 正在获取Google Sheets数据...")
        assignments = extractor.parse_ministry_data()
        
        if not assignments:
            print("❌ 未找到事工安排数据")
            return
        
        print(f"✅ 成功获取 {len(assignments)} 条事工安排")
        
        # 生成负责人日历
        print("📅 正在生成负责人日历...")
        
        try:
            # 设置日期范围
            start_date = date.today() - timedelta(days=30)
            end_date = date.today() + timedelta(days=90)
            
            coordinator_calendar_path = ics_manager.generate_coordinator_calendar(
                assignments, 
                start_date=start_date,
                end_date=end_date
            )
            
            print(f"✅ 负责人日历已生成: {coordinator_calendar_path}")
            
        except Exception as e:
            print(f"❌ 生成负责人日历时出错: {e}")
            print("🔧 尝试直接生成示例事件...")
            
            # 手动生成一些示例事件来展示
            show_sample_events(assignments, template_manager)
            return
        
        # 解析并显示ICS文件内容
        print("\n📋 解析ICS文件内容...")
        events = parse_ics_file(coordinator_calendar_path)
        
        if not events:
            print("⚠️  未找到日历事件")
            return
        
        print(f"✅ 找到 {len(events)} 个日历事件")
        
        # 显示最近5条事件
        print("\n" + "=" * 60)
        print("📅 最近5条负责人日历事件")
        print("=" * 60)
        
        recent_events = events[:5]
        
        for i, event in enumerate(recent_events, 1):
            print(f"\n【事件 {i}】")
            print("-" * 40)
            
            title = event.get('title', '无标题')
            print(f"📌 标题: {title}")
            
            start_time = event.get('start_time', '')
            if start_time:
                formatted_time = format_datetime(start_time)
                print(f"⏰ 时间: {formatted_time}")
            
            description = event.get('description', '无描述')
            print(f"📝 内容:")
            
            # 格式化显示描述内容
            if description and description != '无描述':
                # 分行显示，增加缩进
                lines = description.split('\n')
                for line in lines:
                    if line.strip():
                        print(f"   {line.strip()}")
            else:
                print("   暂无内容")
        
        print("\n" + "=" * 60)
        print("✅ 负责人日历测试完成！")
        print(f"📁 完整日历文件: {coordinator_calendar_path}")
        print("💡 可以将此文件导入到Google Calendar、Apple Calendar等日历应用中")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

def show_sample_events(assignments, template_manager):
    """显示示例事件（当ICS生成失败时）"""
    print("\n📋 生成示例负责人日历事件:")
    print("=" * 60)
    
    try:
        # 获取当前和下个主日的安排
        today = date.today()
        
        # 找到最近的几个主日安排
        recent_assignments = []
        for assignment in assignments:
            if assignment.date >= today:
                recent_assignments.append(assignment)
            if len(recent_assignments) >= 3:
                break
        
        event_count = 0
        
        for assignment in recent_assignments:
            # 周三确认通知事件
            wednesday = assignment.date - timedelta(days=4)  # 主日前4天是周三
            if wednesday >= today - timedelta(days=7):  # 只显示最近一周的
                event_count += 1
                
                print(f"\n【事件 {event_count}】")
                print("-" * 40)
                print(f"📌 标题: 发送周末确认通知 ({assignment.date.month}/{assignment.date.day})")
                print(f"⏰ 时间: {wednesday.strftime('%Y-%m-%d')} 20:00:00")
                print(f"📝 内容:")
                
                # 生成通知内容
                try:
                    notification_content = template_manager.render_weekly_confirmation(assignment)
                    print(f"   发送内容：")
                    print()
                    for line in notification_content.split('\n'):
                        if line.strip():
                            print(f"   {line}")
                except Exception as e:
                    print(f"   生成通知内容时出错: {e}")
                
                if event_count >= 5:
                    break
            
            # 周六提醒通知事件
            saturday = assignment.date - timedelta(days=1)  # 主日前1天是周六
            if saturday >= today - timedelta(days=7):  # 只显示最近一周的
                event_count += 1
                
                print(f"\n【事件 {event_count}】")
                print("-" * 40)
                print(f"📌 标题: 发送主日提醒通知 ({assignment.date.month}/{assignment.date.day})")
                print(f"⏰ 时间: {saturday.strftime('%Y-%m-%d')} 20:00:00")
                print(f"📝 内容:")
                
                # 生成通知内容
                try:
                    notification_content = template_manager.render_sunday_reminder(assignment)
                    print(f"   发送内容：")
                    print()
                    for line in notification_content.split('\n'):
                        if line.strip():
                            print(f"   {line}")
                except Exception as e:
                    print(f"   生成通知内容时出错: {e}")
                
                if event_count >= 5:
                    break
        
        # 月度总览事件
        if event_count < 5:
            first_day = today.replace(day=1)
            if first_day >= today - timedelta(days=30):
                event_count += 1
                
                print(f"\n【事件 {event_count}】")
                print("-" * 40)
                print(f"📌 标题: 发送月度总览通知 ({today.year}年{today.month}月)")
                print(f"⏰ 时间: {first_day.strftime('%Y-%m-%d')} 09:00:00")
                print(f"📝 内容:")
                
                try:
                    # 获取当月的安排
                    monthly_assignments = [
                        a for a in assignments 
                        if a.date.year == today.year and a.date.month == today.month
                    ]
                    
                    sheet_url = f"https://docs.google.com/spreadsheets/d/{os.getenv('GOOGLE_SPREADSHEET_ID', '')}"
                    notification_content = template_manager.render_monthly_overview(
                        monthly_assignments, today.year, today.month, sheet_url
                    )
                    
                    print(f"   发送内容：")
                    print()
                    for line in notification_content.split('\n'):
                        if line.strip():
                            print(f"   {line}")
                except Exception as e:
                    print(f"   生成月度总览内容时出错: {e}")
        
        print("\n" + "=" * 60)
        print("✅ 示例事件展示完成！")
        
    except Exception as e:
        print(f"❌ 生成示例事件时出错: {e}")

if __name__ == "__main__":
    main()
