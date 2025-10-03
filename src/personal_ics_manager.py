#!/usr/bin/env python3
"""
个人ICS日历管理器
为每个服事同工生成独立的可订阅ICS日历文件

功能：
1. 批量生成所有同工的个人ICS文件
2. 为单个同工生成个人ICS文件
3. 管理个人ICS文件的存储和访问
4. 提供订阅URL
"""

import os
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Set
from pathlib import Path
from icalendar import Calendar, Event, Alarm
import pytz

from .models import MinistryAssignment, ServiceRole

# 配置日志
logger = logging.getLogger(__name__)

class PersonalICSManager:
    """个人ICS日历管理器"""
    
    def __init__(self, 
                 output_dir: str = "calendars/personal",
                 timezone_str: str = "America/Los_Angeles"):
        """初始化个人ICS管理器
        
        Args:
            output_dir: ICS文件输出目录
            timezone_str: 时区字符串
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.timezone = pytz.timezone(timezone_str)
        
        # 服事时间配置
        self.service_times = {
            'service_end': '12:00',
            'video_deadline_day': 2,  # 周二
            'video_deadline_time': '20:00'
        }
        
        # 角色到场时间配置（同时也是服事开始时间）
        self.role_arrival_times = {
            ServiceRole.AUDIO_TECH.value: '09:00',
            ServiceRole.VIDEO_DIRECTOR.value: '09:30',
            ServiceRole.PROPRESENTER_PLAY.value: '08:30',
            ServiceRole.PROPRESENTER_UPDATE.value: None,  # ProPresenter更新为远程
            ServiceRole.VIDEO_EDITOR.value: None  # 视频剪辑无需到场
        }
        
        # ProPresenter更新远程工作时间（周六晚上）
        self.propresenter_update_time = {
            'day_offset': -1,  # 主日前1天（周六）
            'start_time': '16:00',  # 下午4点
            'end_time': '21:00'  # 晚上9点
        }
        
        # 提醒时间配置（分钟）
        self.reminder_minutes = {
            'service': 30,    # 服事提前30分钟提醒
            'service_start': 0,  # 服事开始时提醒
            'video_editing': 1440  # 视频剪辑提前1天提醒
        }
        
        # 服事地点
        self.service_location = "200 Cultivate, Irvine, CA 92618"
        
        logger.info(f"个人ICS管理器已初始化，输出目录：{self.output_dir}")
    
    def extract_all_workers(self, assignments: List[MinistryAssignment]) -> Set[str]:
        """从事工安排中提取所有同工名单
        
        Args:
            assignments: 事工安排列表
            
        Returns:
            同工名单集合
        """
        workers = set()
        
        for assignment in assignments:
            # 获取所有非空的事工安排
            all_assignments = assignment.get_all_assignments()
            
            for role, person in all_assignments.items():
                if person and person.strip() and person != "待安排":
                    workers.add(person.strip())
        
        logger.info(f"提取到 {len(workers)} 位同工：{', '.join(sorted(workers))}")
        return workers
    
    def filter_worker_assignments(self, 
                                   assignments: List[MinistryAssignment],
                                   worker_name: str) -> List[Tuple[date, str, MinistryAssignment]]:
        """筛选特定同工的服事安排
        
        Args:
            assignments: 所有事工安排
            worker_name: 同工姓名
            
        Returns:
            (日期, 角色, 事工安排) 的列表
        """
        worker_services = []
        
        for assignment in assignments:
            all_assignments = assignment.get_all_assignments()
            
            for role, person in all_assignments.items():
                if person and person.strip() == worker_name:
                    worker_services.append((assignment.date, role, assignment))
        
        # 按日期排序
        worker_services.sort(key=lambda x: x[0])
        
        logger.info(f"{worker_name} 有 {len(worker_services)} 次服事安排")
        return worker_services
    
    def generate_personal_ics(self,
                              assignments: List[MinistryAssignment],
                              worker_name: str,
                              months_ahead: int = 6) -> Optional[str]:
        """为单个同工生成个人ICS文件
        
        Args:
            assignments: 事工安排列表
            worker_name: 同工姓名
            months_ahead: 生成未来几个月的日历（默认6个月）
            
        Returns:
            生成的ICS文件路径，失败返回None
        """
        try:
            # 筛选未来的服事安排
            today = date.today()
            future_date = today + timedelta(days=30 * months_ahead)
            
            future_assignments = [
                a for a in assignments 
                if today - timedelta(days=7) <= a.date <= future_date
            ]
            
            # 筛选该同工的服事
            worker_services = self.filter_worker_assignments(future_assignments, worker_name)
            
            if not worker_services:
                logger.warning(f"{worker_name} 在未来{months_ahead}个月内没有服事安排")
                return None
            
            # 创建日历
            cal = Calendar()
            cal.add('prodid', f'-//Grace Irvine Ministry Scheduler//Personal Calendar - {worker_name}//CN')
            cal.add('version', '2.0')
            cal.add('calscale', 'GREGORIAN')
            cal.add('method', 'PUBLISH')
            cal.add('x-wr-calname', f'{worker_name} - Grace Irvine 服事日历')
            cal.add('x-wr-caldesc', f'{worker_name}的个人事工服事安排（自动更新）')
            cal.add('x-wr-timezone', 'America/Los_Angeles')
            
            events_created = 0
            
            # 为每次服事创建事件
            for service_date, role, assignment in worker_services:
                events = self._create_service_events(service_date, role, worker_name, assignment)
                
                for event in events:
                    cal.add_component(event)
                    events_created += 1
            
            # 保存ICS文件
            filename = f"{worker_name}_grace_irvine.ics"
            filepath = self.output_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(cal.to_ical())
            
            logger.info(f"✅ 已为 {worker_name} 生成个人日历：{filepath} ({events_created} 个事件)")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ 为 {worker_name} 生成个人日历失败: {e}")
            return None
    
    def _create_service_events(self,
                               service_date: date,
                               role: str,
                               worker_name: str,
                               assignment: MinistryAssignment) -> List[Event]:
        """创建服事事件
        
        Args:
            service_date: 服事日期
            role: 服事角色
            worker_name: 同工姓名
            assignment: 完整的事工安排
            
        Returns:
            事件列表
        """
        events = []
        
        # 远程角色特殊处理
        if role == ServiceRole.VIDEO_EDITOR.value:
            # 视频剪辑：创建截止提醒事件
            deadline_event = self._create_video_editing_event(
                service_date, worker_name, assignment
            )
            events.append(deadline_event)
        elif role == ServiceRole.PROPRESENTER_UPDATE.value:
            # ProPresenter更新：创建周六远程工作事件
            update_event = self._create_propresenter_update_event(
                service_date, worker_name, assignment
            )
            events.append(update_event)
        else:
            # 其他角色：创建现场服事事件
            arrival_time = self.role_arrival_times.get(role, '09:00')
            
            # 创建服事事件
            service_event = self._create_worship_service_event(
                service_date, role, worker_name, arrival_time, assignment
            )
            events.append(service_event)
        
        return events
    
    def _create_worship_service_event(self,
                                      service_date: date,
                                      role: str,
                                      worker_name: str,
                                      arrival_time: str,
                                      assignment: MinistryAssignment) -> Event:
        """创建服事事件"""
        event = Event()
        
        # 事件基本信息
        event.add('uid', f'service_{role}_{service_date.strftime("%Y%m%d")}_{worker_name}@graceirvine.org')
        event.add('summary', f'主日敬拜 - {role}')
        
        # 描述信息
        description_lines = [
            f'服事角色：{role}',
            f'到场时间：{arrival_time}',
            f'服事日期：{service_date.strftime("%Y年%m月%d日")}',
            '',
            '📋 当日服事团队：',
            self._format_team_info(assignment),
            '',
            '💡 提醒事项：',
            '• 请提前检查设备',
            '• 准备好服事内容',
            '• 如有问题请及时联系协调人',
            '',
            '🙏 求主使用，荣耀归主！'
        ]
        event.add('description', '\n'.join(description_lines))
        
        # 时间设置：从到场时间到服事结束
        service_start = self._parse_time(service_date, arrival_time)
        service_end = self._parse_time(service_date, self.service_times['service_end'])
        
        event.add('dtstart', service_start)
        event.add('dtend', service_end)
        event.add('dtstamp', datetime.now(self.timezone))
        event.add('location', self.service_location)
        event.add('categories', ['事工服事', '主日敬拜', role])
        
        # 添加Apple Travel Time提醒功能
        event.add('X-APPLE-TRAVEL-ADVISORY-BEHAVIOR', 'AUTOMATIC')
        
        # 添加三个提醒：Time to Leave、提前30分钟和开始时
        # 提醒1：Apple Time to Leave（出发时间提醒）
        alarm_travel = Alarm()
        alarm_travel.add('action', 'DISPLAY')
        alarm_travel.add('description', f'Time to Leave - {role}')
        alarm_travel.add('trigger', timedelta(minutes=0))  # Apple会自动计算
        # Apple特有属性
        alarm_travel.add('X-APPLE-DEFAULT-ALARM', 'TRUE')
        alarm_travel.add('X-APPLE-PROXIMITY', 'DEPART')
        event.add_component(alarm_travel)
        
        # 提醒2：提前30分钟
        alarm1 = Alarm()
        alarm1.add('action', 'DISPLAY')
        alarm1.add('description', f'提醒：30分钟后开始 - {role}')
        alarm1.add('trigger', timedelta(minutes=-self.reminder_minutes['service']))
        event.add_component(alarm1)
        
        # 提醒3：开始时
        alarm2 = Alarm()
        alarm2.add('action', 'DISPLAY')
        alarm2.add('description', f'提醒：现在开始服事 - {role}')
        alarm2.add('trigger', timedelta(minutes=-self.reminder_minutes['service_start']))
        event.add_component(alarm2)
        
        return event
    
    def _create_propresenter_update_event(self,
                                          service_date: date,
                                          worker_name: str,
                                          assignment: MinistryAssignment) -> Event:
        """创建ProPresenter更新远程工作事件"""
        event = Event()
        
        # 计算工作时间（主日前的周六下午4点到晚上9点）
        saturday = service_date + timedelta(days=self.propresenter_update_time['day_offset'])
        work_start = self._parse_time(saturday, self.propresenter_update_time['start_time'])
        work_end = self._parse_time(saturday, self.propresenter_update_time['end_time'])
        
        # 事件基本信息
        event.add('uid', f'propresenter_update_{service_date.strftime("%Y%m%d")}_{worker_name}@graceirvine.org')
        event.add('summary', f'ProPresenter更新 - {service_date.strftime("%m/%d")}主日')
        
        # 描述信息
        description_lines = [
            f'主日日期：{service_date.strftime("%Y年%m月%d日")}',
            f'工作时间：{saturday.strftime("%Y年%m月%d日")} (周六) {self.propresenter_update_time["start_time"]}-{self.propresenter_update_time["end_time"]}',
            '',
            '📋 当日服事团队：',
            self._format_team_info(assignment),
            '',
            '💡 ProPresenter更新任务：',
            '• 更新主日敬拜歌词',
            '• 检查经文投影',
            '• 准备报告事项',
            '• 测试播放流程',
            '',
            f'⏰ 请在周六 {self.propresenter_update_time["start_time"]}-{self.propresenter_update_time["end_time"]} 完成',
            '',
            '🙏 感谢你的服事！'
        ]
        event.add('description', '\n'.join(description_lines))
        
        # 时间设置
        event.add('dtstart', work_start)
        event.add('dtend', work_end)
        event.add('dtstamp', datetime.now(self.timezone))
        event.add('location', '远程')
        event.add('categories', ['事工服事', 'ProPresenter更新', '远程'])
        
        # 添加提醒（工作开始时）
        alarm = Alarm()
        alarm.add('action', 'DISPLAY')
        alarm.add('description', f'提醒：ProPresenter更新时间 ({service_date.strftime("%m/%d")}主日)')
        alarm.add('trigger', timedelta(minutes=-self.reminder_minutes['service_start']))
        event.add_component(alarm)
        
        return event
    
    def _create_video_editing_event(self,
                                    service_date: date,
                                    worker_name: str,
                                    assignment: MinistryAssignment) -> Event:
        """创建视频剪辑截止提醒事件"""
        event = Event()
        
        # 计算截止时间（主日后的周二晚上8点）
        days_until_tuesday = (self.service_times['video_deadline_day'] - service_date.weekday()) % 7
        if days_until_tuesday == 0:  # 如果主日本身是周二
            days_until_tuesday = 2
        deadline_date = service_date + timedelta(days=days_until_tuesday)
        deadline_time = self._parse_time(deadline_date, self.service_times['video_deadline_time'])
        
        # 事件基本信息
        event.add('uid', f'video_editing_{service_date.strftime("%Y%m%d")}_{worker_name}@graceirvine.org')
        event.add('summary', f'视频剪辑截止 - {service_date.strftime("%m/%d")}主日')
        
        # 描述信息
        description_lines = [
            f'主日日期：{service_date.strftime("%Y年%m月%d日")}',
            f'截止时间：{deadline_date.strftime("%Y年%m月%d日")} {self.service_times["video_deadline_time"]}',
            '',
            '📋 当日服事团队：',
            self._format_team_info(assignment),
            '',
            '💡 视频剪辑要求：',
            '• 完整主日敬拜录像',
            '• 添加片头片尾',
            '• 检查音频质量',
            '• 导出高清版本',
            '',
            f'⏰ 请在 {deadline_date.strftime("%m/%d")} (周二) 晚上8点前完成',
            '',
            '🙏 感谢你的服事！'
        ]
        event.add('description', '\n'.join(description_lines))
        
        # 时间设置（创建一个2小时的时间块用于剪辑）
        event.add('dtstart', deadline_time - timedelta(hours=2))
        event.add('dtend', deadline_time)
        event.add('dtstamp', datetime.now(self.timezone))
        event.add('location', '远程')
        event.add('categories', ['事工服事', '视频剪辑'])
        
        # 添加提醒（提前1天）
        alarm = Alarm()
        alarm.add('action', 'DISPLAY')
        alarm.add('description', f'提醒：视频剪辑截止时间临近 ({service_date.strftime("%m/%d")}主日)')
        alarm.add('trigger', timedelta(minutes=-self.reminder_minutes['video_editing']))
        event.add_component(alarm)
        
        return event
    
    def _format_team_info(self, assignment: MinistryAssignment) -> str:
        """格式化服事团队信息"""
        team_info = []
        all_assignments = assignment.get_all_assignments()
        
        for role, person in all_assignments.items():
            if person:
                team_info.append(f'  • {role}: {person}')
        
        return '\n'.join(team_info) if team_info else '  • (暂无安排)'
    
    def _parse_time(self, date_obj: date, time_str: str) -> datetime:
        """解析时间字符串并转换为datetime对象"""
        hour, minute = map(int, time_str.split(':'))
        dt = datetime.combine(date_obj, datetime.min.time().replace(hour=hour, minute=minute))
        return self.timezone.localize(dt)
    
    def _get_weekday_name(self, weekday: int) -> str:
        """获取星期名称"""
        weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        return weekdays[weekday]
    
    def generate_all_personal_ics(self,
                                  assignments: List[MinistryAssignment],
                                  months_ahead: int = 6) -> Dict[str, str]:
        """批量生成所有同工的个人ICS文件
        
        Args:
            assignments: 事工安排列表
            months_ahead: 生成未来几个月的日历
            
        Returns:
            {同工姓名: ICS文件路径} 的字典
        """
        logger.info("🔄 开始批量生成所有同工的个人ICS文件...")
        
        # 提取所有同工
        workers = self.extract_all_workers(assignments)
        
        # 为每个同工生成ICS
        personal_files = {}
        
        for worker in sorted(workers):
            try:
                filepath = self.generate_personal_ics(assignments, worker, months_ahead)
                if filepath:
                    personal_files[worker] = filepath
            except Exception as e:
                logger.error(f"为 {worker} 生成ICS失败: {e}")
        
        logger.info(f"✅ 批量生成完成！共生成 {len(personal_files)}/{len(workers)} 个个人日历")
        return personal_files
    
    def get_ics_stats(self, filepath: str) -> Dict:
        """获取ICS文件统计信息
        
        Args:
            filepath: ICS文件路径
            
        Returns:
            统计信息字典
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_size = Path(filepath).stat().st_size
            event_count = content.count('BEGIN:VEVENT')
            alarm_count = content.count('BEGIN:VALARM')
            
            return {
                'file_size': file_size,
                'file_size_kb': round(file_size / 1024, 2),
                'event_count': event_count,
                'alarm_count': alarm_count,
                'last_modified': datetime.fromtimestamp(
                    Path(filepath).stat().st_mtime
                ).strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            logger.error(f"获取ICS统计信息失败: {e}")
            return {}
    
    def get_subscription_url(self, 
                            worker_name: str,
                            bucket_name: str,
                            base_url: Optional[str] = None) -> str:
        """获取个人ICS的订阅URL
        
        Args:
            worker_name: 同工姓名
            bucket_name: GCS bucket名称
            base_url: 自定义base URL（可选）
            
        Returns:
            订阅URL
        """
        filename = f"{worker_name}_grace_irvine.ics"
        
        if base_url:
            return f"{base_url}/calendars/personal/{filename}"
        else:
            return f"https://storage.googleapis.com/{bucket_name}/calendars/personal/{filename}"


def main():
    """测试函数"""
    from .scheduler import GoogleSheetsExtractor
    from dotenv import load_dotenv
    import os
    
    try:
        print("🎯 个人ICS日历生成器测试")
        print("=" * 60)
        
        # 加载环境变量
        load_dotenv()
        spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
        
        if not spreadsheet_id:
            print("❌ 错误：未找到 GOOGLE_SPREADSHEET_ID")
            return
        
        # 获取数据
        print("📊 正在从Google Sheets获取数据...")
        extractor = GoogleSheetsExtractor(spreadsheet_id)
        assignments = extractor.parse_ministry_data()
        
        if not assignments:
            print("❌ 未找到事工安排数据")
            return
        
        print(f"✅ 成功获取 {len(assignments)} 条事工安排")
        
        # 创建个人ICS管理器
        manager = PersonalICSManager()
        
        # 为靖铮生成个人日历（示例）
        print("\n👤 为靖铮生成个人日历...")
        jingzheng_ics = manager.generate_personal_ics(assignments, "靖铮")
        
        if jingzheng_ics:
            stats = manager.get_ics_stats(jingzheng_ics)
            print(f"\n📊 靖铮的日历统计：")
            print(f"  • 文件大小：{stats['file_size_kb']} KB")
            print(f"  • 事件数量：{stats['event_count']}")
            print(f"  • 提醒数量：{stats['alarm_count']}")
            print(f"  • 更新时间：{stats['last_modified']}")
            
            # 获取订阅URL示例
            url = manager.get_subscription_url("靖铮", "grace-irvine-scheduler")
            print(f"\n🔗 订阅链接：")
            print(f"  {url}")
        
        # 批量生成所有同工的日历
        print("\n🔄 批量生成所有同工的个人日历...")
        all_files = manager.generate_all_personal_ics(assignments)
        
        print(f"\n✅ 成功生成 {len(all_files)} 个个人日历：")
        for worker, filepath in sorted(all_files.items()):
            stats = manager.get_ics_stats(filepath)
            print(f"  • {worker}: {stats['event_count']} 个事件")
        
        print("\n🎉 测试完成！")
        
    except Exception as e:
        logger.error(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()

