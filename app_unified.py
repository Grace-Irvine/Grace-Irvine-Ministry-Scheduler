#!/usr/bin/env python3
"""
Grace Irvine Ministry Scheduler - 统一应用
恩典尔湾长老教会事工排程管理系统 - 简化架构版本

这是项目的唯一入口点，集成了所有功能：
1. Streamlit Web界面
2. 静态文件服务（ICS日历）
3. 数据处理和通知生成
4. 邮件发送功能
"""

import streamlit as st
import pandas as pd
import os
import sys
import threading
import time
import subprocess
from datetime import datetime, date, timedelta
from pathlib import Path
import json
import io
import logging
from typing import List, Dict, Tuple

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 导入项目模块
from src.models import MinistryAssignment, ServiceRole  # 统一数据模型
from src.data_cleaner import FocusedDataCleaner
from src.template_manager import NotificationTemplateManager
from src.dynamic_template_manager import DynamicTemplateManager
from src.scheduler import GoogleSheetsExtractor, NotificationGenerator
from src.email_sender import EmailSender, EmailRecipient
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== 静态文件服务功能 ====================

# API endpoints for automatic updates
import uvicorn
from fastapi import FastAPI, Response, HTTPException, Header
from fastapi.responses import FileResponse, JSONResponse
import asyncio

# Create FastAPI app for API endpoints
api_app = FastAPI(title="Grace Irvine Ministry Scheduler API", version="2.0")

class StaticFileServer:
    """内置的静态文件服务器，用于提供ICS日历文件"""
    
    @staticmethod
    def serve_calendar_file(filename: str):
        """提供ICS日历文件内容（支持云端存储）"""
        try:
            if not filename.endswith('.ics'):
                return None, "Only ICS files are allowed"
            
            # 使用云端存储管理器读取
            from src.cloud_storage_manager import get_storage_manager
            storage_manager = get_storage_manager()
            
            content = storage_manager.read_ics_calendar(filename)
            
            if content:
                return content, None
            else:
                return None, f"Calendar file {filename} not found"
            
        except Exception as e:
            return None, f"Error serving calendar file: {str(e)}"
    
    @staticmethod
    def get_calendar_status():
        """获取日历文件状态（支持云端存储）"""
        try:
            from src.cloud_storage_manager import get_storage_manager
            storage_manager = get_storage_manager()
            
            # 获取存储状态
            storage_status = storage_manager.get_storage_status()
            
            status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'service': 'Grace Irvine Ministry Scheduler',
                'storage_mode': storage_status['mode'],
                'calendars': {}
            }
            
            # 检查日历文件
            calendar_files = ['grace_irvine_coordinator.ics']
            
            for filename in calendar_files:
                file_status = storage_manager.get_file_status(f"calendars/{filename}")
                
                # 读取文件内容进行分析
                content = storage_manager.read_ics_calendar(filename)
                
                if content:
                    status['calendars'][filename] = {
                        'size': f"{len(content.encode('utf-8')) / 1024:.1f} KB",
                        'events': content.count("BEGIN:VEVENT"),
                        'local_exists': file_status['local_exists'],
                        'cloud_exists': file_status['cloud_exists'],
                        'last_modified': file_status.get('local_modified') or file_status.get('cloud_modified'),
                        'valid_ics': content.startswith('BEGIN:VCALENDAR') and content.endswith('END:VCALENDAR'),
                        'sync_needed': file_status.get('sync_needed', False)
                    }
                else:
                    status['calendars'][filename] = {
                        'error': 'File not found in any storage location'
                    }
            
            return status
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

# ==================== API端点功能 ====================

