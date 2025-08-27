#!/usr/bin/env python3
"""
Google Cloud Functions 邮件通知函数
用于定时发送事工安排通知邮件
"""

import os
import json
import logging
from typing import Any, Dict
from datetime import datetime

# Google Cloud Functions 依赖
import functions_framework
from flask import Request
from google.cloud import secretmanager

# 项目模块
from email_sender import EmailSender, EmailRecipient
from scheduler import GoogleSheetsExtractor, NotificationGenerator
from template_manager import get_default_template_manager

# Cloud Storage for ICS files
from google.cloud import storage

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _get_secret(secret_id: str, project_id: str = "ai-for-god") -> str:
    """从 Secret Manager 获取密钥"""
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Failed to get secret {secret_id}: {e}")
        return ""

def _load_config() -> Dict[str, Any]:
    """从 Secret Manager 加载配置"""
    config = {
        'google_spreadsheet_id': _get_secret('google-spreadsheet-id'),
        'sender_email': _get_secret('sender-email'),
        'sender_name': _get_secret('sender-name'),
        'email_password': _get_secret('email-password'),
        'recipient_emails': _get_secret('recipient-emails').split(','),
        'service_account_key': _get_secret('google-service-account-key')
    }
    
    # 验证必需配置
    if not config['google_spreadsheet_id']:
        raise ValueError("google-spreadsheet-id secret is required")
    if not config['email_password']:
        raise ValueError("email-password secret is required")
    
    # 设置环境变量供其他模块使用
    os.environ['GOOGLE_SPREADSHEET_ID'] = config['google_spreadsheet_id']
    os.environ['SENDER_EMAIL'] = config['sender_email']
    os.environ['SENDER_NAME'] = config['sender_name']
    os.environ['EMAIL_PASSWORD'] = config['email_password']
    
    # 写入服务账号密钥文件到临时位置
    if config['service_account_key']:
        import tempfile
        import json
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        service_account_path = os.path.join(temp_dir, 'service_account.json')
        
        # 写入服务账号密钥
        with open(service_account_path, 'w') as f:
            f.write(config['service_account_key'])
        
        # 设置环境变量
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_path
    
    return config

def _update_ics_calendar(extractor: GoogleSheetsExtractor) -> bool:
    """更新ICS日历文件到Cloud Storage"""
    try:
        logger.info("📅 开始更新ICS日历文件...")
        
        # 获取数据
        assignments = extractor.parse_ministry_data()
        if not assignments:
            logger.warning("未找到事工安排数据")
            return False
        
        template_manager = get_default_template_manager()
        
        # 生成负责人日历ICS内容
        coordinator_ics = _generate_coordinator_ics(assignments, template_manager)
        
        if coordinator_ics:
            # 上传到Cloud Storage
            bucket_name = os.getenv('ICS_STORAGE_BUCKET', 'grace-irvine-calendars')
            success = _upload_to_storage(coordinator_ics, 'grace_irvine_coordinator.ics', bucket_name)
            
            if success:
                logger.info("✅ 负责人日历已更新到Cloud Storage")
                return True
            else:
                logger.error("❌ 上传ICS文件到Cloud Storage失败")
                return False
        else:
            logger.error("❌ 生成负责人日历失败")
            return False
            
    except Exception as e:
        logger.error(f"更新ICS日历失败: {e}")
        return False

