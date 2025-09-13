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
            show_ics_events_content()
        
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
