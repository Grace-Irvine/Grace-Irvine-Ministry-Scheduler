#!/usr/bin/env python3
"""
邮件通知发送脚本
集成Google Sheets数据和邮件发送功能

用法:
  python send_email_notifications.py weekly     # 发送周三确认通知
  python send_email_notifications.py sunday     # 发送周六提醒通知
  python send_email_notifications.py test       # 测试模式（只显示不发送）
"""

import sys
import os
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Any
import logging

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.email_sender import EmailSender, EmailRecipient
from src.scheduler import GoogleSheetsExtractor, NotificationGenerator, MinistryAssignment
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmailNotificationService:
    """邮件通知服务"""
    
    def __init__(self):
        """初始化服务"""
        # 加载环境变量
        load_dotenv()
        
        # 初始化组件
        self.email_sender = EmailSender()
        self.spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
        
        if not self.spreadsheet_id:
            raise ValueError("请在 .env 文件中设置 GOOGLE_SPREADSHEET_ID")
        
        self.extractor = GoogleSheetsExtractor(self.spreadsheet_id)
        self.notification_generator = NotificationGenerator(self.extractor)
        
        # 加载收件人配置
        self.recipients = self._load_recipients()
    
    def _load_recipients(self) -> List[EmailRecipient]:
        """加载收件人列表
        
        可以从环境变量、配置文件或数据库加载
        """
        recipients = []
        
        # 从环境变量加载（用逗号分隔的邮箱列表）
        recipient_emails = os.getenv("RECIPIENT_EMAILS", "")
        if recipient_emails:
            for email in recipient_emails.split(","):
                email = email.strip()
                if email:
                    # 简单处理，使用邮箱用户名作为姓名
                    name = email.split("@")[0].replace(".", " ").title()
                    recipients.append(EmailRecipient(email=email, name=name))
        
        # 如果没有配置收件人，使用默认发件人作为测试
        if not recipients:
            sender_email = os.getenv("SENDER_EMAIL", "jonathanjing@graceirvine.org")
            recipients.append(EmailRecipient(
                email=sender_email,
                name="事工协调员"
            ))
        
        return recipients
    
    def _get_recipients_for_assignment(
        self, 
        assignment: MinistryAssignment
    ) -> List[EmailRecipient]:
        """根据事工安排获取相关收件人
        
        未来可以实现：
        - 只发送给当周有服事的同工
        - 根据角色发送不同的邮件内容
        """
        # 目前返回所有收件人
        return self.recipients
    
    def _assignment_to_schedule_dict(
        self, 
        assignment: MinistryAssignment
    ) -> Dict[str, Any]:
        """将MinistryAssignment转换为邮件模板所需的字典格式"""
        return {
            'date': assignment.date,
            'time': '10:00',  # 默认时间
            'location': 'Grace Irvine 教会',
            'roles': {
                '音控': assignment.audio_tech or '待安排',
                '屏幕': assignment.screen_operator or '待安排',
                '摄像/导播': assignment.camera_operator or '待安排',
                'ProPresenter制作': assignment.propresenter or '待安排',
                '视频剪辑': assignment.video_editor
            },
            'notes': ''  # 可以从其他地方获取备注
        }
    
    def send_weekly_confirmation(self, test_mode: bool = False):
        """发送周三确认通知
        
        Args:
            test_mode: 是否为测试模式（只显示不发送）
        """
        logger.info("=" * 60)
        logger.info("📅 发送周三确认通知")
        logger.info("=" * 60)
        
        # 获取本周的事工安排
        assignment = self.extractor.get_current_week_assignment()
        
        if not assignment:
            logger.warning("未找到本周的事工安排")
            return False
        
        # 转换数据格式
        schedule = self._assignment_to_schedule_dict(assignment)
        
        # 获取收件人
        recipients = self._get_recipients_for_assignment(assignment)
        
        # 显示信息
        logger.info(f"服事日期: {assignment.date}")
        logger.info(f"音控: {assignment.audio_tech or '待安排'}")
        logger.info(f"屏幕: {assignment.screen_operator or '待安排'}")
        logger.info(f"摄像/导播: {assignment.camera_operator or '待安排'}")
        logger.info(f"ProPresenter: {assignment.propresenter or '待安排'}")
        logger.info(f"视频剪辑: {assignment.video_editor}")
        logger.info(f"收件人数量: {len(recipients)}")
        
        if test_mode:
            logger.info("【测试模式】不发送邮件，仅显示内容")
            # 生成微信群通知文本
            wechat_msg = self.notification_generator.generate_weekly_confirmation()
            logger.info("\n微信群通知内容:")
            print(wechat_msg)
            return True
        
        # 发送邮件
        try:
            success = self.email_sender.send_weekly_confirmation(
                recipients=recipients,
                week_schedules=[schedule]
            )
            
            if success:
                logger.info(f"✅ 成功发送周三确认通知给 {len(recipients)} 位收件人")
                for recipient in recipients:
                    logger.info(f"   - {recipient.name} <{recipient.email}>")
            else:
                logger.error("❌ 发送周三确认通知失败")
            
            return success
            
        except Exception as e:
            logger.error(f"发送邮件时出错: {e}")
            return False
    
    def send_sunday_reminder(self, test_mode: bool = False):
        """发送周六提醒通知
        
        Args:
            test_mode: 是否为测试模式（只显示不发送）
        """
        logger.info("=" * 60)
        logger.info("🔔 发送周六提醒通知")
        logger.info("=" * 60)
        
        # 获取明天（周日）的事工安排
        assignment = self.extractor.get_next_sunday_assignment()
        
        if not assignment:
            logger.warning("未找到明日的事工安排")
            return False
        
        # 转换数据格式
        schedule = self._assignment_to_schedule_dict(assignment)
        
        # 获取收件人
        recipients = self._get_recipients_for_assignment(assignment)
        
        # 显示信息
        logger.info(f"明日服事日期: {assignment.date}")
        logger.info(f"音控: {assignment.audio_tech or '待安排'}")
        logger.info(f"屏幕: {assignment.screen_operator or '待安排'}")
        logger.info(f"摄像/导播: {assignment.camera_operator or '待安排'}")
        logger.info(f"ProPresenter: {assignment.propresenter or '待安排'}")
        logger.info(f"视频剪辑: {assignment.video_editor}")
        logger.info(f"收件人数量: {len(recipients)}")
        
        if test_mode:
            logger.info("【测试模式】不发送邮件，仅显示内容")
            # 生成微信群通知文本
            wechat_msg = self.notification_generator.generate_sunday_reminder()
            logger.info("\n微信群通知内容:")
            print(wechat_msg)
            return True
        
        # 发送邮件
        try:
            success = self.email_sender.send_sunday_reminder(
                recipients=recipients,
                sunday_schedule=schedule
            )
            
            if success:
                logger.info(f"✅ 成功发送周六提醒通知给 {len(recipients)} 位收件人")
                for recipient in recipients:
                    logger.info(f"   - {recipient.name} <{recipient.email}>")
            else:
                logger.error("❌ 发送周六提醒通知失败")
            
            return success
            
        except Exception as e:
            logger.error(f"发送邮件时出错: {e}")
            return False
    
    def send_both_notifications(self, test_mode: bool = False):
        """发送所有通知（用于测试）"""
        logger.info("发送所有通知...")
        
        # 发送周三确认
        self.send_weekly_confirmation(test_mode)
        
        logger.info("")  # 空行分隔
        
        # 发送周六提醒
        self.send_sunday_reminder(test_mode)

def main():
    """主函数"""
    # 检查参数
    if len(sys.argv) < 2:
        print("用法:")
        print("  python send_email_notifications.py weekly  # 发送周三确认通知")
        print("  python send_email_notifications.py sunday  # 发送周六提醒通知")
        print("  python send_email_notifications.py all     # 发送所有通知")
        print("  python send_email_notifications.py test    # 测试模式（不发送）")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    try:
        # 初始化服务
        service = EmailNotificationService()
        
        # 根据命令执行相应操作
        if command == "weekly":
            service.send_weekly_confirmation()
        elif command == "sunday":
            service.send_sunday_reminder()
        elif command == "all":
            service.send_both_notifications()
        elif command == "test":
            logger.info("【测试模式】显示通知内容但不发送邮件")
            service.send_both_notifications(test_mode=True)
        else:
            logger.error(f"未知命令: {command}")
            logger.info("支持的命令: weekly, sunday, all, test")
            sys.exit(1)
        
        logger.info("\n✅ 操作完成!")
        
    except Exception as e:
        logger.error(f"❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
