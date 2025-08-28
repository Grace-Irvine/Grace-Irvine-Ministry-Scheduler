#!/usr/bin/env python3
"""
简化的ICS生成测试脚本
直接生成负责人日历，绕过配置问题
"""

import sys
import os
from pathlib import Path
from datetime import datetime, date, timedelta
from icalendar import Calendar, Event
import pytz

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.scheduler import GoogleSheetsExtractor
from src.template_manager import get_default_template_manager
from dotenv import load_dotenv

def create_coordinator_calendar_simple(assignments):
    """简化版本的负责人日历生成"""
    try:
        # 创建日历
        cal = Calendar()
        cal.add('prodid', '-//Grace Irvine Ministry Scheduler//Coordinator Calendar//CN')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')
        cal.add('x-wr-calname', 'Grace Irvine 事工协调日历')
        cal.add('x-wr-caldesc', '事工通知发送提醒日历')
        cal.add('x-wr-timezone', 'America/Los_Angeles')
        
        timezone = pytz.timezone("America/Los_Angeles")
        template_manager = get_default_template_manager()
        
        # 创建事件
        events_created = 0
        today = date.today()
        
        # 为接下来的3个主日生成通知事件
        for assignment in assignments[:3]:  # 只取前3个
            if assignment.date >= today:
                # 周三确认通知事件
                wednesday = assignment.date - timedelta(days=4)  # 主日前4天是周三
                if wednesday >= today - timedelta(days=7):  # 最近一周内的
                    try:
                        notification_content = template_manager.render_weekly_confirmation(assignment)
                        
                        # 创建周三事件
                        event = Event()
                        event.add('uid', f'weekly_confirmation_{wednesday.strftime("%Y%m%d")}@graceirvine.org')
                        event.add('summary', f'发送周末确认通知 ({assignment.date.month}/{assignment.date.day})')
                        
                        description = f"发送内容：\n\n{notification_content}"
                        event.add('description', description)
                        
                        # 设置时间 - 周三晚上8点
                        start_time = timezone.localize(datetime.combine(wednesday, datetime.min.time().replace(hour=20, minute=0)))
                        end_time = start_time + timedelta(minutes=30)
                        
                        event.add('dtstart', start_time)
                        event.add('dtend', end_time)
                        event.add('dtstamp', datetime.now(timezone))
                        event.add('location', 'Grace Irvine 教会')
                        event.add('categories', ['通知提醒', '事工协调'])
                        
                        # 添加提醒
                        alarm = event.add_component('valarm')
                        alarm.add('action', 'DISPLAY')
                        alarm.add('description', f'提醒：发送周末确认通知')
                        alarm.add('trigger', timedelta(minutes=-30))
                        
                        cal.add_component(event)
                        events_created += 1
                        
                    except Exception as e:
                        print(f"创建周三事件时出错: {e}")
                
                # 周六提醒通知事件
                saturday = assignment.date - timedelta(days=1)  # 主日前1天是周六
                if saturday >= today - timedelta(days=7):  # 最近一周内的
                    try:
                        notification_content = template_manager.render_sunday_reminder(assignment)
                        
                        # 创建周六事件
                        event = Event()
                        event.add('uid', f'sunday_reminder_{saturday.strftime("%Y%m%d")}@graceirvine.org')
                        event.add('summary', f'发送主日提醒通知 ({assignment.date.month}/{assignment.date.day})')
                        
                        description = f"发送内容：\n\n{notification_content}"
                        event.add('description', description)
                        
                        # 设置时间 - 周六晚上8点
                        start_time = timezone.localize(datetime.combine(saturday, datetime.min.time().replace(hour=20, minute=0)))
                        end_time = start_time + timedelta(minutes=30)
                        
                        event.add('dtstart', start_time)
                        event.add('dtend', end_time)
                        event.add('dtstamp', datetime.now(timezone))
                        event.add('location', 'Grace Irvine 教会')
                        event.add('categories', ['通知提醒', '事工协调'])
                        
                        # 添加提醒
                        alarm = event.add_component('valarm')
                        alarm.add('action', 'DISPLAY')
                        alarm.add('description', f'提醒：发送主日提醒通知')
                        alarm.add('trigger', timedelta(minutes=-30))
                        
                        cal.add_component(event)
                        events_created += 1
                        
                    except Exception as e:
                        print(f"创建周六事件时出错: {e}")
        
        # 添加月度总览事件
        try:
            first_day = today.replace(day=1)
            monthly_assignments = [a for a in assignments if a.date.year == today.year and a.date.month == today.month]
            
            if monthly_assignments:
                sheet_url = f"https://docs.google.com/spreadsheets/d/{os.getenv('GOOGLE_SPREADSHEET_ID', '')}"
                notification_content = template_manager.render_monthly_overview(
                    monthly_assignments, today.year, today.month, sheet_url
                )
                
                # 创建月度事件
                event = Event()
                event.add('uid', f'monthly_overview_{today.strftime("%Y%m")}@graceirvine.org')
                event.add('summary', f'发送月度总览通知 ({today.year}年{today.month}月)')
                
                description = f"发送内容：\n\n{notification_content}"
                event.add('description', description)
                
                # 设置时间 - 每月1日早上9点
                start_time = timezone.localize(datetime.combine(first_day, datetime.min.time().replace(hour=9, minute=0)))
                end_time = start_time + timedelta(hours=1)
                
                event.add('dtstart', start_time)
                event.add('dtend', end_time)
                event.add('dtstamp', datetime.now(timezone))
                event.add('location', 'Grace Irvine 教会')
                event.add('categories', ['通知提醒', '事工协调', '月度总览'])
                
                # 添加提醒
                alarm = event.add_component('valarm')
                alarm.add('action', 'DISPLAY')
                alarm.add('description', f'提醒：发送月度总览通知')
                alarm.add('trigger', timedelta(hours=-1))
                
                cal.add_component(event)
                events_created += 1
                
        except Exception as e:
            print(f"创建月度事件时出错: {e}")
        
        # 保存ICS文件
        output_dir = Path("calendars/")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"coordinator_calendar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics"
        filepath = output_dir / filename
        
        with open(filepath, 'wb') as f:
            f.write(cal.to_ical())
        
        print(f"✅ 成功生成负责人日历: {filepath}")
        print(f"📋 创建了 {events_created} 个事件")
        
        return str(filepath)
        
    except Exception as e:
        print(f"❌ 生成日历时出错: {e}")
        import traceback
        traceback.print_exc()
        return None