def _generate_coordinator_ics(assignments, template_manager) -> str:
    """生成负责人日历ICS内容"""
    try:
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
        
        from datetime import date, timedelta
        today = date.today()
        future_assignments = [a for a in assignments if a.date >= today][:10]
        
        for assignment in future_assignments:
            # 周三确认通知事件
            wednesday = assignment.date - timedelta(days=4)
            if wednesday >= today - timedelta(days=7):
                try:
                    notification_content = template_manager.render_weekly_confirmation(assignment)
                    event_ics = _create_ics_event(
                        uid=f"weekly_confirmation_{wednesday.strftime('%Y%m%d')}@graceirvine.org",
                        summary=f"发送周末确认通知 ({assignment.date.month}/{assignment.date.day})",
                        description=f"发送内容：\n\n{notification_content}",
                        start_dt=datetime.combine(wednesday, datetime.min.time().replace(hour=20, minute=0)),
                        end_dt=datetime.combine(wednesday, datetime.min.time().replace(hour=20, minute=30))
                    )
                    ics_lines.append(event_ics)
                except Exception as e:
                    logger.error(f"创建周三事件失败: {e}")
            
            # 周六提醒通知事件
            saturday = assignment.date - timedelta(days=1)
            if saturday >= today - timedelta(days=7):
                try:
                    notification_content = template_manager.render_sunday_reminder(assignment)
                    event_ics = _create_ics_event(
                        uid=f"sunday_reminder_{saturday.strftime('%Y%m%d')}@graceirvine.org",
                        summary=f"发送主日提醒通知 ({assignment.date.month}/{assignment.date.day})",
                        description=f"发送内容：\n\n{notification_content}",
                        start_dt=datetime.combine(saturday, datetime.min.time().replace(hour=20, minute=0)),
                        end_dt=datetime.combine(saturday, datetime.min.time().replace(hour=20, minute=30))
                    )
                    ics_lines.append(event_ics)
                except Exception as e:
                    logger.error(f"创建周六事件失败: {e}")
        
        ics_lines.append("END:VCALENDAR")
        return "\n".join(ics_lines)
        
    except Exception as e:
        logger.error(f"生成负责人日历失败: {e}")
        return None

def _create_ics_event(uid: str, summary: str, description: str, start_dt: datetime, end_dt: datetime) -> str:
    """创建ICS事件字符串"""
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
        f"LOCATION:Grace Irvine 教会",
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        f"DESCRIPTION:提醒：{escape_ics_text(summary)}",
        "TRIGGER:-PT30M",
        "END:VALARM",
        "END:VEVENT"
    ]
    
    return "\n".join(event_lines)

def _upload_to_storage(content: str, filename: str, bucket_name: str) -> bool:
    """上传文件到Cloud Storage"""
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(filename)
        
        # 上传内容
        blob.upload_from_string(
            content,
            content_type='text/calendar; charset=utf-8'
        )
        
        # 设置公开访问
        blob.make_public()
        
        logger.info(f"✅ 文件已上传: gs://{bucket_name}/{filename}")
        return True
        
    except Exception as e:
        logger.error(f"上传到Cloud Storage失败: {e}")
        return False

def _create_recipients(email_list: list) -> list:
    """创建收件人列表"""
    recipients = []
    for email in email_list:
        email = email.strip()
        if email:
            name = email.split("@")[0].replace(".", " ").title()
            recipients.append(EmailRecipient(email=email, name=name))
    
    return recipients

