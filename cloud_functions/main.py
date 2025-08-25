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

# 项目模块
from email_sender import EmailSender, EmailRecipient
from scheduler import GoogleSheetsExtractor, NotificationGenerator

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _load_config() -> Dict[str, Any]:
    """从环境变量加载配置"""
    config = {
        'google_spreadsheet_id': os.getenv('GOOGLE_SPREADSHEET_ID'),
        'sender_email': os.getenv('SENDER_EMAIL', 'jonathanjing@graceirvine.org'),
        'sender_name': os.getenv('SENDER_NAME', 'Grace Irvine 事工协调'),
        'email_password': os.getenv('EMAIL_PASSWORD'),
        'recipient_emails': os.getenv('RECIPIENT_EMAILS', '').split(','),
        'service_account_key': os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY')
    }
    
    # 验证必需配置
    if not config['google_spreadsheet_id']:
        raise ValueError("GOOGLE_SPREADSHEET_ID environment variable is required")
    if not config['email_password']:
        raise ValueError("EMAIL_PASSWORD environment variable is required")
    
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
        logger.info("开始执行周三确认通知任务")
        
        # 加载配置
        config = _load_config()
        
        # 初始化服务
        extractor = GoogleSheetsExtractor(config['google_spreadsheet_id'])
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
        logger.info("开始执行周六提醒通知任务")
        
        # 加载配置
        config = _load_config()
        
        # 初始化服务
        extractor = GoogleSheetsExtractor(config['google_spreadsheet_id'])
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
