#!/usr/bin/env python3
"""
简单的负责人ICS日历生成器
使用原生字符串生成ICS格式，避免库依赖问题

用法:
  python simple_coordinator_ics.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime, date, timedelta

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.scheduler import GoogleSheetsExtractor
from src.template_manager import get_default_template_manager
from dotenv import load_dotenv

def format_datetime_for_ics(dt: datetime) -> str:
    """将datetime格式化为ICS格式"""
    # 转换为UTC时间并格式化
    utc_dt = dt.astimezone(datetime.now().astimezone().utcoffset() and 
                          dt.astimezone() or dt)
    return dt.strftime('%Y%m%dT%H%M%S')

def escape_ics_text(text: str) -> str:
    """转义ICS文本中的特殊字符"""
    text = text.replace('\\', '\\\\')
    text = text.replace(',', '\\,')
    text = text.replace(';', '\\;')
    text = text.replace('\n', '\\n')
    return text

def create_ics_event(uid: str, summary: str, description: str, 
                    start_dt: datetime, end_dt: datetime, location: str = "") -> str:
    """创建单个ICS事件"""
    
    # 格式化时间
    start_str = start_dt.strftime('%Y%m%dT%H%M%S')
    end_str = end_dt.strftime('%Y%m%dT%H%M%S')
    dtstamp_str = datetime.now().strftime('%Y%m%dT%H%M%S')
    
    # 转义文本
    summary_esc = escape_ics_text(summary)
    description_esc = escape_ics_text(description)
    location_esc = escape_ics_text(location)
    
    # 创建事件字符串
    event_lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{dtstamp_str}",
        f"DTSTART:{start_str}",
        f"DTEND:{end_str}",
        f"SUMMARY:{summary_esc}",
        f"DESCRIPTION:{description_esc}",
        f"LOCATION:{location_esc}",
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        f"DESCRIPTION:提醒：{summary_esc}",
        "TRIGGER:-PT30M",
        "END:VALARM",
        "END:VEVENT"
    ]
    
    return "\n".join(event_lines)

def main():
    """主函数"""
    try:
        print("🎯 Grace Irvine 负责人日历生成器 (简化版)")
        print("=" * 60)
        
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
        
        # 创建ICS文件头部
        print("📅 正在创建ICS日历...")
        
        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Grace Irvine Ministry Scheduler//Coordinator Calendar//CN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:Grace Irvine 事工协调日历",
            "X-WR-CALDESC:事工通知发送提醒日历",
            "X-WR-TIMEZONE:America/Los_Angeles"
        ]
        
        today = date.today()
        events_created = 0
        
        print("\n📋 生成的日历事件:")
        print("=" * 60)
        
        # 获取未来的事工安排
        future_assignments = [a for a in assignments if a.date >= today][:8]  # 取前8个
        
        for assignment in future_assignments:
            # 周三确认通知事件
            wednesday = assignment.date - timedelta(days=4)  # 主日前4天是周三
            
            if wednesday >= today - timedelta(days=7):  # 包含最近一周的
                try:
                    # 生成通知内容
                    notification_content = template_manager.render_weekly_confirmation(assignment)
                    
                    # 创建事件时间
                    start_time = datetime.combine(wednesday, datetime.min.time().replace(hour=20, minute=0))
                    end_time = start_time + timedelta(minutes=30)
                    
                    # 创建事件
                    event_ics = create_ics_event(
                        uid=f"weekly_confirmation_{wednesday.strftime('%Y%m%d')}@graceirvine.org",
                        summary=f"发送周末确认通知 ({assignment.date.month}/{assignment.date.day})",
                        description=f"发送内容：\n\n{notification_content}",
                        start_dt=start_time,
                        end_dt=end_time,
                        location="Grace Irvine 教会"
                    )
                    
                    ics_lines.append(event_ics)
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
                    
                    # 创建事件时间
                    start_time = datetime.combine(saturday, datetime.min.time().replace(hour=20, minute=0))
                    end_time = start_time + timedelta(minutes=30)
                    
                    # 创建事件
                    event_ics = create_ics_event(
                        uid=f"sunday_reminder_{saturday.strftime('%Y%m%d')}@graceirvine.org",
                        summary=f"发送主日提醒通知 ({assignment.date.month}/{assignment.date.day})",
                        description=f"发送内容：\n\n{notification_content}",
                        start_dt=start_time,
                        end_dt=end_time,
                        location="Grace Irvine 教会"
                    )
                    
                    ics_lines.append(event_ics)
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
                    
                    # 创建事件时间
                    start_time = datetime.combine(first_day, datetime.min.time().replace(hour=9, minute=0))
                    end_time = start_time + timedelta(hours=1)
                    
                    # 创建事件
                    event_ics = create_ics_event(
                        uid=f"monthly_overview_{today.strftime('%Y%m')}@graceirvine.org",
                        summary=f"发送月度总览通知 ({today.year}年{today.month}月)",
                        description=f"发送内容：\n\n{notification_content}",
                        start_dt=start_time,
                        end_dt=end_time,
                        location="Grace Irvine 教会"
                    )
                    
                    ics_lines.append(event_ics)
                    events_created += 1
                    
                    print(f"✅ 月度总览通知 - {first_day.strftime('%Y-%m-%d')} 09:00 ({today.year}年{today.month}月)")
        
        except Exception as e:
            print(f"❌ 创建月度事件失败: {e}")
        
        # 添加ICS文件结尾
        ics_lines.append("END:VCALENDAR")
        
        # 保存ICS文件
        output_dir = Path("calendars/")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"grace_irvine_coordinator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics"
        filepath = output_dir / filename
        
        ics_content = "\n".join(ics_lines)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(ics_content)
        
        print("\n" + "=" * 60)
        print("🎉 负责人日历生成成功！")
        print(f"📋 创建了 {events_created} 个事件")
        print(f"💾 文件位置: {filepath}")
        print(f"📁 文件大小: {filepath.stat().st_size} 字节")
        
        # 显示最近5条事件的内容
        print("\n📋 最近5条事件内容:")
        print("=" * 60)
        
        event_count = 0
        future_assignments = [a for a in assignments if a.date >= today][:3]
        
        for assignment in future_assignments:
            if event_count >= 5:
                break
                
            # 周三确认通知
            wednesday = assignment.date - timedelta(days=4)
            if wednesday >= today - timedelta(days=7):
                event_count += 1
                print(f"\n【事件 {event_count}】")
                print(f"📌 标题: 发送周末确认通知 ({assignment.date.month}/{assignment.date.day})")
                print(f"⏰ 时间: {wednesday.strftime('%Y-%m-%d')} 20:00:00")
                print("📝 内容:")
                
                try:
                    content = template_manager.render_weekly_confirmation(assignment)
                    for line in content.split('\n'):
                        if line.strip():
                            print(f"   {line}")
                except Exception as e:
                    print(f"   ❌ 生成内容失败: {e}")
                
                if event_count >= 5:
                    break
            
            # 周六提醒通知
            saturday = assignment.date - timedelta(days=1)
            if saturday >= today - timedelta(days=7) and event_count < 5:
                event_count += 1
                print(f"\n【事件 {event_count}】")
                print(f"📌 标题: 发送主日提醒通知 ({assignment.date.month}/{assignment.date.day})")
                print(f"⏰ 时间: {saturday.strftime('%Y-%m-%d')} 20:00:00")
                print("📝 内容:")
                
                try:
                    content = template_manager.render_sunday_reminder(assignment)
                    for line in content.split('\n'):
                        if line.strip():
                            print(f"   {line}")
                except Exception as e:
                    print(f"   ❌ 生成内容失败: {e}")
        
        print("\n" + "=" * 60)
        print("💡 使用方法:")
        print("1. 将ICS文件导入到Google Calendar、Apple Calendar或Outlook")
        print("2. 日历会在指定时间提醒发送相应的通知")
        print("3. 点击事件可查看完整的通知内容")
        print("4. 每个事件都包含了完整的模板渲染结果")
        
        return str(filepath)
        
    except Exception as e:
        print(f"❌ 生成过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()
