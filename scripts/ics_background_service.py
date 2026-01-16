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
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from flask import Flask, jsonify, Response
from google.cloud import storage

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.multi_calendar_generator import generate_all_calendars

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)

# 全局变量
data_source_ready = False
last_update_time = None
is_running = True

def initialize_components():
    """初始化组件"""
    global data_source_ready
    
    try:
        # 使用GCS清洗后的JSON数据作为数据源
        data_source_ready = True
        logger.info("✅ 后台服务组件初始化成功（GCS JSON 数据源）")
        return True
        
    except Exception as e:
        logger.error(f"❌ 初始化组件失败: {e}")
        return False

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
        
        if not data_source_ready:
            logger.error("❌ 组件未初始化")
            return {'success': False, 'error': '组件未初始化'}
        
        results = generate_all_calendars()
        if not results or not results.get('calendars'):
            logger.warning("⚠️ 未生成任何日历内容")
            return {'success': False, 'error': '未生成任何日历内容'}
        
        results = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'files_updated': []
        }
        
        for calendar_type, calendar_result in results['calendars'].items():
            if not calendar_result.get('success') or not calendar_result.get('content'):
                continue
            
            filename = f"{calendar_type}.ics"
            content = calendar_result['content']
            if upload_to_cloud_storage(content, filename):
                results['files_updated'].append({
                    'name': filename,
                    'events': calendar_result.get('events', 0),
                    'type': calendar_type
                })
            save_local_backup(content, filename)
        
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
                'data_source_ready': data_source_ready
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
