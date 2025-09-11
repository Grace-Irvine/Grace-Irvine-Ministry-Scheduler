#!/usr/bin/env python3
"""
生成真实的ICS日历文件
Generate real ICS calendar files with actual data
"""

import os
import sys
from pathlib import Path
from datetime import datetime, date, timedelta

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from src.data_cleaner import FocusedDataCleaner
from src.template_manager import NotificationTemplateManager, get_default_template_manager
from dotenv import load_dotenv

def generate_unified_wednesday_template(sunday_date, schedule):
    """统一的周三确认通知模板生成器（与前端一致）"""
    template = f"""【本周{sunday_date.month}月{sunday_date.day}日主日事工安排提醒】🕊️

"""
    
    assignments = schedule.get_all_assignments() if schedule else {}
    
    if assignments:
        for role, person in assignments.items():
            template += f"• {role}：{person}\n"
    else:
        template += "• 音控：待安排\n• 导播/摄影：待安排\n• ProPresenter播放：待安排\n• ProPresenter更新：待安排\n"
    
    template += """• 视频剪辑：靖铮

请大家确认时间，若有冲突请尽快私信我，感谢摆上 🙏"""
    
    return template

def generate_unified_saturday_template(sunday_date, schedule):
    """统一的周六提醒通知模板生成器（与前端一致）"""
    template = f"""【主日服事提醒】✨
明天 8:30布置/ 9:00彩排 / 10:00 正式敬拜  
请各位同工提前到场：  

"""
    
    assignments = schedule.get_all_assignments() if schedule else {}
    
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
    
    template += "\n愿主同在，出入平安。若临时不适请第一时间私信我。🙌"
    
    return template

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

def generate_coordinator_calendar():
    """生成负责人日历"""
    try:
        print("📅 生成负责人日历...")
        
        # 加载环境变量
        load_dotenv()
        
        # 获取数据
        cleaner = FocusedDataCleaner()
        raw_df = cleaner.download_data()
        focused_df = cleaner.extract_focused_columns(raw_df)
        schedules = cleaner.clean_focused_data(focused_df)
        
        if not schedules:
            print("❌ 未找到排程数据")
            return False
        
        template_manager = get_default_template_manager()
        
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
        future_schedules = [s for s in schedules if s.date >= today][:15]  # 未来15周
        events_created = 0
        
        for schedule in future_schedules:
            # 周三确认通知事件
            wednesday = schedule.date - timedelta(days=4)
            if wednesday >= today - timedelta(days=7):
                try:
                    # 使用与前端一致的模板生成逻辑
                    notification_content = generate_unified_wednesday_template(schedule.date, schedule)
                    event_ics = create_ics_event(
                        uid=f"weekly_confirmation_{wednesday.strftime('%Y%m%d')}@graceirvine.org",
                        summary=f"发送周末确认通知 ({schedule.date.month}/{schedule.date.day})",
                        description=f"发送内容：\n\n{notification_content}",
                        start_dt=datetime.combine(wednesday, datetime.min.time().replace(hour=20, minute=0)),
                        end_dt=datetime.combine(wednesday, datetime.min.time().replace(hour=20, minute=30)),
                        location="Grace Irvine 教会"
                    )
                    ics_lines.append(event_ics)
                    events_created += 1
                except Exception as e:
                    print(f"❌ 创建周三事件失败: {e}")
            
            # 周六提醒通知事件
            saturday = schedule.date - timedelta(days=1)
            if saturday >= today - timedelta(days=7):
                try:
                    # 使用与前端一致的模板生成逻辑
                    notification_content = generate_unified_saturday_template(schedule.date, schedule)
                    event_ics = create_ics_event(
                        uid=f"sunday_reminder_{saturday.strftime('%Y%m%d')}@graceirvine.org",
                        summary=f"发送主日提醒通知 ({schedule.date.month}/{schedule.date.day})",
                        description=f"发送内容：\n\n{notification_content}",
                        start_dt=datetime.combine(saturday, datetime.min.time().replace(hour=20, minute=0)),
                        end_dt=datetime.combine(saturday, datetime.min.time().replace(hour=20, minute=30)),
                        location="Grace Irvine 教会"
                    )
                    ics_lines.append(event_ics)
                    events_created += 1
                except Exception as e:
                    print(f"❌ 创建周六事件失败: {e}")
        
        ics_lines.append("END:VCALENDAR")
        ics_content = "\n".join(ics_lines)
        
        # 保存到文件
        calendar_dir = Path("calendars")
        output_file = calendar_dir / "grace_irvine_coordinator.ics"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(ics_content)
        
        print(f"✅ 负责人日历已生成: {output_file}")
        print(f"📋 包含 {events_created} 个事件")
        
        return True
        
    except Exception as e:
        print(f"❌ 生成负责人日历失败: {e}")
        return False

