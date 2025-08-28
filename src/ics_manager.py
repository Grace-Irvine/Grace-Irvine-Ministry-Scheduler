#!/usr/bin/env python3
"""
ICS Calendar Manager - ICS日历管理器
负责生成和管理事工通知的ICS日历文件

功能：
1. 生成负责人日历（通知发送提醒）
2. 生成同工日历（个人服事安排）
3. 自动同步Google Sheets数据
4. 管理日历订阅配置
"""

import os
import uuid
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import yaml
from icalendar import Calendar, Event, vText
import pytz

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class CalendarEvent:
    """日历事件数据结构"""
    uid: str
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    location: str = ""
    categories: List[str] = None
    alarm_minutes: int = 30  # 提前提醒分钟数
    
    def __post_init__(self):
        if self.categories is None:
            self.categories = []

@dataclass
class CalendarConfig:
    """日历配置数据结构"""
    calendar_name: str
    calendar_description: str
    timezone: str = "America/Los_Angeles"
    notification_times: Dict[str, str] = None  # 通知时间配置
    subscribers: List[str] = None  # 订阅者列表
    
    def __post_init__(self):
        if self.notification_times is None:
            self.notification_times = {
                "weekly_confirmation": "20:00",  # 周三晚上8点
                "sunday_reminder": "20:00",      # 周六晚上8点
                "monthly_overview": "09:00"      # 每月1日早上9点
            }
        if self.subscribers is None:
            self.subscribers = []

