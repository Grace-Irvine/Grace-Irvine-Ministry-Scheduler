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
from src.data_cleaner import FocusedDataCleaner
from src.template_manager import NotificationTemplateManager
from src.scheduler import GoogleSheetsExtractor, NotificationGenerator, MinistryAssignment
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
        """提供ICS日历文件内容"""
        try:
            calendar_dir = Path("calendars")
            if not calendar_dir.exists():
                return None, "Calendar directory not found"
            
            file_path = calendar_dir / filename
            if not file_path.exists():
                return None, f"Calendar file {filename} not found"
            
            if not filename.endswith('.ics'):
                return None, "Only ICS files are allowed"
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return content, None
            
        except Exception as e:
            return None, f"Error serving calendar file: {str(e)}"
    
    @staticmethod
    def get_calendar_status():
        """获取日历文件状态"""
        try:
            calendar_dir = Path("calendars")
            status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'service': 'Grace Irvine Ministry Scheduler',
                'calendars': {}
            }
            
            if calendar_dir.exists():
                for ics_file in calendar_dir.glob("*.ics"):
                    try:
                        stat = ics_file.stat()
                        with open(ics_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        status['calendars'][ics_file.name] = {
                            'size': f"{stat.st_size / 1024:.1f} KB",
                            'events': content.count("BEGIN:VEVENT"),
                            'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            'valid_ics': content.startswith('BEGIN:VCALENDAR') and content.endswith('END:VCALENDAR')
                        }
                    except Exception as e:
                        status['calendars'][ics_file.name] = {'error': str(e)}
            
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
            sys.executable, 'generate_real_calendars.py'
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

def show_subscription_info():
    """显示订阅信息"""
    st.markdown("### 🔗 日历订阅信息")
    
    # 获取当前URL（在实际部署时需要配置正确的域名）
    base_url = "http://localhost:8501"  # 本地开发
    if 'K_SERVICE' in os.environ:
        # Cloud Run环境
        base_url = os.getenv('CLOUD_RUN_URL', 'https://your-service-url.run.app')
    
    coordinator_url = f"{base_url}/calendars/grace_irvine_coordinator.ics"
    workers_url = f"{base_url}/calendars/grace_irvine_workers.ics"
    
    st.code(f"负责人日历: {coordinator_url}")
    st.code(f"同工日历: {workers_url}")
    
    st.markdown("""
    **📱 订阅方法:**
    1. **Google Calendar**: 左侧"+" → "从URL添加" → 粘贴链接
    2. **Apple Calendar**: "文件" → "新建日历订阅" → 输入URL  
    3. **Outlook**: "添加日历" → "从Internet订阅" → 输入URL
    
    ⚠️ **重要**: 请使用"订阅URL"而不是"导入文件"，这样才能自动更新
    """)

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

def generate_wednesday_template(sunday_date, schedule):
    """生成周三确认通知模板"""
    template = f"""【本周{sunday_date.month}月{sunday_date.day}日主日事工安排提醒】🕊️

"""
    
    assignments = schedule.get_all_assignments() if schedule else {}
    
    if assignments:
        for role, person in assignments.items():
            template += f"• {role}：{person}\n"
    else:
        template += "• 音控：待安排\n• 导播/摄影：待安排\n• ProPresenter播放：待安排\n• ProPresenter更新：待安排\n"
    
    template += """• 视频剪辑：靖铮

请大家确认时间，若有冲突请尽快私信我，感谢摆上 🙏"""
    
    return template

def generate_saturday_template(sunday_date, schedule):
    """生成周六提醒通知模板"""
    template = f"""【主日服事提醒】✨
明天 8:30布置/ 9:00彩排 / 10:00 正式敬拜  
请各位同工提前到场：  

"""
    
    assignments = schedule.get_all_assignments() if schedule else {}
    
    if assignments.get('音控'):
        template += f"- 音控：{assignments['音控']} 9:00到，随敬拜团排练\n"
    else:
        template += "- 音控：待确认 9:00到，随敬拜团排练\n"
    
    if assignments.get('导播/摄影'):
        template += f"- 导播/摄影: {assignments['导播/摄影']} 9:30到，检查预设机位\n"
    else:
        template += "- 导播/摄影: 待确认 9:30到，检查预设机位\n"
    
    if assignments.get('ProPresenter播放'):
        template += f"- ProPresenter播放：{assignments['ProPresenter播放']} 9:00到，随敬拜团排练\n"
    else:
        template += "- ProPresenter播放：待确认 9:00到，随敬拜团排练\n"
    
    template += "\n愿主同在，出入平安。若临时不适请第一时间私信我。🙌"
    
    return template

def generate_monthly_template(schedules):
    """生成月度总览通知模板"""
    today = date.today()
    if today.month == 12:
        next_month = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month + 1, day=1)
    
    next_month_schedules = [
        s for s in schedules 
        if s.date.year == next_month.year and s.date.month == next_month.month
    ]
    
    template = f"""【{next_month.year}年{next_month.month:02d}月事工排班一览】📅
请各位同工先行预留时间，如有冲突尽快与我沟通：

当月安排预览：
"""
    
    if next_month_schedules:
        for schedule in next_month_schedules:
            date_str = schedule.date.strftime('%m/%d')
            template += f"• {date_str}: "
            
            assignments = schedule.get_all_assignments()
            assignment_list = []
            
            if assignments.get('音控'):
                assignment_list.append(f"音控:{assignments['音控']}")
            if assignments.get('导播/摄影'):
                assignment_list.append(f"导播:{assignments['导播/摄影']}")
            if assignments.get('ProPresenter播放'):
                assignment_list.append(f"PPT播放:{assignments['ProPresenter播放']}")
            
            template += ", ".join(assignment_list) if assignment_list else "待安排"
            template += "\n"
    else:
        template += "• 暂无排班数据\n"
    
    template += """
温馨提示：
- 周三晚发布当周安排（确认/调换）
- 周六晚发布主日提醒（到场时间）
感谢大家同心配搭！🙏"""
    
    return template

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

# ==================== 应用启动 ====================

if __name__ == "__main__":
    # 确保必要目录存在
    for dir_name in ['calendars', 'data', 'logs']:
        Path(dir_name).mkdir(exist_ok=True)
    
    # 启动应用
    main()
