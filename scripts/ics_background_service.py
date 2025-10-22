#!/usr/bin/env python3
"""
ICS后台更新服务
在Cloud Run中运行的后台服务，负责：
1. 定期更新ICS日历文件
2. 提供HTTP API端点供Cloud Scheduler调用
3. 将ICS文件上传到Cloud Storage供用户订阅
4. 监控系统状态
"""

import os
import sys
import logging
import threading
import time
import signal
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from flask import Flask, jsonify, Response, request
from google.cloud import storage

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.scheduler import GoogleSheetsExtractor
from src.template_manager import get_default_template_manager

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)

# 全局变量
sheets_extractor = None
template_manager = None
last_update_time = None
is_running = True

def initialize_components():
    """初始化组件"""
    global sheets_extractor, template_manager
    
    try:
        spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
        
        if not spreadsheet_id:
            logger.error("❌ 未配置GOOGLE_SPREADSHEET_ID")
            return False
        
        sheets_extractor = GoogleSheetsExtractor(spreadsheet_id)
        template_manager = get_default_template_manager()
        
        logger.info("✅ 后台服务组件初始化成功")
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
                    start_dt: datetime, end_dt: datetime, location: str = "Grace Irvine 教会") -> str:
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
            "X-WR-CALDESC:事工通知发送提醒日历（Cloud Run自动更新）",
            "X-WR-TIMEZONE:America/Los_Angeles",
            f"X-WR-CALDESC:最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        
        today = date.today()
        # 保留过去4周的事件，避免每次更新时删除历史记录
        cutoff_date = today - timedelta(days=28)  # 4周前
        # 包含过去4周到未来15周的事件
        relevant_assignments = [a for a in assignments if a.date >= cutoff_date][:19]  # 4周过去 + 15周未来
        
        events_created = 0
        
        for assignment in relevant_assignments:
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
                        end_dt=datetime.combine(wednesday, datetime.min.time().replace(hour=20, minute=30))
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
                        end_dt=datetime.combine(saturday, datetime.min.time().replace(hour=20, minute=30))
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
            "X-WR-CALDESC:同工事工服事安排日历（Cloud Run自动更新）",
            "X-WR-TIMEZONE:America/Los_Angeles",
            f"X-WR-CALDESC:最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        
        today = date.today()
        future_assignments = [a for a in assignments if a.date >= today][:10]
        
        events_created = 0
        
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
                            end_dt=datetime.combine(assignment.date, datetime.min.time().replace(hour=end_hour, minute=end_minute))
                        )
                        ics_lines.append(event_ics)
                        events_created += 1
                    except Exception as e:
                        logger.error(f"创建 {person_name} 服事事件失败: {e}")
        
        ics_lines.append("END:VCALENDAR")
        
        logger.info(f"✅ 同工日历生成完成: {events_created} 个事件")
        return "\n".join(ics_lines)
        
    except Exception as e:
        logger.error(f"生成同工日历失败: {e}")
        return None

def upload_to_cloud_storage(content: str, filename: str) -> bool:
    """上传ICS文件到Cloud Storage"""
    try:
        bucket_name = os.getenv('ICS_STORAGE_BUCKET', 'grace-irvine-calendars')
        
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(filename)
        
        # 上传内容
        blob.upload_from_string(
            content,
            content_type='text/calendar; charset=utf-8'
        )
        
        # 设置公开访问和缓存头
        blob.make_public()
        blob.cache_control = 'public, max-age=3600'  # 1小时缓存
        blob.patch()
        
        public_url = blob.public_url
        logger.info(f"✅ 文件已上传: {public_url}")
        
        return True
        
    except Exception as e:
        logger.error(f"上传到Cloud Storage失败: {e}")
        return False

def save_local_backup(content: str, filename: str) -> bool:
    """保存本地备份文件"""
    try:
        calendar_dir = Path('/app/calendars')
        calendar_dir.mkdir(exist_ok=True)
        
        with open(calendar_dir / filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"✅ 本地备份已保存: {filename}")
        return True
        
    except Exception as e:
        logger.error(f"保存本地备份失败: {e}")
        return False

