#!/usr/bin/env python3
"""
静态日历文件更新器
生成固定文件名的ICS日历，支持用户订阅固定URL进行自动更新

用法:
  python update_static_calendars.py           # 更新所有静态日历文件
  python update_static_calendars.py --watch   # 持续监控并更新
"""

import sys
import os
import argparse
import time
from pathlib import Path
from datetime import datetime, date, timedelta

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.scheduler import GoogleSheetsExtractor
from src.template_manager import get_default_template_manager
from dotenv import load_dotenv

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
    start_str = start_dt.strftime('%Y%m%dT%H%M%S')
    end_str = end_dt.strftime('%Y%m%dT%H%M%S')
    dtstamp_str = datetime.now().strftime('%Y%m%dT%H%M%S')
    
    event_lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{dtstamp_str}",
        f"DTSTART:{start_str}",
        f"DTEND:{end_str}",
        f"SUMMARY:{escape_ics_text(summary)}",
        f"DESCRIPTION:{escape_ics_text(description)}",
        f"LOCATION:{escape_ics_text(location)}",
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        f"DESCRIPTION:提醒：{escape_ics_text(summary)}",
        "TRIGGER:-PT30M",
        "END:VALARM",
        "END:VEVENT"
    ]
    
    return "\n".join(event_lines)

def update_coordinator_calendar() -> bool:
    """更新负责人静态日历文件"""
    try:
        print("📅 更新负责人日历...")
        
        # 获取数据
        load_dotenv()
        spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
        
        if not spreadsheet_id:
            print("❌ 错误: 请在 .env 文件中设置 GOOGLE_SPREADSHEET_ID")
            return False
        
        extractor = GoogleSheetsExtractor(spreadsheet_id)
        assignments = extractor.parse_ministry_data()
        template_manager = get_default_template_manager()
        
        if not assignments:
            print("⚠️  未找到事工安排数据")
            return False
        
        # 创建ICS内容
        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Grace Irvine Ministry Scheduler//Coordinator Calendar//CN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:Grace Irvine 事工协调日历",
            "X-WR-CALDESC:事工通知发送提醒日历（自动更新）",
            "X-WR-TIMEZONE:America/Los_Angeles",
            f"X-WR-CALDESC:最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        
        today = date.today()
        # 保留过去4周的事件，避免每次更新时删除历史记录
        cutoff_date = today - timedelta(days=28)  # 4周前
        relevant_assignments = [a for a in assignments if a.date >= cutoff_date][:19]  # 4周过去 + 15周未来
        events_created = 0
        
        for assignment in relevant_assignments:
            # 周三确认通知事件
            wednesday = assignment.date - timedelta(days=4)
            if wednesday >= today - timedelta(days=7):
                try:
                    notification_content = template_manager.render_weekly_confirmation(assignment)
                    event_ics = create_ics_event(
                        uid=f"weekly_confirmation_{wednesday.strftime('%Y%m%d')}@graceirvine.org",
                        summary=f"发送周末确认通知 ({assignment.date.month}/{assignment.date.day})",
                        description=f"发送内容：\n\n{notification_content}",
                        start_dt=datetime.combine(wednesday, datetime.min.time().replace(hour=20, minute=0)),
                        end_dt=datetime.combine(wednesday, datetime.min.time().replace(hour=20, minute=30)),
                        location="Grace Irvine 教会"
                    )
                    ics_lines.append(event_ics)
                    events_created += 1
                except Exception as e:
                    print(f"❌ 创建周三事件失败 ({assignment.date}): {e}")
            
            # 周六提醒通知事件
            saturday = assignment.date - timedelta(days=1)
            if saturday >= today - timedelta(days=7):
                try:
                    notification_content = template_manager.render_sunday_reminder(assignment)
                    event_ics = create_ics_event(
                        uid=f"sunday_reminder_{saturday.strftime('%Y%m%d')}@graceirvine.org",
                        summary=f"发送主日提醒通知 ({assignment.date.month}/{assignment.date.day})",
                        description=f"发送内容：\n\n{notification_content}",
                        start_dt=datetime.combine(saturday, datetime.min.time().replace(hour=20, minute=0)),
                        end_dt=datetime.combine(saturday, datetime.min.time().replace(hour=20, minute=30)),
                        location="Grace Irvine 教会"
                    )
                    ics_lines.append(event_ics)
                    events_created += 1
                except Exception as e:
                    print(f"❌ 创建周六事件失败 ({assignment.date}): {e}")
        
        # 添加月度总览事件
        try:
            first_day = today.replace(day=1)
            monthly_assignments = [a for a in assignments if a.date.year == today.year and a.date.month == today.month]
            
            if monthly_assignments:
                sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
                notification_content = template_manager.render_monthly_overview(
                    monthly_assignments, today.year, today.month, sheet_url
                )
                
                event_ics = create_ics_event(
                    uid=f"monthly_overview_{today.strftime('%Y%m')}@graceirvine.org",
                    summary=f"发送月度总览通知 ({today.year}年{today.month}月)",
                    description=f"发送内容：\n\n{notification_content}",
                    start_dt=datetime.combine(first_day, datetime.min.time().replace(hour=9, minute=0)),
                    end_dt=datetime.combine(first_day, datetime.min.time().replace(hour=10, minute=0)),
                    location="Grace Irvine 教会"
                )
                ics_lines.append(event_ics)
                events_created += 1
        
        except Exception as e:
            print(f"❌ 创建月度事件失败: {e}")
        
        ics_lines.append("END:VCALENDAR")
        ics_content = "\n".join(ics_lines)
        
        # 保存到固定文件名
        output_dir = Path("calendars/")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        static_file = output_dir / "grace_irvine_coordinator.ics"
        
        with open(static_file, 'w', encoding='utf-8') as f:
            f.write(ics_content)
        
        print(f"✅ 负责人日历已更新: {static_file}")
        print(f"📋 包含 {events_created} 个事件")
        
        return True
        
    except Exception as e:
        print(f"❌ 更新负责人日历失败: {e}")
        return False