def parse_and_display_ics(ics_path):
    """解析并显示ICS文件内容"""
    try:
        with open(ics_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("\n" + "=" * 60)
        print("📅 负责人日历事件内容")
        print("=" * 60)
        
        # 简单解析事件
        import re
        
        # 找到所有事件
        event_pattern = r'BEGIN:VEVENT(.*?)END:VEVENT'
        events = re.findall(event_pattern, content, re.DOTALL)
        
        for i, event_content in enumerate(events[:5], 1):  # 只显示前5个
            print(f"\n【事件 {i}】")
            print("-" * 40)
            
            # 提取标题
            summary_match = re.search(r'SUMMARY:(.*?)(?:\n|$)', event_content)
            if summary_match:
                title = summary_match.group(1).strip()
                print(f"📌 标题: {title}")
            
            # 提取开始时间
            dtstart_match = re.search(r'DTSTART[^:]*:(.*?)(?:\n|$)', event_content)
            if dtstart_match:
                start_time = dtstart_match.group(1).strip()
                try:
                    if 'T' in start_time:
                        if start_time.endswith('Z'):
                            dt = datetime.strptime(start_time, '%Y%m%dT%H%M%SZ')
                        else:
                            dt = datetime.strptime(start_time, '%Y%m%dT%H%M%S')
                        formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                        print(f"⏰ 时间: {formatted_time}")
                except:
                    print(f"⏰ 时间: {start_time}")
            
            # 提取描述
            description_match = re.search(r'DESCRIPTION:(.*?)(?:\n[A-Z]|\n$)', event_content, re.DOTALL)
            if description_match:
                description = description_match.group(1).strip()
                # 处理转义字符
                description = description.replace('\\n', '\n').replace('\\,', ',').replace('\\;', ';')
                
                print(f"📝 内容:")
                lines = description.split('\n')
                for line in lines[:10]:  # 只显示前10行
                    if line.strip():
                        print(f"   {line.strip()}")
                
                if len(lines) > 10:
                    print(f"   ... (还有 {len(lines) - 10} 行)")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"❌ 解析ICS文件时出错: {e}")

def main():
    """主函数"""
    print("🎯 简化版负责人日历生成测试")
    print("=" * 60)
    
    try:
        # 设置环境
        load_dotenv()
        spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
        
        if not spreadsheet_id:
            print("❌ 错误: 请在 .env 文件中设置 GOOGLE_SPREADSHEET_ID")
            return
        
        # 获取数据
        print("📊 正在获取Google Sheets数据...")
        extractor = GoogleSheetsExtractor(spreadsheet_id)
        assignments = extractor.parse_ministry_data()
        
        if not assignments:
            print("❌ 未找到事工安排数据")
            return
        
        print(f"✅ 成功获取 {len(assignments)} 条事工安排")
        
        # 生成日历
        print("📅 正在生成负责人日历...")
        ics_path = create_coordinator_calendar_simple(assignments)
        
        if ics_path:
            # 解析并显示内容
            parse_and_display_ics(ics_path)
            print(f"\n💾 完整日历文件: {ics_path}")
            print("💡 可以将此文件导入到日历应用中使用")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
