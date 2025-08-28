#!/usr/bin/env python3
"""
Unified Scheduler - 统一调度器
集成数据流：Google Sheets → 数据清洗 → 模板生成 → ICS更新 + 邮件发送 → 定时器

数据流程：
1. 从Google Sheets读取数据
2. 清洗并解析数据
3. 根据模板生成待发送内容
4. 同时更新ICS日历和发送邮件通知
5. 统一的定时器管理所有任务
"""

import os
import time
import logging
import threading
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import yaml
import schedule

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UnifiedScheduler:
    """统一调度器 - 集成所有数据流和通知功能"""
    
    def __init__(self, config_path: str = "configs/calendar_config.yaml"):
        """初始化统一调度器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = None
        
        # 核心组件
        self.sheets_extractor = None
        self.template_manager = None
        self.ics_manager = None
        self.email_sender = None
        self.notification_generator = None
        
        # 调度状态
        self.is_running = False
        self.scheduler_thread = None
        self.last_sync_time = None
        self.last_notification_time = None
        self.sync_status = "未开始"
        
        # 初始化
        self.load_config()
        self.initialize_components()
        self.setup_scheduled_tasks()
    
    def load_config(self) -> bool:
        """加载配置文件"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.error(f"Config file not found: {self.config_path}")
                return False
            
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            logger.info(f"Successfully loaded config from {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return False
    
    def initialize_components(self) -> bool:
        """初始化所有核心组件"""
        try:
            # 初始化Google Sheets提取器
            from .scheduler import GoogleSheetsExtractor, NotificationGenerator
            spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID') or self.config.get('sync_settings', {}).get('google_sheets_id', '')
            
            if not spreadsheet_id:
                logger.error("No Google Sheets ID configured")
                return False
            
            self.sheets_extractor = GoogleSheetsExtractor(spreadsheet_id)
            logger.info("✅ Google Sheets extractor initialized")
            
            # 初始化模板管理器
            from .template_manager import get_default_template_manager
            self.template_manager = get_default_template_manager()
            logger.info("✅ Template manager initialized")
            
            # 初始化通知生成器
            self.notification_generator = NotificationGenerator(self.sheets_extractor, self.template_manager)
            logger.info("✅ Notification generator initialized")
            
            # 初始化ICS管理器
            from .ics_manager import ICSManager
            self.ics_manager = ICSManager(self.config_path)
            logger.info("✅ ICS manager initialized")
            
            # 初始化邮件发送器
            try:
                from .email_sender import EmailSender
                self.email_sender = EmailSender()
                logger.info("✅ Email sender initialized")
            except Exception as e:
                logger.warning(f"Email sender initialization failed: {e}")
                self.email_sender = None
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            return False
    
    def setup_scheduled_tasks(self) -> None:
        """设置定时任务"""
        try:
            # 清除之前的任务
            schedule.clear()
            
            # 数据同步任务（每12小时）
            sync_frequency = self.config.get('sync_settings', {}).get('sync_frequency_hours', 12)
            schedule.every(sync_frequency).hours.do(self.sync_data_and_calendars)
            logger.info(f"📅 数据同步任务已设置：每 {sync_frequency} 小时")
            
            # 周三晚上发送确认通知
            notification_time = self.config.get('coordinator_calendar', {}).get('notification_times', {}).get('weekly_confirmation', '20:00')
            schedule.every().wednesday.at(notification_time).do(self.send_weekly_confirmation)
            logger.info(f"📧 周三确认通知已设置：每周三 {notification_time}")
            
            # 周六晚上发送提醒通知
            reminder_time = self.config.get('coordinator_calendar', {}).get('notification_times', {}).get('sunday_reminder', '20:00')
            schedule.every().saturday.at(reminder_time).do(self.send_sunday_reminder)
            logger.info(f"📧 周六提醒通知已设置：每周六 {reminder_time}")
            
            # 每月1日发送月度总览
            monthly_time = self.config.get('coordinator_calendar', {}).get('notification_times', {}).get('monthly_overview', '09:00')
            schedule.every().month.at(monthly_time).do(self.send_monthly_overview)
            logger.info(f"📧 月度总览通知已设置：每月1日 {monthly_time}")
            
        except Exception as e:
            logger.error(f"Failed to setup scheduled tasks: {e}")
    
    def sync_data_and_calendars(self) -> bool:
        """统一的数据同步和日历更新流程"""
        try:
            logger.info("🔄 开始统一数据同步流程...")
            self.sync_status = "同步中"
            
            # 步骤1: 从Google Sheets获取原始数据
            logger.info("📊 步骤1: 读取Google Sheets数据...")
            assignments = self.sheets_extractor.parse_ministry_data()
            
            if not assignments:
                logger.warning("⚠️  未找到事工安排数据")
                self.sync_status = "同步完成 - 无数据"
                return True
            
            logger.info(f"✅ 成功获取 {len(assignments)} 条事工安排")
            
            # 步骤2: 生成模板内容（为后续使用做准备）
            logger.info("📝 步骤2: 预生成模板内容...")
            template_contents = self._generate_all_template_contents(assignments)
            logger.info("✅ 模板内容生成完成")
            
            # 步骤3: 更新ICS日历文件
            logger.info("📅 步骤3: 更新ICS日历文件...")
            self._update_ics_calendars(assignments, template_contents)
            logger.info("✅ ICS日历更新完成")
            
            # 步骤4: 更新同步状态
            self.last_sync_time = datetime.now()
            self.sync_status = f"同步成功 - {self.last_sync_time.strftime('%Y-%m-%d %H:%M:%S')}"
            self._save_sync_status()
            
            logger.info("🎉 统一数据同步流程完成！")
            return True
            
        except Exception as e:
            logger.error(f"❌ 统一数据同步失败: {e}")
            self.sync_status = f"同步失败 - {str(e)}"
            import traceback
            traceback.print_exc()
            return False
    
    def _generate_all_template_contents(self, assignments: List) -> Dict[str, Any]:
        """生成所有模板内容"""
        template_contents = {
            'weekly_confirmations': {},
            'sunday_reminders': {},
            'monthly_overviews': {}
        }
        
        try:
            # 生成周三确认通知内容
            current_assignment = self.sheets_extractor.get_current_week_assignment()
            if current_assignment:
                template_contents['weekly_confirmations']['current'] = {
                    'assignment': current_assignment,
                    'content': self.notification_generator.generate_weekly_confirmation()
                }
            
            # 生成周六提醒通知内容
            next_assignment = self.sheets_extractor.get_next_sunday_assignment()
            if next_assignment:
                template_contents['sunday_reminders']['next'] = {
                    'assignment': next_assignment,
                    'content': self.notification_generator.generate_sunday_reminder()
                }
            
            # 生成月度总览内容
            today = date.today()
            monthly_content = self.notification_generator.generate_monthly_overview(today.year, today.month)
            template_contents['monthly_overviews']['current'] = {
                'year': today.year,
                'month': today.month,
                'content': monthly_content
            }
            
            logger.info("✅ 所有模板内容生成完成")
            return template_contents
            
        except Exception as e:
            logger.error(f"生成模板内容时出错: {e}")
            return template_contents
    
    def _update_ics_calendars(self, assignments: List, template_contents: Dict) -> None:
        """更新ICS日历文件"""
        try:
            # 生成负责人日历
            coordinator_path = self.ics_manager.generate_coordinator_calendar(
                assignments,
                start_date=date.today() - timedelta(days=30),
                end_date=date.today() + timedelta(days=90)
            )
            logger.info(f"📋 负责人日历已更新: {coordinator_path}")
            
            # 生成综合同工日历
            worker_path = self.ics_manager.generate_worker_calendar(assignments)
            logger.info(f"👥 同工日历已更新: {worker_path}")
            
            # 生成个人日历
            self._generate_personal_calendars(assignments)
            
        except Exception as e:
            logger.error(f"更新ICS日历时出错: {e}")
    
    def _generate_personal_calendars(self, assignments: List) -> None:
        """为每个同工生成个人日历"""
        try:
            # 收集所有同工名单
            workers = set()
            for assignment in assignments:
                if assignment.audio_tech and assignment.audio_tech != "待安排":
                    workers.add(assignment.audio_tech)
                if assignment.screen_operator and assignment.screen_operator != "待安排":
                    workers.add(assignment.screen_operator)
                if assignment.camera_operator and assignment.camera_operator != "待安排":
                    workers.add(assignment.camera_operator)
                if assignment.propresenter and assignment.propresenter != "待安排":
                    workers.add(assignment.propresenter)
            
            logger.info(f"🔧 为 {len(workers)} 位同工生成个人日历...")
            
            for worker in workers:
                try:
                    personal_path = self.ics_manager.generate_worker_calendar(assignments, worker)
                    logger.info(f"👤 {worker} 的个人日历已生成: {personal_path}")
                except Exception as e:
                    logger.error(f"生成 {worker} 个人日历时出错: {e}")
            
        except Exception as e:
            logger.error(f"生成个人日历时出错: {e}")
    
    def send_weekly_confirmation(self) -> bool:
        """发送周三确认通知"""
        try:
            logger.info("📧 开始发送周三确认通知...")
            
            if not self.email_sender:
                logger.warning("邮件发送器未初始化，跳过邮件发送")
                return False
            
            # 获取当前周的事工安排
            assignment = self.sheets_extractor.get_current_week_assignment()
            if not assignment:
                logger.warning("未找到本周事工安排，跳过通知发送")
                return False
            
            # 生成通知内容
            notification_content = self.notification_generator.generate_weekly_confirmation()
            
            # 发送邮件
            success = self._send_notification_email(
                subject=f"【本周{assignment.date.month}月{assignment.date.day}日主日事工安排提醒】",
                content=notification_content,
                notification_type="weekly_confirmation"
            )
            
            if success:
                logger.info("✅ 周三确认通知发送成功")
                self.last_notification_time = datetime.now()
                
                # 同时触发数据同步（确保日历是最新的）
                self.sync_data_and_calendars()
                
            return success
            
        except Exception as e:
            logger.error(f"发送周三确认通知时出错: {e}")
            return False
    
    def send_sunday_reminder(self) -> bool:
        """发送周六提醒通知"""
        try:
            logger.info("📧 开始发送周六提醒通知...")
            
            if not self.email_sender:
                logger.warning("邮件发送器未初始化，跳过邮件发送")
                return False
            
            # 获取下个主日的事工安排
            assignment = self.sheets_extractor.get_next_sunday_assignment()
            if not assignment:
                logger.warning("未找到下个主日事工安排，跳过通知发送")
                return False
            
            # 生成通知内容
            notification_content = self.notification_generator.generate_sunday_reminder()
            
            # 发送邮件
            success = self._send_notification_email(
                subject="【主日服事提醒】",
                content=notification_content,
                notification_type="sunday_reminder"
            )
            
            if success:
                logger.info("✅ 周六提醒通知发送成功")
                self.last_notification_time = datetime.now()
                
                # 同时触发数据同步
                self.sync_data_and_calendars()
                
            return success
            
        except Exception as e:
            logger.error(f"发送周六提醒通知时出错: {e}")
            return False
    
    def send_monthly_overview(self) -> bool:
        """发送月度总览通知"""
        try:
            logger.info("📧 开始发送月度总览通知...")
            
            if not self.email_sender:
                logger.warning("邮件发送器未初始化，跳过邮件发送")
                return False
            
            # 生成月度总览内容
            today = date.today()
            notification_content = self.notification_generator.generate_monthly_overview(today.year, today.month)
            
            # 发送邮件
            success = self._send_notification_email(
                subject=f"【{today.year}年{today.month:02d}月事工排班一览】",
                content=notification_content,
                notification_type="monthly_overview"
            )
            
            if success:
                logger.info("✅ 月度总览通知发送成功")
                self.last_notification_time = datetime.now()
                
                # 同时触发数据同步
                self.sync_data_and_calendars()
                
            return success
            
        except Exception as e:
            logger.error(f"发送月度总览通知时出错: {e}")
            return False
    
    def _send_notification_email(self, subject: str, content: str, notification_type: str) -> bool:
        """发送通知邮件"""
        try:
            # 获取收件人列表
            recipients = self._get_notification_recipients(notification_type)
            
            if not recipients:
                logger.warning(f"未找到 {notification_type} 的收件人列表")
                return False
            
            # 发送邮件
            from .email_sender import EmailRecipient
            recipient_objects = [EmailRecipient(email=email, name="") for email in recipients]
            
            success = self.email_sender.send_notification_email(
                subject=subject,
                content=content,
                recipients=recipient_objects
            )
            
            return success
            
        except Exception as e:
            logger.error(f"发送邮件时出错: {e}")
            return False
    
    def _get_notification_recipients(self, notification_type: str) -> List[str]:
        """获取通知收件人列表"""
        try:
            # 从配置中获取收件人
            coordinator_subscribers = self.config.get('coordinator_calendar', {}).get('subscribers', [])
            worker_subscribers = self.config.get('worker_calendar', {}).get('subscribers', [])
            
            # 根据通知类型返回相应的收件人
            if notification_type in ['weekly_confirmation', 'sunday_reminder', 'monthly_overview']:
                # 负责人通知发给协调员
                return coordinator_subscribers
            else:
                # 其他通知发给所有人
                return list(set(coordinator_subscribers + worker_subscribers))
            
        except Exception as e:
            logger.error(f"获取收件人列表时出错: {e}")
            return []
    
    def _save_sync_status(self) -> bool:
        """保存同步状态"""
        try:
            if self.config and 'sync_settings' in self.config:
                self.config['sync_settings']['last_sync'] = self.last_sync_time.isoformat() if self.last_sync_time else None
                
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False, indent=2)
                
                return True
        except Exception as e:
            logger.error(f"Failed to save sync status: {e}")
            return False
    
    def start(self) -> bool:
        """启动统一调度器"""
        try:
            if self.is_running:
                logger.warning("统一调度器已在运行")
                return False
            
            # 检查自动同步设置
            auto_sync_enabled = self.config.get('sync_settings', {}).get('auto_sync_enabled', True)
            if not auto_sync_enabled:
                logger.warning("自动同步已禁用")
                return False
            
            # 启动调度线程
            self.is_running = True
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            
            logger.info("🚀 统一调度器已启动")
            
            # 立即执行一次数据同步
            self.sync_data_and_calendars()
            
            return True
            
        except Exception as e:
            logger.error(f"启动统一调度器失败: {e}")
            return False
    
    def stop(self) -> bool:
        """停止统一调度器"""
        try:
            if not self.is_running:
                logger.warning("统一调度器未在运行")
                return False
            
            self.is_running = False
            schedule.clear()
            
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5)
            
            logger.info("🛑 统一调度器已停止")
            return True
            
        except Exception as e:
            logger.error(f"停止统一调度器失败: {e}")
            return False
    
    def _run_scheduler(self) -> None:
        """运行调度器主循环"""
        logger.info("📅 调度器主循环已启动")
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                logger.error(f"调度器运行出错: {e}")
                time.sleep(60)
        
        logger.info("📅 调度器主循环已停止")
    
    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'is_running': self.is_running,
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'last_notification_time': self.last_notification_time.isoformat() if self.last_notification_time else None,
            'sync_status': self.sync_status,
            'components_status': {
                'sheets_extractor': self.sheets_extractor is not None,
                'template_manager': self.template_manager is not None,
                'ics_manager': self.ics_manager is not None,
                'email_sender': self.email_sender is not None,
                'notification_generator': self.notification_generator is not None
            },
            'scheduled_tasks': len(schedule.jobs),
            'auto_sync_enabled': self.config.get('sync_settings', {}).get('auto_sync_enabled', False),
            'sync_frequency_hours': self.config.get('sync_settings', {}).get('sync_frequency_hours', 12)
        }
    
    def force_sync(self) -> bool:
        """强制立即同步"""
        logger.info("🔧 手动触发统一数据同步...")
        return self.sync_data_and_calendars()
    
    def force_send_notification(self, notification_type: str) -> bool:
        """强制发送指定类型的通知"""
        logger.info(f"🔧 手动触发 {notification_type} 通知发送...")
        
        if notification_type == 'weekly':
            return self.send_weekly_confirmation()
        elif notification_type == 'sunday':
            return self.send_sunday_reminder()
        elif notification_type == 'monthly':
            return self.send_monthly_overview()
        else:
            logger.error(f"未知的通知类型: {notification_type}")
            return False

def main():
    """测试函数"""
    try:
        print("🎯 统一调度器测试")
        print("=" * 50)
        
        # 初始化统一调度器
        scheduler = UnifiedScheduler()
        
        # 显示状态
        status = scheduler.get_status()
        print("📊 系统状态:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        # 测试数据同步
        print("\n🔄 测试数据同步...")
        success = scheduler.force_sync()
        print(f"同步结果: {'✅ 成功' if success else '❌ 失败'}")
        
        # 显示更新后的状态
        status = scheduler.get_status()
        print(f"\n📅 最后同步时间: {status['last_sync_time']}")
        print(f"📝 同步状态: {status['sync_status']}")
        
        print("\n✅ 统一调度器测试完成！")
        
    except Exception as e:
        logger.error(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