def update_workers_calendar() -> bool:
    """更新同工静态日历文件"""
    try:
        print("👥 更新同工日历...")
        
        # 获取数据
        load_dotenv()
        spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
        
        extractor = GoogleSheetsExtractor(spreadsheet_id)
        assignments = extractor.parse_ministry_data()
        
        # 创建同工日历ICS内容
        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Grace Irvine Ministry Scheduler//Workers Calendar//CN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:Grace Irvine 同工服事日历",
            "X-WR-CALDESC:同工事工服事安排日历（自动更新）",
            "X-WR-TIMEZONE:America/Los_Angeles",
            f"X-WR-CALDESC:最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        
        today = date.today()
        # 保留过去4周的事件
        cutoff_date = today - timedelta(days=28)
        relevant_assignments = [a for a in assignments if a.date >= cutoff_date][:14]  # 4周过去 + 10周未来
        events_created = 0
        
        for assignment in relevant_assignments:
            # 为每个角色创建服事事件
            service_roles = [
                ("音控", assignment.audio_tech, "09:00", "12:00"),
                ("导播/摄影", assignment.camera_operator, "09:30", "12:00"),
                ("ProPresenter播放", assignment.propresenter, "09:00", "12:00")
            ]
            
            for role_name, person_name, start_time, end_time in service_roles:
                if person_name and person_name.strip():
                    try:
                        start_hour, start_minute = map(int, start_time.split(':'))
                        end_hour, end_minute = map(int, end_time.split(':'))
                        
                        event_ics = create_ics_event(
                            uid=f"service_{role_name}_{assignment.date.strftime('%Y%m%d')}_{person_name}@graceirvine.org",
                            summary=f"主日服事 - {role_name}",
                            description=f"角色：{role_name}\n负责人：{person_name}\n到场时间：{start_time}\n\n愿主同在，出入平安！",
                            start_dt=datetime.combine(assignment.date, datetime.min.time().replace(hour=start_hour, minute=start_minute)),
                            end_dt=datetime.combine(assignment.date, datetime.min.time().replace(hour=end_hour, minute=end_minute)),
                            location="Grace Irvine 教会"
                        )
                        ics_lines.append(event_ics)
                        events_created += 1
                    except Exception as e:
                        print(f"❌ 创建 {person_name} 服事事件失败: {e}")
        
        ics_lines.append("END:VCALENDAR")
        ics_content = "\n".join(ics_lines)
        
        # 保存到固定文件名
        output_dir = Path("calendars/")
        static_file = output_dir / "grace_irvine_workers.ics"
        
        with open(static_file, 'w', encoding='utf-8') as f:
            f.write(ics_content)
        
        print(f"✅ 同工日历已更新: {static_file}")
        print(f"📋 包含 {events_created} 个事件")
        
        return True
        
    except Exception as e:
        print(f"❌ 更新同工日历失败: {e}")
        return False

def cmd_update():
    """更新所有静态日历文件"""
    print("🔄 更新静态日历文件")
    print("=" * 50)
    
    success_count = 0
    
    # 更新负责人日历
    if update_coordinator_calendar():
        success_count += 1
    
    # 更新同工日历
    if update_workers_calendar():
        success_count += 1
    
    print(f"\n📊 更新结果: {success_count}/2 个日历文件更新成功")
    
    if success_count == 2:
        print("✅ 所有日历文件更新完成！")
        
        # 显示订阅信息
        print("\n🔗 日历订阅信息:")
        print("=" * 50)
        print("📋 固定文件名日历（推荐用于订阅）:")
        print("  负责人日历: calendars/grace_irvine_coordinator.ics")
        print("  同工日历: calendars/grace_irvine_workers.ics")
        
        print("\n💡 使用方法:")
        print("1. 将文件上传到Web服务器")
        print("2. 在日历应用中订阅URL（如 https://your-server.com/calendars/grace_irvine_coordinator.ics）")
        print("3. 定期运行此脚本更新文件内容")
        print("4. 日历应用会自动检测文件变化并更新")
        
    else:
        print("⚠️  部分日历文件更新失败")

def cmd_watch():
    """持续监控并更新日历文件"""
    print("👁️ 启动日历文件监控模式")
    print("=" * 50)
    print("🔄 每30分钟自动更新一次日历文件")
    print("按 Ctrl+C 停止监控")
    
    try:
        while True:
            print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 开始更新...")
            cmd_update()
            
            print(f"😴 等待30分钟后下次更新...")
            time.sleep(1800)  # 30分钟 = 1800秒
            
    except KeyboardInterrupt:
        print("\n🛑 监控已停止")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Grace Irvine 静态日历文件更新器",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--watch', action='store_true', help='持续监控模式（每30分钟更新）')
    
    args = parser.parse_args()
    
    print("🎯 Grace Irvine 静态日历更新器")
    print(f"⏰ 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 检查环境
    load_dotenv()
    if not os.getenv('GOOGLE_SPREADSHEET_ID'):
        print("❌ 错误: 请在 .env 文件中设置 GOOGLE_SPREADSHEET_ID")
        sys.exit(1)
    
    if args.watch:
        cmd_watch()
    else:
        cmd_update()

if __name__ == "__main__":
    main()
