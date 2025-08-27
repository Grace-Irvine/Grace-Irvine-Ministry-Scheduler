#!/usr/bin/env python3
"""
带ICS端点的Streamlit应用
集成API端点到Streamlit应用中，支持Cloud Scheduler触发

端点：
- /api/update-calendars - Cloud Scheduler触发更新
- /calendars/grace_irvine_coordinator.ics - 负责人日历订阅
- /calendars/grace_irvine_workers.ics - 同工日历订阅
"""

import streamlit as st
import os
import sys
from pathlib import Path
from datetime import datetime, date, timedelta
import json

# 设置项目路径
sys.path.append(str(Path(__file__).parent))

# 检查是否为API请求
query_params = st.experimental_get_query_params()
path_info = os.environ.get('PATH_INFO', '')

def handle_api_request():
    """处理API请求"""
    try:
        if path_info == '/api/update-calendars':
            return handle_update_calendars_api()
        elif path_info == '/api/status':
            return handle_status_api()
        elif path_info.startswith('/calendars/'):
            return handle_calendar_file_request()
        else:
            return None
    except Exception as e:
        st.error(f"API请求处理失败: {e}")
        return None

def handle_update_calendars_api():
    """处理日历更新API请求"""
    try:
        from src.scheduler import GoogleSheetsExtractor
        from src.template_manager import get_default_template_manager
        
        # 获取数据
        spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
        extractor = GoogleSheetsExtractor(spreadsheet_id)
        assignments = extractor.parse_ministry_data()
        template_manager = get_default_template_manager()
        
        # 更新日历文件
        calendar_dir = Path('/tmp/calendars')  # Cloud Run临时目录
        calendar_dir.mkdir(exist_ok=True)
        
        # 生成负责人日历
        coordinator_ics = generate_coordinator_calendar_content(assignments)
        workers_ics = generate_workers_calendar_content(assignments)
        
        # 保存文件
        with open(calendar_dir / 'grace_irvine_coordinator.ics', 'w', encoding='utf-8') as f:
            f.write(coordinator_ics)
        
        with open(calendar_dir / 'grace_irvine_workers.ics', 'w', encoding='utf-8') as f:
            f.write(workers_ics)
        
        # 返回结果
        result = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'coordinator_events': coordinator_ics.count('BEGIN:VEVENT'),
            'workers_events': workers_ics.count('BEGIN:VEVENT'),
            'assignments_count': len(assignments)
        }
        
        st.json(result)
        return True
        
    except Exception as e:
        st.error(f"更新失败: {e}")
        return False

# 如果是API请求，处理API逻辑
if path_info.startswith('/api/') or path_info.startswith('/calendars/'):
    api_result = handle_api_request()
    if api_result:
        st.stop()

# 否则正常运行Streamlit应用
exec(open('streamlit_app.py').read())
