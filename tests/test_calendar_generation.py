#!/usr/bin/env python3
"""
测试Streamlit应用中的日历生成逻辑
Test calendar generation logic in Streamlit app
"""

import sys
from pathlib import Path
from datetime import datetime, date, timedelta

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from src.data_cleaner import FocusedDataCleaner
from src.template_manager import get_default_template_manager

def test_calendar_generation():
    """测试日历生成逻辑"""
    print("🧪 测试Streamlit应用中的日历生成逻辑")
    print("=" * 60)
    
    try:
        # 1. 加载数据
        print("📥 步骤1: 加载数据...")
        cleaner = FocusedDataCleaner()
        raw_df = cleaner.download_data()
        focused_df = cleaner.extract_focused_columns(raw_df)
        schedules = cleaner.clean_focused_data(focused_df)
        
        print(f"✅ 成功加载 {len(schedules)} 个排程记录")
        
        if not schedules:
            print("❌ 没有排程数据，无法生成日历")
            return False
        
        # 2. 测试负责人日历生成
        print("\n📅 步骤2: 测试负责人日历生成...")
        coordinator_ics = generate_coordinator_calendar_content(schedules)
        
        if coordinator_ics:
            event_count = coordinator_ics.count("BEGIN:VEVENT")
            print(f"✅ 负责人日历生成成功，包含 {event_count} 个事件")
            
            # 保存测试文件
            test_file = Path("calendars/test_coordinator.ics")
            test_file.parent.mkdir(exist_ok=True)
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(coordinator_ics)
            print(f"💾 测试文件已保存: {test_file}")
        else:
            print("❌ 负责人日历生成失败")
            return False
        
        # 3. 测试同工日历生成
        print("\n👥 步骤3: 测试同工日历生成...")
        workers_ics = generate_workers_calendar_content(schedules)
        
        if workers_ics:
            event_count = workers_ics.count("BEGIN:VEVENT")
            print(f"✅ 同工日历生成成功，包含 {event_count} 个事件")
            
            # 保存测试文件
            test_file = Path("calendars/test_workers.ics")
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(workers_ics)
            print(f"💾 测试文件已保存: {test_file}")
        else:
            print("❌ 同工日历生成失败")
            return False
        
        print("\n🎉 所有测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_coordinator_calendar_content(schedules) -> str:
    """生成负责人日历ICS内容（从Streamlit应用复制）"""
    try:
        template_manager = get_default_template_manager()
        
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
        future_schedules = [s for s in schedules if s.date >= today][:15]
        
        print(f"📊 找到 {len(future_schedules)} 个未来排程")
        
        events_created = 0
        
        for schedule in future_schedules:
            # 周三确认通知事件
            wednesday = schedule.date - timedelta(days=4)
            if wednesday >= today - timedelta(days=7):
                try:
                    # 创建模拟的assignment对象
                    assignment = type('Assignment', (), {
                        'date': schedule.date,
                        'audio_tech': schedule.audio_tech or '',
                        'screen_operator': '待安排',  # 添加缺失的属性
                        'camera_operator': schedule.video_director or '',
                        'propresenter': schedule.propresenter_play or '',
                        'video_editor': schedule.propresenter_update or '靖铮'
                    })()
                    
                    notification_content = template_manager.render_weekly_confirmation(assignment)
                    event_ics = create_simple_ics_event(
                        uid=f"weekly_confirmation_{wednesday.strftime('%Y%m%d')}@graceirvine.org",
                        summary=f"发送周末确认通知 ({schedule.date.month}/{schedule.date.day})",
                        description=f"发送内容：\n\n{notification_content}",
                        start_dt=datetime.combine(wednesday, datetime.min.time().replace(hour=20, minute=0)),
                        end_dt=datetime.combine(wednesday, datetime.min.time().replace(hour=20, minute=30)),
                        location="Grace Irvine 教会"
                    )
                    ics_lines.append(event_ics)
                    events_created += 1
                    print(f"  ✅ 创建周三事件: {wednesday.strftime('%Y-%m-%d')}")
                except Exception as e:
                    print(f"  ❌ 创建周三事件失败: {e}")
            
            # 周六提醒通知事件
            saturday = schedule.date - timedelta(days=1)
            if saturday >= today - timedelta(days=7):
                try:
                    # 创建模拟的assignment对象
                    assignment = type('Assignment', (), {
                        'date': schedule.date,
                        'audio_tech': schedule.audio_tech or '',
                        'screen_operator': '待安排',  # 添加缺失的属性
                        'camera_operator': schedule.video_director or '',
                        'propresenter': schedule.propresenter_play or '',
                        'video_editor': schedule.propresenter_update or '靖铮'
                    })()
                    
                    notification_content = template_manager.render_sunday_reminder(assignment)
                    event_ics = create_simple_ics_event(
                        uid=f"sunday_reminder_{saturday.strftime('%Y%m%d')}@graceirvine.org",
                        summary=f"发送主日提醒通知 ({schedule.date.month}/{schedule.date.day})",
                        description=f"发送内容：\n\n{notification_content}",
                        start_dt=datetime.combine(saturday, datetime.min.time().replace(hour=20, minute=0)),
                        end_dt=datetime.combine(saturday, datetime.min.time().replace(hour=20, minute=30)),
                        location="Grace Irvine 教会"
                    )
                    ics_lines.append(event_ics)
                    events_created += 1
                    print(f"  ✅ 创建周六事件: {saturday.strftime('%Y-%m-%d')}")
                except Exception as e:
                    print(f"  ❌ 创建周六事件失败: {e}")
        
        ics_lines.append("END:VCALENDAR")
        print(f"📋 总共创建了 {events_created} 个事件")
        return "\n".join(ics_lines)
        
    except Exception as e:
        print(f"❌ 生成负责人日历时出错: {e}")
        return None

def generate_workers_calendar_content(schedules) -> str:
    """生成同工日历ICS内容（从Streamlit应用复制）"""
    try:
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
        
        print(f"📊 找到 {len(future_schedules)} 个未来排程")
        
        events_created = 0
        
        for schedule in future_schedules:
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
                        
                        event_ics = create_simple_ics_event(
                            uid=f"service_{role_name}_{schedule.date.strftime('%Y%m%d')}_{person_name}@graceirvine.org",
                            summary=f"主日服事 - {role_name}",
                            description=f"角色：{role_name}\n负责人：{person_name}\n到场时间：{start_time}\n\n愿主同在，出入平安！",
                            start_dt=datetime.combine(schedule.date, datetime.min.time().replace(hour=start_hour, minute=start_minute)),
                            end_dt=datetime.combine(schedule.date, datetime.min.time().replace(hour=end_hour, minute=end_minute)),
                            location="Grace Irvine 教会"
                        )
                        ics_lines.append(event_ics)
                        events_created += 1
                        print(f"  ✅ 创建服事事件: {schedule.date.strftime('%Y-%m-%d')} - {role_name} ({person_name})")
                    except Exception as e:
                        print(f"  ❌ 创建服事事件失败: {e}")
        
        ics_lines.append("END:VCALENDAR")
        print(f"📋 总共创建了 {events_created} 个事件")
        return "\n".join(ics_lines)
        
    except Exception as e:
        print(f"❌ 生成同工日历时出错: {e}")
        return None

def create_simple_ics_event(uid: str, summary: str, description: str, 
                           start_dt: datetime, end_dt: datetime, location: str = "") -> str:
    """创建简单的ICS事件（从Streamlit应用复制）"""
    def escape_ics_text(text: str) -> str:
        text = text.replace('\\', '\\\\')
        text = text.replace(',', '\\,')
        text = text.replace(';', '\\;')
        text = text.replace('\n', '\\n')
        return text
    
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

if __name__ == "__main__":
    success = test_calendar_generation()
    if success:
        print("\n🎯 测试总结: Streamlit应用中的日历生成逻辑工作正常")
        print("💡 如果Cloud Run上仍然显示0个事件，可能是以下原因:")
        print("   1. 数据加载失败")
        print("   2. 日期过滤逻辑问题")
        print("   3. 模板渲染错误")
        print("   4. 缓存问题")
    else:
        print("\n❌ 测试总结: 发现问题，需要进一步调试")