def update_all_calendars() -> Dict[str, Any]:
    """更新所有ICS日历文件"""
    global last_update_time
    
    try:
        logger.info("🔄 开始更新ICS日历文件...")
        
        if not sheets_extractor or not template_manager:
            logger.error("❌ 组件未初始化")
            return {'success': False, 'error': '组件未初始化'}
        
        # 获取最新数据
        assignments = sheets_extractor.parse_ministry_data()
        
        if not assignments:
            logger.warning("⚠️ 未找到事工安排数据")
            return {'success': False, 'error': '未找到事工安排数据'}
        
        logger.info(f"📊 获取到 {len(assignments)} 条事工安排")
        
        results = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'assignments_count': len(assignments),
            'files_updated': []
        }
        
        # 生成负责人日历
        coordinator_ics = generate_coordinator_ics(assignments)
        if coordinator_ics:
            # 上传到Cloud Storage
            if upload_to_cloud_storage(coordinator_ics, 'grace_irvine_coordinator.ics'):
                results['files_updated'].append({
                    'name': 'grace_irvine_coordinator.ics',
                    'events': coordinator_ics.count('BEGIN:VEVENT'),
                    'type': '负责人日历'
                })
            
            # 保存本地备份
            save_local_backup(coordinator_ics, 'grace_irvine_coordinator.ics')
        
        # 生成同工日历
        workers_ics = generate_workers_ics(assignments)
        if workers_ics:
            # 上传到Cloud Storage
            if upload_to_cloud_storage(workers_ics, 'grace_irvine_workers.ics'):
                results['files_updated'].append({
                    'name': 'grace_irvine_workers.ics',
                    'events': workers_ics.count('BEGIN:VEVENT'),
                    'type': '同工日历'
                })
            
            # 保存本地备份
            save_local_backup(workers_ics, 'grace_irvine_workers.ics')
        
        # 更新时间戳
        last_update_time = datetime.now()
        
        # 保存更新时间到文件
        timestamp_file = Path('/app/calendars/last_update.txt')
        timestamp_file.parent.mkdir(exist_ok=True)
        with open(timestamp_file, 'w') as f:
            f.write(last_update_time.strftime('%Y-%m-%d %H:%M:%S'))
        
        logger.info(f"✅ ICS日历更新完成: {len(results['files_updated'])} 个文件")
        return results
        
    except Exception as e:
        logger.error(f"❌ 更新ICS日历失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

# API端点
@app.route('/api/update-calendars', methods=['POST', 'GET'])
def api_update_calendars():
    """API端点：更新日历文件"""
    try:
        logger.info("📡 收到日历更新API请求")
        result = update_all_calendars()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"❌ API请求处理失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/status')
def api_status():
    """API端点：获取系统状态"""
    try:
        status = {
            'service': 'ICS Background Service',
            'status': 'running' if is_running else 'stopped',
            'last_update': last_update_time.isoformat() if last_update_time else None,
            'components': {
                'sheets_extractor': sheets_extractor is not None,
                'template_manager': template_manager is not None
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # 检查本地文件状态
        calendar_dir = Path('/app/calendars')
        if calendar_dir.exists():
            status['local_files'] = {}
            for ics_file in calendar_dir.glob('*.ics'):
                try:
                    stat = ics_file.stat()
                    with open(ics_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    status['local_files'][ics_file.name] = {
                        'size_kb': round(stat.st_size / 1024, 1),
                        'events': content.count('BEGIN:VEVENT'),
                        'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    }
                except Exception as e:
                    status['local_files'][ics_file.name] = {'error': str(e)}
        
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"❌ 获取状态失败: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/calendars/<filename>')
def serve_calendar_file(filename):
    """提供ICS文件下载"""
    try:
        calendar_dir = Path('/app/calendars')
        file_path = calendar_dir / filename
        
        if not file_path.exists():
            # 如果文件不存在，尝试生成
            logger.info(f"📅 文件不存在，尝试生成: {filename}")
            update_all_calendars()
            
            if not file_path.exists():
                return f"Calendar file {filename} not found", 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        response = Response(
            content,
            mimetype='text/calendar',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Cache-Control': 'public, max-age=3600'  # 1小时缓存
            }
        )
        
        logger.info(f"📥 提供日历文件: {filename}")
        return response
        
    except Exception as e:
        logger.error(f"❌ 提供日历文件失败: {e}")
        return f"Error serving calendar file: {e}", 500

@app.route('/health')
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'healthy',
        'service': 'ICS Background Service',
        'timestamp': datetime.now().isoformat()
    })

def background_update_loop():
    """后台更新循环"""
    global is_running
    
    logger.info("🔄 启动后台ICS更新循环")
    
    # 立即执行一次更新
    update_all_calendars()
    
    while is_running:
        try:
            # 每30分钟更新一次
            time.sleep(1800)  # 30分钟 = 1800秒
            
            if is_running:
                logger.info("⏰ 定时更新ICS日历...")
                update_all_calendars()
                
        except Exception as e:
            logger.error(f"❌ 后台更新循环出错: {e}")
            time.sleep(300)  # 出错后等待5分钟再重试

def signal_handler(signum, frame):
    """信号处理器"""
    global is_running
    logger.info("🛑 收到停止信号，正在关闭后台服务...")
    is_running = False

def main():
    """主函数"""
    global is_running
    
    logger.info("🚀 启动ICS后台更新服务")
    
    # 注册信号处理器
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # 初始化组件
    if not initialize_components():
        logger.error("❌ 组件初始化失败，退出")
        sys.exit(1)
    
    # 启动后台更新线程
    update_thread = threading.Thread(target=background_update_loop, daemon=True)
    update_thread.start()
    
    # 启动Flask API服务
    logger.info("🔗 启动API服务 (端口 5000)")
    logger.info("📋 可用端点:")
    logger.info("  POST /api/update-calendars - 更新日历文件")
    logger.info("  GET /api/status - 获取系统状态")
    logger.info("  GET /calendars/<filename> - 下载ICS文件")
    logger.info("  GET /health - 健康检查")
    
    try:
        # 在生产环境中运行
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except Exception as e:
        logger.error(f"❌ API服务启动失败: {e}")
        is_running = False

if __name__ == "__main__":
    main()
