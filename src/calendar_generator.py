#!/usr/bin/env python3
"""
ICS日历生成器
ICS Calendar Generator

负责生成事工排程的ICS日历文件，包括：
- 负责人日历（通知提醒事件）
- 同工日历（服事安排事件）
"""

import os
import sys
from pathlib import Path
from datetime import datetime, date, timedelta

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_cleaner import FocusedDataCleaner
from src.dynamic_template_manager import DynamicTemplateManager
from dotenv import load_dotenv

# 全局模板管理器实例
template_manager = None

def get_template_manager():
    """获取模板管理器实例"""
    global template_manager
    if template_manager is None:
        template_manager = DynamicTemplateManager()
    return template_manager

def generate_unified_wednesday_template(sunday_date, schedule):
    """统一的周三确认通知模板生成器（使用动态模板）"""
    manager = get_template_manager()
    return manager.render_weekly_confirmation(sunday_date, schedule)

def generate_unified_saturday_template(sunday_date, schedule):
    """统一的周六提醒通知模板生成器（使用动态模板）"""
    manager = get_template_manager()
    return manager.render_saturday_reminder(sunday_date, schedule)

def escape_ics_text(text: str) -> str:
    """转义ICS文本中的特殊字符"""
    text = text.replace('\\', '\\\\')
    text = text.replace(',', '\\,')
    text = text.replace(';', '\\;')
    text = text.replace('\n', '\\n')
    return text

def calculate_event_date(sunday_date: date, target_weekday: int) -> date:
    """计算事件日期（相对于主日）
    
    Args:
        sunday_date: 主日日期
        target_weekday: 目标星期几 (0=Monday, 6=Sunday)
    
    Returns:
        计算出的事件日期
    """
    # 周日 = 6, 周一 = 0, 周二 = 1, ..., 周六 = 5
    sunday_weekday = 6  # 周日的weekday值
    
    if target_weekday == sunday_weekday:
        # 如果目标是周日，直接返回
        return sunday_date
    else:
        # 计算相对于周日的天数偏移
        # 周一到周六都是在周日之前
        days_offset = target_weekday - sunday_weekday
        if days_offset > 0:
            days_offset -= 7  # 向前一周
        
        return sunday_date + timedelta(days=days_offset)

