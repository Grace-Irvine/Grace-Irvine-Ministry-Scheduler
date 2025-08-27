#!/usr/bin/env python3
"""
ICS日历更新Cloud Function
供Cloud Scheduler调用，更新ICS日历文件并上传到Cloud Storage

功能：
1. 从Google Sheets获取最新数据
2. 生成ICS日历文件
3. 上传到Cloud Storage
4. 提供公开URL供用户订阅
"""

import os
import sys
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from google.cloud import storage
import functions_framework

# 设置项目路径
sys.path.append(str(Path(__file__).parent.parent))

from src.scheduler import GoogleSheetsExtractor
from src.template_manager import get_default_template_manager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def escape_ics_text(text: str) -> str:
    """转义ICS文本中的特殊字符"""
    text = text.replace('\\', '\\\\')
    text = text.replace(',', '\\,')
    text = text.replace(';', '\\;')
    text = text.replace('\n', '\\n')
    return text

def create_ics_event(uid: str, summary: str, description: str, 
                    start_dt: datetime, end_dt: datetime, location: str = "") -> str:
    """创建ICS事件字符串"""
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

def generate_coordinator_ics(assignments) -> str:
    """生成负责人日历ICS内容"""
    try:
        template_manager = get_default_template_manager()
        
        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Grace Irvine Ministry Scheduler//Coordinator Calendar//CN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:Grace Irvine 事工协调日历",
            "X-WR-CALDESC:事工通知发送提醒日历（Cloud Scheduler自动更新）",
            "X-WR-TIMEZONE:America/Los_Angeles",
            f"X-WR-CALDESC:最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        
        today = date.today()
        future_assignments = [a for a in assignments if a.date >= today][:15]
        
        events_created = 0
        
        for assignment in future_assignments:
            # 周三确认通知事件
            wednesday = assignment.date - timedelta(days=4)
            if wednesday >= today - timedelta(days=7):
                try:
                    notification_content = template_manager.render_weekly_confirmation(assignment)
                    event_ics = create_ics_event(
                        uid=f"weekly_confirmation_{wednesday.strftime('%Y%m%d')}@graceirvine.org",
                        summary=f"发送周末确认通知 ({assignment.date.month}/{assignment.date.day})",
                        description=f"发送内容：\n\n{notification_content}",
                        start_dt=datetime.combine(wednesday, datetime.min.time().replace(hour=20, minute=0)),
                        end_dt=datetime.combine(wednesday, datetime.min.time().replace(hour=20, minute=30)),
                        location="Grace Irvine 教会"
                    )
                    ics_lines.append(event_ics)
                    events_created += 1
                except Exception as e:
                    logger.error(f"创建周三事件失败: {e}")
            
            # 周六提醒通知事件
            saturday = assignment.date - timedelta(days=1)
            if saturday >= today - timedelta(days=7):
                try:
                    notification_content = template_manager.render_sunday_reminder(assignment)
                    event_ics = create_ics_event(
                        uid=f"sunday_reminder_{saturday.strftime('%Y%m%d')}@graceirvine.org",
                        summary=f"发送主日提醒通知 ({assignment.date.month}/{assignment.date.day})",
                        description=f"发送内容：\n\n{notification_content}",
                        start_dt=datetime.combine(saturday, datetime.min.time().replace(hour=20, minute=0)),
                        end_dt=datetime.combine(saturday, datetime.min.time().replace(hour=20, minute=30)),
                        location="Grace Irvine 教会"
                    )
                    ics_lines.append(event_ics)
                    events_created += 1
                except Exception as e:
                    logger.error(f"创建周六事件失败: {e}")
        
        ics_lines.append("END:VCALENDAR")
        
        logger.info(f"✅ 负责人日历生成完成: {events_created} 个事件")
        return "\n".join(ics_lines)
        
    except Exception as e:
        logger.error(f"生成负责人日历失败: {e}")
        return None

def upload_to_cloud_storage(content: str, filename: str, bucket_name: str) -> str:
    """上传ICS文件到Cloud Storage"""
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(f"calendars/{filename}")
        
        # 设置适当的内容类型和缓存头
        blob.upload_from_string(
            content,
            content_type='text/calendar; charset=utf-8'
        )
        
        # 设置公开访问
        blob.make_public()
        
        public_url = blob.public_url
        logger.info(f"✅ 文件已上传: {public_url}")
        
        return public_url
        
    except Exception as e:
        logger.error(f"上传到Cloud Storage失败: {e}")
        return None

@functions_framework.http
def update_ics_calendars(request):
    """Cloud Function入口点 - 更新ICS日历"""
    try:
        logger.info("📅 开始更新ICS日历...")
        
        # 获取配置
        spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
        bucket_name = os.getenv('STORAGE_BUCKET_NAME', 'grace-irvine-calendars')
        
        if not spreadsheet_id:
            return {
                'success': False,
                'error': '未配置GOOGLE_SPREADSHEET_ID'
            }, 400
        
        # 获取数据
        extractor = GoogleSheetsExtractor(spreadsheet_id)
        assignments = extractor.parse_ministry_data()
        
        if not assignments:
            return {
                'success': False,
                'error': '未找到事工安排数据'
            }, 400
        
        logger.info(f"📊 获取到 {len(assignments)} 条事工安排")
        
        # 生成日历文件
        coordinator_ics = generate_coordinator_ics(assignments)
        
        if not coordinator_ics:
            return {
                'success': False,
                'error': '生成负责人日历失败'
            }, 500
        
        # 上传到Cloud Storage
        coordinator_url = upload_to_cloud_storage(
            coordinator_ics, 
            'grace_irvine_coordinator.ics', 
            bucket_name
        )
        
        if not coordinator_url:
            return {
                'success': False,
                'error': '上传日历文件失败'
            }, 500
        
        # 返回结果
        result = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'coordinator_calendar': {
                'url': coordinator_url,
                'events': coordinator_ics.count('BEGIN:VEVENT')
            },
            'assignments_processed': len(assignments),
            'message': 'ICS日历更新成功'
        }
        
        logger.info("✅ ICS日历更新完成")
        return result
        
    except Exception as e:
        logger.error(f"❌ 更新ICS日历失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, 500

# 如果直接运行，用于本地测试
if __name__ == "__main__":
    import json
    from flask import Flask, request as flask_request
    
    app = Flask(__name__)
    
    @app.route('/api/update-calendars', methods=['POST', 'GET'])
    def test_update():
        result = update_ics_calendars(flask_request)
        return json.dumps(result[0], indent=2, ensure_ascii=False)
    
    print("🧪 本地测试服务器启动: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
