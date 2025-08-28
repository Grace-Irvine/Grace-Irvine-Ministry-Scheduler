#!/usr/bin/env python3
"""
ICS日历API端点
为Cloud Scheduler提供HTTP端点来触发ICS日历更新

端点：
- /api/update-calendars - 更新所有ICS日历文件
- /api/calendar/coordinator - 获取负责人日历
- /api/calendar/workers - 获取同工日历
- /api/status - 获取系统状态
"""

import os
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

from flask import Flask, Response, jsonify, request, send_file
from flask_cors import CORS

# 设置项目路径
import sys
sys.path.append(str(Path(__file__).parent))

from src.scheduler import GoogleSheetsExtractor
from src.template_manager import get_default_template_manager

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 全局变量
sheets_extractor = None
template_manager = None

def initialize_components():
    """初始化组件"""
    global sheets_extractor, template_manager
    
    try:
        # 从环境变量或Cloud Secret Manager获取配置
        spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
        
        if not spreadsheet_id:
            logger.error("❌ 未配置GOOGLE_SPREADSHEET_ID")
            return False
        
        sheets_extractor = GoogleSheetsExtractor(spreadsheet_id)
        template_manager = get_default_template_manager()
        
        logger.info("✅ API组件初始化成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ 初始化组件失败: {e}")
        return False

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
                except Exception as e:
                    logger.error(f"创建周六事件失败: {e}")
        
        ics_lines.append("END:VCALENDAR")
        return "\n".join(ics_lines)
        
    except Exception as e:
        logger.error(f"生成负责人日历失败: {e}")
        return None

@app.route('/api/update-calendars', methods=['POST', 'GET'])
def update_calendars():
    """更新所有ICS日历文件 - 供Cloud Scheduler调用"""
    try:
        logger.info("📅 收到日历更新请求")
        
        if not sheets_extractor or not template_manager:
            return jsonify({
                'success': False,
                'error': '组件未初始化'
            }), 500
        
        # 获取最新数据
        assignments = sheets_extractor.parse_ministry_data()
        
        if not assignments:
            return jsonify({
                'success': False,
                'error': '未找到事工安排数据'
            }), 400
        
        # 确保目录存在
        calendar_dir = Path('/app/calendars')
        calendar_dir.mkdir(exist_ok=True)
        
        # 生成负责人日历
        coordinator_ics = generate_coordinator_ics(assignments)
        if coordinator_ics:
            with open(calendar_dir / 'grace_irvine_coordinator.ics', 'w', encoding='utf-8') as f:
                f.write(coordinator_ics)
            coordinator_events = coordinator_ics.count('BEGIN:VEVENT')
        else:
            coordinator_events = 0
        
        # 生成同工日历（简化版）
        workers_ics = generate_workers_ics(assignments)
        if workers_ics:
            with open(calendar_dir / 'grace_irvine_workers.ics', 'w', encoding='utf-8') as f:
                f.write(workers_ics)
            workers_events = workers_ics.count('BEGIN:VEVENT')
        else:
            workers_events = 0
        
        # 更新时间戳
        with open(calendar_dir / 'last_update.txt', 'w') as f:
            f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        result = {
            'success': True,
            'message': '日历文件更新成功',
            'timestamp': datetime.now().isoformat(),
            'files_updated': {
                'coordinator_calendar': {
                    'filename': 'grace_irvine_coordinator.ics',
                    'events': coordinator_events
                },
                'workers_calendar': {
                    'filename': 'grace_irvine_workers.ics', 
                    'events': workers_events
                }
            },
            'assignments_processed': len(assignments)
        }
        
        logger.info(f"✅ 日历更新完成: {coordinator_events + workers_events} 个事件")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ 更新日历失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/calendars/grace_irvine_coordinator.ics')
def serve_coordinator_calendar():
    """提供负责人日历文件"""
    try:
        calendar_file = Path('/app/calendars/grace_irvine_coordinator.ics')
        
        if not calendar_file.exists():
            # 如果文件不存在，立即生成一个
            logger.info("📅 日历文件不存在，立即生成...")
            update_result = update_calendars()
            if not update_result[0].get_json().get('success', False):
                return "Calendar file not available", 404
        
        return send_file(
            calendar_file,
            as_attachment=True,
            download_name='grace_irvine_coordinator.ics',
            mimetype='text/calendar'
        )
        
    except Exception as e:
        logger.error(f"❌ 提供负责人日历失败: {e}")
        return f"Error serving calendar: {e}", 500