@api_app.get("/api/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@api_app.get("/api/status")
async def get_api_status():
    """获取系统状态"""
    status = StaticFileServer.get_calendar_status()
    return JSONResponse(content=status)

@api_app.get("/api/ics/{filename}")
async def get_ics_file_content(filename: str):
    """获取ICS文件内容"""
    try:
        content, error = StaticFileServer.serve_calendar_file(filename)
        if error:
            raise HTTPException(status_code=404, detail=error)
        
        return Response(
            content=content,
            media_type="text/calendar; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache, no-store, must-revalidate"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving ICS file: {str(e)}")

@api_app.get("/api/ics/{filename}/events")
async def get_ics_events(filename: str):
    """获取ICS文件中的事件列表（解析后的JSON格式）"""
    try:
        content, error = StaticFileServer.serve_calendar_file(filename)
        if error:
            raise HTTPException(status_code=404, detail=error)
        
        # 解析ICS文件中的事件
        events = parse_ics_events(content)
        
        return JSONResponse(content={
            "filename": filename,
            "events_count": len(events),
            "events": events,
            "last_updated": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing ICS events: {str(e)}")

@api_app.get("/api/ics/{filename}/event/{event_uid}")
async def get_ics_event_detail(filename: str, event_uid: str):
    """获取特定事件的详细信息"""
    try:
        content, error = StaticFileServer.serve_calendar_file(filename)
        if error:
            raise HTTPException(status_code=404, detail=error)
        
        # 解析ICS文件中的事件
        events = parse_ics_events(content)
        
        # 查找特定的事件
        target_event = None
        for event in events:
            if event.get('uid') == event_uid:
                target_event = event
                break
        
        if not target_event:
            raise HTTPException(status_code=404, detail=f"Event with UID {event_uid} not found")
        
        return JSONResponse(content={
            "filename": filename,
            "event": target_event,
            "retrieved_at": datetime.now().isoformat()
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving event detail: {str(e)}")

@api_app.post("/api/update-ics")
async def trigger_ics_update(auth_token: str = Header(None, alias="X-Auth-Token")):
    """
    触发ICS文件更新
    需要认证令牌（用于Cloud Scheduler）
    """
    # 验证认证令牌
    expected_token = os.getenv("SCHEDULER_AUTH_TOKEN", "grace-irvine-scheduler-2025")
    if auth_token != expected_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        logger.info("Starting automatic ICS update from API endpoint")
        
        # 执行自动更新流程
        result = await automatic_ics_update()
        
        if result["success"]:
            return JSONResponse(
                content={
                    "status": "success",
                    "message": result["message"],
                    "details": result.get("details", {}),
                    "timestamp": datetime.now().isoformat()
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": result["message"],
                    "timestamp": datetime.now().isoformat()
                }
            )
    except Exception as e:
        logger.error(f"Error in API update endpoint: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

async def automatic_ics_update():
    """
    自动更新ICS文件的核心函数
    1. 从Google Sheets读取最新数据
    2. 从Bucket读取最新模板
    3. 生成新的ICS文件
    4. 上传到Bucket
    """
    try:
        # 1. 从Google Sheets读取最新数据
        logger.info("Step 1: Loading data from Google Sheets")
        cleaner = FocusedDataCleaner()
        raw_df = cleaner.download_data()
        focused_df = cleaner.extract_focused_columns(raw_df)
        schedules = cleaner.clean_focused_data(focused_df)
        
        if not schedules:
            return {
                "success": False,
                "message": "No schedule data found in Google Sheets"
            }
        
        # 2. 从Bucket读取最新模板
        logger.info("Step 2: Loading templates from cloud storage")
        from src.cloud_storage_manager import get_storage_manager
        storage_manager = get_storage_manager()
        
        # 确保使用最新的云端模板
        template_content = storage_manager.read_file("templates/dynamic_templates.json", "json")
        if template_content:
            # 更新本地模板缓存
            local_template_path = Path("templates/dynamic_templates.json")
            with open(local_template_path, 'w', encoding='utf-8') as f:
                json.dump(template_content, f, ensure_ascii=False, indent=2)
        
        # 3. 生成新的ICS文件
        logger.info("Step 3: Generating ICS calendar files")
        from src.calendar_generator import generate_coordinator_calendar
        
        # 生成日历
        success = generate_coordinator_calendar()
        
        if not success:
            return {
                "success": False,
                "message": "Failed to generate ICS calendar"
            }
        
        # 4. 确保上传到Bucket
        logger.info("Step 4: Uploading to cloud storage")
        calendar_path = Path("calendars/grace_irvine_coordinator.ics")
        
        if calendar_path.exists():
            # 读取生成的文件
            with open(calendar_path, 'r', encoding='utf-8') as f:
                ics_content = f.read()
            
            # 上传到云端
            upload_success = storage_manager.write_ics_calendar(
                ics_content, 
                "grace_irvine_coordinator.ics"
            )
            
            if upload_success:
                # 获取公开URL
                public_url = storage_manager.get_public_calendar_url("grace_irvine_coordinator.ics")
                
                return {
                    "success": True,
                    "message": "ICS calendar updated successfully",
                    "details": {
                        "events_count": ics_content.count("BEGIN:VEVENT"),
                        "file_size": f"{len(ics_content.encode('utf-8')) / 1024:.1f} KB",
                        "public_url": public_url,
                        "update_time": datetime.now().isoformat()
                    }
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to upload ICS to cloud storage"
                }
        else:
            return {
                "success": False,
                "message": "ICS file not found after generation"
            }
            
    except Exception as e:
        logger.error(f"Error in automatic ICS update: {e}")
        return {
            "success": False,
            "message": f"Update failed: {str(e)}"
        }

# ==================== 应用配置 ====================

st.set_page_config(
    page_title="Grace Irvine Ministry Scheduler",
    page_icon="⛪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CSS样式 ====================

def load_css():
    """加载自定义CSS样式"""
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        color: #1f4e79;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 2rem;
    }
    
    .section-header {
        color: #2c5aa0;
        font-size: 1.5rem;
        font-weight: bold;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #e6f2ff;
        padding-bottom: 0.5rem;
    }
    
    .success-message {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .warning-message {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .info-box {
        background-color: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 1rem;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

# ==================== 核心功能函数 ====================

@st.cache_data(ttl=300)  # 缓存5分钟
def load_ministry_data():
    """加载和清洗事工数据"""
    try:
        cleaner = FocusedDataCleaner()
        
        # 下载和处理数据
        raw_df = cleaner.download_data()
        focused_df = cleaner.extract_focused_columns(raw_df)
        schedules = cleaner.clean_focused_data(focused_df)
        
        # 生成汇总报告
        summary_report = cleaner.generate_summary_report(schedules)
        
        return {
            'success': True,
            'schedules': schedules,
            'summary_report': summary_report,
            'stats': cleaner.stats,
            'raw_data': raw_df,
            'focused_data': focused_df
        }
    except Exception as e:
        logger.error(f"加载数据失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'schedules': [],
            'summary_report': {},
            'stats': {}
        }

def generate_calendar_files():
    """生成ICS日历文件"""
    try:
        # 检查是否在云端环境（通过K_SERVICE环境变量判断）
        is_cloud_run = os.getenv("K_SERVICE") is not None or os.getenv("STORAGE_MODE") == "cloud"
        
        if is_cloud_run:
            return call_api_update()
        else:
            # 本地环境，直接调用本地函数
            return call_local_update()
            
    except Exception as e:
        return False, f"生成异常: {str(e)}"

def call_api_update():
    """调用API服务进行更新"""
    try:
        import requests
        
        # 获取API服务URL
        api_url = os.getenv("API_SERVICE_URL", "https://grace-irvine-api-760303847302.us-central1.run.app")
        auth_token = os.getenv("SCHEDULER_AUTH_TOKEN", "grace-irvine-scheduler-2025")
        
        headers = {"X-Auth-Token": auth_token}
        response = requests.post(f"{api_url}/api/update-ics", headers=headers, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            details = result.get("details", {})
            files_count = details.get("files_count", "N/A")
            return True, f"日历文件更新成功 (上传文件: {files_count})"
        else:
            return False, f"API调用失败: HTTP {response.status_code}"
            
    except Exception as e:
        return False, f"API调用异常: {str(e)}"

def call_local_update():
    """本地更新（用于开发环境）"""
    try:
        # 运行日历生成脚本
        result = subprocess.run([
            sys.executable, '-m', 'src.calendar_generator'
        ], capture_output=True, text=True, timeout=60, cwd=PROJECT_ROOT)
        
        if result.returncode == 0:
            return True, "日历文件生成成功"
        else:
            return False, f"生成失败: {result.stderr}"
            
    except Exception as e:
        return False, f"生成异常: {str(e)}"

# ==================== UI组件 ====================

def show_header():
    """显示页面头部"""
    st.markdown("""
    <div class="main-header">
        ⛪ Grace Irvine Ministry Scheduler
        <br><small style="font-size: 1rem; color: #666;">恩典尔湾长老教会事工排程管理系统</small>
    </div>
    """, unsafe_allow_html=True)

def show_data_overview(data_result):
    """显示数据概览"""
    st.markdown('<div class="section-header">📊 数据概览</div>', unsafe_allow_html=True)
    
    if not data_result['success']:
        st.error(f"❌ 数据加载失败: {data_result['error']}")
        return
    
    stats = data_result['stats']
    summary = data_result['summary_report']
    schedules = data_result['schedules']
    
    # 显示统计信息
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📋 总行数", stats.get('total_rows', 0))
    with col2:
        st.metric("✅ 有效排程", stats.get('valid_rows', 0))
    with col3:
        st.metric("👥 志愿者总数", summary.get('volunteer_statistics', {}).get('total_volunteers', 0))
    with col4:
        st.metric("🧹 清洗人名", stats.get('cleaned_names', 0))
    
    # 显示近期排程
    if schedules:
        st.markdown("### 📅 近期排程")
        
        # 获取未来4周的数据
        today = date.today()
        future_schedules = [s for s in schedules if s.date >= today][:8]
        
        if future_schedules:
            schedule_data = []
            for schedule in future_schedules:
                assignments = schedule.get_all_assignments()
                schedule_data.append({
                    '日期': schedule.date.strftime('%Y-%m-%d'),
                    '星期': ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][schedule.date.weekday()],
                    '音控': assignments.get('音控', ''),
                    '导播/摄影': assignments.get('导播/摄影', ''),
                    'ProPresenter播放': assignments.get('ProPresenter播放', ''),
                    'ProPresenter更新': assignments.get('ProPresenter更新', '')
                })
            
            df_schedule = pd.DataFrame(schedule_data)
            st.dataframe(df_schedule, use_container_width=True)

def show_template_generator(data_result):
    """显示模板生成器"""
    st.markdown('<div class="section-header">📝 通知模板生成器</div>', unsafe_allow_html=True)
    
    if not data_result['success']:
        st.info("请先成功加载数据")
        return
    
    schedules = data_result['schedules']
    
    # 模板类型选择
    template_type = st.selectbox(
        "选择通知模板类型",
        ["周三确认通知", "周六提醒通知", "月度总览通知"]
    )
    
    # 获取下周日期
    today = date.today()
    days_until_sunday = (6 - today.weekday()) % 7
    if days_until_sunday == 0:
        days_until_sunday = 7
    next_sunday = today + timedelta(days=days_until_sunday)
    
    # 查找对应的排程
    next_week_schedule = None
    for schedule in schedules:
        if schedule.date == next_sunday:
            next_week_schedule = schedule
            break
    
    if template_type in ["周三确认通知", "周六提醒通知"] and not next_week_schedule:
        st.warning(f"未找到 {next_sunday.strftime('%Y年%m月%d日')} 的排程数据")
        return
    
    # 生成模板内容
    template_content = ""
    
    if template_type == "周三确认通知":
        template_content = generate_wednesday_template(next_sunday, next_week_schedule)
    elif template_type == "周六提醒通知":
        template_content = generate_saturday_template(next_sunday, next_week_schedule)
    else:  # 月度总览
        template_content = generate_monthly_template(schedules)
    
    # 显示生成的模板
    st.markdown("### 📋 生成的通知模板")
    st.text_area(
        "复制以下内容到微信群:",
        value=template_content,
        height=300,
        key="template_output"
    )
    
    # 操作按钮
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 保存模板到文件", use_container_width=True):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"notification_template_{timestamp}.txt"
            filepath = PROJECT_ROOT / "data" / filename
            
            filepath.parent.mkdir(exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            st.success(f"✅ 模板已保存到: {filepath}")
    
    with col2:
        if st.button("📧 发送到邮箱", type="primary", use_container_width=True):
            send_template_email(template_content, template_type)

def show_calendar_management():
    """显示ICS日历管理"""
    st.markdown('<div class="section-header">📅 ICS日历管理</div>', unsafe_allow_html=True)
    
    # 显示当前状态
    status = StaticFileServer.get_calendar_status()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 日历状态")
        if status['status'] == 'healthy':
            st.success("✅ 服务正常")
        else:
            st.error(f"❌ 服务异常: {status.get('error', '未知错误')}")
        
        # 显示文件信息
        calendars = status.get('calendars', {})
        if calendars:
            for filename, info in calendars.items():
                if 'error' in info:
                    st.error(f"❌ {filename}: {info['error']}")
                else:
                    st.info(f"📄 {filename}: {info['events']} 个事件, {info['size']}")
    
    with col2:
        st.markdown("#### 🔧 操作")
        
        if st.button("🔄 生成/更新日历文件", use_container_width=True):
            with st.spinner("正在生成日历文件..."):
                success, message = generate_calendar_files()
                if success:
                    st.success(f"✅ {message}")
                    st.rerun()  # 刷新页面显示最新状态
                else:
                    st.error(f"❌ {message}")
        
        if st.button("📋 显示订阅信息", use_container_width=True):
            show_subscription_info()
        
        if st.button("🔍 查看ICS事件内容", use_container_width=True):
            show_ics_events_content_enhanced()
        
        if st.button("☁️ 推送到云端Bucket", type="primary", use_container_width=True):
            upload_ics_to_bucket()

def show_subscription_info():
    """显示订阅信息"""
    st.markdown("### 🔗 日历订阅信息")
    
    try:
        # 获取云存储管理器
        from src.cloud_storage_manager import get_storage_manager
        storage_manager = get_storage_manager()
        
        # 根据存储模式显示不同的订阅URL
        if storage_manager.is_cloud_mode and storage_manager.storage_client:
            # 云端模式 - 使用GCS公开URL
            st.success("☁️ 云端模式 - 推荐使用云端订阅链接")
            coordinator_url = storage_manager.get_public_calendar_url("grace_irvine_coordinator.ics")
            st.code(f"负责人日历（云端）: {coordinator_url}")
            
            # 显示bucket信息
            st.info(f"📂 存储位置: gs://{storage_manager.config.bucket_name}/calendars/")
            
        else:
            # 本地模式
            st.info("💻 本地模式 - 使用应用服务器链接")
            base_url = "http://localhost:8501"
            if 'K_SERVICE' in os.environ:
                base_url = os.getenv('CLOUD_RUN_URL', 'https://your-service-url.run.app')
            
            coordinator_url = f"{base_url}/calendars/grace_irvine_coordinator.ics"
            st.code(f"负责人日历（本地）: {coordinator_url}")
            
            st.warning("💡 提示：推送到云端Bucket后可获得更稳定的订阅链接")
        
        st.info("📝 同工日历功能留到下阶段开发")
        
        st.markdown("""
        **📱 订阅方法:**
        1. **Google Calendar**: 左侧"+" → "从URL添加" → 粘贴链接
        2. **Apple Calendar**: "文件" → "新建日历订阅" → 输入URL  
        3. **Outlook**: "添加日历" → "从Internet订阅" → 输入URL
        
        ⚠️ **重要**: 请使用"订阅URL"而不是"导入文件"，这样才能自动更新
        
        **☁️ 云端订阅优势:**
        - 🔄 自动同步更新
        - 🌐 全球CDN加速
        - 📱 移动设备友好
        - 🔒 稳定可靠访问
        """)
        
    except Exception as e:
        st.error(f"❌ 获取订阅信息失败: {str(e)}")
        st.markdown("请检查云存储配置或联系管理员")

def upload_ics_to_bucket():
    """上传ICS文件到云端Bucket"""
    st.markdown("### ☁️ 推送ICS到云端Bucket")
    
    try:
        # 获取云存储管理器
        from src.cloud_storage_manager import get_storage_manager
        storage_manager = get_storage_manager()
        
        # 检查是否支持云端上传
        if not storage_manager.is_cloud_mode or not storage_manager.storage_client:
            st.warning("⚠️ 云端存储不可用，请检查以下配置：")
            st.code("""
环境变量配置：
export GCP_STORAGE_BUCKET=grace-irvine-ministry-scheduler
export GOOGLE_CLOUD_PROJECT=ai-for-god
export STORAGE_MODE=cloud
            """)
            return
        
        # 显示当前bucket信息
        st.info(f"🗂️ 目标Bucket: `gs://{storage_manager.config.bucket_name}`")
        
        # 获取本地ICS文件列表
        calendar_dir = Path("calendars")
        if not calendar_dir.exists():
            st.error("📁 本地日历目录不存在，请先生成日历文件")
            return
        
        ics_files = list(calendar_dir.glob("*.ics"))
        if not ics_files:
            st.warning("📄 未找到ICS文件，请先生成日历文件")
            return
        
        # 显示可上传的文件
        st.markdown("#### 📋 可上传的ICS文件")
        upload_results = {}
        
        with st.spinner("正在推送ICS文件到云端..."):
            for ics_file in ics_files:
                try:
                    # 读取文件内容
                    with open(ics_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 上传到bucket
                    success = storage_manager.write_ics_calendar(content, ics_file.name)
                    upload_results[ics_file.name] = success
                    
                    if success:
                        st.success(f"✅ {ics_file.name} 上传成功")
                    else:
                        st.error(f"❌ {ics_file.name} 上传失败")
                        
                except Exception as e:
                    st.error(f"❌ {ics_file.name} 上传异常: {str(e)}")
                    upload_results[ics_file.name] = False
        
        # 显示上传结果统计
        successful_uploads = sum(1 for success in upload_results.values() if success)
        total_files = len(upload_results)
        
        if successful_uploads == total_files:
            st.success(f"🎉 全部完成！成功推送 {successful_uploads} 个ICS文件到云端")
        elif successful_uploads > 0:
            st.warning(f"⚠️ 部分完成：{successful_uploads}/{total_files} 个文件推送成功")
        else:
            st.error("❌ 推送失败，请检查网络连接和权限配置")
        
        # 显示云端访问URL
        if successful_uploads > 0:
            st.markdown("#### 🔗 云端访问链接")
            for filename, success in upload_results.items():
                if success:
                    public_url = storage_manager.get_public_calendar_url(filename)
                    st.code(f"📅 {filename}: {public_url}")
        
        # 同步其他重要文件的选项
        if st.button("🔄 同步所有配置文件", use_container_width=True):
            with st.spinner("正在同步配置文件..."):
                sync_results = storage_manager.sync_all_files()
                
                for file_path, success in sync_results.items():
                    if success:
                        st.success(f"✅ 同步成功: {file_path}")
                    else:
                        st.error(f"❌ 同步失败: {file_path}")
                        
    except Exception as e:
        st.error(f"❌ 推送过程中出现异常: {str(e)}")
        st.markdown("**可能的解决方案：**")
        st.markdown("1. 检查网络连接")
        st.markdown("2. 验证GCP权限配置")
        st.markdown("3. 确认Bucket是否存在")

def show_ics_viewer_page():
    """单独的ICS查看器页面"""
    st.markdown('<div class="section-header">🔍 ICS日历查看器</div>', unsafe_allow_html=True)
    
    st.markdown("""
    ### 📖 功能说明
    这是一个专用的ICS日历文件查看器，支持：
    - 🌐 智能数据源选择（云端/本地）
    - 📅 事件详细信息查看
    - 📊 统计分析和筛选
    - 🔧 原始数据查看
    - 📱 响应式设计
    """)
    
    st.markdown("---")
    
    # 数据源选择区域
    st.markdown("#### 🎯 数据源选择")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        data_source = st.radio(
            "选择数据源:",
            ["🌐 智能读取（本地优先）", "💻 仅本地文件", "☁️ 仅云端"],
            key="ics_viewer_data_source",
            help="智能读取会自动选择最佳数据源"
        )
    
    with col2:
        # 文件选择
        available_files = get_available_ics_files(data_source)
        if not available_files:
            if "云端" in data_source:
                st.warning("📄 云端未找到可用的ICS文件")
                
                # 检查云端存储状态
                from src.cloud_storage_manager import get_storage_manager
                storage_manager = get_storage_manager()
                
                if not storage_manager.is_cloud_mode:
                    st.info("💡 **云端模式未启用**")
                    st.markdown("- 当前运行在本地模式下")
                    st.markdown("- 建议选择 **🌐 智能读取** 或 **💻 仅本地文件**")
                elif not storage_manager.storage_client:
                    st.error("❌ **云端存储不可用**")
                    st.markdown("- GCP 认证未配置")
                    st.markdown("- 请检查认证凭据或在云端环境中运行")
                    st.markdown("- 建议选择 **💻 仅本地文件**")
                else:
                    st.info("☁️ **云端存储可用但文件为空**")
                    st.markdown("- 可能需要先从本地上传文件到云端")
                    st.markdown("- 请在 **📅 日历管理** 页面生成并上传文件")
                    
                    if st.button("🔄 尝试从本地上传到云端", type="primary"):
                        with st.spinner("正在上传..."):
                            try:
                                local_file = Path("calendars/grace_irvine_coordinator.ics")
                                if local_file.exists():
                                    with open(local_file, 'r', encoding='utf-8') as f:
                                        content = f.read()
                                    success = storage_manager.write_ics_calendar(content, "grace_irvine_coordinator.ics")
                                    if success:
                                        st.success("✅ 上传成功！")
                                        st.rerun()
                                    else:
                                        st.error("❌ 上传失败")
                                else:
                                    st.error("❌ 本地文件不存在，请先生成日历文件")
                            except Exception as e:
                                st.error(f"❌ 上传过程出错: {e}")
            else:
                st.warning("📄 未找到可用的ICS文件")
                st.info("💡 请先在 **📅 日历管理** 页面生成日历文件")
            return
        
        selected_file = st.selectbox(
            "选择要查看的ICS文件:",
            options=available_files,
            key="ics_viewer_file_selector",
            help="选择要查看的日历文件"
        )
    
    if not selected_file:
        return
    
    st.markdown("---")
    
    # 文件内容读取和显示
    with st.spinner(f"正在读取文件: {selected_file}..."):
        content, source_info = read_ics_file_smart(selected_file, data_source)
    
    if not content:
        st.error(f"❌ 无法读取文件: {selected_file}")
        st.markdown("**可能的原因：**")
        st.markdown("- 文件不存在或已损坏")
        st.markdown("- 云端存储连接问题")
        st.markdown("- 文件权限问题")
        
        # 提供故障排除选项
        if st.button("🔧 尝试重新生成文件", type="primary"):
            with st.spinner("正在重新生成日历文件..."):
                success, message = generate_calendar_files()
                if success:
                    st.success(f"✅ {message}")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
        return
    
    # 显示数据源信息
    st.success(f"✅ 文件读取成功 | 📊 数据源: {source_info}")
    
    # 解析事件
    try:
        events = parse_ics_events(content)
        
        if not events:
            st.warning("📄 文件中没有找到有效的事件")
            return
        
        # 创建主要的标签页
        tab1, tab2, tab3, tab4 = st.tabs(["📅 事件列表", "📊 统计分析", "🔧 原始数据", "⚙️ 工具"])
        
        with tab1:
            show_events_list_tab(events, selected_file)
        
        with tab2:
            show_statistics_tab(events, selected_file)
        
        with tab3:
            show_raw_data_tab(content, selected_file)
        
        with tab4:
            show_tools_tab(content, selected_file, source_info)
            
    except Exception as e:
        st.error(f"❌ 解析ICS文件时出错: {e}")
        st.markdown("**可能的原因：**")
        st.markdown("- ICS文件格式不正确")
        st.markdown("- 文件内容损坏")
        st.markdown("- 编码问题")

def show_events_list_tab(events, filename):
    """显示事件列表标签页"""
    st.markdown(f"#### 📋 {filename} 包含的事件 ({len(events)} 个)")
    
    if not events:
        st.info("📭 没有找到事件")
        return
    
    # 事件筛选和排序控制
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_type = st.selectbox(
            "事件类型筛选:",
            ["全部", "通知事件", "服事事件", "其他事件"],
            key="event_filter_viewer"
        )
    
    with col2:
        sort_by = st.selectbox(
            "排序方式:",
            ["时间顺序", "标题", "类型"],
            key="event_sort_viewer"
        )
    
    with col3:
        view_mode = st.selectbox(
            "显示模式:",
            ["详细模式", "紧凑模式", "列表模式"],
            key="event_view_mode_viewer"
        )
    
    # 筛选和排序事件
    filtered_events = filter_events(events, filter_type)
    sorted_events = sort_events(filtered_events, sort_by)
    
    if not filtered_events:
        st.info(f"📭 没有找到符合条件的事件 ({filter_type})")
        return
    
    st.markdown(f"**筛选结果:** {len(filtered_events)} 个事件")
    
    # 显示事件
    for i, event in enumerate(sorted_events, 1):
        if view_mode == "详细模式":
            show_event_detailed(event, i)
        elif view_mode == "紧凑模式":
            show_event_compact(event, i)
        else:  # 列表模式
            show_event_list(event, i)

def show_event_detailed(event, index):
    """详细模式显示事件"""
    with st.expander(f"🗓️ {index}. {event.get('summary', '未知事件')}", expanded=index <= 3):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📅 时间信息**")
            if event.get('start_time'):
                st.text(f"开始: {event['start_time']}")
            if event.get('end_time'):
                st.text(f"结束: {event['end_time']}")
            
            if event.get('location'):
                st.markdown("**📍 位置**")
                st.text(event['location'])
        
        with col2:
            if event.get('description'):
                st.markdown("**📝 描述**")
                st.text_area(
                    "事件描述", 
                    value=event['description'], 
                    height=100,
                    disabled=True,
                    key=f"desc_{event.get('uid', index)}"
                )
        
        if event.get('uid'):
            st.code(f"UID: {event['uid']}", language="text")

def show_event_compact(event, index):
    """紧凑模式显示事件"""
    col1, col2, col3 = st.columns([3, 2, 1])
    
    with col1:
        st.markdown(f"**{index}. {event.get('summary', '未知事件')}**")
        if event.get('description'):
            desc = event['description'][:100] + "..." if len(event['description']) > 100 else event['description']
            st.text(desc)
    
    with col2:
        if event.get('start_time'):
            st.text(f"⏰ {event['start_time']}")
        if event.get('location'):
            st.text(f"📍 {event['location']}")
    
    with col3:
        if st.button("详情", key=f"detail_{index}"):
            st.session_state[f"show_detail_{index}"] = not st.session_state.get(f"show_detail_{index}", False)
    
    # 如果点击了详情按钮，显示完整信息
    if st.session_state.get(f"show_detail_{index}", False):
        with st.container():
            if event.get('description'):
                st.text_area("完整描述", value=event['description'], height=150, disabled=True, key=f"full_desc_{index}")

def show_event_list(event, index):
    """列表模式显示事件"""
    cols = st.columns([1, 3, 2, 2])
    
    with cols[0]:
        st.text(str(index))
    
    with cols[1]:
        st.text(event.get('summary', '未知事件'))
    
    with cols[2]:
        st.text(event.get('start_time', '未知时间'))
    
    with cols[3]:
        st.text(event.get('location', '未知位置'))

def show_statistics_tab(events, filename):
    """显示统计分析标签页"""
    st.markdown(f"#### 📊 {filename} 统计分析")
    
    # 基本统计
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总事件数", len(events))
    
    with col2:
        notification_events = len([e for e in events if "通知" in e.get('summary', '')])
        st.metric("通知事件", notification_events)
    
    with col3:
        service_events = len([e for e in events if any(word in e.get('summary', '') for word in ["服事", "敬拜", "主日"])])
        st.metric("服事事件", service_events)
    
    with col4:
        other_events = len(events) - notification_events - service_events
        st.metric("其他事件", other_events)
    
    st.markdown("---")
    
    # 事件类型分布图表
    if events:
        try:
            import pandas as pd
            
            # 准备数据
            event_types = []
            for event in events:
                summary = event.get('summary', '')
                if "通知" in summary:
                    event_types.append("通知事件")
                elif any(word in summary for word in ["服事", "敬拜", "主日"]):
                    event_types.append("服事事件")
                else:
                    event_types.append("其他事件")
            
            df = pd.DataFrame({'类型': event_types})
            type_counts = df['类型'].value_counts()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📈 事件类型分布**")
                st.bar_chart(type_counts)
            
            with col2:
                st.markdown("**📋 详细统计**")
                for event_type, count in type_counts.items():
                    percentage = (count / len(events)) * 100
                    st.text(f"{event_type}: {count} 个 ({percentage:.1f}%)")
                
        except ImportError:
            st.info("📊 需要安装pandas来显示图表")
    
    # 时间分布分析
    st.markdown("---")
    st.markdown("**⏰ 时间分布分析**")
    
    time_slots = {}
    for event in events:
        start_time = event.get('start_time', '')
        if start_time:
            try:
                # 提取小时
                if 'T' in start_time:
                    time_part = start_time.split('T')[1][:2]
                    hour = int(time_part)
                    
                    if 6 <= hour < 12:
                        slot = "上午 (6-12)"
                    elif 12 <= hour < 18:
                        slot = "下午 (12-18)"
                    elif 18 <= hour < 24:
                        slot = "晚上 (18-24)"
                    else:
                        slot = "深夜/凌晨 (0-6)"
                    
                    time_slots[slot] = time_slots.get(slot, 0) + 1
            except:
                pass
    
    if time_slots:
        for slot, count in time_slots.items():
            st.text(f"{slot}: {count} 个事件")

def show_raw_data_tab(content, filename):
    """显示原始数据标签页"""
    st.markdown(f"#### 🔧 {filename} 原始ICS内容")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("**📄 文件信息**")
        lines = content.split('\n')
        st.text(f"总行数: {len(lines)}")
        st.text(f"文件大小: {len(content.encode('utf-8'))} 字节")
    
    with col2:
        if st.button("📋 复制内容", use_container_width=True):
            st.success("内容已复制到剪贴板！")
        
        if st.button("💾 下载文件", use_container_width=True):
            st.download_button(
                label="下载ICS文件",
                data=content,
                file_name=filename,
                mime="text/calendar"
            )
    
    st.markdown("---")
    
    # 显示原始内容，添加行号
    st.markdown("**📝 原始内容（带行号）**")
    
    # 分页显示，避免内容过长
    lines_per_page = 50
    total_lines = len(content.split('\n'))
    total_pages = (total_lines + lines_per_page - 1) // lines_per_page
    
    if total_pages > 1:
        page = st.selectbox(f"选择页面 (每页{lines_per_page}行)", range(1, total_pages + 1))
        start_line = (page - 1) * lines_per_page
        end_line = min(start_line + lines_per_page, total_lines)
        
        lines = content.split('\n')[start_line:end_line]
        numbered_content = '\n'.join([f"{start_line + i + 1:3d}| {line}" for i, line in enumerate(lines)])
        
        st.code(numbered_content, language="text")
        st.text(f"显示第 {start_line + 1}-{end_line} 行 (共 {total_lines} 行)")
    else:
        lines = content.split('\n')
        numbered_content = '\n'.join([f"{i + 1:3d}| {line}" for i, line in enumerate(lines)])
        st.code(numbered_content, language="text")

def show_tools_tab(content, filename, source_info):
    """显示工具标签页"""
    st.markdown(f"#### ⚙️ {filename} 工具箱")
    
    # 文件信息
    st.markdown("**📊 文件详情**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"**文件名:** {filename}")
        st.info(f"**数据源:** {source_info}")
    
    with col2:
        file_size = len(content.encode('utf-8'))
        st.info(f"**文件大小:** {file_size:,} 字节")
        st.info(f"**行数:** {len(content.split('\n'))}")
    
    with col3:
        events = parse_ics_events(content)
        st.info(f"**事件数量:** {len(events)}")
        st.info(f"**文件格式:** ICS/iCalendar")
    
    st.markdown("---")
    
    # 操作工具
    st.markdown("**🔧 操作工具**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📤 导出工具**")
        
        if st.button("📋 复制到剪贴板", use_container_width=True):
            st.code(content[:200] + "..." if len(content) > 200 else content)
            st.success("✅ 内容已显示，请手动复制")
        
        if st.button("💾 下载ICS文件", use_container_width=True):
            st.download_button(
                label="⬇️ 下载文件",
                data=content,
                file_name=filename,
                mime="text/calendar",
                use_container_width=True
            )
    
    with col2:
        st.markdown("**🔄 刷新工具**")
        
        if st.button("🔃 重新读取文件", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        if st.button("🔄 重新生成文件", use_container_width=True):
            with st.spinner("正在重新生成ICS文件..."):
                success, message = generate_calendar_files()
                if success:
                    st.success(f"✅ {message}")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
    
    st.markdown("---")
    
    # 验证工具
    st.markdown("**✅ 验证工具**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 验证ICS格式", use_container_width=True):
            validation_result = validate_ics_format(content)
            if validation_result['valid']:
                st.success("✅ ICS格式有效")
                st.info(f"📊 找到 {validation_result['event_count']} 个事件")
            else:
                st.error(f"❌ ICS格式无效: {validation_result['error']}")
    
    with col2:
        if st.button("📊 生成报告", use_container_width=True):
            generate_ics_report(content, filename, events)

def validate_ics_format(content):
    """验证ICS文件格式"""
    try:
        if not content.strip().startswith('BEGIN:VCALENDAR'):
            return {'valid': False, 'error': '缺少VCALENDAR开始标记'}
        
        if not content.strip().endswith('END:VCALENDAR'):
            return {'valid': False, 'error': '缺少VCALENDAR结束标记'}
        
        events = parse_ics_events(content)
        
        return {
            'valid': True, 
            'event_count': len(events),
            'message': 'ICS格式验证通过'
        }
    except Exception as e:
        return {'valid': False, 'error': str(e)}

def generate_ics_report(content, filename, events):
    """生成ICS文件报告"""
    st.markdown("### 📋 ICS文件分析报告")
    
    # 基本信息
    st.markdown("#### 📊 基本信息")
    st.text(f"文件名: {filename}")
    st.text(f"文件大小: {len(content.encode('utf-8'))} 字节")
    st.text(f"总行数: {len(content.split('\n'))}")
    st.text(f"事件数量: {len(events)}")
    
    # 事件统计
    if events:
        st.markdown("#### 📅 事件统计")
        
        # 按类型统计
        notification_count = len([e for e in events if "通知" in e.get('summary', '')])
        service_count = len([e for e in events if any(word in e.get('summary', '') for word in ["服事", "敬拜", "主日"])])
        other_count = len(events) - notification_count - service_count
        
        st.text(f"通知事件: {notification_count}")
        st.text(f"服事事件: {service_count}")
        st.text(f"其他事件: {other_count}")
        
        # 时间范围
        start_times = [e.get('start_time') for e in events if e.get('start_time')]
        if start_times:
            st.text(f"时间范围: {min(start_times)} 到 {max(start_times)}")
    
    st.success("✅ 报告生成完成")

def show_ics_events_content():
    """显示ICS事件内容"""
    st.markdown("### 🔍 ICS事件内容查看器")
    
    calendar_dir = Path("calendars")
    if not calendar_dir.exists():
        st.error("📁 日历目录不存在")
        return
    
    ics_files = list(calendar_dir.glob("*.ics"))
    if not ics_files:
        st.warning("📄 未找到ICS文件，请先生成日历文件")
        return
    
    # 选择要查看的文件
    selected_file = st.selectbox(
        "选择要查看的ICS文件:",
        options=[f.name for f in ics_files],
        key="ics_file_selector"
    )
    
    if selected_file:
        file_path = calendar_dir / selected_file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析ICS事件
            events = parse_ics_events(content)
            
            st.markdown(f"#### 📋 {selected_file} 包含的事件")
            
            if events:
                for i, event in enumerate(events, 1):
                    with st.expander(f"事件 {i}: {event.get('summary', '未知事件')}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**基本信息:**")
                            st.text(f"标题: {event.get('summary', 'N/A')}")
                            st.text(f"开始时间: {event.get('start_time', 'N/A')}")
                            st.text(f"结束时间: {event.get('end_time', 'N/A')}")
                            st.text(f"地点: {event.get('location', 'N/A')}")
                        
                        with col2:
                            st.markdown("**事件描述:**")
                            description = event.get('description', 'N/A')
                            st.text_area(
                                "内容:",
                                value=description,
                                height=150,
                                key=f"event_desc_{i}",
                                disabled=True
                            )
                
                # 显示统计信息
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📊 事件总数", len(events))
                with col2:
                    notification_events = [e for e in events if "通知" in e.get('summary', '')]
                    st.metric("📢 通知事件", len(notification_events))
                with col3:
                    service_events = [e for e in events if "服事" in e.get('summary', '')]
                    st.metric("🙏 服事事件", len(service_events))
            else:
                st.info("📄 该文件中未找到事件")
            
            # 显示原始内容（可选）
            with st.expander("🔧 查看原始ICS内容"):
                st.code(content, language="text")
                
        except Exception as e:
            st.error(f"❌ 读取文件失败: {e}")

def show_ics_events_content_enhanced():
    """增强版ICS事件内容查看器 - 支持云端读取"""
    st.markdown("### 🔍 增强版ICS事件内容查看器")
    st.markdown("💡 支持从云端和本地自动读取ICS文件内容并解析事件详情")
    
    # 数据源选择
    col1, col2 = st.columns(2)
    with col1:
        data_source = st.radio(
            "选择数据源:",
            ["🌐 智能读取（云端优先）", "💻 本地文件", "☁️ 仅云端"],
            key="ics_data_source"
        )
    
    with col2:
        available_files = get_available_ics_files(data_source)
        if not available_files:
            st.warning("📄 未找到可用的ICS文件")
            return
        
        selected_file = st.selectbox(
            "选择ICS文件:",
            options=available_files,
            key="enhanced_ics_file_selector"
        )
    
    if selected_file:
        # 读取文件内容
        content, source_info = read_ics_file_smart(selected_file, data_source)
        
        if not content:
            st.error(f"❌ 无法读取文件: {selected_file}")
            return
        
        # 显示数据源信息
        st.info(f"📊 数据源: {source_info}")
        
        # 解析事件
        try:
            events = parse_ics_events(content)
            
            # 创建标签页
            tab1, tab2, tab3 = st.tabs(["📅 事件列表", "📊 统计分析", "🔧 原始数据"])
            
            with tab1:
                st.markdown(f"#### 📋 {selected_file} 包含的事件 ({len(events)} 个)")
                
                if events:
                    # 事件筛选
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        filter_type = st.selectbox(
                            "事件类型筛选:",
                            ["全部", "通知事件", "服事事件", "其他事件"],
                            key="event_filter"
                        )
                    
                    with col2:
                        sort_by = st.selectbox(
                            "排序方式:",
                            ["时间顺序", "标题", "类型"],
                            key="event_sort"
                        )
                    
                    with col3:
                        view_mode = st.selectbox(
                            "显示模式:",
                            ["详细模式", "紧凑模式", "列表模式"],
                            key="event_view_mode"
                        )
                    
                    # 筛选和排序事件
                    filtered_events = filter_events(events, filter_type)
                    sorted_events = sort_events(filtered_events, sort_by)
                    
                    # 显示事件
                    if view_mode == "列表模式":
                        show_events_table(sorted_events)
                    else:
                        show_events_detailed(sorted_events, view_mode == "详细模式")
                else:
                    st.info("📄 该文件中未找到事件")
            
            with tab2:
                show_events_statistics(events, content)
            
            with tab3:
                show_raw_ics_content(content, selected_file)
                
        except Exception as e:
            st.error(f"❌ 解析ICS文件失败: {e}")

def get_available_ics_files(data_source: str) -> List[str]:
    """获取可用的ICS文件列表"""
    files = []
    cloud_available = False
    
    try:
        if "智能读取" in data_source or "云端" in data_source:
            # 从云端获取文件列表
            from src.cloud_storage_manager import get_storage_manager
            storage_manager = get_storage_manager()
            
            if storage_manager.is_cloud_mode and storage_manager.storage_client:
                try:
                    prefix = storage_manager.config.calendars_path
                    for blob in storage_manager.bucket.list_blobs(prefix=prefix):
                        if blob.name.endswith('.ics'):
                            filename = blob.name.replace(prefix, '')
                            files.append(f"☁️ {filename}")
                    cloud_available = True
                    logger.info(f"云端文件列表获取成功: {len([f for f in files if f.startswith('☁️')])} 个文件")
                except Exception as e:
                    logger.error(f"获取云端文件列表失败: {e}")
            else:
                logger.warning(f"云端存储不可用: is_cloud_mode={storage_manager.is_cloud_mode}, storage_client={'是' if storage_manager.storage_client else '否'}")
        
        if "智能读取" in data_source or "本地" in data_source:
            # 从本地获取文件列表
            calendar_dir = Path("calendars")
            if calendar_dir.exists():
                for file_path in calendar_dir.glob("*.ics"):
                    filename = file_path.name
                    if f"☁️ {filename}" not in files:  # 避免重复
                        files.append(f"💻 {filename}")
                logger.info(f"本地文件列表获取成功: {len([f for f in files if f.startswith('💻')])} 个文件")
    
    except Exception as e:
        logger.error(f"获取文件列表失败: {e}")
    
    # 如果是仅云端模式但云端不可用，返回空列表并记录警告
    if "仅云端" in data_source and not cloud_available:
        logger.warning("仅云端模式但云端存储不可用，无法获取文件列表")
        return []
    
    # 去除前缀，返回纯文件名用于显示
    clean_files = []
    for file in files:
        if file.startswith("☁️ ") or file.startswith("💻 "):
            clean_files.append(file[2:])  # 移除前缀
        else:
            clean_files.append(file)
    
    return list(set(clean_files))  # 去重

def read_ics_file_smart(filename: str, data_source: str) -> tuple:
    """智能读取ICS文件内容"""
    content = None
    source_info = ""
    
    try:
        from src.cloud_storage_manager import get_storage_manager
        storage_manager = get_storage_manager()
        
        if "智能读取" in data_source:
            # 智能读取：先尝试本地，再尝试云端
            local_path = Path("calendars") / filename
            if local_path.exists():
                try:
                    with open(local_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    source_info = "💻 本地文件 (智能读取)"
                    logger.info(f"从本地文件读取ICS成功: {filename}")
                except Exception as e:
                    logger.error(f"本地文件读取失败: {e}")
            
            # 如果本地读取失败，尝试云端
            if not content:
                try:
                    cloud_content = storage_manager.read_ics_calendar(filename)
                    if cloud_content:
                        content = cloud_content
                        source_info = "☁️ 云端存储 (智能读取)"
                        logger.info(f"从云端读取ICS成功: {filename}")
                except Exception as e:
                    logger.error(f"云端读取失败: {e}")
        
        elif "云端" in data_source:
            # 仅云端
            try:
                content = storage_manager.read_ics_calendar(filename)
                source_info = "☁️ 云端存储" if content else "❌ 云端文件不存在"
                if content:
                    logger.info(f"从云端读取ICS成功: {filename}")
            except Exception as e:
                logger.error(f"云端读取失败: {e}")
                source_info = f"❌ 云端读取失败: {str(e)}"
        
        elif "本地" in data_source:
            # 仅本地
            local_path = Path("calendars") / filename
            if local_path.exists():
                try:
                    with open(local_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    source_info = "💻 本地文件"
                    logger.info(f"从本地文件读取ICS成功: {filename}")
                except Exception as e:
                    logger.error(f"本地文件读取失败: {e}")
                    source_info = f"❌ 本地文件读取失败: {str(e)}"
            else:
                source_info = "❌ 本地文件不存在"
    
    except Exception as e:
        logger.error(f"读取ICS文件失败: {e}")
        source_info = f"❌ 读取失败: {str(e)}"
    
    return content, source_info

def filter_events(events: List[Dict], filter_type: str) -> List[Dict]:
    """筛选事件"""
    if filter_type == "全部":
        return events
    elif filter_type == "通知事件":
        return [e for e in events if "通知" in e.get('summary', '')]
    elif filter_type == "服事事件":
        return [e for e in events if "服事" in e.get('summary', '')]
    else:  # 其他事件
        return [e for e in events if "通知" not in e.get('summary', '') and "服事" not in e.get('summary', '')]

def sort_events(events: List[Dict], sort_by: str) -> List[Dict]:
    """排序事件"""
    if sort_by == "标题":
        return sorted(events, key=lambda x: x.get('summary', ''))
    elif sort_by == "类型":
        def get_event_type(event):
            summary = event.get('summary', '')
            if "通知" in summary:
                return "1_通知"
            elif "服事" in summary:
                return "2_服事"
            else:
                return "3_其他"
        return sorted(events, key=get_event_type)
    else:  # 时间顺序
        return sorted(events, key=lambda x: x.get('start_time', ''))

def show_events_table(events: List[Dict]):
    """以表格形式显示事件"""
    if not events:
        st.info("没有符合条件的事件")
        return
    
    # 创建数据框
    table_data = []
    for i, event in enumerate(events, 1):
        table_data.append({
            '序号': i,
            '标题': event.get('summary', 'N/A'),
            '开始时间': event.get('start_time', 'N/A'),
            '结束时间': event.get('end_time', 'N/A'),
            '地点': event.get('location', 'N/A'),
            'UID': event.get('uid', 'N/A')[:20] + '...' if event.get('uid', '') else 'N/A'
        })
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True)

def show_events_detailed(events: List[Dict], detailed: bool = True):
    """详细显示事件"""
    if not events:
        st.info("没有符合条件的事件")
        return
    
    for i, event in enumerate(events, 1):
        summary = event.get('summary', '未知事件')
        
        if detailed:
            with st.expander(f"🎯 事件 {i}: {summary}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📋 基本信息**")
                    st.text(f"标题: {event.get('summary', 'N/A')}")
                    st.text(f"开始时间: {event.get('start_time', 'N/A')}")
                    st.text(f"结束时间: {event.get('end_time', 'N/A')}")
                    st.text(f"地点: {event.get('location', 'N/A')}")
                    st.text(f"UID: {event.get('uid', 'N/A')}")
                
                with col2:
                    st.markdown("**📝 事件描述**")
                    description = event.get('description', 'N/A')
                    st.text_area(
                        "详细内容:",
                        value=description,
                        height=200,
                        key=f"enhanced_event_desc_{i}_{event.get('uid', i)}",
                        disabled=True
                    )
                
                # 操作按钮
                if st.button(f"📋 复制事件内容", key=f"copy_event_{i}_{event.get('uid', i)}"):
                    event_text = f"事件: {summary}\n时间: {event.get('start_time', 'N/A')} - {event.get('end_time', 'N/A')}\n地点: {event.get('location', 'N/A')}\n描述: {description}"
                    st.code(event_text, language=None)
                    st.success("✅ 事件内容已显示，可复制上方文本框内容")
        else:
            # 紧凑模式
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.markdown(f"**{i}. {summary}**")
            with col2:
                st.text(event.get('start_time', 'N/A'))
            with col3:
                if st.button("详情", key=f"detail_btn_{i}_{event.get('uid', i)}"):
                    show_event_detail_modal(event)

def show_event_detail_modal(event: Dict):
    """显示事件详情模态框"""
    with st.container():
        st.markdown("---")
        st.markdown(f"### 📋 事件详情: {event.get('summary', '未知事件')}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**基本信息:**")
            st.text(f"标题: {event.get('summary', 'N/A')}")
            st.text(f"开始时间: {event.get('start_time', 'N/A')}")
            st.text(f"结束时间: {event.get('end_time', 'N/A')}")
            st.text(f"地点: {event.get('location', 'N/A')}")
            st.text(f"UID: {event.get('uid', 'N/A')}")
        
        with col2:
            st.markdown("**事件描述:**")
            description = event.get('description', 'N/A')
            st.text_area(
                "内容:",
                value=description,
                height=150,
                disabled=True
            )
        st.markdown("---")

def show_events_statistics(events: List[Dict], content: str):
    """显示事件统计信息"""
    st.markdown("#### 📊 事件统计分析")
    
    if not events:
        st.info("📄 无事件数据可统计")
        return
    
    # 基础统计
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 事件总数", len(events))
    
    with col2:
        notification_events = [e for e in events if "通知" in e.get('summary', '')]
        st.metric("📢 通知事件", len(notification_events))
    
    with col3:
        service_events = [e for e in events if "服事" in e.get('summary', '')]
        st.metric("🙏 服事事件", len(service_events))
    
    with col4:
        other_events = len(events) - len(notification_events) - len(service_events)
        st.metric("📝 其他事件", other_events)
    
    # 时间分布分析
    st.markdown("#### 📅 时间分布")
    
    # 按月份统计
    month_count = {}
    for event in events:
        start_time = event.get('start_time', '')
        if start_time and len(start_time) >= 7:  # 至少包含年月信息
            month_key = start_time[:7]  # YYYY-MM
            month_count[month_key] = month_count.get(month_key, 0) + 1
    
    if month_count:
        st.bar_chart(month_count)
    else:
        st.info("无法解析事件时间信息进行月份统计")
    
    # 事件类型饼图
    st.markdown("#### 🥧 事件类型分布")
    
    type_count = {
        "通知事件": len(notification_events),
        "服事事件": len(service_events),
        "其他事件": other_events
    }
    
    # 创建简单的图表数据
    chart_data = pd.DataFrame(
        list(type_count.items()),
        columns=['类型', '数量']
    )
    
    if not chart_data.empty:
        st.bar_chart(chart_data.set_index('类型'))
    
    # 文件信息
    st.markdown("#### 📄 文件信息")
    col1, col2 = st.columns(2)
    
    with col1:
        file_size = len(content.encode('utf-8'))
        st.metric("文件大小", f"{file_size / 1024:.1f} KB")
    
    with col2:
        valid_ics = content.startswith('BEGIN:VCALENDAR') and content.endswith('END:VCALENDAR')
        st.metric("ICS格式", "✅ 有效" if valid_ics else "❌ 无效")

def show_raw_ics_content(content: str, filename: str):
    """显示原始ICS内容"""
    st.markdown(f"#### 🔧 {filename} 原始内容")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown("**文件信息:**")
        st.text(f"文件大小: {len(content.encode('utf-8'))} 字节")
        newline = '\n'
        st.text(f"行数: {len(content.split(newline))}")
        st.text(f"字符数: {len(content)}")
        
        # 验证按钮
        if st.button("✅ 验证ICS格式", use_container_width=True):
            is_valid = validate_ics_content(content)
            if is_valid:
                st.success("✅ ICS格式有效")
            else:
                st.error("❌ ICS格式无效")
    
    with col2:
        st.markdown("**原始内容:**")
        st.code(content, language="text")
        
        # 下载按钮
        st.download_button(
            label="💾 下载ICS文件",
            data=content,
            file_name=filename,
            mime="text/calendar",
            use_container_width=True
        )

def validate_ics_content(content: str) -> bool:
    """验证ICS内容格式"""
    try:
        # 基本格式检查
        if not content.strip():
            return False
        
        lines = content.strip().split('\n')
        
        # 检查开始和结束标记
        if not lines[0].strip().startswith('BEGIN:VCALENDAR'):
            return False
        
        if not lines[-1].strip().startswith('END:VCALENDAR'):
            return False
        
        # 检查必需的属性
        has_version = any('VERSION:' in line for line in lines)
        has_prodid = any('PRODID:' in line for line in lines)
        
        if not (has_version and has_prodid):
            return False
        
        # 检查事件格式
        event_starts = sum(1 for line in lines if line.strip() == 'BEGIN:VEVENT')
        event_ends = sum(1 for line in lines if line.strip() == 'END:VEVENT')
        
        if event_starts != event_ends:
            return False
        
        return True
        
    except Exception:
        return False

def show_reminder_settings():
    """显示提醒设置页面"""
    st.markdown('<div class="section-header">⏰ 提醒时间设置</div>', unsafe_allow_html=True)
    st.markdown("配置ICS日历事件的提醒时间，包括事件发生时间和提醒提前时间")
    
    # 获取提醒配置管理器
    try:
        from src.reminder_config_manager import get_reminder_manager
        reminder_manager = get_reminder_manager()
    except ImportError as e:
        st.error(f"❌ 无法加载提醒配置管理器: {e}")
        return
    except Exception as e:
        st.error(f"❌ 初始化提醒配置管理器失败: {e}")
        return
    
    # 显示详细的存储状态
    storage_status = reminder_manager.get_storage_status()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if storage_status['cloud_mode']:
            if storage_status['cloud_storage_available']:
                st.success("☁️ 云端存储模式")
                st.caption(f"Bucket: {storage_status['bucket_name']}")
            else:
                st.warning("☁️ 云端模式（连接异常）")
        else:
            st.info("💻 本地存储模式")
    
    with col2:
        # 配置文件状态
        if storage_status['cloud_file_exists']:
            st.success("✅ 云端配置存在")
            if storage_status['last_sync_time']:
                last_sync = datetime.fromisoformat(storage_status['last_sync_time'].replace('Z', '+00:00')).strftime('%m-%d %H:%M')
                st.caption(f"最后同步: {last_sync}")
        else:
            st.warning("⚠️ 云端配置缺失")
        
        if storage_status['local_file_exists']:
            st.info("📁 本地备份存在")
        else:
            st.warning("📁 本地备份缺失")
    
    with col3:
        if st.button("🔄 重新加载配置", use_container_width=True):
            if reminder_manager.load_configs():
                st.success("✅ 配置重新加载成功")
                st.rerun()
            else:
                st.error("❌ 配置重新加载失败")
        
        if storage_status['cloud_mode'] and st.button("☁️ 强制云端同步", use_container_width=True):
            if reminder_manager.force_sync_to_cloud():
                st.success("✅ 强制同步成功")
                st.rerun()
            else:
                st.error("❌ 强制同步失败")
    
    # 获取当前配置
    configs = reminder_manager.get_all_configs()
    
    # 创建标签页
    tab1, tab2, tab3 = st.tabs(["📝 编辑配置", "📊 配置预览", "⚙️ 高级设置"])
    
    with tab1:
        st.markdown("### 📝 编辑提醒配置")
        
        # 选择要编辑的配置
        config_options = {}
        for event_type, config in configs.items():
            config_options[f"{config.name} ({event_type})"] = event_type
        
        selected_key = st.selectbox(
            "选择要编辑的提醒配置:",
            options=list(config_options.keys()),
            key="reminder_config_selector"
        )
        
        if selected_key:
            event_type = config_options[selected_key]
            current_config = configs[event_type]
            
            # 显示当前配置的编辑界面
            edited_config = show_config_editor(current_config, event_type)
            
            if edited_config:
                # 保存按钮
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("💾 保存配置", type="primary", use_container_width=True):
                        # 验证配置
                        errors = reminder_manager.validate_config(edited_config)
                        if errors:
                            st.error(f"❌ 配置验证失败:\n" + "\n".join([f"• {error}" for error in errors]))
                        else:
                            if reminder_manager.update_config(event_type, edited_config):
                                st.success("✅ 配置保存成功！")
                                st.rerun()
                            else:
                                st.error("❌ 配置保存失败")
                
                with col2:
                    if st.button("🔄 重置为默认", use_container_width=True):
                        default_configs = reminder_manager.get_default_configs()
                        if event_type in default_configs:
                            if reminder_manager.update_config(event_type, default_configs[event_type]):
                                st.success("✅ 已重置为默认配置")
                                st.rerun()
                            else:
                                st.error("❌ 重置失败")
                
                with col3:
                    if st.button("🧪 测试配置", use_container_width=True):
                        show_config_test(edited_config)
    
    with tab2:
        show_configs_preview(configs)
    
    with tab3:
        show_advanced_settings(reminder_manager)

def show_config_editor(config, event_type: str):
    """显示单个配置的编辑界面"""
    st.markdown(f"#### ⚙️ 编辑 {config.name}")
    
    # 基本信息
    col1, col2 = st.columns(2)
    
    with col1:
        enabled = st.checkbox(
            "启用此提醒",
            value=config.enabled,
            key=f"enabled_{event_type}"
        )
        
        name = st.text_input(
            "配置名称",
            value=config.name,
            key=f"name_{event_type}"
        )
    
    with col2:
        description = st.text_area(
            "配置描述",
            value=config.description,
            height=100,
            key=f"description_{event_type}"
        )
    
    # 事件时间设置
    st.markdown("#### 📅 事件时间设置")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        weekday = st.selectbox(
            "星期几",
            options=list(range(7)),
            index=config.event_timing.weekday,
            format_func=lambda x: ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][x],
            key=f"weekday_{event_type}"
        )
    
    with col2:
        hour = st.number_input(
            "小时 (0-23)",
            min_value=0,
            max_value=23,
            value=config.event_timing.hour,
            key=f"hour_{event_type}"
        )
    
    with col3:
        minute = st.number_input(
            "分钟 (0-59)",
            min_value=0,
            max_value=59,
            value=config.event_timing.minute,
            key=f"minute_{event_type}"
        )
    
    with col4:
        duration = st.number_input(
            "持续时间（分钟）",
            min_value=1,
            max_value=480,
            value=config.event_timing.duration_minutes,
            key=f"duration_{event_type}"
        )
    
    # 提醒时间设置
    st.markdown("#### ⏰ 提醒时间设置")
    st.markdown("💡 可以组合使用多个时间单位，如：提前1天2小时30分钟")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        days_before = st.number_input(
            "提前天数",
            min_value=0,
            max_value=7,
            value=config.reminder_timing.days_before,
            key=f"days_before_{event_type}"
        )
    
    with col2:
        hours_before = st.number_input(
            "提前小时数",
            min_value=0,
            max_value=23,
            value=config.reminder_timing.hours_before,
            key=f"hours_before_{event_type}"
        )
    
    with col3:
        minutes_before = st.number_input(
            "提前分钟数",
            min_value=0,
            max_value=59,
            value=config.reminder_timing.minutes_before,
            key=f"minutes_before_{event_type}"
        )
    
    # 创建新的配置对象
    try:
        from src.reminder_config_manager import NotificationConfig, EventTiming, ReminderTiming
        
        new_event_timing = EventTiming(
            weekday=weekday,
            hour=hour,
            minute=minute,
            duration_minutes=duration
        )
        
        new_reminder_timing = ReminderTiming(
            days_before=days_before,
            hours_before=hours_before,
            minutes_before=minutes_before
        )
        
        new_config = NotificationConfig(
            event_type=event_type,
            name=name,
            description=description,
            event_timing=new_event_timing,
            reminder_timing=new_reminder_timing,
            enabled=enabled
        )
        
        # 显示预览
        show_config_preview(new_config)
        
        return new_config
        
    except Exception as e:
        st.error(f"❌ 配置处理失败: {e}")
        return None

def show_config_preview(config):
    """显示配置预览"""
    st.markdown("#### 👁️ 配置预览")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**事件信息:**")
        weekday_name = config.event_timing.get_weekday_name()
        time_str = f"{config.event_timing.hour:02d}:{config.event_timing.minute:02d}"
        st.text(f"时间: {weekday_name} {time_str}")
        st.text(f"持续: {config.event_timing.duration_minutes} 分钟")
        st.text(f"状态: {'✅ 启用' if config.enabled else '❌ 禁用'}")
    
    with col2:
        st.markdown("**提醒设置:**")
        total_minutes = (config.reminder_timing.minutes_before + 
                        config.reminder_timing.hours_before * 60 + 
                        config.reminder_timing.days_before * 24 * 60)
        
        st.text(f"提前时间: {format_reminder_time(config.reminder_timing)}")
        st.text(f"ICS格式: {config.reminder_timing.to_ics_trigger()}")
        st.text(f"总分钟数: {total_minutes} 分钟")

def format_reminder_time(reminder_timing) -> str:
    """格式化提醒时间显示"""
    parts = []
    
    if reminder_timing.days_before > 0:
        parts.append(f"{reminder_timing.days_before}天")
    
    if reminder_timing.hours_before > 0:
        parts.append(f"{reminder_timing.hours_before}小时")
    
    if reminder_timing.minutes_before > 0:
        parts.append(f"{reminder_timing.minutes_before}分钟")
    
    if not parts:
        return "无提醒"
    
    return "".join(parts)

def show_configs_preview(configs):
    """显示所有配置的预览"""
    st.markdown("### 📊 当前配置总览")
    
    # 创建配置表格
    table_data = []
    for event_type, config in configs.items():
        weekday_name = config.event_timing.get_weekday_name()
        time_str = f"{config.event_timing.hour:02d}:{config.event_timing.minute:02d}"
        reminder_str = format_reminder_time(config.reminder_timing)
        
        table_data.append({
            "配置名称": config.name,
            "事件类型": event_type,
            "状态": "✅ 启用" if config.enabled else "❌ 禁用",
            "事件时间": f"{weekday_name} {time_str}",
            "持续时间": f"{config.event_timing.duration_minutes}分钟",
            "提醒设置": reminder_str,
            "ICS触发器": config.reminder_timing.to_ics_trigger()
        })
    
    if table_data:
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)
        
        # 统计信息
        col1, col2, col3 = st.columns(3)
        
        with col1:
            enabled_count = sum(1 for config in configs.values() if config.enabled)
            st.metric("启用配置", f"{enabled_count}/{len(configs)}")
        
        with col2:
            avg_reminder_minutes = sum(
                config.reminder_timing.minutes_before + 
                config.reminder_timing.hours_before * 60 + 
                config.reminder_timing.days_before * 24 * 60
                for config in configs.values()
            ) / len(configs) if configs else 0
            st.metric("平均提醒时间", f"{avg_reminder_minutes:.0f}分钟")
        
        with col3:
            unique_days = len(set(config.event_timing.weekday for config in configs.values()))
            st.metric("涉及天数", f"{unique_days}天")
    else:
        st.info("📄 暂无配置数据")

def show_config_test(config):
    """显示配置测试结果"""
    st.markdown("#### 🧪 配置测试")
    
    try:
        from src.reminder_config_manager import get_reminder_manager
        reminder_manager = get_reminder_manager()
        
        # 验证配置
        errors = reminder_manager.validate_config(config)
        
        if errors:
            st.error("❌ 配置验证失败:")
            for error in errors:
                st.error(f"• {error}")
        else:
            st.success("✅ 配置验证通过!")
            
            # 显示详细测试结果
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**时间计算测试:**")
                weekday_name = config.event_timing.get_weekday_name()
                st.text(f"事件时间: {weekday_name} {config.event_timing.hour:02d}:{config.event_timing.minute:02d}")
                
                # 计算下次发生时间
                from datetime import datetime, timedelta
                today = datetime.now().date()
                days_ahead = config.event_timing.weekday - today.weekday()
                if days_ahead <= 0:  # 如果今天是这一天或已过，则计算下周
                    days_ahead += 7
                
                next_event_date = today + timedelta(days=days_ahead)
                next_event_datetime = datetime.combine(
                    next_event_date, 
                    config.event_timing.to_time()
                )
                
                st.text(f"下次事件: {next_event_datetime.strftime('%Y-%m-%d %H:%M')}")
                
                # 计算提醒时间
                total_reminder_minutes = (
                    config.reminder_timing.minutes_before + 
                    config.reminder_timing.hours_before * 60 + 
                    config.reminder_timing.days_before * 24 * 60
                )
                
                reminder_datetime = next_event_datetime - timedelta(minutes=total_reminder_minutes)
                st.text(f"提醒时间: {reminder_datetime.strftime('%Y-%m-%d %H:%M')}")
            
            with col2:
                st.markdown("**ICS格式测试:**")
                st.code(f"TRIGGER:{config.reminder_timing.to_ics_trigger()}", language="text")
                
                # 显示完整的ICS事件示例
                sample_ics = f"""BEGIN:VEVENT
UID:test_event@graceirvine.org
SUMMARY:{config.name}测试
DTSTART:{next_event_datetime.strftime('%Y%m%dT%H%M%S')}
DTEND:{(next_event_datetime + timedelta(minutes=config.event_timing.duration_minutes)).strftime('%Y%m%dT%H%M%S')}
DESCRIPTION:{config.description}
BEGIN:VALARM
ACTION:DISPLAY
DESCRIPTION:提醒：{config.name}测试
TRIGGER:{config.reminder_timing.to_ics_trigger()}
END:VALARM
END:VEVENT"""
                
                with st.expander("📄 ICS事件示例"):
                    st.code(sample_ics, language="text")
    
    except Exception as e:
        st.error(f"❌ 测试失败: {e}")

def show_advanced_settings(reminder_manager):
    """显示高级设置"""
    st.markdown("### ⚙️ 高级设置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔄 配置管理")
        
        if st.button("🔄 重置所有配置", use_container_width=True):
            if st.session_state.get('confirm_reset', False):
                if reminder_manager.reset_to_defaults():
                    st.success("✅ 所有配置已重置为默认值")
                    st.rerun()
                else:
                    st.error("❌ 重置失败")
                st.session_state['confirm_reset'] = False
            else:
                st.warning("⚠️ 再次点击确认重置所有配置")
                st.session_state['confirm_reset'] = True
        
        if st.button("💾 导出配置", use_container_width=True):
            configs = reminder_manager.get_all_configs()
            config_json = {
                'version': '1.0',
                'exported_at': datetime.now().isoformat(),
                'reminder_configs': {k: v.to_dict() for k, v in configs.items()}
            }
            
            st.download_button(
                label="📥 下载配置文件",
                data=json.dumps(config_json, ensure_ascii=False, indent=2),
                file_name=f"reminder_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    with col2:
        st.markdown("#### 📊 存储信息")
        
        storage_status = reminder_manager.get_storage_status()
        
        st.markdown("**存储状态详情:**")
        
        # 存储模式
        mode_text = "云端模式" if storage_status['cloud_mode'] else "本地模式"
        availability_text = "可用" if storage_status['cloud_storage_available'] else "不可用"
        st.text(f"存储模式: {mode_text}")
        st.text(f"云端存储: {availability_text}")
        
        if storage_status['bucket_name']:
            st.text(f"Bucket: {storage_status['bucket_name']}")
        
        # 文件状态
        st.text(f"云端配置文件: {'✅ 存在' if storage_status['cloud_file_exists'] else '❌ 不存在'}")
        st.text(f"本地配置文件: {'✅ 存在' if storage_status['local_file_exists'] else '❌ 不存在'}")
        
        if storage_status['last_sync_time']:
            last_sync = datetime.fromisoformat(storage_status['last_sync_time'].replace('Z', '+00:00'))
            st.text(f"最后同步时间: {last_sync.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 同步状态判断
        if storage_status['cloud_mode']:
            if storage_status['cloud_file_exists'] and storage_status['local_file_exists']:
                st.success("✅ 配置已同步")
            elif storage_status['cloud_file_exists']:
                st.info("ℹ️ 仅云端存在")
            elif storage_status['local_file_exists']:
                st.warning("⚠️ 需要同步到云端")
            else:
                st.error("❌ 配置缺失")
        else:
            if storage_status['local_file_exists']:
                st.success("✅ 本地配置存在")
            else:
                st.error("❌ 本地配置缺失")
    
    # 配置文件上传
    st.markdown("#### 📤 导入配置")
    uploaded_file = st.file_uploader(
        "选择配置文件",
        type=['json'],
        key="config_upload"
    )
    
    if uploaded_file is not None:
        try:
            config_data = json.load(uploaded_file)
            
            # 验证配置格式
            if 'reminder_configs' in config_data:
                st.success("✅ 配置文件格式正确")
                
                if st.button("📥 导入配置", type="primary"):
                    # 这里可以添加导入逻辑
                    st.info("💡 导入功能开发中...")
            else:
                st.error("❌ 配置文件格式不正确")
                
        except json.JSONDecodeError:
            st.error("❌ 无法解析JSON文件")
        except Exception as e:
            st.error(f"❌ 处理文件失败: {e}")

def parse_ics_events(ics_content: str) -> list:
    """解析ICS文件中的事件"""
    events = []
    lines = ics_content.split('\n')
    current_event = {}
    in_event = False
    in_alarm = False
    
    for line in lines:
        line = line.strip()
        
        if line == "BEGIN:VEVENT":
            in_event = True
            in_alarm = False
            current_event = {}
        elif line == "END:VEVENT":
            if current_event:
                events.append(current_event.copy())
            in_event = False
            in_alarm = False
            current_event = {}
        elif line == "BEGIN:VALARM":
            in_alarm = True
        elif line == "END:VALARM":
            in_alarm = False
        elif in_event and not in_alarm and ':' in line:
            key, value = line.split(':', 1)
            
            # 处理特殊字符转义
            value = value.replace('\\n', '\n').replace('\\,', ',').replace('\\;', ';')
            
            if key == "SUMMARY":
                current_event['summary'] = value
            elif key == "DESCRIPTION":
                current_event['description'] = value
            elif key == "LOCATION":
                current_event['location'] = value
            elif key == "DTSTART":
                current_event['start_time'] = format_ics_datetime(value)
            elif key == "DTEND":
                current_event['end_time'] = format_ics_datetime(value)
            elif key == "UID":
                current_event['uid'] = value
    
    return events

def format_ics_datetime(dt_str: str) -> str:
    """格式化ICS日期时间"""
    try:
        if len(dt_str) == 15 and dt_str.endswith('T'):
            # 格式: 20241215T200000
            dt_str = dt_str.replace('T', '')
        
        if len(dt_str) == 14:
            # 格式: 20241215200000
            year = dt_str[:4]
            month = dt_str[4:6]
            day = dt_str[6:8]
            hour = dt_str[8:10]
            minute = dt_str[10:12]
            return f"{year}-{month}-{day} {hour}:{minute}"
        else:
            return dt_str
    except:
        return dt_str

# ==================== 模板生成函数 ====================

# 初始化动态模板管理器
@st.cache_resource
def get_template_manager():
    """获取动态模板管理器实例（缓存）"""
    return DynamicTemplateManager()

def generate_wednesday_template(sunday_date, schedule):
    """生成周三确认通知模板（使用动态模板）"""
    template_manager = get_template_manager()
    return template_manager.render_weekly_confirmation(sunday_date, schedule)

def generate_saturday_template(sunday_date, schedule):
    """生成周六提醒通知模板（使用动态模板）"""
    template_manager = get_template_manager()
    return template_manager.render_saturday_reminder(sunday_date, schedule)

def generate_monthly_template(schedules):
    """生成月度总览通知模板（使用动态模板）"""
    today = date.today()
    if today.month == 12:
        next_month = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month + 1, day=1)
    
    next_month_schedules = [
        s for s in schedules 
        if s.date.year == next_month.year and s.date.month == next_month.month
    ]
    
    # 获取Google Sheets链接
    spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID', '1wescUQe9rIVLNcKdqmSLpzlAw9BGXMZmkFvjEF296nM')
    sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
    
    template_manager = get_template_manager()
    return template_manager.render_monthly_overview(
        next_month_schedules, 
        next_month.year, 
        next_month.month, 
        sheet_url
    )

def send_template_email(template_content, template_type):
    """发送模板到邮箱"""
    try:
        email_sender = EmailSender()
        sender_email = os.getenv("SENDER_EMAIL", "jonathanjing@graceirvine.org")
        recipient = EmailRecipient(email=sender_email, name="事工协调员")
        
        subject = f"【微信群通知模板】{template_type}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>📱 微信群通知模板</h2>
            <h3>{template_type}</h3>
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; font-family: monospace; white-space: pre-line;">
{template_content}
            </div>
            <p><small>此邮件由事工管理系统自动发送 · {datetime.now().strftime('%Y年%m月%d日 %H:%M')}</small></p>
        </body>
        </html>
        """
        
        with st.spinner("正在发送邮件..."):
            success = email_sender.send_email(
                recipients=[recipient],
                subject=subject,
                html_content=html_content,
                text_content=template_content
            )
        
        if success:
            st.success(f"✅ 邮件发送成功！已发送到: {recipient.email}")
        else:
            st.error("❌ 邮件发送失败！请检查邮件配置和网络连接")
            
    except Exception as e:
        st.error(f"❌ 发送邮件时出错: {e}")

# ==================== 主应用 ====================

def main():
    """主应用函数"""
    load_css()
    show_header()
    
    # 侧边栏导航
    with st.sidebar:
        st.markdown("### 🧭 导航菜单")
        
        page_options = [
            "📊 数据概览", 
            "📝 模板生成器",
            "🛠️ 模板编辑器", 
            "📖 经文管理",
            "📅 日历管理",
            "🔍 ICS查看器",
            "⏰ 提醒设置",
            "⚙️ 系统设置"
        ]
        
        page = st.selectbox("选择页面", page_options)
        
        st.markdown("---")
        st.markdown("### ⚡ 快速操作")
        
        if st.button("🔄 刷新数据", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown("### ℹ️ 系统信息")
        st.text(f"版本: v2.0.0 (简化版)")
        st.text(f"更新: {datetime.now().strftime('%Y-%m-%d')}")
    
    # 加载数据
    with st.spinner("正在加载数据..."):
        data_result = load_ministry_data()
    
    # 根据选择的页面显示内容
    if page == "📊 数据概览":
        show_data_overview(data_result)
    
    elif page == "📝 模板生成器":
        show_template_generator(data_result)
    
    elif page == "🛠️ 模板编辑器":
        show_dynamic_template_editor()
    
    elif page == "📖 经文管理":
        show_scripture_management()
    
    elif page == "📅 日历管理":
        show_calendar_management()
    
    elif page == "🔍 ICS查看器":
        show_ics_viewer_page()
    
    elif page == "⏰ 提醒设置":
        show_reminder_settings()
    
    elif page == "⚙️ 系统设置":
        show_system_settings()
    
    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        Grace Irvine Ministry Scheduler v2.0 (简化版) | 
        Made with ❤️ for Grace Irvine Presbyterian Church
    </div>
    """, unsafe_allow_html=True)

def show_system_settings():
    """显示系统设置"""
    st.markdown('<div class="section-header">⚙️ 系统设置</div>', unsafe_allow_html=True)
    
    st.markdown("### 📊 Google Sheets 配置")
    current_id = os.getenv('GOOGLE_SPREADSHEET_ID', '1wescUQe9rIVLNcKdqmSLpzlAw9BGXMZmkFvjEF296nM')
    st.code(f"当前表格ID: {current_id}")
    
    st.markdown("### 📧 邮件配置")
    sender_email = os.getenv('SENDER_EMAIL', '未设置')
    st.code(f"发送邮箱: {sender_email}")
    
    st.markdown("### 💾 缓存管理")
    if st.button("🔄 清除所有缓存"):
        st.cache_data.clear()
        st.success("✅ 缓存已清除")
    
    st.markdown("### 📁 文件状态")
    calendar_dir = Path("calendars")
    if calendar_dir.exists():
        ics_files = list(calendar_dir.glob("*.ics"))
        st.info(f"📅 找到 {len(ics_files)} 个ICS文件")
        for file in ics_files:
            st.text(f"  • {file.name}")
    else:
        st.warning("📁 日历目录不存在")

def show_dynamic_template_editor():
    """显示动态模板编辑器"""
    st.markdown('<div class="section-header">🛠️ 动态模板编辑器</div>', unsafe_allow_html=True)
    st.markdown("在线编辑通知模板，支持本地和云端存储")
    
    # 获取模板管理器
    template_manager = get_template_manager()
    
    # 显示当前模板来源
    col1, col2 = st.columns(2)
    with col1:
        if template_manager.is_cloud_mode:
            st.info("🌐 当前使用云端模板存储")
            if template_manager.gcp_bucket_name:
                st.code(f"Bucket: {template_manager.gcp_bucket_name}")
        else:
            st.info("💻 当前使用本地模板存储")
            st.code(f"文件: {template_manager.local_template_file}")
    
    with col2:
        metadata = template_manager.templates_data.get('metadata', {})
        last_updated = metadata.get('last_updated', '未知')
        st.metric("最后更新", last_updated[:16] if last_updated != '未知' else '未知')
    
    # 创建标签页
    tab1, tab2, tab3 = st.tabs(["📝 编辑模板", "👁️ 预览效果", "💾 保存管理"])
    
    with tab1:
        # 选择要编辑的模板
        template_types = {
            'weekly_confirmation': '📅 周三确认通知',
            'saturday_reminder': '🔔 周六提醒通知', 
            'monthly_overview': '📊 月度总览通知'
        }
        
        selected_type = st.selectbox(
            "选择要编辑的模板:",
            options=list(template_types.keys()),
            format_func=lambda x: template_types[x]
        )
        
        template_config = template_manager.get_template(selected_type)
        if not template_config:
            st.error("模板配置不存在")
            return
        
        # 根据模板类型显示不同的编辑界面
        if selected_type == 'saturday_reminder':
            show_saturday_template_detailed_editor(template_manager, template_config)
        else:
            show_standard_template_editor(template_manager, template_config, selected_type)
    
    with tab2:
        st.markdown("### 👁️ 模板预览")
        
        # 创建测试数据
        test_date = date.today() + timedelta(days=7)
        test_schedule = MinistryAssignment(
            date=test_date,
            audio_tech="Jimmy",
            video_director="靖铮",
            propresenter_play="张宇",
            propresenter_update="Daniel"
        )
        
        if selected_type == 'saturday_reminder':
            # 周六模板的特殊预览界面
            st.markdown("#### 🔔 周六提醒通知预览效果")
            
            # 显示当前配置摘要
            service_times = template_config.get('service_times', {})
            service_instructions = template_config.get('service_instructions', {})
            
            with st.expander("📋 当前配置摘要"):
                st.markdown("**到岗时间设置:**")
                for role, time in service_times.items():
                    st.text(f"• {role}: {time}")
                
                st.markdown("**具体说明设置:**")
                for role, instruction in service_instructions.items():
                    st.text(f"• {role}: {instruction}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### ✅ 有人员安排时")
                try:
                    preview = template_manager.render_saturday_reminder(test_date, test_schedule)
                    st.code(preview, language=None)
                    
                    # 显示detail解析
                    st.markdown("**Detail解析:**")
                    detail_format = template_config.get('detail_format', '{person} {time}到，{instruction}')
                    
                    roles = {
                        'audio_tech': '音控',
                        'video_director': '导播/摄影', 
                        'propresenter_play': 'ProPresenter播放',
                        'propresenter_update': 'ProPresenter更新'
                    }
                    
                    for var_name, role_name in roles.items():
                        person = getattr(test_schedule, var_name, None)
                        if person:
                            time = service_times.get(role_name, '9:00')
                            instruction = service_instructions.get(role_name, '请提前到场')
                            detail = detail_format.format(person=person, time=time, instruction=instruction)
                            st.text(f"• {var_name}_detail: {detail}")
                    
                except Exception as e:
                    st.error(f"❌ 预览生成失败: {e}")
            
            with col2:
                st.markdown("#### ❌ 无人员安排时")
                try:
                    no_preview = template_manager.render_saturday_reminder(test_date, None)
                    st.code(no_preview, language=None)
                    
                    # 显示默认detail解析
                    st.markdown("**默认Detail解析:**")
                    default_detail = template_config.get('default_detail', '待确认 {time}到，{instruction}')
                    
                    for var_name, role_name in roles.items():
                        time = service_times.get(role_name, '9:00')
                        instruction = service_instructions.get(role_name, '请提前到场')
                        detail = default_detail.format(time=time, instruction=instruction)
                        st.text(f"• {var_name}_detail: {detail}")
                    
                except Exception as e:
                    st.error(f"❌ 无安排预览生成失败: {e}")
            
            # 实时预览工具
            st.markdown("---")
            st.markdown("#### 🧪 实时预览工具")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                test_person = st.text_input("测试人员名字:", value="测试同工", key="preview_person")
            
            with col2:
                test_time = st.text_input("测试到岗时间:", value="9:15", key="preview_time") 
            
            with col3:
                test_instruction = st.text_input("测试具体说明:", value="提前调试设备", key="preview_instruction")
            
            if st.button("🔍 生成实时预览", use_container_width=True, key="generate_live_preview"):
                detail_format = template_config.get('detail_format', '{person} {time}到，{instruction}')
                test_detail = detail_format.format(person=test_person, time=test_time, instruction=test_instruction)
                st.success(f"生成的Detail: **{test_detail}**")
        
        else:
            # 其他模板的标准预览
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 有安排时的效果")
                try:
                    if selected_type == 'weekly_confirmation':
                        preview = template_manager.render_weekly_confirmation(test_date, test_schedule)
                    elif selected_type == 'monthly_overview':
                        preview = template_manager.render_monthly_overview([test_schedule], test_date.year, test_date.month)
                    
                    st.code(preview, language=None)
                    
                except Exception as e:
                    st.error(f"❌ 预览生成失败: {e}")
            
            with col2:
                st.markdown("#### 无安排时的效果")
                try:
                    if selected_type == 'weekly_confirmation':
                        no_preview = template_manager.render_weekly_confirmation(test_date, None)
                        st.code(no_preview, language=None)
                    else:
                        st.markdown("#### 模板说明")
                        st.markdown(f"**{template_config.get('name', selected_type)}**")
                        st.markdown(template_config.get('description', '暂无描述'))
                        
                except Exception as e:
                    st.error(f"❌ 无安排预览生成失败: {e}")
    
    with tab3:
        st.markdown("### 💾 保存和管理")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 保存到本地", use_container_width=True):
                if template_manager.save_templates(update_cloud=False):
                    st.success("✅ 已保存到本地文件")
                else:
                    st.error("❌ 保存到本地失败")
        
        with col2:
            # 检查云端存储可用性
            cloud_available = (template_manager.storage_manager.is_cloud_mode and 
                             template_manager.storage_manager.storage_client)
            
            if st.button("☁️ 保存到云端", type="primary", use_container_width=True, 
                        disabled=not cloud_available):
                if cloud_available:
                    with st.spinner("正在保存到云端..."):
                        if template_manager.save_templates(update_cloud=True):
                            st.success("✅ 已保存到云端存储")
                            
                            # 验证云端保存
                            import time
                            time.sleep(1)  # 等待云端上传完成
                            
                            verification = template_manager.storage_manager.verify_cloud_save("templates/dynamic_templates.json")
                            
                            if verification['success']:
                                st.success("🔍 云端保存验证成功")
                                
                                # 显示详细信息
                                details = verification['details']
                                st.info(f"📂 云端位置: {details['cloud_path']}")
                                st.info(f"📊 文件大小: {details['size']} 字节")
                                st.info(f"🕐 更新时间: {details['updated'][:19] if details['updated'] else '未知'}")
                                
                                # 显示内容预览
                                if 'content_preview' in details:
                                    with st.expander("📄 内容预览"):
                                        st.code(details['content_preview'], language='json')
                            else:
                                st.warning(f"⚠️ 云端保存验证失败: {verification['message']}")
                        else:
                            st.error("❌ 保存到云端失败")
                            st.error("请检查网络连接和GCP权限配置")
                else:
                    st.error("❌ 云端存储不可用")
            
            # 显示云端状态提示
            if not cloud_available:
                if not template_manager.storage_manager.is_cloud_mode:
                    st.caption("💡 当前为本地模式，需要云端环境才能保存到云端")
                elif not template_manager.storage_manager.storage_client:
                    st.caption("⚠️ 云端存储客户端未初始化，请检查GCP配置")
        
        with col3:
            if st.button("🔄 重新加载", use_container_width=True):
                # 清除缓存并重新加载
                st.cache_resource.clear()
                template_manager.load_templates()
                st.success("✅ 模板已重新加载")
                st.rerun()
        
        # 备份管理
        st.markdown("---")
        st.markdown("#### 🗂️ 备份管理")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 创建备份", use_container_width=True):
                if template_manager.backup_templates():
                    st.success("✅ 备份创建成功")
                else:
                    st.error("❌ 备份创建失败")
        
        with col2:
            # 显示模板统计
            templates = template_manager.templates_data.get('templates', {})
            st.metric("模板数量", len(templates))
        
        # 显示当前配置
        with st.expander("🔧 查看完整配置"):
            st.json(template_manager.templates_data)
        
        # 云端存储状态检查
        st.markdown("---")
        st.markdown("#### ☁️ 云端存储状态")
        
        col1, col2 = st.columns(2)
        
        with col1:
            storage_status = template_manager.storage_manager.get_storage_status()
            
            if storage_status['mode'] == 'cloud':
                st.success("🌐 云端模式")
                if storage_status['storage_available']:
                    st.success("✅ 云端存储可用")
                else:
                    st.error("❌ 云端存储不可用")
            else:
                st.info("💻 本地模式")
            
            st.text(f"Bucket: {storage_status.get('bucket_name', 'N/A')}")
        
        with col2:
            col2a, col2b = st.columns(2)
            
            with col2a:
                if st.button("🔍 检查文件状态", use_container_width=True):
                    template_file_status = template_manager.storage_manager.get_file_status("templates/dynamic_templates.json")
                    
                    st.markdown("**模板文件状态:**")
                    st.text(f"本地存在: {'✅' if template_file_status['local_exists'] else '❌'}")
                    st.text(f"云端存在: {'✅' if template_file_status['cloud_exists'] else '❌'}")
                    
                    if template_file_status['local_modified']:
                        st.text(f"本地修改: {template_file_status['local_modified'][:19]}")
                    if template_file_status['cloud_modified']:
                        st.text(f"云端修改: {template_file_status['cloud_modified'][:19]}")
                    
                    # 处理同步状态
                    sync_needed = template_file_status['sync_needed']
                    if sync_needed is None:
                        st.info("ℹ️ 无法确定同步状态（本地模式）")
                    elif sync_needed:
                        st.warning("⚠️ 需要同步")
                        # 显示时间差信息
                        if template_file_status['local_modified'] and template_file_status['cloud_modified']:
                            from datetime import datetime
                            local_time = datetime.fromisoformat(template_file_status['local_modified'])
                            cloud_time = datetime.fromisoformat(template_file_status['cloud_modified'])
                            time_diff = abs((local_time - cloud_time).total_seconds())
                            st.caption(f"时间差: {time_diff:.0f} 秒")
                    else:
                        st.success("✅ 已同步")
            
            with col2b:
                # 强制同步按钮
                cloud_available = (template_manager.storage_manager.is_cloud_mode and 
                                 template_manager.storage_manager.storage_client)
                
                if st.button("🔄 强制同步", use_container_width=True, disabled=not cloud_available):
                    if cloud_available:
                        with st.spinner("正在强制同步到云端..."):
                            # 强制保存到云端
                            success = template_manager.save_templates(update_cloud=True)
                            if success:
                                st.success("✅ 强制同步成功！")
                                
                                # 验证同步结果
                                import time
                                time.sleep(2)  # 等待云端上传完成
                                
                                verification = template_manager.storage_manager.verify_cloud_save("templates/dynamic_templates.json")
                                if verification['success']:
                                    st.success("🔍 云端同步验证成功")
                                    details = verification['details']
                                    st.caption(f"云端文件大小: {details['size']} 字节")
                                    st.caption(f"更新时间: {details['updated'][:19] if details['updated'] else '未知'}")
                                else:
                                    st.warning(f"⚠️ 同步验证失败: {verification['message']}")
                                
                                # 刷新页面状态
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ 强制同步失败")
                    else:
                        st.error("❌ 云端存储不可用")

def show_saturday_template_detailed_editor(template_manager, template_config):
    """显示周六模板的详细编辑器"""
    st.markdown("#### 🔔 周六提醒通知 - 详细编辑")
    st.info("💡 在这里可以分别编辑每个服事角色的到岗时间和说明，人员名字会作为变量动态插入")
    
    # 创建子标签页
    detail_tab1, detail_tab2, detail_tab3 = st.tabs(["📝 主模板", "⏰ 时间配置", "📋 说明配置"])
    
    with detail_tab1:
        # 主模板编辑
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("#### 主模板内容")
            current_template = template_config.get('template', '')
            new_template = st.text_area(
                "模板内容:",
                value=current_template,
                height=200,
                help="使用 {角色_detail} 来插入详细信息",
                key="saturday_main_template"
            )
            
            # detail_format 编辑
            st.markdown("#### Detail格式模板")
            current_detail_format = template_config.get('detail_format', '{person} {time}到，{instruction}')
            new_detail_format = st.text_input(
                "Detail格式:",
                value=current_detail_format,
                help="可用变量: {person}=人员名字, {time}=到岗时间, {instruction}=具体说明",
                key="saturday_detail_format"
            )
            
            # default_detail 编辑
            current_default_detail = template_config.get('default_detail', '待确认 {time}到，{instruction}')
            new_default_detail = st.text_input(
                "无人员时的格式:",
                value=current_default_detail,
                help="当没有安排人员时使用的格式",
                key="saturday_default_detail"
            )
        
        with col2:
            st.markdown("#### 可用变量")
            st.code("{audio_tech_detail}")
            st.caption("音控详细安排")
            st.code("{video_director_detail}")
            st.caption("导播/摄影详细安排")
            st.code("{propresenter_play_detail}")
            st.caption("ProPresenter播放详细安排")
            st.code("{propresenter_update_detail}")
            st.caption("ProPresenter更新详细安排")
            
            st.markdown("#### Detail格式变量")
            st.code("{person}")
            st.caption("人员名字（动态插入）")
            st.code("{time}")
            st.caption("到岗时间")
            st.code("{instruction}")
            st.caption("具体说明")
    
    with detail_tab2:
        st.markdown("#### ⏰ 各角色到岗时间设置")
        
        service_times = template_config.get('service_times', {})
        roles = {
            '音控': 'audio_tech',
            '导播/摄影': 'video_director',
            'ProPresenter播放': 'propresenter_play',
            'ProPresenter更新': 'propresenter_update'
        }
        
        new_service_times = {}
        
        for role_name, role_key in roles.items():
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown(f"**{role_name}**")
            
            with col2:
                current_time = service_times.get(role_name, '9:00')
                new_time = st.text_input(
                    f"到岗时间:",
                    value=current_time,
                    key=f"time_{role_key}",
                    help="例如: 9:00, 9:30, 提前等"
                )
                new_service_times[role_name] = new_time
        
        st.markdown("---")
        st.markdown("#### 📋 时间预设模板")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎵 敬拜排练模式", use_container_width=True, key="worship_rehearsal_time"):
                new_service_times['音控'] = '9:00'
                new_service_times['导播/摄影'] = '9:30'
                new_service_times['ProPresenter播放'] = '9:00'
                new_service_times['ProPresenter更新'] = '提前'
                st.success("✅ 已设置为敬拜排练时间")
                st.rerun()
        
        with col2:
            if st.button("🕐 统一时间", use_container_width=True, key="unified_time"):
                unified_time = '9:00'
                for role in new_service_times:
                    new_service_times[role] = unified_time
                st.success(f"✅ 已统一设置为 {unified_time}")
                st.rerun()
        
        with col3:
            if st.button("🔄 重置默认", use_container_width=True, key="reset_default_time"):
                new_service_times = {
                    '音控': '9:00',
                    '导播/摄影': '9:30',
                    'ProPresenter播放': '9:00',
                    'ProPresenter更新': '提前'
                }
                st.success("✅ 已重置为默认时间")
                st.rerun()
    
    with detail_tab3:
        st.markdown("#### 📋 各角色具体说明设置")
        
        service_instructions = template_config.get('service_instructions', {})
        new_service_instructions = {}
        
        for role_name, role_key in roles.items():
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown(f"**{role_name}**")
            
            with col2:
                current_instruction = service_instructions.get(role_name, '请提前到场')
                new_instruction = st.text_input(
                    f"具体说明:",
                    value=current_instruction,
                    key=f"instruction_{role_key}",
                    help="例如: 随敬拜团排练, 检查预设机位, 提前准备内容等"
                )
                new_service_instructions[role_name] = new_instruction
        
        st.markdown("---")
        st.markdown("#### 📋 说明预设模板")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🎵 敬拜配合模式", use_container_width=True, key="worship_cooperation_mode"):
                new_service_instructions['音控'] = '随敬拜团排练'
                new_service_instructions['导播/摄影'] = '检查预设机位'
                new_service_instructions['ProPresenter播放'] = '随敬拜团排练'
                new_service_instructions['ProPresenter更新'] = '提前准备内容'
                st.success("✅ 已设置为敬拜配合说明")
                st.rerun()
        
        with col2:
            if st.button("🔄 重置默认", use_container_width=True, key="reset_default_instructions"):
                new_service_instructions = {
                    '音控': '随敬拜团排练',
                    '导播/摄影': '检查预设机位',
                    'ProPresenter播放': '随敬拜团排练',
                    'ProPresenter更新': '提前准备内容'
                }
                st.success("✅ 已重置为默认说明")
                st.rerun()
    
    # 应用更改按钮
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 保存主模板", type="primary", use_container_width=True, key="save_main_template"):
            template_config['template'] = new_template
            template_config['detail_format'] = new_detail_format
            template_config['default_detail'] = new_default_detail
            template_manager.update_template('saturday_reminder', template_config)
            st.success("✅ 主模板已保存！")
            st.rerun()
    
    with col2:
        if st.button("⏰ 保存时间配置", type="primary", use_container_width=True, key="save_time_config"):
            template_config['service_times'] = new_service_times
            template_manager.update_template('saturday_reminder', template_config)
            st.success("✅ 时间配置已保存！")
            st.rerun()
    
    with col3:
        if st.button("📋 保存说明配置", type="primary", use_container_width=True, key="save_instruction_config"):
            template_config['service_instructions'] = new_service_instructions
            template_manager.update_template('saturday_reminder', template_config)
            st.success("✅ 说明配置已保存！")
            st.rerun()

def show_standard_template_editor(template_manager, template_config, selected_type):
    """显示标准模板编辑器（用于非周六模板）"""
    # 编辑模板内容
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 主模板内容")
        current_template = template_config.get('template', '')
        new_template = st.text_area(
            "模板内容:",
            value=current_template,
            height=300,
            help="使用 {变量名} 来插入动态内容",
            key=f"template_{selected_type}"
        )
        
        # 验证模板
        is_valid, validation_msg = template_manager.validate_template(selected_type, new_template)
        if is_valid:
            st.success(f"✅ {validation_msg}")
        else:
            st.error(f"❌ {validation_msg}")
    
    with col2:
        st.markdown("#### 可用变量")
        variables = template_manager.get_template_variables(selected_type)
        if variables:
            for var, desc in variables.items():
                st.code(f"{{{var}}}")
                st.caption(desc)
        else:
            st.info("该模板暂无变量说明")
        
        # 模板操作
        st.markdown("#### 操作")
        if st.button("💾 应用更改", type="primary", use_container_width=True):
            if is_valid:
                template_config['template'] = new_template
                template_manager.update_template(selected_type, template_config)
                st.success("✅ 模板更改已应用！")
                st.rerun()
            else:
                st.error("❌ 模板验证失败，无法应用更改")

def show_scripture_management():
    """显示经文管理页面"""
    st.markdown('<div class="section-header">📖 经文分享管理</div>', unsafe_allow_html=True)
    st.markdown("管理周三通知中的经文分享内容，支持添加、编辑、删除和排序")
    
    # 获取经文管理器
    from src.scripture_manager import get_scripture_manager
    scripture_manager = get_scripture_manager()
    
    # 显示当前经文统计
    stats = scripture_manager.get_scripture_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📚 经文总数", stats.get('total_count', 0))
    with col2:
        st.metric("📍 当前位置", stats.get('current_index', 0) + 1)
    with col3:
        next_index = (stats.get('current_index', 0) + 1) % max(stats.get('total_count', 1), 1)
        st.metric("⏭️ 下一位置", next_index + 1)
    with col4:
        if stats.get('last_updated'):
            last_updated = stats['last_updated'][:10] if stats['last_updated'] != 'Unknown' else '未知'
            st.metric("📅 更新日期", last_updated)
        else:
            st.metric("📅 更新日期", "未知")
    
    # 创建标签页
    tab1, tab2, tab3, tab4 = st.tabs(["📝 经文列表", "➕ 添加经文", "🔧 编辑经文", "📊 使用预览"])
    
    with tab1:
        st.markdown("### 📚 当前经文列表")
        
        scriptures = scripture_manager.get_all_scriptures()
        current_index = stats.get('current_index', 0)
        
        if scriptures:
            for i, scripture in enumerate(scriptures):
                # 标记当前经文
                is_current = (i == current_index)
                icon = "👉" if is_current else "📖"
                status = " **(下一个使用)** " if is_current else ""
                
                # 获取经文的第一行作为标题
                content = scripture.get('content', '')
                first_line = content.split('\n')[0] if content else '未知经文'
                if len(first_line) > 20:
                    first_line = first_line[:20] + "..."
                
                with st.expander(f"{icon} {first_line}{status}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown("**经文内容：**")
                        # 显示完整经文内容，保持换行格式
                        content_lines = scripture.get('content', '').split('\n')
                        for line in content_lines:
                            if line.strip():
                                st.markdown(f"> {line}")
                    
                    with col2:
                        st.markdown("**操作**")
                        if st.button("🗑️ 删除", key=f"delete_{scripture.get('id')}", use_container_width=True):
                            if scripture_manager.delete_scripture(scripture.get('id')):
                                st.success("✅ 删除成功！")
                                st.rerun()
                            else:
                                st.error("❌ 删除失败")
        else:
            st.info("📄 暂无经文内容，请添加新经文")
        
        # 管理操作
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 重置索引", use_container_width=True):
                if scripture_manager.reset_index():
                    st.success("✅ 索引已重置到开头")
                    st.rerun()
                else:
                    st.error("❌ 重置失败")
        
        with col2:
            if st.button("⏭️ 跳过当前", use_container_width=True):
                next_scripture = scripture_manager.get_next_scripture()
                if next_scripture:
                    st.success(f"✅ 已跳到: {next_scripture.get('verse', 'Unknown')}")
                    st.rerun()
                else:
                    st.error("❌ 跳过失败")
        
        with col3:
            if st.button("💾 保存配置", use_container_width=True):
                if scripture_manager.save_scriptures():
                    st.success("✅ 配置已保存")
                else:
                    st.error("❌ 保存失败")
    
    with tab2:
        st.markdown("### ➕ 添加新经文")
        
        st.markdown("**格式说明：** 请按以下格式粘贴经文内容：")
        st.code("""看哪，弟兄和睦同居
是何等地善，何等地美！
(诗篇 133:1 和合本)""")
        
        with st.form("add_scripture_form"):
            content = st.text_area(
                "经文内容", 
                placeholder="看哪，弟兄和睦同居\n是何等地善，何等地美！\n(诗篇 133:1 和合本)", 
                height=150,
                help="请粘贴完整的经文内容，包括经文和出处"
            )
            
            submitted = st.form_submit_button("📝 添加经文", type="primary")
            
            if submitted:
                if content.strip():
                    if scripture_manager.add_scripture(content.strip()):
                        st.success("✅ 经文添加成功！")
                        st.rerun()
                    else:
                        st.error("❌ 添加失败，请检查输入")
                else:
                    st.error("❌ 请填写经文内容")
    
    with tab3:
        st.markdown("### 🔧 编辑现有经文")
        
        scriptures = scripture_manager.get_all_scriptures()
        if scriptures:
            # 选择要编辑的经文
            scripture_options = {}
            for s in scriptures:
                content = s.get('content', '')
                first_line = content.split('\n')[0] if content else 'Unknown'
                if len(first_line) > 30:
                    first_line = first_line[:30] + "..."
                scripture_options[f"{s.get('id')}: {first_line}"] = s
            
            selected_key = st.selectbox("选择要编辑的经文", options=list(scripture_options.keys()))
            
            if selected_key:
                selected_scripture = scripture_options[selected_key]
                
                st.markdown("**格式说明：** 请按以下格式编辑经文内容：")
                st.code("""看哪，弟兄和睦同居
是何等地善，何等地美！
(诗篇 133:1 和合本)""")
                
                with st.form("edit_scripture_form"):
                    edit_content = st.text_area(
                        "经文内容", 
                        value=selected_scripture.get('content', ''), 
                        height=150,
                        help="请编辑完整的经文内容，包括经文和出处"
                    )
                    
                    edit_submitted = st.form_submit_button("💾 保存修改", type="primary")
                    
                    if edit_submitted:
                        if edit_content.strip():
                            if scripture_manager.update_scripture(
                                selected_scripture.get('id'), 
                                edit_content.strip()
                            ):
                                st.success("✅ 经文更新成功！")
                                st.rerun()
                            else:
                                st.error("❌ 更新失败")
                        else:
                            st.error("❌ 请填写经文内容")
        else:
            st.info("📄 暂无经文可编辑，请先添加经文")
    
    with tab4:
        st.markdown("### 📊 使用预览")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📖 当前经文预览")
            current_scripture = scripture_manager.get_current_scripture()
            if current_scripture:
                formatted = scripture_manager.format_scripture_for_template(current_scripture)
                st.code(formatted, language=None)
                
                st.markdown("**详细信息：**")
                st.json(current_scripture)
            else:
                st.info("暂无当前经文")
        
        with col2:
            st.markdown("#### 🔮 下一经文预览")
            # 临时获取下一个经文（不更新索引）
            next_index = (stats.get('current_index', 0) + 1) % max(stats.get('total_count', 1), 1)
            scriptures = scripture_manager.get_all_scriptures()
            
            if scriptures and next_index < len(scriptures):
                next_scripture = scriptures[next_index]
                next_formatted = scripture_manager.format_scripture_for_template(next_scripture)
                st.code(next_formatted, language=None)
                
                st.markdown("**详细信息：**")
                st.json(next_scripture)
            else:
                st.info("暂无下一经文")
        
        # 模板集成预览
        st.markdown("---")
        st.markdown("#### 🔧 模板集成预览")
        
        if st.button("🧪 测试周三通知模板", use_container_width=True):
            try:
                # 获取模板管理器
                template_manager = get_template_manager()
                
                # 创建测试数据
                from datetime import date, timedelta
                test_date = date.today() + timedelta(days=7)
                
                from src.models import MinistryAssignment
                test_schedule = MinistryAssignment(
                    date=test_date,
                    audio_tech="Jimmy",
                    video_director="靖铮",
                    propresenter_play="张宇",
                    propresenter_update="Daniel"
                )
                
                # 生成包含经文的通知
                notification = template_manager.render_weekly_confirmation(test_date, test_schedule)
                
                st.markdown("**生成的通知内容：**")
                st.code(notification, language=None)
                
            except Exception as e:
                st.error(f"❌ 测试失败: {e}")
        
        # 显示使用统计
        if stats:
            st.markdown("---")
            st.markdown("#### 📈 使用统计")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("下次使用", f"第 {stats.get('current_index', 0) + 1} 段")
            
            with col2:
                if stats.get('last_updated'):
                    last_updated = stats['last_updated'][:16] if stats['last_updated'] != 'Unknown' else '未知'
                    st.metric("最后更新", last_updated)

# ==================== 应用启动 ====================

if __name__ == "__main__":
    # 确保必要目录存在
    for dir_name in ['calendars', 'data', 'logs']:
        Path(dir_name).mkdir(exist_ok=True)
    
    # 启动应用
    main()