def create_ics_event(uid: str, summary: str, description: str, 
                    start_dt: datetime, end_dt: datetime, location: str = "", 
                    reminder_trigger: str = "-PT30M") -> str:
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
        f"TRIGGER:{reminder_trigger}",
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
        
        # 使用动态模板管理器
        dynamic_template_manager = get_template_manager()
        
        # 获取提醒配置管理器
        try:
            from .reminder_config_manager import get_reminder_manager
            reminder_manager = get_reminder_manager()
            reminder_configs = reminder_manager.get_all_configs()
            print(f"📋 加载了 {len(reminder_configs)} 个提醒配置")
        except Exception as e:
            print(f"⚠️ 无法加载提醒配置，使用默认设置: {e}")
            reminder_configs = {}
            reminder_manager = None
        
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
        # 包含过去4周到未来15周的事件
        relevant_schedules = [s for s in schedules if s.date >= cutoff_date][:19]  # 4周过去 + 15周未来
        events_created = 0
        
        for schedule in relevant_schedules:
            # 周三确认通知事件
            if 'weekly_confirmation' in reminder_configs and reminder_configs['weekly_confirmation'].enabled:
                config = reminder_configs['weekly_confirmation']
                # 计算事件日期（相对于主日）
                event_date = calculate_event_date(schedule.date, config.event_timing.weekday)
                
                if event_date >= today - timedelta(days=7):
                    try:
                        # 使用与前端一致的模板生成逻辑，使用基于日期的固定经文
                        notification_content = dynamic_template_manager.render_weekly_confirmation(schedule.date, schedule, for_ics_generation=True)
                        
                        # 使用配置的时间
                        start_dt = datetime.combine(
                            event_date, 
                            config.event_timing.to_time()
                        )
                        end_dt = start_dt + timedelta(minutes=config.event_timing.duration_minutes)
                        
                        event_ics = create_ics_event(
                            uid=f"weekly_confirmation_{event_date.strftime('%Y%m%d')}@graceirvine.org",
                            summary=f"发送周末确认通知 ({schedule.date.month}/{schedule.date.day})",
                            description=f"发送内容：{chr(10)}{chr(10)}{notification_content}",
                            start_dt=start_dt,
                            end_dt=end_dt,
                            location="Grace Irvine 教会",
                            reminder_trigger=config.reminder_timing.to_ics_trigger()
                        )
                        ics_lines.append(event_ics)
                        events_created += 1
                    except Exception as e:
                        print(f"❌ 创建周三事件失败: {e}")
            else:
                # 使用默认设置（保持向后兼容）
                wednesday = schedule.date - timedelta(days=4)
                if wednesday >= today - timedelta(days=7):
                    try:
                        notification_content = dynamic_template_manager.render_weekly_confirmation(schedule.date, schedule, for_ics_generation=True)
                        event_ics = create_ics_event(
                            uid=f"weekly_confirmation_{wednesday.strftime('%Y%m%d')}@graceirvine.org",
                            summary=f"发送周末确认通知 ({schedule.date.month}/{schedule.date.day})",
                            description=f"发送内容：{chr(10)}{chr(10)}{notification_content}",
                            start_dt=datetime.combine(wednesday, datetime.min.time().replace(hour=20, minute=0)),
                            end_dt=datetime.combine(wednesday, datetime.min.time().replace(hour=20, minute=30)),
                            location="Grace Irvine 教会",
                            reminder_trigger="-PT30M"
                        )
                        ics_lines.append(event_ics)
                        events_created += 1
                    except Exception as e:
                        print(f"❌ 创建周三事件失败: {e}")
            
            # 周六提醒通知事件
            if 'saturday_reminder' in reminder_configs and reminder_configs['saturday_reminder'].enabled:
                config = reminder_configs['saturday_reminder']
                # 计算事件日期（相对于主日）
                event_date = calculate_event_date(schedule.date, config.event_timing.weekday)
                
                if event_date >= today - timedelta(days=7):
                    try:
                        # 使用与前端一致的模板生成逻辑
                        notification_content = dynamic_template_manager.render_saturday_reminder(schedule.date, schedule)
                        
                        # 使用配置的时间
                        start_dt = datetime.combine(
                            event_date, 
                            config.event_timing.to_time()
                        )
                        end_dt = start_dt + timedelta(minutes=config.event_timing.duration_minutes)
                        
                        event_ics = create_ics_event(
                            uid=f"sunday_reminder_{event_date.strftime('%Y%m%d')}@graceirvine.org",
                            summary=f"发送主日提醒通知 ({schedule.date.month}/{schedule.date.day})",
                            description=f"发送内容：{chr(10)}{chr(10)}{notification_content}",
                            start_dt=start_dt,
                            end_dt=end_dt,
                            location="Grace Irvine 教会",
                            reminder_trigger=config.reminder_timing.to_ics_trigger()
                        )
                        ics_lines.append(event_ics)
                        events_created += 1
                    except Exception as e:
                        print(f"❌ 创建周六事件失败: {e}")
            else:
                # 使用默认设置（保持向后兼容）
                saturday = schedule.date - timedelta(days=1)
                if saturday >= today - timedelta(days=7):
                    try:
                        notification_content = dynamic_template_manager.render_saturday_reminder(schedule.date, schedule)
                        event_ics = create_ics_event(
                            uid=f"sunday_reminder_{saturday.strftime('%Y%m%d')}@graceirvine.org",
                            summary=f"发送主日提醒通知 ({schedule.date.month}/{schedule.date.day})",
                            description=f"发送内容：{chr(10)}{chr(10)}{notification_content}",
                            start_dt=datetime.combine(saturday, datetime.min.time().replace(hour=20, minute=0)),
                            end_dt=datetime.combine(saturday, datetime.min.time().replace(hour=20, minute=30)),
                            location="Grace Irvine 教会",
                            reminder_trigger="-PT30M"
                        )
                        ics_lines.append(event_ics)
                        events_created += 1
                    except Exception as e:
                        print(f"❌ 创建周六事件失败: {e}")
        
        ics_lines.append("END:VCALENDAR")
        ics_content = "\n".join(ics_lines)
        
        # 使用云端存储管理器保存
        from .cloud_storage_manager import get_storage_manager
        storage_manager = get_storage_manager()
        
        if storage_manager.write_ics_calendar(ics_content, "grace_irvine_coordinator.ics"):
            print(f"✅ 负责人日历已生成并保存")
            print(f"📋 包含 {events_created} 个事件")
            
            # 获取公开访问URL
            public_url = storage_manager.get_public_calendar_url("grace_irvine_coordinator.ics")
            print(f"🔗 公开订阅URL: {public_url}")
        else:
            print("❌ 日历文件保存失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 生成负责人日历失败: {e}")
        return False

# TODO: 同工日历功能留到下阶段开发
# def generate_workers_calendar():
#     """生成同工日历 - 留到下阶段开发"""
#     pass

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
    
    # 生成负责人日历
    if generate_coordinator_calendar():
        print("✅ 负责人日历生成完成！")
        
        # 显示订阅信息
        print("\n🔗 日历订阅信息:")
        print("=" * 50)
        print("📋 负责人日历（用于订阅）:")
        print("  负责人日历: http://localhost:8080/calendars/grace_irvine_coordinator.ics")
        
        print("\n💡 使用方法:")
        print("1. 在日历应用中订阅URL")
        print("2. 定期运行此脚本更新文件内容")
        print("3. 日历应用会自动检测文件变化并更新")
        
        print("\n📝 注意:")
        print("  同工日历功能留到下阶段开发")
        
    else:
        print("❌ 负责人日历生成失败")
        print("请检查Google Sheets连接和数据格式")

if __name__ == "__main__":
    main()