def generate_workers_calendar():
    """生成同工日历"""
    try:
        print("📅 生成同工日历...")
        
        # 加载环境变量
        load_dotenv()
        
        # 获取数据
        cleaner = FocusedDataCleaner()
        raw_df = cleaner.download_data()
        focused_df = cleaner.extract_focused_columns(raw_df)
        schedules = cleaner.clean_focused_data(focused_df)
        
        if not schedules:
            print("❌ 未找到排程数据")
            return False
        
        # 创建ICS内容
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
        future_schedules = [s for s in schedules if s.date >= today][:10]
        events_created = 0
        
        for schedule in future_schedules:
            # 为每个角色创建服事事件
            service_roles = [
                ("音控", schedule.audio_tech, "09:00", "12:00"),
                ("导播/摄影", schedule.video_director, "09:30", "12:00"),
                ("ProPresenter播放", schedule.propresenter_play, "09:00", "12:00")
            ]
            
            for role_name, person_name, start_time, end_time in service_roles:
                if person_name and person_name.strip():
                    try:
                        start_hour, start_minute = map(int, start_time.split(':'))
                        end_hour, end_minute = map(int, end_time.split(':'))
                        
                        event_ics = create_ics_event(
                            uid=f"service_{role_name}_{schedule.date.strftime('%Y%m%d')}_{person_name}@graceirvine.org",
                            summary=f"主日服事 - {role_name}",
                            description=f"角色：{role_name}\n负责人：{person_name}\n到场时间：{start_time}\n\n愿主同在，出入平安！",
                            start_dt=datetime.combine(schedule.date, datetime.min.time().replace(hour=start_hour, minute=start_minute)),
                            end_dt=datetime.combine(schedule.date, datetime.min.time().replace(hour=end_hour, minute=end_minute)),
                            location="Grace Irvine 教会"
                        )
                        ics_lines.append(event_ics)
                        events_created += 1
                    except Exception as e:
                        print(f"❌ 创建 {person_name} 服事事件失败: {e}")
        
        ics_lines.append("END:VCALENDAR")
        ics_content = "\n".join(ics_lines)
        
        # 保存到文件
        calendar_dir = Path("calendars")
        output_file = calendar_dir / "grace_irvine_workers.ics"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(ics_content)
        
        print(f"✅ 同工日历已生成: {output_file}")
        print(f"📋 包含 {events_created} 个事件")
        
        return True
        
    except Exception as e:
        print(f"❌ 生成同工日历失败: {e}")
        return False

def main():
    """主函数"""
    print("🔄 生成真实ICS日历文件")
    print("=" * 50)
    
    # 检查环境
    load_dotenv()
    if not os.getenv('GOOGLE_SPREADSHEET_ID'):
        print("❌ 错误: 请在 .env 文件中设置 GOOGLE_SPREADSHEET_ID")
        print("💡 或者设置环境变量: export GOOGLE_SPREADSHEET_ID=your_sheet_id")
        sys.exit(1)
    
    success_count = 0
    
    # 生成负责人日历
    if generate_coordinator_calendar():
        success_count += 1
    
    # 生成同工日历
    if generate_workers_calendar():
        success_count += 1
    
    print(f"\n📊 生成结果: {success_count}/2 个日历文件生成成功")
    
    if success_count == 2:
        print("✅ 所有日历文件生成完成！")
        
        # 显示订阅信息
        print("\n🔗 日历订阅信息:")
        print("=" * 50)
        print("📋 固定文件名日历（用于订阅）:")
        print("  负责人日历: http://localhost:8080/calendars/grace_irvine_coordinator.ics")
        print("  同工日历: http://localhost:8080/calendars/grace_irvine_workers.ics")
        
        print("\n💡 使用方法:")
        print("1. 在日历应用中订阅URL")
        print("2. 定期运行此脚本更新文件内容")
        print("3. 日历应用会自动检测文件变化并更新")
        
    else:
        print("⚠️ 部分日历文件生成失败")
        print("请检查Google Sheets连接和数据格式")

if __name__ == "__main__":
    main()