@app.route('/calendars/grace_irvine_workers.ics')
def serve_workers_calendar():
    """提供同工日历文件"""
    try:
        calendar_file = Path('/app/calendars/grace_irvine_workers.ics')
        
        if not calendar_file.exists():
            # 如果文件不存在，立即生成一个
            logger.info("📅 日历文件不存在，立即生成...")
            update_result = update_calendars()
            if not update_result[0].get_json().get('success', False):
                return "Calendar file not available", 404
        
        return send_file(
            calendar_file,
            as_attachment=True,
            download_name='grace_irvine_workers.ics',
            mimetype='text/calendar'
        )
        
    except Exception as e:
        logger.error(f"❌ 提供同工日历失败: {e}")
        return f"Error serving calendar: {e}", 500

@app.route('/api/status')
def get_status():
    """获取系统状态"""
    try:
        calendar_dir = Path('/app/calendars')
        status = {
            'timestamp': datetime.now().isoformat(),
            'components': {
                'sheets_extractor': sheets_extractor is not None,
                'template_manager': template_manager is not None
            },
            'calendar_files': {}
        }
        
        # 检查日历文件状态
        if calendar_dir.exists():
            for ics_file in calendar_dir.glob('*.ics'):
                try:
                    stat = ics_file.stat()
                    with open(ics_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    status['calendar_files'][ics_file.name] = {
                        'size_kb': round(stat.st_size / 1024, 1),
                        'events': content.count('BEGIN:VEVENT'),
                        'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    }
                except Exception as e:
                    status['calendar_files'][ics_file.name] = {
                        'error': str(e)
                    }
        
        # 检查最后更新时间
        timestamp_file = calendar_dir / 'last_update.txt'
        if timestamp_file.exists():
            try:
                with open(timestamp_file, 'r') as f:
                    status['last_calendar_update'] = f.read().strip()
            except:
                pass
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"❌ 获取状态失败: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

def generate_workers_ics(assignments) -> str:
    """生成同工日历ICS内容"""
    try:
        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Grace Irvine Ministry Scheduler//Workers Calendar//CN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:Grace Irvine 同工服事日历",
            "X-WR-CALDESC:同工事工服事安排日历（Cloud Scheduler自动更新）",
            "X-WR-TIMEZONE:America/Los_Angeles",
            f"X-WR-CALDESC:最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        
        today = date.today()
        future_assignments = [a for a in assignments if a.date >= today][:10]
        
        for assignment in future_assignments:
            service_roles = [
                ("音控", assignment.audio_tech, "09:00", "12:00"),
                ("导播/摄影", assignment.camera_operator, "09:30", "12:00"),
                ("ProPresenter播放", assignment.propresenter, "09:00", "12:00")
            ]
            
            for role_name, person_name, start_time, end_time in service_roles:
                if person_name and person_name.strip():
                    try:
                        start_hour, start_minute = map(int, start_time.split(':'))
                        end_hour, end_minute = map(int, end_time.split(':'))
                        
                        event_ics = create_ics_event(
                            uid=f"service_{role_name}_{assignment.date.strftime('%Y%m%d')}_{person_name}@graceirvine.org",
                            summary=f"主日服事 - {role_name}",
                            description=f"角色：{role_name}\n负责人：{person_name}\n到场时间：{start_time}\n\n愿主同在，出入平安！",
                            start_dt=datetime.combine(assignment.date, datetime.min.time().replace(hour=start_hour, minute=start_minute)),
                            end_dt=datetime.combine(assignment.date, datetime.min.time().replace(hour=end_hour, minute=end_minute)),
                            location="Grace Irvine 教会"
                        )
                        ics_lines.append(event_ics)
                    except Exception as e:
                        logger.error(f"创建 {person_name} 服事事件失败: {e}")
        
        ics_lines.append("END:VCALENDAR")
        return "\n".join(ics_lines)
        
    except Exception as e:
        logger.error(f"生成同工日历失败: {e}")
        return None

# 初始化组件
initialize_components()

if __name__ == '__main__':
    # 开发环境运行
    app.run(host='0.0.0.0', port=5000, debug=True)