@functions_framework.http
def send_weekly_confirmation(request: Request) -> tuple:
    """
    发送周三确认通知的Cloud Function
    
    Args:
        request: HTTP请求对象
        
    Returns:
        响应元组 (消息, 状态码)
    """
    try:
        import tempfile
        logger.info("开始执行周三确认通知任务")
        
        # 加载配置
        config = _load_config()
        
        # 初始化服务
        # 使用临时服务账号文件路径
        temp_dir = tempfile.mkdtemp()
        service_account_path = os.path.join(temp_dir, 'service_account.json')
        
        # 写入服务账号密钥
        with open(service_account_path, 'w') as f:
            f.write(config['service_account_key'])
        
        extractor = GoogleSheetsExtractor(config['google_spreadsheet_id'], service_account_path)
        notification_generator = NotificationGenerator(extractor)
        email_sender = EmailSender()
        
        # 获取本周安排
        assignment = extractor.get_current_week_assignment()
        if not assignment:
            logger.warning("未找到本周的事工安排")
            return json.dumps({
                'success': False,
                'message': '未找到本周的事工安排',
                'timestamp': datetime.now().isoformat()
            }, ensure_ascii=False), 200
        
        # 创建收件人列表
        recipients = _create_recipients(config['recipient_emails'])
        
        # 发送邮件
        email_success = email_sender.send_weekly_confirmation(
            recipients=recipients,
            notification_generator=notification_generator
        )
        
        # 同时更新ICS日历
        ics_success = _update_ics_calendar(extractor)
        
        if email_success:
            logger.info(f"✅ 成功发送周三确认通知给 {len(recipients)} 位收件人")
            
            result = {
                'success': True,
                'message': f'成功发送周三确认通知给 {len(recipients)} 位收件人',
                'recipients_count': len(recipients),
                'assignment_date': str(assignment.date),
                'ics_calendar_updated': ics_success,
                'timestamp': datetime.now().isoformat()
            }
            
            if ics_success:
                result['message'] += ' 并更新了ICS日历'
            
            return json.dumps(result, ensure_ascii=False), 200
        else:
            logger.error("❌ 发送周三确认通知失败")
            return json.dumps({
                'success': False,
                'message': '发送周三确认通知失败',
                'timestamp': datetime.now().isoformat()
            }, ensure_ascii=False), 500
            
    except Exception as e:
        logger.error(f"执行周三确认通知时出错: {e}")
        return json.dumps({
            'success': False,
            'message': f'执行出错: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }, ensure_ascii=False), 500

@functions_framework.http
def send_sunday_reminder(request: Request) -> tuple:
    """
    发送周六提醒通知的Cloud Function
    
    Args:
        request: HTTP请求对象
        
    Returns:
        响应元组 (消息, 状态码)
    """
    try:
        import tempfile
        logger.info("开始执行周六提醒通知任务")
        
        # 加载配置
        config = _load_config()
        
        # 初始化服务
        # 使用临时服务账号文件路径
        temp_dir = tempfile.mkdtemp()
        service_account_path = os.path.join(temp_dir, 'service_account.json')
        
        # 写入服务账号密钥
        with open(service_account_path, 'w') as f:
            f.write(config['service_account_key'])
        
        extractor = GoogleSheetsExtractor(config['google_spreadsheet_id'], service_account_path)
        notification_generator = NotificationGenerator(extractor)
        email_sender = EmailSender()
        
        # 获取明日安排
        assignment = extractor.get_next_sunday_assignment()
        if not assignment:
            logger.warning("未找到明日的事工安排")
            return json.dumps({
                'success': False,
                'message': '未找到明日的事工安排',
                'timestamp': datetime.now().isoformat()
            }, ensure_ascii=False), 200
        
        # 创建收件人列表
        recipients = _create_recipients(config['recipient_emails'])
        
        # 发送邮件
        email_success = email_sender.send_sunday_reminder(
            recipients=recipients,
            notification_generator=notification_generator
        )
        
        # 同时更新ICS日历
        ics_success = _update_ics_calendar(extractor)
        
        if email_success:
            logger.info(f"✅ 成功发送周六提醒通知给 {len(recipients)} 位收件人")
            
            result = {
                'success': True,
                'message': f'成功发送周六提醒通知给 {len(recipients)} 位收件人',
                'recipients_count': len(recipients),
                'assignment_date': str(assignment.date),
                'ics_calendar_updated': ics_success,
                'timestamp': datetime.now().isoformat()
            }
            
            if ics_success:
                result['message'] += ' 并更新了ICS日历'
            
            return json.dumps(result, ensure_ascii=False), 200
        else:
            logger.error("❌ 发送周六提醒通知失败")
            return json.dumps({
                'success': False,
                'message': '发送周六提醒通知失败',
                'timestamp': datetime.now().isoformat()
            }, ensure_ascii=False), 500
            
    except Exception as e:
        logger.error(f"执行周六提醒通知时出错: {e}")
        return json.dumps({
            'success': False,
            'message': f'执行出错: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }, ensure_ascii=False), 500

# 健康检查端点
@functions_framework.http
def health_check(request: Request) -> tuple:
    """健康检查端点"""
    return json.dumps({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Grace Irvine Ministry Scheduler'
    }, ensure_ascii=False), 200