class ICSManager:
    """ICS日历管理器"""
    
    def __init__(self, config_path: str = "configs/calendar_config.yaml"):
        """初始化ICS管理器
        
        Args:
            config_path: 日历配置文件路径
        """
        self.config_path = config_path
        self.config = None
        self.timezone = pytz.timezone("America/Los_Angeles")
        self.load_config()
    
    def load_config(self) -> bool:
        """加载日历配置
        
        Returns:
            是否加载成功
        """
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.warning(f"Config file not found: {self.config_path}, creating default config")
                self._create_default_config()
                return True
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # 解析配置
            self.config = {
                'coordinator_calendar': CalendarConfig(**config_data.get('coordinator_calendar', {})),
                'worker_calendar': CalendarConfig(**config_data.get('worker_calendar', {})),
                'sync_settings': config_data.get('sync_settings', {}),
                'output_directory': config_data.get('output_directory', 'calendars/')
            }
            
            logger.info(f"Successfully loaded calendar config from {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load calendar config: {e}")
            self._create_default_config()
            return False
    
    def save_config(self) -> bool:
        """保存日历配置
        
        Returns:
            是否保存成功
        """
        try:
            config_file = Path(self.config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 转换为可序列化的字典
            config_data = {
                'coordinator_calendar': {
                    'calendar_name': self.config['coordinator_calendar'].calendar_name,
                    'calendar_description': self.config['coordinator_calendar'].calendar_description,
                    'timezone': self.config['coordinator_calendar'].timezone,
                    'notification_times': self.config['coordinator_calendar'].notification_times,
                    'subscribers': self.config['coordinator_calendar'].subscribers
                },
                'worker_calendar': {
                    'calendar_name': self.config['worker_calendar'].calendar_name,
                    'calendar_description': self.config['worker_calendar'].calendar_description,
                    'timezone': self.config['worker_calendar'].timezone,
                    'notification_times': self.config['worker_calendar'].notification_times,
                    'subscribers': self.config['worker_calendar'].subscribers
                },
                'sync_settings': self.config['sync_settings'],
                'output_directory': self.config['output_directory']
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False, indent=2)
            
            logger.info(f"Successfully saved calendar config to {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save calendar config: {e}")
            return False
    
    def _create_default_config(self):
        """创建默认配置"""
        self.config = {
            'coordinator_calendar': CalendarConfig(
                calendar_name="Grace Irvine 事工协调日历",
                calendar_description="事工通知发送提醒日历",
                timezone="America/Los_Angeles",
                notification_times={
                    "weekly_confirmation": "20:00",
                    "sunday_reminder": "20:00", 
                    "monthly_overview": "09:00"
                },
                subscribers=["coordinator@example.com"]
            ),
            'worker_calendar': CalendarConfig(
                calendar_name="Grace Irvine 同工服事日历",
                calendar_description="个人事工服事安排日历",
                timezone="America/Los_Angeles",
                subscribers=[]
            ),
            'sync_settings': {
                'sync_frequency_hours': 12,
                'auto_sync_enabled': True,
                'last_sync': None,
                'google_sheets_id': os.getenv('GOOGLE_SPREADSHEET_ID', ''),
                'service_account_path': 'configs/service_account.json'
            },
            'output_directory': 'calendars/'
        }
        self.save_config()
    
    def generate_coordinator_calendar(self, assignments: List, start_date: date = None, end_date: date = None) -> str:
        """生成负责人日历（通知发送提醒）
        
        Args:
            assignments: 事工安排列表
            start_date: 开始日期（默认为当前月份）
            end_date: 结束日期（默认为3个月后）
            
        Returns:
            ICS文件路径
        """
        try:
            # 设置默认日期范围
            if start_date is None:
                start_date = date.today().replace(day=1)  # 当月第一天
            if end_date is None:
                end_date = start_date + timedelta(days=90)  # 3个月后
            
            # 创建日历
            cal = Calendar()
            cal.add('prodid', '-//Grace Irvine Ministry Scheduler//Coordinator Calendar//CN')
            cal.add('version', '2.0')
            cal.add('calscale', 'GREGORIAN')
            cal.add('method', 'PUBLISH')
            cal.add('x-wr-calname', self.config['coordinator_calendar'].calendar_name)
            cal.add('x-wr-caldesc', self.config['coordinator_calendar'].calendar_description)
            cal.add('x-wr-timezone', self.config['coordinator_calendar'].timezone)
            
            events = []
            
            # 生成通知事件
            current_date = start_date
            while current_date <= end_date:
                # 周三晚上的确认通知
                wednesday = self._get_weekday(current_date, 2)  # 2 = 周三
                if wednesday >= start_date and wednesday <= end_date:
                    events.extend(self._create_weekly_confirmation_events(wednesday, assignments))
                
                # 周六晚上的提醒通知
                saturday = self._get_weekday(current_date, 5)  # 5 = 周六
                if saturday >= start_date and saturday <= end_date:
                    events.extend(self._create_sunday_reminder_events(saturday, assignments))
                
                # 每月1日的月度总览
                if current_date.day == 1:
                    events.extend(self._create_monthly_overview_events(current_date, assignments))
                
                current_date += timedelta(days=7)
            
            # 添加事件到日历
            for event_data in events:
                event = Event()
                event.add('uid', event_data.uid)
                event.add('summary', event_data.title)
                event.add('description', event_data.description)
                event.add('dtstart', event_data.start_time)
                event.add('dtend', event_data.end_time)
                event.add('dtstamp', datetime.now(self.timezone))
                event.add('location', event_data.location)
                
                # 添加分类
                if event_data.categories:
                    event.add('categories', event_data.categories)
                
                # 添加提醒
                if event_data.alarm_minutes > 0:
                    alarm = event.add_component('valarm')
                    alarm.add('action', 'DISPLAY')
                    alarm.add('description', f'提醒：{event_data.title}')
                    alarm.add('trigger', timedelta(minutes=-event_data.alarm_minutes))
                
                cal.add_component(event)
            
            # 保存ICS文件
            output_dir = Path(self.config['output_directory'])
            output_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"coordinator_calendar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics"
            filepath = output_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(cal.to_ical())
            
            logger.info(f"Successfully generated coordinator calendar: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to generate coordinator calendar: {e}")
            raise
    
    def generate_worker_calendar(self, assignments: List, worker_name: str = None) -> str:
        """生成同工日历（个人服事安排）
        
        Args:
            assignments: 事工安排列表
            worker_name: 同工姓名（为空则生成所有同工的综合日历）
            
        Returns:
            ICS文件路径
        """
        try:
            # 创建日历
            cal = Calendar()
            cal.add('prodid', '-//Grace Irvine Ministry Scheduler//Worker Calendar//CN')
            cal.add('version', '2.0')
            cal.add('calscale', 'GREGORIAN')
            cal.add('method', 'PUBLISH')
            
            calendar_name = self.config['worker_calendar'].calendar_name
            if worker_name:
                calendar_name = f"{worker_name} - {calendar_name}"
            
            cal.add('x-wr-calname', calendar_name)
            cal.add('x-wr-caldesc', self.config['worker_calendar'].calendar_description)
            cal.add('x-wr-timezone', self.config['worker_calendar'].timezone)
            
            # 生成服事事件
            for assignment in assignments:
                events = self._create_ministry_events(assignment, worker_name)
                for event_data in events:
                    event = Event()
                    event.add('uid', event_data.uid)
                    event.add('summary', event_data.title)
                    event.add('description', event_data.description)
                    event.add('dtstart', event_data.start_time)
                    event.add('dtend', event_data.end_time)
                    event.add('dtstamp', datetime.now(self.timezone))
                    event.add('location', event_data.location)
                    
                    # 添加分类
                    if event_data.categories:
                        event.add('categories', event_data.categories)
                    
                    # 添加提醒
                    if event_data.alarm_minutes > 0:
                        alarm = event.add_component('valarm')
                        alarm.add('action', 'DISPLAY')
                        alarm.add('description', f'提醒：{event_data.title}')
                        alarm.add('trigger', timedelta(minutes=-event_data.alarm_minutes))
                    
                    cal.add_component(event)
            
            # 保存ICS文件
            output_dir = Path(self.config['output_directory'])
            output_dir.mkdir(parents=True, exist_ok=True)
            
            filename_suffix = f"_{worker_name}" if worker_name else "_all_workers"
            filename = f"worker_calendar{filename_suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics"
            filepath = output_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(cal.to_ical())
            
            logger.info(f"Successfully generated worker calendar: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to generate worker calendar: {e}")
            raise
    
    def _get_weekday(self, reference_date: date, target_weekday: int) -> date:
        """获取指定日期所在周的指定星期几
        
        Args:
            reference_date: 参考日期
            target_weekday: 目标星期几 (0=周一, 6=周日)
            
        Returns:
            目标日期
        """
        days_ahead = target_weekday - reference_date.weekday()
        if days_ahead < 0:  # 如果目标日期已过，取下周的
            days_ahead += 7
        return reference_date + timedelta(days=days_ahead)
    
    def _create_weekly_confirmation_events(self, wednesday: date, assignments: List) -> List[CalendarEvent]:
        """创建周三确认通知事件
        
        Args:
            wednesday: 周三日期
            assignments: 事工安排列表
            
        Returns:
            事件列表
        """
        events = []
        
        # 找到对应周日的安排
        sunday = wednesday + timedelta(days=4)  # 周三+4天=周日
        assignment = self._find_assignment_by_date(assignments, sunday)
        
        if assignment:
            # 生成通知内容
            from .template_manager import get_default_template_manager
            template_manager = get_default_template_manager()
            notification_content = template_manager.render_weekly_confirmation(assignment)
            
            # 创建事件
            notification_time = self.config['coordinator_calendar'].notification_times.get('weekly_confirmation', '20:00')
            start_time = self._combine_date_time(wednesday, notification_time)
            end_time = start_time + timedelta(minutes=30)
            
            event = CalendarEvent(
                uid=f"weekly_confirmation_{wednesday.strftime('%Y%m%d')}@graceirvine.org",
                title=f"发送周末确认通知 ({sunday.month}/{sunday.day})",
                description=f"发送内容：\n\n{notification_content}",
                start_time=start_time,
                end_time=end_time,
                location="Grace Irvine 教会",
                categories=["通知提醒", "事工协调"],
                alarm_minutes=30
            )
            events.append(event)
        
        return events
    
    def _create_sunday_reminder_events(self, saturday: date, assignments: List) -> List[CalendarEvent]:
        """创建周六提醒通知事件
        
        Args:
            saturday: 周六日期
            assignments: 事工安排列表
            
        Returns:
            事件列表
        """
        events = []
        
        # 找到对应周日的安排
        sunday = saturday + timedelta(days=1)  # 周六+1天=周日
        assignment = self._find_assignment_by_date(assignments, sunday)
        
        if assignment:
            # 生成通知内容
            from .template_manager import get_default_template_manager
            template_manager = get_default_template_manager()
            notification_content = template_manager.render_sunday_reminder(assignment)
            
            # 创建事件
            notification_time = self.config['coordinator_calendar'].notification_times.get('sunday_reminder', '20:00')
            start_time = self._combine_date_time(saturday, notification_time)
            end_time = start_time + timedelta(minutes=30)
            
            event = CalendarEvent(
                uid=f"sunday_reminder_{saturday.strftime('%Y%m%d')}@graceirvine.org",
                title=f"发送主日提醒通知 ({sunday.month}/{sunday.day})",
                description=f"发送内容：\n\n{notification_content}",
                start_time=start_time,
                end_time=end_time,
                location="Grace Irvine 教会",
                categories=["通知提醒", "事工协调"],
                alarm_minutes=30
            )
            events.append(event)
        
        return events
    
    def _create_monthly_overview_events(self, first_day: date, assignments: List) -> List[CalendarEvent]:
        """创建月度总览通知事件
        
        Args:
            first_day: 月初日期
            assignments: 事工安排列表
            
        Returns:
            事件列表
        """
        events = []
        
        # 筛选当月的安排
        monthly_assignments = [
            a for a in assignments 
            if a.date.year == first_day.year and a.date.month == first_day.month
        ]
        
        if monthly_assignments:
            # 生成通知内容
            from .template_manager import get_default_template_manager
            template_manager = get_default_template_manager()
            sheet_url = f"https://docs.google.com/spreadsheets/d/{self.config['sync_settings'].get('google_sheets_id', '')}"
            notification_content = template_manager.render_monthly_overview(
                monthly_assignments, first_day.year, first_day.month, sheet_url
            )
            
            # 创建事件
            notification_time = self.config['coordinator_calendar'].notification_times.get('monthly_overview', '09:00')
            start_time = self._combine_date_time(first_day, notification_time)
            end_time = start_time + timedelta(minutes=60)
            
            event = CalendarEvent(
                uid=f"monthly_overview_{first_day.strftime('%Y%m')}@graceirvine.org",
                title=f"发送月度总览通知 ({first_day.year}年{first_day.month}月)",
                description=f"发送内容：\n\n{notification_content}",
                start_time=start_time,
                end_time=end_time,
                location="Grace Irvine 教会",
                categories=["通知提醒", "事工协调", "月度总览"],
                alarm_minutes=60
            )
            events.append(event)
        
        return events
    
    def _create_ministry_events(self, assignment, worker_name: str = None) -> List[CalendarEvent]:
        """创建服事事件
        
        Args:
            assignment: 事工安排
            worker_name: 同工姓名（为空则创建所有相关事件）
            
        Returns:
            事件列表
        """
        events = []
        
        # 服事时间配置
        service_date = assignment.date
        setup_time = "08:30"
        rehearsal_time = "09:00" 
        service_time = "10:00"
        service_end_time = "12:00"
        
        # 检查同工是否参与此次服事
        worker_roles = []
        if not worker_name or assignment.audio_tech == worker_name:
            worker_roles.append(("音控", assignment.audio_tech, rehearsal_time))
        if not worker_name or assignment.screen_operator == worker_name:
            worker_roles.append(("屏幕操作", assignment.screen_operator, rehearsal_time))
        if not worker_name or assignment.camera_operator == worker_name:
            worker_roles.append(("摄像/导播", assignment.camera_operator, "09:30"))
        if not worker_name or assignment.propresenter == worker_name:
            worker_roles.append(("ProPresenter制作", assignment.propresenter, rehearsal_time))
        
        # 为每个角色创建事件
        for role_name, person_name, arrival_time in worker_roles:
            if person_name and person_name != "待安排":
                # 彩排事件
                rehearsal_start = self._combine_date_time(service_date, arrival_time)
                rehearsal_end = self._combine_date_time(service_date, service_time)
                
                rehearsal_event = CalendarEvent(
                    uid=f"rehearsal_{role_name}_{service_date.strftime('%Y%m%d')}_{person_name}@graceirvine.org",
                    title=f"主日彩排 - {role_name}",
                    description=f"角色：{role_name}\n到场时间：{arrival_time}\n负责人：{person_name}\n\n请提前检查设备，做好服事准备。",
                    start_time=rehearsal_start,
                    end_time=rehearsal_end,
                    location="Grace Irvine 教会",
                    categories=["事工服事", "彩排", role_name],
                    alarm_minutes=60
                )
                events.append(rehearsal_event)
                
                # 正式服事事件
                service_start = self._combine_date_time(service_date, service_time)
                service_end = self._combine_date_time(service_date, service_end_time)
                
                service_event = CalendarEvent(
                    uid=f"service_{role_name}_{service_date.strftime('%Y%m%d')}_{person_name}@graceirvine.org",
                    title=f"主日敬拜 - {role_name}",
                    description=f"角色：{role_name}\n负责人：{person_name}\n\n愿主同在，出入平安！",
                    start_time=service_start,
                    end_time=service_end,
                    location="Grace Irvine 教会",
                    categories=["事工服事", "主日敬拜", role_name],
                    alarm_minutes=30
                )
                events.append(service_event)
        
        return events
    
    def _find_assignment_by_date(self, assignments: List, target_date: date):
        """根据日期查找事工安排
        
        Args:
            assignments: 事工安排列表
            target_date: 目标日期
            
        Returns:
            匹配的事工安排或None
        """
        for assignment in assignments:
            if assignment.date == target_date:
                return assignment
        return None
    
    def _combine_date_time(self, date_obj: date, time_str: str) -> datetime:
        """合并日期和时间字符串
        
        Args:
            date_obj: 日期对象
            time_str: 时间字符串 (格式: "HH:MM")
            
        Returns:
            带时区的datetime对象
        """
        hour, minute = map(int, time_str.split(':'))
        dt = datetime.combine(date_obj, datetime.min.time().replace(hour=hour, minute=minute))
        return self.timezone.localize(dt)
    
    def add_subscriber(self, calendar_type: str, email: str) -> bool:
        """添加日历订阅者
        
        Args:
            calendar_type: 日历类型 ('coordinator' 或 'worker')
            email: 订阅者邮箱
            
        Returns:
            是否添加成功
        """
        try:
            config_key = f"{calendar_type}_calendar"
            if config_key in self.config:
                if email not in self.config[config_key].subscribers:
                    self.config[config_key].subscribers.append(email)
                    self.save_config()
                    logger.info(f"Added subscriber {email} to {calendar_type} calendar")
                    return True
                else:
                    logger.warning(f"Subscriber {email} already exists in {calendar_type} calendar")
                    return False
            else:
                logger.error(f"Invalid calendar type: {calendar_type}")
                return False
        except Exception as e:
            logger.error(f"Failed to add subscriber: {e}")
            return False
    
    def remove_subscriber(self, calendar_type: str, email: str) -> bool:
        """移除日历订阅者
        
        Args:
            calendar_type: 日历类型 ('coordinator' 或 'worker')
            email: 订阅者邮箱
            
        Returns:
            是否移除成功
        """
        try:
            config_key = f"{calendar_type}_calendar"
            if config_key in self.config:
                if email in self.config[config_key].subscribers:
                    self.config[config_key].subscribers.remove(email)
                    self.save_config()
                    logger.info(f"Removed subscriber {email} from {calendar_type} calendar")
                    return True
                else:
                    logger.warning(f"Subscriber {email} not found in {calendar_type} calendar")
                    return False
            else:
                logger.error(f"Invalid calendar type: {calendar_type}")
                return False
        except Exception as e:
            logger.error(f"Failed to remove subscriber: {e}")
            return False
    
    def get_subscribers(self, calendar_type: str) -> List[str]:
        """获取日历订阅者列表
        
        Args:
            calendar_type: 日历类型 ('coordinator' 或 'worker')
            
        Returns:
            订阅者邮箱列表
        """
        config_key = f"{calendar_type}_calendar"
        if config_key in self.config:
            return self.config[config_key].subscribers.copy()
        return []

def main():
    """测试函数"""
    try:
        # 初始化ICS管理器
        ics_manager = ICSManager()
        
        # 模拟一些事工安排数据
        from .scheduler import MinistryAssignment
        from datetime import date, timedelta
        
        today = date.today()
        next_sunday = today + timedelta(days=(6-today.weekday()))
        
        test_assignments = [
            MinistryAssignment(
                date=next_sunday,
                audio_tech="张三",
                screen_operator="李四", 
                camera_operator="王五",
                propresenter="赵六",
                video_editor="靖铮"
            ),
            MinistryAssignment(
                date=next_sunday + timedelta(days=7),
                audio_tech="李四",
                screen_operator="王五",
                camera_operator="赵六", 
                propresenter="张三",
                video_editor="靖铮"
            )
        ]
        
        # 生成负责人日历
        print("生成负责人日历...")
        coordinator_calendar = ics_manager.generate_coordinator_calendar(test_assignments)
        print(f"负责人日历已生成: {coordinator_calendar}")
        
        # 生成同工日历
        print("生成同工日历...")
        worker_calendar = ics_manager.generate_worker_calendar(test_assignments)
        print(f"同工日历已生成: {worker_calendar}")
        
        # 生成特定同工的日历
        print("生成张三的个人日历...")
        personal_calendar = ics_manager.generate_worker_calendar(test_assignments, "张三")
        print(f"张三的个人日历已生成: {personal_calendar}")
        
        print("ICS日历系统测试完成！")
        
    except Exception as e:
        logger.error(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
