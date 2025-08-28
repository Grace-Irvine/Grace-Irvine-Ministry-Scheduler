#!/usr/bin/env python3
"""
简化的ICS后台服务
在Cloud Run中提供ICS文件生成和服务功能
"""

import os
import sys
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from flask import Flask, jsonify, Response

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.scheduler import GoogleSheetsExtractor
from src.template_manager import get_default_template_manager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/health')
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'service': 'ICS Background Service',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/update-calendars', methods=['POST'])
def update_calendars():
    """更新ICS日历文件"""
    try:
        logger.info("📅 开始更新ICS日历...")
        
        # 获取数据
        spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
        extractor = GoogleSheetsExtractor(spreadsheet_id)
        assignments = extractor.parse_ministry_data()
        template_manager = get_default_template_manager()
        
        if not assignments:
            return jsonify({
                'success': False,
                'error': '未找到事工安排数据'
            }), 400
        
        # 生成ICS内容
        coordinator_ics = generate_simple_coordinator_ics(assignments, template_manager)
        
        # 保存到本地
        calendar_dir = Path('/app/calendars')
        calendar_dir.mkdir(exist_ok=True)
        
        with open(calendar_dir / 'grace_irvine_coordinator.ics', 'w', encoding='utf-8') as f:
            f.write(coordinator_ics)
        
        # 保存时间戳
        with open(calendar_dir / 'last_update.txt', 'w') as f:
            f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        result = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'events_created': coordinator_ics.count('BEGIN:VEVENT'),
            'assignments_processed': len(assignments)
        }
        
        logger.info("✅ ICS日历更新完成")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ 更新失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/calendars/<filename>')
def serve_calendar(filename):
    """提供ICS文件下载"""
    try:
        calendar_dir = Path('/app/calendars')
        file_path = calendar_dir / filename
        
        if not file_path.exists():
            return f"File {filename} not found", 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return Response(
            content,
            mimetype='text/calendar',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Cache-Control': 'public, max-age=3600'
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 服务文件失败: {e}")
        return f"Error: {e}", 500

def generate_simple_coordinator_ics(assignments, template_manager) -> str:
    """生成简化的负责人日历"""
    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Grace Irvine Ministry Scheduler//Coordinator Calendar//CN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Grace Irvine 事工协调日历",
        "X-WR-CALDESC:事工通知发送提醒日历",
        "X-WR-TIMEZONE:America/Los_Angeles"
    ]
    
    today = date.today()
    future_assignments = [a for a in assignments if a.date >= today][:8]
    
    for assignment in future_assignments:
        # 周三确认通知
        wednesday = assignment.date - timedelta(days=4)
        if wednesday >= today - timedelta(days=7):
            try:
                content = template_manager.render_weekly_confirmation(assignment)
                event = f"""BEGIN:VEVENT
UID:weekly_{wednesday.strftime('%Y%m%d')}@graceirvine.org
SUMMARY:发送周末确认通知 ({assignment.date.month}/{assignment.date.day})
DESCRIPTION:{content.replace(chr(10), '\\n')}
DTSTART:{wednesday.strftime('%Y%m%d')}T200000
DTEND:{wednesday.strftime('%Y%m%d')}T203000
LOCATION:Grace Irvine 教会
END:VEVENT"""
                ics_lines.append(event)
            except:
                pass
        
        # 周六提醒通知
        saturday = assignment.date - timedelta(days=1)
        if saturday >= today - timedelta(days=7):
            try:
                content = template_manager.render_sunday_reminder(assignment)
                event = f"""BEGIN:VEVENT
UID:sunday_{saturday.strftime('%Y%m%d')}@graceirvine.org
SUMMARY:发送主日提醒通知 ({assignment.date.month}/{assignment.date.day})
DESCRIPTION:{content.replace(chr(10), '\\n')}
DTSTART:{saturday.strftime('%Y%m%d')}T200000
DTEND:{saturday.strftime('%Y%m%d')}T203000
LOCATION:Grace Irvine 教会
END:VEVENT"""
                ics_lines.append(event)
            except:
                pass
    
    ics_lines.append("END:VCALENDAR")
    return "\n".join(ics_lines)

if __name__ == '__main__':
    logger.info("🚀 启动简化ICS后台服务")
    
    # 初始化组件
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
        if spreadsheet_id:
            logger.info("✅ 环境配置正常")
        else:
            logger.warning("⚠️ 未设置GOOGLE_SPREADSHEET_ID")
    except:
        pass
    
    # 启动Flask应用
    app.run(host='0.0.0.0', port=5000, debug=False)
