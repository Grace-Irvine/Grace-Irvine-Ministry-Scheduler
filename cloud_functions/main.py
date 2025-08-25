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
        success = email_sender.send_weekly_confirmation(
            recipients=recipients,
            notification_generator=notification_generator
        )
        
        if success:
            logger.info(f"✅ 成功发送周三确认通知给 {len(recipients)} 位收件人")
            return json.dumps({
                'success': True,
                'message': f'成功发送周三确认通知给 {len(recipients)} 位收件人',
                'recipients_count': len(recipients),
                'assignment_date': str(assignment.date),
                'timestamp': datetime.now().isoformat()
            }, ensure_ascii=False), 200
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
        success = email_sender.send_sunday_reminder(
            recipients=recipients,
            notification_generator=notification_generator
        )
        
        if success:
            logger.info(f"✅ 成功发送周六提醒通知给 {len(recipients)} 位收件人")
            return json.dumps({
                'success': True,
                'message': f'成功发送周六提醒通知给 {len(recipients)} 位收件人',
                'recipients_count': len(recipients),
                'assignment_date': str(assignment.date),
                'timestamp': datetime.now().isoformat()
            }, ensure_ascii=False), 200
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
