#!/usr/bin/env python3
"""
负责人日历演示脚本
手动生成负责人ICS日历并显示内容
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

def main():
    """主函数"""
    print("🎯 负责人日历演示")
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
        template_manager = get_default_template_manager()
        
        if not assignments:
            print("❌ 未找到事工安排数据")
            return
        
        print(f"✅ 成功获取 {len(assignments)} 条事工安排")
        
        # 创建日历
        print("📅 正在生成负责人日历...")
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
        
        # 显示和创建事件
        print("\n" + "=" * 60)
        print("📅 负责人日历事件内容（最近5条）")
        print("=" * 60)
        
        # 找到未来的事工安排
        future_assignments = [a for a in assignments if a.date >= today][:3]
        
        event_count = 0
        
        for assignment in future_assignments:
            # 周三确认通知事件
            wednesday = assignment.date - timedelta(days=4)  # 主日前4天是周三
            
            if wednesday >= today - timedelta(days=7):  # 最近一周内的
                event_count += 1
                
                print(f"\n【事件 {event_count}】")
                print("-" * 40)
                print(f"📌 标题: 发送周末确认通知 ({assignment.date.month}/{assignment.date.day})")
                print(f"⏰ 时间: {wednesday.strftime('%Y-%m-%d')} 20:00:00")
                
                # 生成通知内容
                try:
                    notification_content = template_manager.render_weekly_confirmation(assignment)
                    print(f"📝 内容:")
                    print(f"   发送内容：")
                    print()
                    for line in notification_content.split('\n'):
                        if line.strip():
                            print(f"   {line}")
                    
                    # 创建ICS事件
                    event = Event()
                    event.add('uid', f'weekly_confirmation_{wednesday.strftime("%Y%m%d")}@graceirvine.org')
                    event.add('summary', f'发送周末确认通知 ({assignment.date.month}/{assignment.date.day})')
                    event.add('description', f"发送内容：\n\n{notification_content}")
                    
                    # 设置时间
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
                    print(f"   ❌ 生成通知内容时出错: {e}")
                
                if event_count >= 5:
                    break
            
            # 周六提醒通知事件
            saturday = assignment.date - timedelta(days=1)  # 主日前1天是周六
            
            if saturday >= today - timedelta(days=7) and event_count < 5:
                event_count += 1
                
                print(f"\n【事件 {event_count}】")
                print("-" * 40)
                print(f"📌 标题: 发送主日提醒通知 ({assignment.date.month}/{assignment.date.day})")
                print(f"⏰ 时间: {saturday.strftime('%Y-%m-%d')} 20:00:00")
                
                # 生成通知内容
                try:
                    notification_content = template_manager.render_sunday_reminder(assignment)
                    print(f"📝 内容:")
                    print(f"   发送内容：")
                    print()
                    for line in notification_content.split('\n'):
                        if line.strip():
                            print(f"   {line}")
                    
                    # 创建ICS事件
                    event = Event()
                    event.add('uid', f'sunday_reminder_{saturday.strftime("%Y%m%d")}@graceirvine.org')
                    event.add('summary', f'发送主日提醒通知 ({assignment.date.month}/{assignment.date.day})')
                    event.add('description', f"发送内容：\n\n{notification_content}")
                    
                    # 设置时间
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
                    print(f"   ❌ 生成通知内容时出错: {e}")
                
                if event_count >= 5:
                    break
        
        # 添加月度总览事件（如果还没有5个事件）
        if event_count < 5:
            event_count += 1
            
            first_day = today.replace(day=1)
            monthly_assignments = [a for a in assignments if a.date.year == today.year and a.date.month == today.month]
            
            print(f"\n【事件 {event_count}】")
            print("-" * 40)
            print(f"📌 标题: 发送月度总览通知 ({today.year}年{today.month}月)")
            print(f"⏰ 时间: {first_day.strftime('%Y-%m-%d')} 09:00:00")
            
            try:
                sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
                notification_content = template_manager.render_monthly_overview(
                    monthly_assignments, today.year, today.month, sheet_url
                )
                
                print(f"📝 内容:")
                print(f"   发送内容：")
                print()
                for line in notification_content.split('\n')[:15]:  # 只显示前15行
                    if line.strip():
                        print(f"   {line}")
                
                if len(notification_content.split('\n')) > 15:
                    print(f"   ... (还有更多内容)")
                
                # 创建ICS事件
                event = Event()
                event.add('uid', f'monthly_overview_{today.strftime("%Y%m")}@graceirvine.org')
                event.add('summary', f'发送月度总览通知 ({today.year}年{today.month}月)')
                event.add('description', f"发送内容：\n\n{notification_content}")
                
                # 设置时间
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
                print(f"   ❌ 生成月度总览内容时出错: {e}")
        
        # 保存ICS文件
        output_dir = Path("calendars/")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"coordinator_calendar_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics"
        filepath = output_dir / filename
        
        with open(filepath, 'wb') as f:
            f.write(cal.to_ical())
        
        print("\n" + "=" * 60)
        print("✅ 负责人日历生成完成！")
        print(f"📋 创建了 {events_created} 个事件")
        print(f"💾 日历文件: {filepath}")
        print("\n💡 使用方法:")
        print("1. 将ICS文件导入到Google Calendar、Apple Calendar或Outlook")
        print("2. 日历会在指定时间提醒发送相应的通知")
        print("3. 点击事件可查看完整的通知内容")
        print("4. 每个事件都包含了完整的模板渲染结果")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
