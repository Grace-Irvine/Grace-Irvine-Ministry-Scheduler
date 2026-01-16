#!/usr/bin/env python3
"""
ICS日历更新Cloud Function
供Cloud Scheduler调用，更新ICS日历文件并上传到Cloud Storage

功能：
1. 从GCS读取清洗后的JSON数据
2. 生成ICS日历文件（周三确认、周六提醒）
3. 上传到Cloud Storage
4. 提供公开URL供用户订阅
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from google.cloud import storage
import functions_framework

# 设置项目路径
sys.path.append(str(Path(__file__).parent.parent))

from src.multi_calendar_generator import generate_all_calendars

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        
        bucket_name = os.getenv('STORAGE_BUCKET_NAME', 'grace-irvine-calendars')
        
        # 生成日历内容（来自GCS清洗JSON）
        results = generate_all_calendars()
        if not results or not results.get('calendars'):
            return {
                'success': False,
                'error': '未生成任何日历内容'
            }, 500
        
        uploaded = {}
        for calendar_type, calendar_result in results['calendars'].items():
            if not calendar_result.get('success') or not calendar_result.get('content'):
                continue
            
            filename = f"{calendar_type}.ics"
            public_url = upload_to_cloud_storage(
                calendar_result['content'],
                filename,
                bucket_name
            )
            if public_url:
                uploaded[calendar_type] = {
                    'url': public_url,
                    'events': calendar_result.get('events', 0)
                }
        
        if not uploaded:
            return {
                'success': False,
                'error': '上传日历文件失败'
            }, 500
        
        result = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'calendars': uploaded,
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
