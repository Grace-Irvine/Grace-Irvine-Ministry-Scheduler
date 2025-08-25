#!/usr/bin/env python3
"""
邮件发送模块 - Email Sender Module
用于发送事工安排通知邮件
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from jinja2 import Environment, FileSystemLoader, Template
from dataclasses import dataclass

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class EmailConfig:
    """邮件配置"""
    smtp_server: str = "smtp.gmail.com"  # Gmail SMTP服务器
    smtp_port: int = 587  # TLS端口
    sender_email: str = "jonathanjing@graceirvine.org"
    sender_name: str = "Grace Irvine 事工协调"
    sender_password: str = ""  # 从环境变量读取
    use_tls: bool = True

@dataclass
class EmailRecipient:
    """邮件接收者"""
    email: str
    name: str
    role: Optional[str] = None

class EmailSender:
    """邮件发送器"""
    
    def __init__(self, config: Optional[EmailConfig] = None):
        """初始化邮件发送器
        
        Args:
            config: 邮件配置，如果为None则使用默认配置
        """
        self.config = config or EmailConfig()
        self._load_config_from_env()
        self._setup_template_engine()
    
    def _load_config_from_env(self):
        """从环境变量加载配置"""
        # 从环境变量读取敏感信息
        self.config.sender_password = os.getenv("EMAIL_PASSWORD", "")
        self.config.smtp_server = os.getenv("SMTP_SERVER", self.config.smtp_server)
        self.config.smtp_port = int(os.getenv("SMTP_PORT", str(self.config.smtp_port)))
        self.config.sender_email = os.getenv("SENDER_EMAIL", self.config.sender_email)
        self.config.sender_name = os.getenv("SENDER_NAME", self.config.sender_name)
        
        if not self.config.sender_password:
            logger.warning("EMAIL_PASSWORD not set in environment variables")
    
    def _setup_template_engine(self):
        """设置Jinja2模板引擎"""
        template_dir = Path(__file__).parent.parent / "templates" / "email"
        if template_dir.exists():
            self.template_env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                autoescape=True
            )
            # 添加自定义过滤器
            self.template_env.filters['chinese_date'] = self._format_chinese_date
            self.template_env.filters['chinese_time'] = self._format_chinese_time
            self.template_env.filters['chinese_weekday'] = self._format_chinese_weekday
        else:
            logger.warning(f"Template directory not found: {template_dir}")
            self.template_env = None
    
    def _format_chinese_date(self, date_obj: date) -> str:
        """格式化为中文日期"""
        if isinstance(date_obj, str):
            try:
                date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
            except:
                return date_obj
        return f"{date_obj.year}年{date_obj.month}月{date_obj.day}日"
    
    def _format_chinese_time(self, time_str: str) -> str:
        """格式化为中文时间"""
        try:
            if ":" in time_str:
                parts = time_str.split(":")
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
                
                period = "上午" if hour < 12 else "下午"
                if hour > 12:
                    hour -= 12
                elif hour == 0:
                    hour = 12
                
                if minute == 0:
                    return f"{period}{hour}点"
                else:
                    return f"{period}{hour}点{minute}分"
        except:
            pass
        return time_str
    
    def _format_chinese_weekday(self, date_obj: date) -> str:
        """格式化为中文星期"""
        if isinstance(date_obj, str):
            try:
                date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
            except:
                return ""
        
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        return weekdays[date_obj.weekday()]
    
    def _connect_smtp(self) -> smtplib.SMTP:
        """连接到SMTP服务器"""
        try:
            # 创建SMTP连接
            if self.config.use_tls:
                server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.config.smtp_server, self.config.smtp_port)
            
            # 登录
            if self.config.sender_password:
                server.login(self.config.sender_email, self.config.sender_password)
                logger.info(f"Successfully connected to SMTP server: {self.config.smtp_server}")
            else:
                logger.warning("No password provided, attempting to send without authentication")
            
            return server
            
        except Exception as e:
            logger.error(f"Failed to connect to SMTP server: {e}")
            raise
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """渲染邮件模板
        
        Args:
            template_name: 模板文件名
            context: 模板上下文数据
            
        Returns:
            渲染后的HTML内容
        """
        if not self.template_env:
            logger.error("Template engine not initialized")
            return ""
        
        try:
            template = self.template_env.get_template(template_name)
            
            # 添加默认上下文
            default_context = {
                'church_name': 'Grace Irvine 恩典尔湾教会',
                'generated_at': datetime.now(),
                'year': datetime.now().year
            }
            default_context.update(context)
            
            return template.render(**default_context)
            
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            return ""
    
    def send_email(
        self,
        recipients: List[EmailRecipient],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        cc: Optional[List[EmailRecipient]] = None,
        bcc: Optional[List[EmailRecipient]] = None
    ) -> bool:
        """发送邮件
        
        Args:
            recipients: 收件人列表
            subject: 邮件主题
            html_content: HTML格式的邮件内容
            text_content: 纯文本格式的邮件内容（可选）
            cc: 抄送列表
            bcc: 密送列表
            
        Returns:
            是否发送成功
        """
        try:
            # 创建邮件消息
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = formataddr((self.config.sender_name, self.config.sender_email))
            
            # 设置收件人
            to_emails = [formataddr((r.name, r.email)) for r in recipients]
            msg['To'] = ', '.join(to_emails)
            
            # 设置抄送
            if cc:
                cc_emails = [formataddr((r.name, r.email)) for r in cc]
                msg['Cc'] = ', '.join(cc_emails)
            
            # 添加纯文本内容
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # 添加HTML内容
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 收集所有收件人地址
            all_recipients = [r.email for r in recipients]
            if cc:
                all_recipients.extend([r.email for r in cc])
            if bcc:
                all_recipients.extend([r.email for r in bcc])
            
            # 连接服务器并发送
            with self._connect_smtp() as server:
                server.send_message(msg, to_addrs=all_recipients)
                logger.info(f"Email sent successfully to {len(all_recipients)} recipients")
                return True
                
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def send_weekly_confirmation(
        self,
        recipients: List[EmailRecipient],
        notification_generator,
        wechat_message: str = ""
    ) -> bool:
        """发送周三确认通知邮件（包含微信群模板）
        
        Args:
            recipients: 收件人列表
            notification_generator: NotificationGenerator实例
            wechat_message: 微信群通知文本（如果为空则自动生成）
            
        Returns:
            是否发送成功
        """
        # 如果没有提供微信群消息，则使用NotificationGenerator生成
        if not wechat_message:
            wechat_message = notification_generator.generate_weekly_confirmation()
        
        # 获取本周安排用于统计
        assignment = notification_generator.extractor.get_current_week_assignment()
        
        # 准备模板上下文
        context = {
            'wechat_message': wechat_message,
            'week_range': self._get_week_range(),
            'assignment': assignment
        }
        
        # 如果有具体安排，添加统计信息
        if assignment:
            roles = {
                '音控': assignment.audio_tech,
                '屏幕': assignment.screen_operator,
                '摄像/导播': assignment.camera_operator,
                'ProPresenter制作': assignment.propresenter,
                '视频剪辑': assignment.video_editor
            }
            
            # 过滤出有人员的角色
            active_roles = {k: v for k, v in roles.items() if v}
            
            context.update({
                'total_services': 1,
                'total_assignments': len(active_roles),
                'unique_volunteers': len(set(active_roles.values())),
                'volunteer_list': list(set(active_roles.values())),
                'roles': active_roles
            })
        else:
            context.update({
                'total_services': 0,
                'total_assignments': 0,
                'unique_volunteers': 0,
                'volunteer_list': [],
                'roles': {}
            })
        
        # 渲染模板
        html_content = self.render_template('weekly_confirmation_wechat.html', context)
        
        # 发送邮件
        subject = f"【微信群通知模板】本周事工安排确认 - {context['week_range']}"
        return self.send_email(
            recipients=recipients,
            subject=subject,
            html_content=html_content,
            text_content=wechat_message
        )
    
    def send_sunday_reminder(
        self,
        recipients: List[EmailRecipient],
        notification_generator,
        wechat_message: str = ""
    ) -> bool:
        """发送周六提醒通知邮件（包含微信群模板）
        
        Args:
            recipients: 收件人列表
            notification_generator: NotificationGenerator实例
            wechat_message: 微信群通知文本（如果为空则自动生成）
            
        Returns:
            是否发送成功
        """
        # 如果没有提供微信群消息，则使用NotificationGenerator生成
        if not wechat_message:
            wechat_message = notification_generator.generate_sunday_reminder()
        
        # 获取明日安排
        assignment = notification_generator.extractor.get_next_sunday_assignment()
        
        # 准备模板上下文
        tomorrow = date.today() + timedelta(days=1)
        context = {
            'wechat_message': wechat_message,
            'service_date': tomorrow,
            'service_time': '10:00',
            'arrival_time': '09:30',
            'location': 'Grace Irvine 教会',
            'assignment': assignment
        }
        
        # 如果有具体安排，添加详细信息
        if assignment:
            roles = {
                '音控': assignment.audio_tech,
                '屏幕': assignment.screen_operator,
                '摄像/导播': assignment.camera_operator,
                'ProPresenter制作': assignment.propresenter,
                '视频剪辑': assignment.video_editor
            }
            
            # 过滤出有人员的角色
            active_roles = {k: v for k, v in roles.items() if v}
            
            context.update({
                'assignments_count': len(active_roles),
                'roles': active_roles
            })
        else:
            context.update({
                'assignments_count': 0,
                'roles': {}
            })
        
        # 渲染模板
        html_content = self.render_template('sunday_reminder_wechat.html', context)
        
        # 发送邮件
        subject = f"【微信群通知模板】明日主日服事提醒 - {self._format_chinese_date(tomorrow)}"
        return self.send_email(
            recipients=recipients,
            subject=subject,
            html_content=html_content,
            text_content=wechat_message
        )
    
    def _get_week_range(self) -> str:
        """获取本周日期范围"""
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        return f"{start_of_week.month}月{start_of_week.day}日-{end_of_week.month}月{end_of_week.day}日"
    
    def _generate_weekly_text(self, week_schedules: List[Dict[str, Any]]) -> str:
        """生成周三确认通知的纯文本版本"""
        text = f"【本周事工安排确认】\n"
        text += f"{self._get_week_range()}\n\n"
        
        for schedule in week_schedules:
            text += f"日期：{schedule.get('date', '')}\n"
            text += f"时间：{schedule.get('time', '')}\n"
            text += f"地点：{schedule.get('location', '')}\n"
            
            roles = schedule.get('roles', {})
            if roles:
                text += "服事安排：\n"
                for service_type, person in roles.items():
                    text += f"  - {service_type}：{person}\n"
            
            if schedule.get('notes'):
                text += f"备注：{schedule['notes']}\n"
            text += "\n"
        
        text += "请确认您的服事安排，如有冲突请及时联系协调。\n"
        text += "愿神祝福您的服事！"
        
        return text
    
    def _generate_sunday_text(self, sunday_schedule: Dict[str, Any]) -> str:
        """生成周六提醒通知的纯文本版本"""
        tomorrow = date.today() + timedelta(days=1)
        text = f"【明日主日服事提醒】\n"
        text += f"{self._format_chinese_date(tomorrow)}\n\n"
        
        text += "聚会时间：上午10:00\n"
        text += "建议到达时间：上午9:30\n\n"
        
        roles = sunday_schedule.get('roles', {})
        if roles:
            text += "您的服事安排：\n"
            for service_type, person in roles.items():
                text += f"  - {service_type}：{person}\n"
        
        text += "\n请提前到达做好准备。\n"
        text += "如有紧急情况无法服事，请立即联系协调员。\n"
        text += "愿神赐福您的服事！"
        
        return text

# 便捷函数
def create_email_sender() -> EmailSender:
    """创建邮件发送器实例"""
    return EmailSender()

def test_connection() -> bool:
    """测试邮件服务器连接"""
    sender = create_email_sender()
    try:
        with sender._connect_smtp() as server:
            logger.info("Email server connection test successful")
            return True
    except Exception as e:
        logger.error(f"Email server connection test failed: {e}")
        return False
