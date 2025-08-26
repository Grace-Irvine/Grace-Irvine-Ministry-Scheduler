#!/usr/bin/env python3
"""
负责人ICS日历生成器
生成包含完整通知内容的负责人日历文件

用法:
  python generate_coordinator_ics.py
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

def create_coordinator_ics():
    """创建负责人ICS日历"""
    try:
        print("🎯 Grace Irvine 负责人日历生成器")
        print("=" * 60)
        
        # 设置环境
        load_dotenv()
        spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
        
        if not spreadsheet_id:
            print("❌ 错误: 请在 .env 文件中设置 GOOGLE_SPREADSHEET_ID")
            return None
        
        # 获取数据
        print("📊 正在获取Google Sheets数据...")
        extractor = GoogleSheetsExtractor(spreadsheet_id)
        assignments = extractor.parse_ministry_data()
        template_manager = get_default_template_manager()
        
        if not assignments:
            print("❌ 未找到事工安排数据")
            return None
        
        print(f"✅ 成功获取 {len(assignments)} 条事工安排")
        
        # 创建日历
        print("📅 正在创建ICS日历...")
        cal = Calendar()
        cal.add('prodid', '-//Grace Irvine Ministry Scheduler//Coordinator Calendar//CN')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')
        cal.add('x-wr-calname', 'Grace Irvine 事工协调日历')
        cal.add('x-wr-caldesc', '事工通知发送提醒日历')
        cal.add('x-wr-timezone', 'America/Los_Angeles')
        
        timezone = pytz.timezone("America/Los_Angeles")
        today = date.today()
        events_created = 0
        
        print("\n📋 生成的日历事件:")
        print("=" * 60)
        
        # 获取未来的事工安排
        future_assignments = [a for a in assignments if a.date >= today][:10]  # 取前10个
        
        for assignment in future_assignments:
            # 周三确认通知事件
            wednesday = assignment.date - timedelta(days=4)  # 主日前4天是周三
            
            if wednesday >= today - timedelta(days=7):  # 包含最近一周的
                try:
                    # 生成通知内容
                    notification_content = template_manager.render_weekly_confirmation(assignment)
                    
                    # 创建事件
                    event = Event()
                    event.add('uid', f'weekly_confirmation_{wednesday.strftime("%Y%m%d")}@graceirvine.org')
                    event.add('summary', f'发送周末确认通知 ({assignment.date.month}/{assignment.date.day})')
                    event.add('description', f"发送内容：\n\n{notification_content}")
                    
                    # 设置时间 - 周三晚上8点
                    start_time = timezone.localize(datetime.combine(wednesday, datetime.min.time().replace(hour=20, minute=0)))
                    end_time = start_time + timedelta(minutes=30)
                    
                    event.add('dtstart', start_time)
                    event.add('dtend', end_time)
                    event.add('dtstamp', datetime.now(timezone))
                    event.add('location', 'Grace Irvine 教会')
                    
                    # 添加提醒
                    from icalendar import vDuration
                    alarm = event.add_component('valarm')
                    alarm.add('action', 'DISPLAY')
                    alarm.add('description', f'提醒：发送周末确认通知')
                    alarm.add('trigger', vDuration(-timedelta(minutes=30)))
                    
                    cal.add_component(event)
                    events_created += 1
                    
                    print(f"✅ 周三确认通知 - {wednesday.strftime('%Y-%m-%d')} 20:00 ({assignment.date.month}/{assignment.date.day})")
                    
                except Exception as e:
                    print(f"❌ 创建周三事件失败 ({assignment.date}): {e}")
            
            # 周六提醒通知事件
            saturday = assignment.date - timedelta(days=1)  # 主日前1天是周六
            
            if saturday >= today - timedelta(days=7):  # 包含最近一周的
                try:
                    # 生成通知内容
                    notification_content = template_manager.render_sunday_reminder(assignment)
                    
                    # 创建事件
                    event = Event()
                    event.add('uid', f'sunday_reminder_{saturday.strftime("%Y%m%d")}@graceirvine.org')
                    event.add('summary', f'发送主日提醒通知 ({assignment.date.month}/{assignment.date.day})')
                    event.add('description', f"发送内容：\n\n{notification_content}")
                    
                    # 设置时间 - 周六晚上8点
                    start_time = timezone.localize(datetime.combine(saturday, datetime.min.time().replace(hour=20, minute=0)))
                    end_time = start_time + timedelta(minutes=30)
                    
                    event.add('dtstart', start_time)
                    event.add('dtend', end_time)
                    event.add('dtstamp', datetime.now(timezone))
                    event.add('location', 'Grace Irvine 教会')
                    
                    # 添加提醒
                    from icalendar import vDuration
                    alarm = event.add_component('valarm')
                    alarm.add('action', 'DISPLAY')
                    alarm.add('description', f'提醒：发送主日提醒通知')
                    alarm.add('trigger', vDuration(-timedelta(minutes=30)))
                    
                    cal.add_component(event)
                    events_created += 1
                    
                    print(f"✅ 周六提醒通知 - {saturday.strftime('%Y-%m-%d')} 20:00 ({assignment.date.month}/{assignment.date.day})")
                    
                except Exception as e:
                    print(f"❌ 创建周六事件失败 ({assignment.date}): {e}")
        
        # 添加月度总览事件
        try:
            first_day = today.replace(day=1)
            if first_day >= today - timedelta(days=30):  # 本月的
                monthly_assignments = [a for a in assignments if a.date.year == today.year and a.date.month == today.month]
                
                if monthly_assignments:
                    sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
                    notification_content = template_manager.render_monthly_overview(
                        monthly_assignments, today.year, today.month, sheet_url
                    )
                    
                    # 创建月度事件
                    event = Event()
                    event.add('uid', f'monthly_overview_{today.strftime("%Y%m")}@graceirvine.org')
                    event.add('summary', f'发送月度总览通知 ({today.year}年{today.month}月)')
                    event.add('description', f"发送内容：\n\n{notification_content}")
                    
                    # 设置时间 - 每月1日早上9点
                    start_time = timezone.localize(datetime.combine(first_day, datetime.min.time().replace(hour=9, minute=0)))
                    end_time = start_time + timedelta(hours=1)
                    
                    event.add('dtstart', start_time)
                    event.add('dtend', end_time)
                    event.add('dtstamp', datetime.now(timezone))
                    event.add('location', 'Grace Irvine 教会')
                    
                    # 添加提醒
                    from icalendar import vDuration
                    alarm = event.add_component('valarm')
                    alarm.add('action', 'DISPLAY')
                    alarm.add('description', f'提醒：发送月度总览通知')
                    alarm.add('trigger', vDuration(-timedelta(hours=1)))
                    
                    cal.add_component(event)
                    events_created += 1
                    
                    print(f"✅ 月度总览通知 - {first_day.strftime('%Y-%m-%d')} 09:00 ({today.year}年{today.month}月)")
        
        except Exception as e:
            print(f"❌ 创建月度事件失败: {e}")
        
        # 保存ICS文件
        output_dir = Path("calendars/")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"grace_irvine_coordinator_calendar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics"
        filepath = output_dir / filename
        
        with open(filepath, 'wb') as f:
            f.write(cal.to_ical())
        
        print("\n" + "=" * 60)
        print("🎉 负责人日历生成成功！")
        print(f"📋 创建了 {events_created} 个事件")
        print(f"💾 文件位置: {filepath}")
        print(f"📁 文件大小: {filepath.stat().st_size} 字节")
        
        return str(filepath)
        
    except Exception as e:
        print(f"❌ 生成过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return None

def display_ics_content(ics_path: str):
    """显示ICS文件内容概览"""
    try:
        print("\n📋 ICS文件内容预览:")
        print("=" * 60)
        
        with open(ics_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 统计信息
        event_count = content.count('BEGIN:VEVENT')
        alarm_count = content.count('BEGIN:VALARM')
        
        print(f"📊 统计信息:")
        print(f"  • 事件数量: {event_count}")
        print(f"  • 提醒数量: {alarm_count}")
        print(f"  • 文件行数: {len(content.splitlines())}")
        
        # 显示前几个事件的标题
        import re
        summaries = re.findall(r'SUMMARY:(.*)', content)
        if summaries:
            print(f"\n📅 事件列表:")
            for i, summary in enumerate(summaries[:5], 1):
                print(f"  {i}. {summary}")
            if len(summaries) > 5:
                print(f"  ... 还有 {len(summaries) - 5} 个事件")
        
        print(f"\n💡 导入方法:")
        print(f"  1. Google Calendar: 设置 → 导入和导出 → 导入")
        print(f"  2. Apple Calendar: 双击ICS文件")
        print(f"  3. Outlook: 文件 → 打开和导出 → 导入/导出")
        
    except Exception as e:
        print(f"❌ 显示ICS内容时出错: {e}")

def main():
    """主函数"""
    ics_path = create_coordinator_ics()
    
    if ics_path and Path(ics_path).exists():
        display_ics_content(ics_path)
        
        print(f"\n🎯 完成！")
        print(f"负责人日历文件已生成: {ics_path}")
    else:
        print("❌ 日历生成失败")

if __name__ == "__main__":
    main()
