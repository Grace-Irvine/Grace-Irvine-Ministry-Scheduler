#!/usr/bin/env python3
"""
Grace Irvine Ministry Scheduler - Streamlit Web App
恩典尔湾长老教会事工排程管理系统

简洁的 Web 界面，用于：
1. 查看清洗后的数据
2. 生成下周的通知模板
3. 数据质量监控
"""
import streamlit as st
import pandas as pd
import os
from datetime import datetime, date, timedelta
from pathlib import Path
import json
import io
from typing import List, Dict, Any

# 云环境配置（必须在其他导入之前）
try:
    import streamlit_cloud_config  # 自动设置云环境
except ImportError:
    pass

# 导入我们的数据清洗模块
from src.data_cleaner import FocusedDataCleaner
from src.template_manager import NotificationTemplateManager
from src.scheduler import GoogleSheetsExtractor, NotificationGenerator, MinistryAssignment

# 导入ICS日历相关模块
try:
    from src.calendar_subscription_server import CalendarSubscriptionManager
    ICS_AVAILABLE = True
except ImportError:
    ICS_AVAILABLE = False

# 本地环境的环境变量加载
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 页面配置
st.set_page_config(
    page_title="Grace Irvine Ministry Scheduler",
    page_icon="⛪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

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
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem 0;
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
    
    /* 模板编辑器样式 */
    .template-editor-container {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .template-preview {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        line-height: 1.6;
        white-space: pre-wrap;
        max-height: 400px;
        overflow-y: auto;
    }
    
    .template-stats {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .help-section {
        background: #e8f5e8;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

def show_header():
    """显示页面头部"""
    st.markdown("""
    <div class="main-header">
        ⛪ Grace Irvine Ministry Scheduler
        <br><small style="font-size: 1rem; color: #666;">恩典尔湾长老教会事工排程管理系统</small>
    </div>
    """, unsafe_allow_html=True)

def get_spreadsheet_config():
    """获取表格配置"""
    # 从环境变量或默认值获取配置
    default_id = "1wescUQe9rIVLNcKdqmSLpzlAw9BGXMZmkFvjEF296nM"
    
    # 尝试从 .env 文件读取
    try:
        from dotenv import load_dotenv
        load_dotenv()
        spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID', default_id)
    except:
        spreadsheet_id = default_id
    
    return spreadsheet_id

@st.cache_data(ttl=300)  # 缓存5分钟
def load_data():
    """加载和清洗数据"""
    try:
        cleaner = FocusedDataCleaner()
        
        # 下载原始数据
        raw_df = cleaner.download_data()
        
        # 提取指定列
        focused_df = cleaner.extract_focused_columns(raw_df)
        
        # 清洗数据并转换为排程对象
        schedules = cleaner.clean_focused_data(focused_df)
        
        # 转换为 DataFrame 用于显示
        if schedules:
            cleaned_data = []
            for schedule in schedules:
                cleaned_data.append({
                    '日期': schedule.date.strftime('%Y-%m-%d'),
                    '星期': ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][schedule.date.weekday()],
                    '音控': schedule.audio_tech or '',
                    '导播/摄影': schedule.video_director or '',
                    'ProPresenter播放': schedule.propresenter_play or '',
                    'ProPresenter更新': schedule.propresenter_update or ''
                })
            cleaned_df = pd.DataFrame(cleaned_data)
        else:
            cleaned_df = pd.DataFrame()
        
        # 生成汇总报告
        summary_report = cleaner.generate_summary_report(schedules)
        
        return {
            'success': True,
            'raw_data': raw_df,
            'focused_data': focused_df,
            'cleaned_data': cleaned_df,
            'schedules': schedules,
            'summary_report': summary_report,
            'stats': cleaner.stats
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'raw_data': pd.DataFrame(),
            'focused_data': pd.DataFrame(),
            'cleaned_data': pd.DataFrame(),
            'schedules': [],
            'summary_report': {},
            'stats': {}
        }

def show_data_overview(data_result):
    """显示数据概览"""
    st.markdown('<div class="section-header">📊 数据概览 / Data Overview</div>', unsafe_allow_html=True)
    
    if not data_result['success']:
        st.error(f"❌ 数据加载失败: {data_result['error']}")
        st.markdown("""
        <div class="warning-message">
        <strong>故障排除建议:</strong><br>
        1. 检查网络连接<br>
        2. 确认 Google Sheets 为公开访问<br>
        3. 验证 Spreadsheet ID 正确<br>
        4. 检查表格是否有数据
        </div>
        """, unsafe_allow_html=True)
        return
    
    # 数据统计
    stats = data_result['stats']
    summary = data_result['summary_report']
    schedules = data_result['schedules']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📋 总行数",
            value=stats.get('total_rows', 0)
        )
    
    with col2:
        st.metric(
            label="✅ 有效排程",
            value=stats.get('valid_rows', 0)
        )
    
    with col3:
        st.metric(
            label="👥 志愿者总数",
            value=summary.get('volunteer_statistics', {}).get('total_volunteers', 0)
        )
    
    with col4:
        st.metric(
            label="🧹 清洗人名",
            value=stats.get('cleaned_names', 0)
        )
    
    # 角色统计
    if summary.get('role_statistics'):
        st.markdown("### 🎯 角色统计")
        role_stats = summary['role_statistics']
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🎤 音控", role_stats.get('音控', 0))
            st.metric("📹 导播/摄影", role_stats.get('导播/摄影', 0))
        
        with col2:
            st.metric("🖥️ ProPresenter播放", role_stats.get('ProPresenter播放', 0))
            st.metric("🔄 ProPresenter更新", role_stats.get('ProPresenter更新', 0))
    
    # 周程安排概览
    if schedules:
        show_weekly_schedule_overview(schedules)
    
    # 日期范围
    if summary.get('date_range'):
        st.info(f"📅 **数据范围**: {summary['date_range']}")
    
    # 数据质量检查
    if stats.get('invalid_dates', 0) > 0:
        st.warning(f"⚠️ 发现 {stats['invalid_dates']} 个无效日期")
    else:
        st.success("✅ 数据质量良好，日期格式正确")

def get_sunday_of_week(target_date):
    """获取指定日期所在周的周日日期"""
    days_since_sunday = target_date.weekday() + 1  # Monday=0 -> 1, Sunday=6 -> 0
    if days_since_sunday == 7:  # 如果是周日
        days_since_sunday = 0
    return target_date - timedelta(days=days_since_sunday)

def show_weekly_schedule_overview(schedules):
    """显示周程安排概览"""
    st.markdown("### 📅 周程安排概览")
    
    # 获取当前日期和相关周日
    today = date.today()
    current_sunday = get_sunday_of_week(today)
    
    # 计算目标周日期（前两周到未来几周）
    target_sundays = []
    for i in range(-2, 8):  # 前2周 + 当前周 + 未来7周 = 10周
        sunday = current_sunday + timedelta(weeks=i)
        target_sundays.append(sunday)
    
    # 按周日分组排程数据
    schedule_by_sunday = {}
    for schedule in schedules:
        sunday = get_sunday_of_week(schedule.date)
        if sunday in target_sundays:
            schedule_by_sunday[sunday] = schedule
    
    # 显示周程概览表格
    overview_data = []
    for sunday in target_sundays:
        week_label = get_week_label(sunday, today)
        schedule = schedule_by_sunday.get(sunday)
        
        if schedule:
            assignments = schedule.get_all_assignments()
            row = {
                '周次': week_label,
                '日期': sunday.strftime('%Y-%m-%d'),
                '音控': assignments.get('音控', ''),
                '导播/摄影': assignments.get('导播/摄影', ''),
                'ProPresenter播放': assignments.get('ProPresenter播放', ''),
                'ProPresenter更新': assignments.get('ProPresenter更新', ''),
                '状态': get_schedule_status(sunday, today)
            }
        else:
            row = {
                '周次': week_label,
                '日期': sunday.strftime('%Y-%m-%d'),
                '音控': '',
                '导播/摄影': '',
                'ProPresenter播放': '',
                'ProPresenter更新': '',
                '状态': '暂无安排'
            }
        
        overview_data.append(row)
    
    # 创建 DataFrame 并显示
    if overview_data:
        df_overview = pd.DataFrame(overview_data)
        
        # 使用 Streamlit 的表格显示，带有条件格式
        st.dataframe(
            df_overview,
            use_container_width=True,
            height=400,
            column_config={
                '周次': st.column_config.TextColumn('周次', width='medium'),
                '日期': st.column_config.DateColumn('日期', format='YYYY-MM-DD'),
                '音控': st.column_config.TextColumn('🎤 音控'),
                '导播/摄影': st.column_config.TextColumn('📹 导播/摄影'),
                'ProPresenter播放': st.column_config.TextColumn('🖥️ PP播放'),
                'ProPresenter更新': st.column_config.TextColumn('🔄 PP更新'),
                '状态': st.column_config.TextColumn('状态', width='small')
            }
        )
        
        # 显示统计信息
        col1, col2, col3 = st.columns(3)
        
        with col1:
            arranged_weeks = sum(1 for row in overview_data if any([
                row['音控'], row['导播/摄影'], row['ProPresenter播放'], row['ProPresenter更新']
            ]))
            st.metric("📋 已安排周数", f"{arranged_weeks}/{len(overview_data)}")
        
        with col2:
            past_weeks = sum(1 for row in overview_data if row['状态'] == '已完成')
            st.metric("✅ 已完成", past_weeks)
        
        with col3:
            future_weeks = sum(1 for row in overview_data if row['状态'] in ['本周', '未来'])
            st.metric("📅 待进行", future_weeks)
        
        # 显示重点提醒
        show_schedule_alerts(overview_data, today)

def get_week_label(sunday, today):
    """获取周次标签"""
    current_sunday = get_sunday_of_week(today)
    week_diff = (sunday - current_sunday).days // 7
    
    if week_diff == -2:
        return "前两周"
    elif week_diff == -1:
        return "上周"
    elif week_diff == 0:
        return "本周"
    elif week_diff == 1:
        return "下周"
    elif week_diff == 2:
        return "下下周"
    elif week_diff > 2:
        return f"未来第{week_diff}周"
    else:
        return f"过去第{abs(week_diff)}周"

def get_schedule_status(sunday, today):
    """获取排程状态"""
    if sunday < get_sunday_of_week(today):
        return "已完成"
    elif sunday == get_sunday_of_week(today):
        return "本周"
    else:
        return "未来"

def show_schedule_alerts(overview_data, today):
    """显示排程提醒"""
    alerts = []
    
    # 检查未安排的周次
    unscheduled = [row for row in overview_data if row['状态'] == '暂无安排' and row['状态'] != '已完成']
    if unscheduled:
        alert_dates = [row['日期'] for row in unscheduled[:3]]  # 只显示前3个
        alerts.append(f"⚠️ 发现 {len(unscheduled)} 个未安排的周次: {', '.join(alert_dates)}")
    
    # 检查本周和下周的安排
    this_week = next((row for row in overview_data if row['周次'] == '本周'), None)
    next_week = next((row for row in overview_data if row['周次'] == '下周'), None)
    
    if this_week and not any([this_week['音控'], this_week['导播/摄影'], this_week['ProPresenter播放']]):
        alerts.append("🚨 本周主日暂无完整安排，请尽快确认！")
    
    if next_week and not any([next_week['音控'], next_week['导播/摄影'], next_week['ProPresenter播放']]):
        alerts.append("⏰ 下周主日安排不完整，建议提前准备")
    
    # 检查人员重复安排
    for row in overview_data:
        assignments = [row['音控'], row['导播/摄影'], row['ProPresenter播放'], row['ProPresenter更新']]
        assignments = [a for a in assignments if a]  # 移除空值
        if len(assignments) != len(set(assignments)):  # 有重复
            duplicates = [a for a in set(assignments) if assignments.count(a) > 1]
            alerts.append(f"👥 {row['日期']} 发现重复安排: {', '.join(duplicates)}")
    
    # 显示提醒
    if alerts:
        st.markdown("### 🔔 重要提醒")
        for alert in alerts:
            if "🚨" in alert:
                st.error(alert)
            elif "⏰" in alert:
                st.warning(alert)
            else:
                st.info(alert)
    else:
        st.success("✅ 排程安排良好，暂无需要特别关注的问题")

def show_nearby_schedule_preview(data_result):
    """显示当前日期附近的排程预览"""
    st.markdown("### 📋 近期排程预览")
    
    schedules = data_result['schedules']
    if not schedules:
        st.info("暂无排程数据")
        return
    
    today = date.today()
    
    # 获取当前日期前后4周的数据（共8周）
    start_date = today - timedelta(weeks=2)
    end_date = today + timedelta(weeks=6)
    
    # 过滤近期数据
    nearby_schedules = [
        s for s in schedules 
        if start_date <= s.date <= end_date
    ]
    
    if not nearby_schedules:
        st.warning("未找到近期的排程数据")
        return
    
    # 转换为显示格式
    preview_data = []
    for schedule in sorted(nearby_schedules, key=lambda x: x.date):
        # 确定状态和样式
        if schedule.date < today:
            status = "已完成"
            status_emoji = "✅"
        elif schedule.date == today:
            status = "今天"
            status_emoji = "📍"
        elif schedule.date <= today + timedelta(days=7):
            status = "本周"
            status_emoji = "🔥"
        elif schedule.date <= today + timedelta(days=14):
            status = "下周"
            status_emoji = "⏰"
        else:
            status = "未来"
            status_emoji = "📅"
        
        assignments = schedule.get_all_assignments()
        
        preview_data.append({
            '状态': f"{status_emoji} {status}",
            '日期': schedule.date.strftime('%Y-%m-%d'),
            '星期': ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][schedule.date.weekday()],
            '音控': assignments.get('音控', ''),
            '导播/摄影': assignments.get('导播/摄影', ''),
            'ProPresenter播放': assignments.get('ProPresenter播放', ''),
            'ProPresenter更新': assignments.get('ProPresenter更新', ''),
        })
    
    # 创建 DataFrame 并显示
    df_preview = pd.DataFrame(preview_data)
    
    # 使用 Streamlit 的数据编辑器显示，支持条件格式
    st.dataframe(
        df_preview,
        use_container_width=True,
        height=min(400, len(preview_data) * 35 + 100),  # 动态高度
        column_config={
            '状态': st.column_config.TextColumn('状态', width='small'),
            '日期': st.column_config.DateColumn('日期', format='YYYY-MM-DD'),
            '星期': st.column_config.TextColumn('星期', width='small'),
            '音控': st.column_config.TextColumn('🎤 音控'),
            '导播/摄影': st.column_config.TextColumn('📹 导播/摄影'),
            'ProPresenter播放': st.column_config.TextColumn('🖥️ PP播放'),
            'ProPresenter更新': st.column_config.TextColumn('🔄 PP更新'),
        }
    )
    
    # 显示预览统计
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        completed_count = sum(1 for item in preview_data if '已完成' in item['状态'])
        st.metric("✅ 已完成", completed_count)
    
    with col2:
        current_count = sum(1 for item in preview_data if '今天' in item['状态'] or '本周' in item['状态'])
        st.metric("🔥 当前", current_count)
    
    with col3:
        upcoming_count = sum(1 for item in preview_data if '下周' in item['状态'])
        st.metric("⏰ 下周", upcoming_count)
    
    with col4:
        future_count = sum(1 for item in preview_data if '未来' in item['状态'])
        st.metric("📅 未来", future_count)
    
    # 显示重点关注
    show_preview_highlights(preview_data, today)

def show_preview_highlights(preview_data, today):
    """显示预览重点信息"""
    highlights = []
    
    # 检查今天和本周的安排
    today_items = [item for item in preview_data if '今天' in item['状态']]
    this_week_items = [item for item in preview_data if '本周' in item['状态']]
    next_week_items = [item for item in preview_data if '下周' in item['状态']]
    
    if today_items:
        for item in today_items:
            if any([item['音控'], item['导播/摄影'], item['ProPresenter播放']]):
                highlights.append(f"📍 **今天主日**: {item['音控'] or '待定'} (音控), {item['导播/摄影'] or '待定'} (导播)")
            else:
                highlights.append("🚨 **今天主日暂无完整安排**")
    
    if this_week_items:
        for item in this_week_items:
            if not any([item['音控'], item['导播/摄影'], item['ProPresenter播放']]):
                highlights.append(f"⚠️ **{item['日期']} 本周主日安排不完整**")
    
    if next_week_items:
        incomplete_next_week = [item for item in next_week_items 
                               if not any([item['音控'], item['导播/摄影'], item['ProPresenter播放']])]
        if incomplete_next_week:
            dates = [item['日期'] for item in incomplete_next_week]
            highlights.append(f"⏰ **下周需要关注**: {', '.join(dates)}")
    
    # 检查人员重复
    for item in preview_data:
        if item['状态'] not in ['✅ 已完成']:  # 只检查未完成的
            assignments = [item['音控'], item['导播/摄影'], item['ProPresenter播放'], item['ProPresenter更新']]
            assignments = [a for a in assignments if a]  # 移除空值
            if len(assignments) != len(set(assignments)):  # 有重复
                duplicates = [a for a in set(assignments) if assignments.count(a) > 1]
                highlights.append(f"👥 **{item['日期']}** 重复安排: {', '.join(duplicates)}")
    
    # 显示重点信息
    if highlights:
        st.markdown("#### 🔔 重点关注")
        for highlight in highlights[:5]:  # 最多显示5个重点
            if "🚨" in highlight:
                st.error(highlight)
            elif "⚠️" in highlight or "⏰" in highlight:
                st.warning(highlight)
            elif "👥" in highlight:
                st.info(highlight)
            else:
                st.success(highlight)
    else:
        st.success("✅ 近期排程安排良好")

def show_data_viewer(data_result):
    """显示数据查看器"""
    st.markdown('<div class="section-header">🔍 数据查看器 / Data Viewer</div>', unsafe_allow_html=True)
    
    if not data_result['success']:
        st.info("请先成功加载数据")
        return
    
    cleaned_df = data_result['cleaned_data']
    
    if cleaned_df.empty:
        st.warning("没有可显示的数据")
        return
    
    # 数据过滤选项
    col1, col2 = st.columns(2)
    
    with col1:
        # 日期范围过滤
        date_columns = [col for col in cleaned_df.columns if 'date' in col.lower() or '日期' in col or 'parsed' in col.lower()]
        if date_columns:
            date_col = date_columns[0]
            if cleaned_df[date_col].notna().any():
                min_date = pd.to_datetime(cleaned_df[date_col].dropna()).min().date()
                max_date = pd.to_datetime(cleaned_df[date_col].dropna()).max().date()
                
                selected_start = st.date_input("开始日期", value=min_date, min_value=min_date, max_value=max_date)
                selected_end = st.date_input("结束日期", value=max_date, min_value=min_date, max_value=max_date)
                
                # 应用日期过滤
                mask = (pd.to_datetime(cleaned_df[date_col]) >= pd.to_datetime(selected_start)) & \
                       (pd.to_datetime(cleaned_df[date_col]) <= pd.to_datetime(selected_end))
                filtered_df = cleaned_df[mask]
            else:
                filtered_df = cleaned_df
        else:
            filtered_df = cleaned_df
    
    with col2:
        # 显示行数限制
        max_rows = st.slider("显示行数", min_value=10, max_value=min(500, len(filtered_df)), value=min(50, len(filtered_df)))
        filtered_df = filtered_df.head(max_rows)
    
    # 显示数据表格
    st.dataframe(
        filtered_df,
        use_container_width=True,
        height=400
    )
    
    # 数据下载
    col1, col2 = st.columns(2)
    
    with col1:
        # Excel 下载
        excel_buffer = io.BytesIO()
        filtered_df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)
        
        st.download_button(
            label="📥 下载 Excel 文件",
            data=excel_buffer,
            file_name=f"grace_irvine_schedule_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    with col2:
        # CSV 下载
        csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 下载 CSV 文件",
            data=csv,
            file_name=f"grace_irvine_schedule_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

def generate_next_week_template(data_result):
    """生成下周通知模板"""
    st.markdown('<div class="section-header">📝 下周通知模板生成器 / Next Week Template Generator</div>', unsafe_allow_html=True)
    
    if not data_result['success']:
        st.info("请先成功加载数据")
        return
    
    schedules = data_result['schedules']
    
    if not schedules:
        st.warning("没有可用的数据生成模板")
        return
    
    # 获取下周日期
    today = date.today()
    days_until_sunday = (6 - today.weekday()) % 7
    if days_until_sunday == 0:  # 如果今天是周日
        days_until_sunday = 7
    next_sunday = today + timedelta(days=days_until_sunday)
    
    st.info(f"📅 下周主日日期: {next_sunday.strftime('%Y年%m月%d日')}")
    
    # 查找下周的数据
    next_week_schedule = None
    for schedule in schedules:
        if schedule.date == next_sunday:
            next_week_schedule = schedule
            break
    
    if not next_week_schedule:
        st.warning(f"未找到 {next_sunday.strftime('%Y年%m月%d日')} 的排程数据")
        
        # 显示可用的日期供参考
        available_dates = sorted([s.date for s in schedules if s.date >= today])
        
        if available_dates:
            st.info("📋 可用的日期:")
            for d in available_dates[:10]:  # 只显示前10个
                st.text(f"  • {d.strftime('%Y年%m月%d日')}")
        return
    
    # 生成模板选择
    template_type = st.selectbox(
        "选择通知模板类型",
        ["周三确认通知", "周六提醒通知", "月度总览通知"]
    )
    
    if template_type == "周三确认通知":
        template = generate_wednesday_template_focused(next_sunday, next_week_schedule)
    elif template_type == "周六提醒通知":
        template = generate_saturday_template_focused(next_sunday, next_week_schedule)
    else:
        template = generate_monthly_template_focused(schedules)
    
    # 显示生成的模板
    st.markdown("### 📋 生成的通知模板")
    st.text_area(
        "复制以下内容到微信群:",
        value=template,
        height=300,
        key="template_output"
    )
    
    # 操作按钮
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 保存模板到文件
        if st.button("💾 保存模板到文件", use_container_width=True):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"notification_template_{timestamp}.txt"
            filepath = PROJECT_ROOT / "data" / filename
            
            # 确保目录存在
            filepath.parent.mkdir(exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(template)
            
            st.success(f"✅ 模板已保存到: {filepath}")
    
    with col2:
        # 发送邮件按钮
        if st.button("📧 发送到邮箱", type="primary", use_container_width=True):
            send_template_email(template, template_type, next_sunday if template_type != "月度总览通知" else None)
    
    with col3:
        # 复制到剪贴板提示
        if st.button("📋 复制提示", use_container_width=True):
            st.info("💡 请手动选择上方文本框中的内容进行复制")

def generate_wednesday_template_focused(sunday_date, schedule):
    """生成周三确认通知模板 - 专注版"""
    template = f"""【本周{sunday_date.month}月{sunday_date.day}日主日事工安排提醒】🕊️

"""
    
    # 添加事工安排
    assignments = schedule.get_all_assignments()
    if assignments:
        for role, person in assignments.items():
            template += f"• {role}：{person}\n"
    else:
        template += "• 音控：待安排\n• 导播/摄影：待安排\n• ProPresenter播放：待安排\n• ProPresenter更新：待安排\n"
    
    template += """• 视频剪辑：靖铮

请大家确认时间，若有冲突请尽快私信我，感谢摆上 🙏"""
    
    return template

def generate_saturday_template_focused(sunday_date, schedule):
    """生成周六提醒通知模板 - 专注版"""
    template = f"""【主日服事提醒】✨
明天 8:30布置/ 9:00彩排 / 10:00 正式敬拜  
请各位同工提前到场：  

"""
    
    assignments = schedule.get_all_assignments()
    
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
    
    if assignments.get('ProPresenter更新'):
        template += f"- ProPresenter更新：{assignments['ProPresenter更新']} 提前准备内容\n"
    else:
        template += "- ProPresenter更新：待确认 提前准备内容\n"
    
    template += "\n愿主同在，出入平安。若临时不适请第一时间私信我。🙌"
    
    return template

def generate_monthly_template_focused(schedules):
    """生成月度总览通知模板 - 专注版"""
    # 获取下个月的数据
    today = date.today()
    if today.month == 12:
        next_month = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month + 1, day=1)
    
    # 过滤下个月的数据
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
            if assignments.get('ProPresenter更新'):
                assignment_list.append(f"PPT更新:{assignments['ProPresenter更新']}")
            
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

def generate_wednesday_template(sunday_date, row, name_columns):
    """生成周三确认通知模板"""
    # 提取人名信息
    assignments = {}
    for col in name_columns:
        if pd.notna(row[col]) and str(row[col]).strip():
            # 根据列名推断角色
            original_col = col.replace('_cleaned', '')
            if '音控' in original_col or 'sound' in original_col.lower():
                assignments['音控'] = str(row[col]).strip()
            elif '导播' in original_col or '摄影' in original_col or 'video' in original_col.lower():
                assignments['摄像/导播'] = str(row[col]).strip()
            elif '司琴' in original_col or 'piano' in original_col.lower():
                assignments['司琴'] = str(row[col]).strip()
            elif '敬拜' in original_col and '带领' in original_col:
                assignments['敬拜带领'] = str(row[col]).strip()
            elif 'propresenter' in original_col.lower() or '投影' in original_col:
                assignments['ProPresenter'] = str(row[col]).strip()
    
    template = f"""【本周{sunday_date.month}月{sunday_date.day}日主日事工安排提醒】🕊️

"""
    
    # 添加事工安排
    if assignments:
        for role, person in assignments.items():
            template += f"• {role}：{person}\n"
    else:
        template += "• 音控：待安排\n• 摄像/导播：待安排\n• ProPresenter：待安排\n"
    
    template += """• 视频剪辑：靖铮

请大家确认时间，若有冲突请尽快私信我，感谢摆上 🙏"""
    
    return template

def generate_saturday_template(sunday_date, row, name_columns):
    """生成周六提醒通知模板"""
    # 提取人名信息
    assignments = {}
    for col in name_columns:
        if pd.notna(row[col]) and str(row[col]).strip():
            original_col = col.replace('_cleaned', '')
            if '音控' in original_col:
                assignments['音控'] = str(row[col]).strip()
            elif '导播' in original_col or '摄影' in original_col:
                assignments['摄像/导播'] = str(row[col]).strip()
            elif 'propresenter' in original_col.lower() or '投影' in original_col:
                assignments['ProPresenter'] = str(row[col]).strip()
    
    template = f"""【主日服事提醒】✨
明天 8:30布置/ 9:00彩排 / 10:00 正式敬拜  
请各位同工提前到场：  

"""
    
    if assignments.get('音控'):
        template += f"- 音控：{assignments['音控']} 9:00到，随敬拜团排练\n"
    else:
        template += "- 音控：待确认 9:00到，随敬拜团排练\n"
    
    if assignments.get('ProPresenter'):
        template += f"- ProPresenter：{assignments['ProPresenter']} 9:00到，随敬拜团排练\n"
    else:
        template += "- ProPresenter：待确认 9:00到，随敬拜团排练\n"
    
    if assignments.get('摄像/导播'):
        template += f"- 摄像/导播: {assignments['摄像/导播']} 9:30到，检查预设机位\n"
    else:
        template += "- 摄像/导播: 待确认 9:30到，检查预设机位\n"
    
    template += "\n愿主同在，出入平安。若临时不适请第一时间私信我。🙌"
    
    return template

def generate_monthly_template(df, date_col):
    """生成月度总览通知模板"""
    # 获取下个月的数据
    today = date.today()
    if today.month == 12:
        next_month = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month + 1, day=1)
    
    # 过滤下个月的数据
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    next_month_data = df[
        (df[date_col].dt.year == next_month.year) & 
        (df[date_col].dt.month == next_month.month)
    ]
    
    template = f"""【{next_month.year}年{next_month.month:02d}月事工排班一览】📅
请各位同工先行预留时间，如有冲突尽快与我沟通：

当月安排预览：
"""
    
    if not next_month_data.empty:
        for _, row in next_month_data.iterrows():
            date_str = pd.to_datetime(row[date_col]).strftime('%m/%d')
            template += f"• {date_str}: "
            
            # 提取人名信息
            assignments = []
            name_columns = [col for col in df.columns if 'cleaned' in col.lower()]
            for col in name_columns:
                if pd.notna(row[col]) and str(row[col]).strip():
                    original_col = col.replace('_cleaned', '')
                    if '音控' in original_col:
                        assignments.append(f"音控:{row[col]}")
                    elif '导播' in original_col or '摄影' in original_col:
                        assignments.append(f"摄像:{row[col]}")
                    elif 'propresenter' in original_col.lower():
                        assignments.append(f"PPT:{row[col]}")
            
            template += ", ".join(assignments) if assignments else "待安排"
            template += "\n"
    else:
        template += "• 暂无排班数据\n"
    
    template += """
温馨提示：
- 周三晚发布当周安排（确认/调换）
- 周六晚发布主日提醒（到场时间）
感谢大家同心配搭！🙏"""
    
    return template

def show_settings():
    """显示设置页面"""
    st.markdown('<div class="section-header">⚙️ 系统设置 / Settings</div>', unsafe_allow_html=True)
    
    # Google Sheets 配置
    st.subheader("📊 Google Sheets 配置")
    
    current_id = get_spreadsheet_config()
    new_id = st.text_input(
        "Spreadsheet ID",
        value=current_id,
        help="从 Google Sheets URL 中提取的 ID"
    )
    
    if new_id != current_id:
        st.info("💡 要保存新的 Spreadsheet ID，请在项目根目录创建 .env 文件并添加: GOOGLE_SPREADSHEET_ID=your_id_here")
    
    # 测试连接
    if st.button("🔗 测试 Google Sheets 连接"):
        with st.spinner("正在测试连接..."):
            try:
                cleaner = SimpleDataCleaner(new_id)
                df = cleaner.download_data()
                if not df.empty:
                    st.success(f"✅ 连接成功！找到 {len(df)} 行数据")
                else:
                    st.warning("⚠️ 连接成功，但表格为空")
            except Exception as e:
                st.error(f"❌ 连接失败: {str(e)}")
    
    # 数据清理设置
    st.subheader("🧹 数据清理设置")
    
    st.markdown("""
    <div class="info-box">
    <strong>自动清理规则:</strong><br>
    • 移除空白行和无效数据<br>
    • 标准化人名格式<br>
    • 解析多种日期格式<br>
    • 去除重复记录
    </div>
    """, unsafe_allow_html=True)
    
    # 缓存管理
    st.subheader("💾 缓存管理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 清除数据缓存"):
            st.cache_data.clear()
            st.success("✅ 缓存已清除")
    
    with col2:
        if st.button("📊 查看缓存状态"):
            st.info("数据缓存有效期: 5分钟")

def main():
    """主函数"""
    load_css()
    show_header()
    
    # 侧边栏导航
    with st.sidebar:
        st.markdown("### 🧭 导航菜单")
        
        # 处理页面重定向
        if 'page_redirect' in st.session_state:
            default_page = st.session_state.page_redirect
            del st.session_state.page_redirect
        else:
            default_page = "📊 数据概览"
        
        page_options = ["📊 数据概览", "🔍 数据查看器", "📝 模板生成器", "🛠️ 模板编辑器", "📅 ICS日历管理", "⚙️ 系统设置"]
        default_index = page_options.index(default_page) if default_page in page_options else 0
        
        page = st.selectbox(
            "选择页面",
            page_options,
            index=default_index
        )
        
        st.markdown("---")
        
        # 快速操作
        st.markdown("### ⚡ 快速操作")
        
        if st.button("🔄 刷新数据", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        if st.button("🛠️ 快速编辑模板", use_container_width=True):
            st.session_state.page_redirect = "🛠️ 模板编辑器"
            st.rerun()
        
        st.markdown("---")
        
        # 系统信息
        st.markdown("### ℹ️ 系统信息")
        st.text(f"版本: v1.0.0")
        st.text(f"更新: {datetime.now().strftime('%Y-%m-%d')}")
    
    # 加载数据
    with st.spinner("正在加载数据..."):
        data_result = load_data()
    
    # 根据选择的页面显示内容
    if page == "📊 数据概览":
        show_data_overview(data_result)
        
        # 如果数据加载成功，显示当前日期附近的数据
        if data_result['success'] and not data_result['cleaned_data'].empty:
            show_nearby_schedule_preview(data_result)
    
    elif page == "🔍 数据查看器":
        show_data_viewer(data_result)
    
    elif page == "📝 模板生成器":
        generate_next_week_template(data_result)
    
    elif page == "🛠️ 模板编辑器":
        show_template_editor()
    
    elif page == "📅 ICS日历管理":
        show_ics_calendar_management(data_result)
    
    elif page == "⚙️ 系统设置":
        show_settings()
    
    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        Grace Irvine Ministry Scheduler v1.0 | 
        Made with ❤️ for Grace Irvine Presbyterian Church
    </div>
    """, unsafe_allow_html=True)

def show_template_editor():
    """显示模板编辑器页面"""
    st.markdown('<div class="section-header">🛠️ 通知模板编辑器</div>', unsafe_allow_html=True)
    st.markdown("通过可视化界面编辑和管理微信群通知模板")
    
    # 初始化模板管理器
    if 'template_manager' not in st.session_state:
        st.session_state.template_manager = NotificationTemplateManager()
    
    template_manager = st.session_state.template_manager
    
    # 创建选项卡布局
    tab1, tab2, tab3 = st.tabs(["📝 编辑模板", "👁️ 预览效果", "🧪 真实测试"])
    
    with tab1:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # 模板类型选择
            template_types = {
                'weekly_confirmation': '📅 周三确认通知',
                'sunday_reminder': '🔔 周六提醒通知',
                'monthly_overview': '📊 月度总览通知'
            }
            
            selected_template = st.selectbox(
                "选择要编辑的模板:",
                options=list(template_types.keys()),
                format_func=lambda x: template_types[x],
                key="template_selector"
            )
            
            # 获取当前模板配置
            template_config = template_manager.templates.get(selected_template, {})
            
            # 编辑主模板
            st.markdown("#### 主模板内容")
            current_template = template_config.get('template', '')
            new_template = st.text_area(
                "模板内容:",
                value=current_template,
                height=250,
                help="使用 {变量名} 来插入动态内容，如 {audio_tech}、{month}、{day} 等",
                key=f"main_template_{selected_template}"
            )
            
            # 编辑无安排模板
            if selected_template in ['weekly_confirmation', 'sunday_reminder']:
                st.markdown("#### 无安排时的模板")
                current_no_assignment = template_config.get('no_assignment_template', '')
                new_no_assignment = st.text_area(
                    "无安排模板内容:",
                    value=current_no_assignment,
                    height=120,
                    key=f"no_assignment_template_{selected_template}"
                )
        
        with col2:
            # 默认值设置
            st.markdown("#### 默认值设置")
            defaults = template_config.get('defaults', {})
            new_defaults = {}
            
            if selected_template in ['weekly_confirmation', 'sunday_reminder']:
                default_fields = {
                    'audio_tech': '音控',
                    'screen_operator': '屏幕操作',
                    'camera_operator': '摄像/导播',
                    'propresenter': 'ProPresenter制作',
                    'video_editor': '视频剪辑'
                }
                
                for key, label in default_fields.items():
                    new_defaults[key] = st.text_input(
                        f"{label}默认值:",
                        value=defaults.get(key, '待安排'),
                        key=f"default_{key}_{selected_template}"
                    )
            
            # 操作按钮
            st.markdown("#### 操作")
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("📝 应用更改", type="primary", use_container_width=True):
                    template_manager.set_template(selected_template, 'template', new_template)
                    if selected_template in ['weekly_confirmation', 'sunday_reminder']:
                        template_manager.set_template(selected_template, 'no_assignment_template', new_no_assignment)
                        template_manager.templates[selected_template]['defaults'] = new_defaults
                    st.success("✅ 更改已应用!")
                    st.rerun()
            
            with col_btn2:
                if st.button("💾 保存到文件", use_container_width=True):
                    if template_manager.save_templates():
                        st.success("✅ 模板已保存到文件!")
                    else:
                        st.error("❌ 保存失败!")
    
    with tab2:
        st.markdown("### 👁️ 模板预览")
        
        # 创建测试数据
        test_assignment = MinistryAssignment(
            date=date.today() + timedelta(days=3),
            audio_tech="Jimmy",
            screen_operator="张三",
            camera_operator="李四",
            propresenter="王五",
            video_editor="靖铮"
        )
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### 有安排时的效果")
            try:
                if selected_template == 'weekly_confirmation':
                    preview = template_manager.render_weekly_confirmation(test_assignment)
                elif selected_template == 'sunday_reminder':
                    preview = template_manager.render_sunday_reminder(test_assignment)
                elif selected_template == 'monthly_overview':
                    preview = template_manager.render_monthly_overview(
                        [test_assignment], 
                        test_assignment.date.year, 
                        test_assignment.date.month,
                        "https://docs.google.com/spreadsheets/d/example"
                    )
                
                st.code(preview, language=None)
                
            except Exception as e:
                st.error(f"❌ 预览生成失败: {e}")
        
        with col2:
            # 无安排预览
            if selected_template in ['weekly_confirmation', 'sunday_reminder']:
                st.markdown("#### 无安排时的效果")
                try:
                    if selected_template == 'weekly_confirmation':
                        no_assignment_preview = template_manager.render_weekly_confirmation(None)
                    else:
                        no_assignment_preview = template_manager.render_sunday_reminder(None)
                    
                    st.code(no_assignment_preview, language=None)
                except Exception as e:
                    st.error(f"❌ 无安排预览生成失败: {e}")
            else:
                st.markdown("#### 变量说明")
                if selected_template == 'monthly_overview':
                    st.markdown("""
                    **可用变量:**
                    - `{year}` - 年份
                    - `{month}` - 月份
                    - `{sheet_url}` - Google Sheets链接
                    - `{schedule_text}` - 自动生成的安排列表
                    """)
                else:
                    st.markdown("""
                    **可用变量:**
                    - `{month}` - 月份
                    - `{day}` - 日期
                    - `{audio_tech}` - 音控人员
                    - `{screen_operator}` - 屏幕操作人员
                    - `{camera_operator}` - 摄像/导播人员
                    - `{propresenter}` - ProPresenter制作人员
                    - `{video_editor}` - 视频剪辑人员
                    """)
    
    with tab3:
        st.markdown("### 🧪 真实数据测试")
        
        # 尝试连接Google Sheets进行真实测试
        spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
        if spreadsheet_id:
            try:
                with st.spinner("正在连接Google Sheets..."):
                    extractor = GoogleSheetsExtractor(spreadsheet_id)
                    generator = NotificationGenerator(extractor, template_manager)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("#### 📅 周三确认通知")
                    weekly_msg = generator.generate_weekly_confirmation()
                    st.code(weekly_msg, language=None)
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("📋 复制提示", key="copy_weekly"):
                            st.info("请手动复制上面的内容")
                    with col_btn2:
                        if st.button("📧 发送邮件", key="email_weekly", type="primary"):
                            send_template_email(weekly_msg, "周三确认通知")
                
                with col2:
                    st.markdown("#### 🔔 周六提醒通知")
                    sunday_msg = generator.generate_sunday_reminder()
                    st.code(sunday_msg, language=None)
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("📋 复制提示", key="copy_sunday"):
                            st.info("请手动复制上面的内容")
                    with col_btn2:
                        if st.button("📧 发送邮件", key="email_sunday", type="primary"):
                            send_template_email(sunday_msg, "周六提醒通知")
                
                with col3:
                    st.markdown("#### 📊 月度总览通知")
                    monthly_msg = generator.generate_monthly_overview()
                    st.code(monthly_msg, language=None)
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("📋 复制提示", key="copy_monthly"):
                            st.info("请手动复制上面的内容")
                    with col_btn2:
                        if st.button("📧 发送邮件", key="email_monthly", type="primary"):
                            send_template_email(monthly_msg, "月度总览通知")
                
                # 显示数据统计
                st.markdown("---")
                st.markdown("#### 📊 数据统计")
                
                current_assignment = extractor.get_current_week_assignment()
                next_assignment = extractor.get_next_sunday_assignment()
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("本周安排", "有安排" if current_assignment else "无安排")
                
                with col2:
                    st.metric("下周安排", "有安排" if next_assignment else "无安排")
                
                with col3:
                    if current_assignment:
                        roles_count = sum([1 for role in [current_assignment.audio_tech, current_assignment.screen_operator, 
                                         current_assignment.camera_operator, current_assignment.propresenter] if role])
                        st.metric("本周服事人数", roles_count)
                    else:
                        st.metric("本周服事人数", 0)
                
                with col4:
                    monthly_assignments = extractor.get_monthly_assignments()
                    st.metric("本月总安排", len(monthly_assignments))
                
            except Exception as e:
                st.error(f"❌ 连接Google Sheets失败: {e}")
                st.info("💡 请确保已正确配置Google Sheets访问权限")
                st.code(f"错误详情: {str(e)}")
        else:
            st.warning("⚠️ 未设置GOOGLE_SPREADSHEET_ID环境变量")
            st.info("请在.env文件中配置Google Sheets ID以使用真实数据测试功能")
    
    # 帮助信息
    with st.expander("💡 使用帮助", expanded=False):
        st.markdown("""
        ### 模板编辑指南
        
        **1. 基本操作**
        - 在"编辑模板"选项卡中修改模板内容
        - 在"预览效果"选项卡中查看渲染结果
        - 在"真实测试"选项卡中使用实际数据测试
        
        **2. 变量语法**
        - 使用 `{变量名}` 插入动态内容
        - 常用变量：`{month}`, `{day}`, `{audio_tech}` 等
        - 变量会自动替换为实际数据
        
        **3. 保存机制**
        - "应用更改"：将修改应用到内存中
        - "保存到文件"：将修改永久保存到配置文件
        
        **4. 注意事项**
        - 修改后记得点击"应用更改"
        - 重要修改请及时"保存到文件"
        - 可以随时在预览中查看效果
        """)

def send_template_email(template_content, template_type, service_date=None):
    """发送模板到邮箱"""
    try:
        # 导入邮件发送模块
        from src.email_sender import EmailSender, EmailRecipient
        
        # 初始化邮件发送器
        email_sender = EmailSender()
        
        # 创建收件人（默认发送给配置的邮箱）
        sender_email = os.getenv("SENDER_EMAIL", "jonathanjing@graceirvine.org")
        recipient = EmailRecipient(
            email=sender_email,
            name="事工协调员"
        )
        
        # 根据模板类型设置邮件主题
        if template_type == "周三确认通知":
            if service_date:
                subject = f"【微信群通知模板】周三确认通知 - {service_date.month}月{service_date.day}日"
            else:
                subject = "【微信群通知模板】周三确认通知"
        elif template_type == "周六提醒通知":
            if service_date:
                subject = f"【微信群通知模板】周六提醒通知 - {service_date.month}月{service_date.day}日"
            else:
                subject = "【微信群通知模板】周六提醒通知"
        else:
            subject = "【微信群通知模板】月度总览通知"
        
        # 创建HTML邮件内容
        html_content = f"""
        <html>
        <body style="font-family: 'Microsoft YaHei', sans-serif; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 800px; margin: 0 auto; background-color: #ffffff; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); overflow: hidden;">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #2E5984 0%, #4A90B8 100%); color: #ffffff; padding: 30px; text-align: center;">
                    <h1 style="margin: 0; font-size: 24px;">📱 微信群通知模板</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Grace Irvine 恩典尔湾教会</p>
                </div>
                
                <!-- Content -->
                <div style="padding: 30px;">
                    <div style="background-color: #e8f5e8; border: 1px solid #28a745; border-radius: 8px; padding: 20px; margin-bottom: 25px;">
                        <h3 style="margin: 0 0 15px 0; color: #155724; font-size: 18px;">📋 使用说明</h3>
                        <ol style="margin: 0; padding-left: 20px; color: #155724;">
                            <li>复制下方的微信群通知内容</li>
                            <li>打开相应的微信群聊天窗口</li>
                            <li>粘贴并发送通知</li>
                            <li>如需修改，可以直接在微信中编辑</li>
                        </ol>
                    </div>
                    
                    <div style="background-color: #f8f9fa; border: 2px solid #F4B942; border-radius: 8px; padding: 20px; margin: 25px 0; position: relative;">
                        <div style="background-color: #F4B942; color: #ffffff; padding: 10px 15px; margin: -20px -20px 15px -20px; font-weight: bold; font-size: 16px; border-radius: 6px 6px 0 0;">
                            📅 {template_type} - 微信群通知内容
                        </div>
                        <div style="font-family: 'Courier New', monospace; font-size: 14px; line-height: 1.8; white-space: pre-line; background-color: #ffffff; padding: 15px; border-radius: 4px; border: 1px solid #e0e0e0; color: #333;">
{template_content}
                        </div>
                    </div>
                    
                    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; padding: 15px; margin: 20px 0; color: #856404;">
                        <h4 style="margin: 0 0 10px 0;">⚠️ 发送建议</h4>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li><strong>周三确认通知</strong>：建议在周三晚上8:00 PM发送</li>
                            <li><strong>周六提醒通知</strong>：建议在周六晚上8:00 PM发送</li>
                            <li><strong>月度总览通知</strong>：建议在月初发送</li>
                            <li>发送前请再次确认人员信息是否正确</li>
                        </ul>
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666; border-top: 1px solid #e0e0e0;">
                    <p><strong>Grace Irvine 恩典尔湾教会</strong></p>
                    <p>此邮件由事工管理系统自动发送 · {datetime.now().strftime('%Y年%m月%d日 %H:%M')}</p>
                    <p>如有技术问题，请联系系统管理员</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # 创建纯文本版本
        text_content = f"""
{template_type} - 微信群通知模板

使用说明：
1. 复制下方的微信群通知内容
2. 打开相应的微信群聊天窗口
3. 粘贴并发送通知
4. 如需修改，可以直接在微信中编辑

微信群通知内容：
{template_content}

---
此邮件由 Grace Irvine 恩典尔湾教会事工管理系统自动发送
生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}
        """
        
        # 发送邮件
        with st.spinner("正在发送邮件..."):
            success = email_sender.send_email(
                recipients=[recipient],
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
        
        if success:
            st.success(f"✅ 邮件发送成功！")
            st.info(f"📧 已发送到: {recipient.email}")
            
            # 显示发送详情
            with st.expander("📋 发送详情", expanded=False):
                st.write(f"**收件人**: {recipient.email}")
                st.write(f"**主题**: {subject}")
                st.write(f"**发送时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.write(f"**模板类型**: {template_type}")
                if service_date:
                    st.write(f"**服事日期**: {service_date.strftime('%Y年%m月%d日')}")
        else:
            st.error("❌ 邮件发送失败！")
            st.info("请检查邮件配置和网络连接")
            
    except ImportError:
        st.error("❌ 邮件发送模块未找到！")
        st.info("请确保已正确安装邮件发送依赖")
        
    except Exception as e:
        st.error(f"❌ 发送邮件时出错: {e}")
        st.info("请检查邮件配置是否正确")
        
        # 显示错误详情（仅在调试时）
        with st.expander("🔧 错误详情", expanded=False):
            st.code(str(e))

def show_ics_calendar_management(data_result):
    """显示ICS日历管理页面"""
    st.header("📅 ICS日历管理")
    st.markdown("管理事工通知的ICS日历，支持自动订阅和更新")
    
    if not ICS_AVAILABLE:
        st.error("❌ ICS日历功能不可用")
        st.info("请安装依赖: pip install icalendar pytz schedule")
        return
    
    if not data_result or not data_result.get('success', False):
        st.error("❌ 无法加载数据，请先检查Google Sheets连接")
        return
    
    assignments = data_result.get('assignments', [])
    if not assignments:
        st.warning("⚠️ 未找到事工安排数据")
        return
    
    # 创建标签页
    tab1, tab2, tab3, tab4 = st.tabs(["📋 日历生成", "🔗 订阅管理", "⚙️ 自动更新", "📊 系统状态"])
    
    with tab1:
        st.subheader("📅 生成ICS日历文件")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 👨‍💼 负责人日历")
            st.info("包含通知发送提醒事件（周三、周六、月初）")
            
            if st.button("🔄 生成负责人日历", use_container_width=True):
                with st.spinner("正在生成负责人日历..."):
                    try:
                        coordinator_ics = generate_coordinator_calendar_content(assignments)
                        
                        if coordinator_ics:
                            st.success("✅ 负责人日历生成成功！")
                            
                            # 提供下载
                            st.download_button(
                                label="📥 下载负责人日历",
                                data=coordinator_ics,
                                file_name=f"grace_irvine_coordinator_{datetime.now().strftime('%Y%m%d')}.ics",
                                mime="text/calendar",
                                use_container_width=True
                            )
                            
                            # 显示统计信息
                            event_count = coordinator_ics.count("BEGIN:VEVENT")
                            st.metric("📊 事件数量", event_count)
                            
                        else:
                            st.error("❌ 生成失败")
                            
                    except Exception as e:
                        st.error(f"❌ 生成失败: {e}")
        
        with col2:
            st.markdown("#### 👥 同工日历")
            st.info("包含个人服事安排事件（彩排、正式服事）")
            
            if st.button("🔄 生成同工日历", use_container_width=True):
                with st.spinner("正在生成同工日历..."):
                    try:
                        workers_ics = generate_workers_calendar_content(assignments)
                        
                        if workers_ics:
                            st.success("✅ 同工日历生成成功！")
                            
                            # 提供下载
                            st.download_button(
                                label="📥 下载同工日历",
                                data=workers_ics,
                                file_name=f"grace_irvine_workers_{datetime.now().strftime('%Y%m%d')}.ics",
                                mime="text/calendar",
                                use_container_width=True
                            )
                            
                            # 显示统计信息
                            event_count = workers_ics.count("BEGIN:VEVENT")
                            st.metric("📊 事件数量", event_count)
                            
                        else:
                            st.error("❌ 生成失败")
                            
                    except Exception as e:
                        st.error(f"❌ 生成失败: {e}")
        
        # 个人日历生成
        st.markdown("#### 👤 个人日历")
        
        # 获取同工列表
        workers = get_worker_list(assignments)
        if workers:
            selected_worker = st.selectbox("选择同工", [""] + sorted(workers))
            
            if selected_worker:
                if st.button(f"🔄 生成 {selected_worker} 的个人日历", use_container_width=True):
                    with st.spinner(f"正在生成 {selected_worker} 的个人日历..."):
                        try:
                            personal_ics = generate_personal_calendar_content(assignments, selected_worker)
                            
                            if personal_ics:
                                st.success(f"✅ {selected_worker} 的个人日历生成成功！")
                                
                                # 提供下载
                                st.download_button(
                                    label=f"📥 下载 {selected_worker} 的个人日历",
                                    data=personal_ics,
                                    file_name=f"grace_irvine_{selected_worker}_{datetime.now().strftime('%Y%m%d')}.ics",
                                    mime="text/calendar",
                                    use_container_width=True
                                )
                                
                                # 显示统计信息
                                event_count = personal_ics.count("BEGIN:VEVENT")
                                st.metric("📊 事件数量", event_count)
                                
                            else:
                                st.error("❌ 生成失败")
                                
                        except Exception as e:
                            st.error(f"❌ 生成失败: {e}")
    
    with tab2:
        st.subheader("🔗 日历订阅管理")
        
        st.markdown("""
        ### 📱 自动更新订阅方式
        
        为了实现双击添加后自动更新，请使用以下订阅方式：
        """)
        
        # 方案1: 静态文件订阅
        st.markdown("#### 方案1: 静态文件订阅 (推荐)")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info("""
            **优点**: 简单、稳定、兼容性好
            **适用**: 所有主流日历应用
            **更新**: 通过定时任务自动更新文件
            """)
        
        with col2:
            if st.button("🔄 更新静态文件", use_container_width=True):
                with st.spinner("正在更新静态日历文件..."):
                    try:
                        # 生成静态文件
                        coordinator_ics = generate_coordinator_calendar_content(assignments)
                        workers_ics = generate_workers_calendar_content(assignments)
                        
                        # 保存到固定文件名
                        calendar_dir = Path("calendars")
                        calendar_dir.mkdir(exist_ok=True)
                        
                        with open(calendar_dir / "grace_irvine_coordinator.ics", 'w', encoding='utf-8') as f:
                            f.write(coordinator_ics)
                        
                        with open(calendar_dir / "grace_irvine_workers.ics", 'w', encoding='utf-8') as f:
                            f.write(workers_ics)
                        
                        st.success("✅ 静态文件更新完成！")
                        
                    except Exception as e:
                        st.error(f"❌ 更新失败: {e}")
        
        # 显示订阅URL和Cloud Scheduler集成
        st.markdown("#### 📡 Cloud Scheduler集成")
        
        st.info("""
        **✅ 已集成Cloud Scheduler**
        - 周三和周六的触发器已在Cloud Scheduler中设置
        - 系统会自动调用API端点更新ICS文件
        - 无需容器内后台服务
        """)
        
        # API端点信息
        st.markdown("#### 🔗 API端点")
        
        # 获取当前应用URL（如果在Cloud Run中）
        cloud_run_url = os.getenv('CLOUD_RUN_URL', 'https://your-app-url.run.app')
        
        api_endpoints = {
            "更新日历": f"{cloud_run_url}/api/update-calendars",
            "系统状态": f"{cloud_run_url}/api/status",
            "负责人日历": f"{cloud_run_url}/calendars/grace_irvine_coordinator.ics",
            "同工日历": f"{cloud_run_url}/calendars/grace_irvine_workers.ics"
        }
        
        for endpoint_name, url in api_endpoints.items():
            st.code(f"{endpoint_name}: {url}")
        
        # 手动触发更新
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 触发后台服务更新", use_container_width=True):
                with st.spinner("正在调用后台服务..."):
                    try:
                        import requests
                        # 调用本地后台服务API
                        response = requests.post("http://localhost:5000/api/update-calendars", timeout=30)
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.success("✅ 后台服务更新成功！")
                            st.json(result)
                        else:
                            st.error(f"❌ 后台服务更新失败: {response.status_code}")
                            
                    except Exception as e:
                        st.error(f"❌ 调用后台服务失败: {e}")
        
        with col2:
            if st.button("📊 查看后台服务状态", use_container_width=True):
                try:
                    import requests
                    response = requests.get("http://localhost:5000/api/status", timeout=10)
                    
                    if response.status_code == 200:
                        status = response.json()
                        st.success("✅ 后台服务运行正常")
                        
                        # 显示关键信息
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.metric("服务状态", status.get('status', '未知'))
                        with col_b:
                            last_update = status.get('last_update')
                            if last_update:
                                update_time = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                                st.metric("最后更新", update_time.strftime('%H:%M:%S'))
                        
                        # 显示详细状态
                        with st.expander("📋 详细状态"):
                            st.json(status)
                    else:
                        st.error("❌ 后台服务无响应")
                        
                except Exception as e:
                    st.error(f"❌ 无法连接后台服务: {e}")
                    st.info("💡 后台服务可能正在启动中，请稍后重试")
        
        # 订阅链接
        if st.checkbox("📱 显示订阅链接"):
            st.markdown("#### 📋 用户订阅链接")
            
            coordinator_url = f"{cloud_run_url}/calendars/grace_irvine_coordinator.ics"
            workers_url = f"{cloud_run_url}/calendars/grace_irvine_workers.ics"
            
            st.code(f"负责人日历: {coordinator_url}")
            st.code(f"同工日历: {workers_url}")
            
            st.markdown("""
            **📱 订阅方法:**
            1. **Google Calendar**: 左侧"+" → "从URL添加" → 粘贴链接
            2. **Apple Calendar**: "文件" → "新建日历订阅" → 输入URL  
            3. **Outlook**: "添加日历" → "从Internet订阅" → 输入URL
            
            ⚠️ **重要**: 请使用"订阅URL"而不是"导入文件"，这样才能自动更新
            """)
    
    with tab3:
        st.subheader("⚙️ 自动更新设置")
        
        st.markdown("""
        ### 🔄 自动更新机制
        
        为确保日历内容始终最新，需要设置自动更新：
        """)
        
        # 更新频率设置
        update_frequency = st.selectbox(
            "更新频率",
            ["每小时", "每30分钟", "每2小时", "每6小时", "每12小时"],
            index=0
        )
        
        frequency_map = {
            "每小时": "0 * * * *",
            "每30分钟": "*/30 * * * *", 
            "每2小时": "0 */2 * * *",
            "每6小时": "0 */6 * * *",
            "每12小时": "0 */12 * * *"
        }
        
        cron_expression = frequency_map[update_frequency]
        
        st.markdown("#### 🖥️ 服务器端设置")
        
        st.markdown("**Cron任务设置:**")
        st.code(f"{cron_expression} cd /path/to/project && python3 scripts/update_static_calendars.py")
        
        st.markdown("**Docker部署:**")
        st.code("""
# 在Dockerfile中添加
COPY scripts/ ./scripts/
RUN pip install icalendar pytz schedule

# 启动时同时运行更新服务
CMD python3 scripts/update_static_calendars.py --watch & streamlit run streamlit_app.py --server.port=8080
        """)
        
        # 手动触发更新
        st.markdown("#### 🔧 手动更新")
        
        if st.button("🔄 立即更新所有日历文件", type="primary", use_container_width=True):
            with st.spinner("正在更新所有日历文件..."):
                try:
                    # 更新静态文件
                    coordinator_ics = generate_coordinator_calendar_content(assignments)
                    workers_ics = generate_workers_calendar_content(assignments)
                    
                    # 保存文件
                    calendar_dir = Path("calendars")
                    calendar_dir.mkdir(exist_ok=True)
                    
                    files_updated = []
                    
                    # 保存负责人日历
                    coord_file = calendar_dir / "grace_irvine_coordinator.ics"
                    with open(coord_file, 'w', encoding='utf-8') as f:
                        f.write(coordinator_ics)
                    files_updated.append(f"负责人日历 ({coordinator_ics.count('BEGIN:VEVENT')} 个事件)")
                    
                    # 保存同工日历
                    workers_file = calendar_dir / "grace_irvine_workers.ics"
                    with open(workers_file, 'w', encoding='utf-8') as f:
                        f.write(workers_ics)
                    files_updated.append(f"同工日历 ({workers_ics.count('BEGIN:VEVENT')} 个事件)")
                    
                    # 保存时间戳文件
                    timestamp_file = calendar_dir / "last_update.txt"
                    with open(timestamp_file, 'w') as f:
                        f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    
                    st.success("✅ 所有日历文件更新完成！")
                    
                    for file_info in files_updated:
                        st.write(f"📋 {file_info}")
                    
                    st.info(f"🕒 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    
                except Exception as e:
                    st.error(f"❌ 更新失败: {e}")
    
    with tab4:
        st.subheader("📊 ICS系统状态")
        
        # 显示文件状态
        calendar_dir = Path("calendars")
        if calendar_dir.exists():
            st.markdown("#### 📁 日历文件状态")
            
            ics_files = list(calendar_dir.glob("*.ics"))
            if ics_files:
                files_data = []
                for file_path in ics_files:
                    try:
                        stat = file_path.stat()
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        files_data.append({
                            "文件名": file_path.name,
                            "大小": f"{stat.st_size / 1024:.1f} KB",
                            "事件数量": content.count("BEGIN:VEVENT"),
                            "最后修改": datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                        })
                    except Exception as e:
                        files_data.append({
                            "文件名": file_path.name,
                            "大小": "错误",
                            "事件数量": "错误", 
                            "最后修改": f"读取失败: {e}"
                        })
                
                st.dataframe(files_data, use_container_width=True)
            else:
                st.info("📁 未找到ICS日历文件")
        
        # 显示系统组件状态
        st.markdown("#### 🔧 系统组件状态")
        
        components_status = {
            "Google Sheets连接": "✅ 正常" if data_result.get('success') else "❌ 异常",
            "模板管理器": "✅ 正常" if data_result.get('success') else "❌ 异常",
            "ICS日历功能": "✅ 可用" if ICS_AVAILABLE else "❌ 不可用",
            "数据记录数": len(assignments) if assignments else 0
        }
        
        for component, status in components_status.items():
            st.write(f"**{component}**: {status}")
        
        # 显示最后更新时间
        timestamp_file = calendar_dir / "last_update.txt"
        if timestamp_file.exists():
            try:
                with open(timestamp_file, 'r') as f:
                    last_update = f.read().strip()
                st.info(f"🕒 最后更新时间: {last_update}")
            except:
                pass

def generate_coordinator_calendar_content(assignments) -> str:
    """生成负责人日历ICS内容"""
    try:
        from src.template_manager import get_default_template_manager
        
        template_manager = get_default_template_manager()
        
        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0", 
            "PRODID:-//Grace Irvine Ministry Scheduler//Coordinator Calendar//CN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:Grace Irvine 事工协调日历",
            "X-WR-CALDESC:事工通知发送提醒日历（自动更新）",
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
                    event_ics = create_simple_ics_event(
                        uid=f"weekly_confirmation_{wednesday.strftime('%Y%m%d')}@graceirvine.org",
                        summary=f"发送周末确认通知 ({assignment.date.month}/{assignment.date.day})",
                        description=f"发送内容：\n\n{notification_content}",
                        start_dt=datetime.combine(wednesday, datetime.min.time().replace(hour=20, minute=0)),
                        end_dt=datetime.combine(wednesday, datetime.min.time().replace(hour=20, minute=30)),
                        location="Grace Irvine 教会"
                    )
                    ics_lines.append(event_ics)
                except Exception:
                    pass
            
            # 周六提醒通知事件
            saturday = assignment.date - timedelta(days=1)
            if saturday >= today - timedelta(days=7):
                try:
                    notification_content = template_manager.render_sunday_reminder(assignment)
                    event_ics = create_simple_ics_event(
                        uid=f"sunday_reminder_{saturday.strftime('%Y%m%d')}@graceirvine.org",
                        summary=f"发送主日提醒通知 ({assignment.date.month}/{assignment.date.day})",
                        description=f"发送内容：\n\n{notification_content}",
                        start_dt=datetime.combine(saturday, datetime.min.time().replace(hour=20, minute=0)),
                        end_dt=datetime.combine(saturday, datetime.min.time().replace(hour=20, minute=30)),
                        location="Grace Irvine 教会"
                    )
                    ics_lines.append(event_ics)
                except Exception:
                    pass
        
        ics_lines.append("END:VCALENDAR")
        return "\n".join(ics_lines)
        
    except Exception as e:
        st.error(f"生成负责人日历时出错: {e}")
        return None

def generate_workers_calendar_content(assignments) -> str:
    """生成同工日历ICS内容"""
    try:
        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Grace Irvine Ministry Scheduler//Workers Calendar//CN", 
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:Grace Irvine 同工服事日历",
            "X-WR-CALDESC:同工事工服事安排日历（自动更新）",
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
                        
                        event_ics = create_simple_ics_event(
                            uid=f"service_{role_name}_{assignment.date.strftime('%Y%m%d')}_{person_name}@graceirvine.org",
                            summary=f"主日服事 - {role_name}",
                            description=f"角色：{role_name}\n负责人：{person_name}\n到场时间：{start_time}\n\n愿主同在，出入平安！",
                            start_dt=datetime.combine(assignment.date, datetime.min.time().replace(hour=start_hour, minute=start_minute)),
                            end_dt=datetime.combine(assignment.date, datetime.min.time().replace(hour=end_hour, minute=end_minute)),
                            location="Grace Irvine 教会"
                        )
                        ics_lines.append(event_ics)
                    except Exception:
                        pass
        
        ics_lines.append("END:VCALENDAR")
        return "\n".join(ics_lines)
        
    except Exception as e:
        st.error(f"生成同工日历时出错: {e}")
        return None

def generate_personal_calendar_content(assignments, worker_name: str) -> str:
    """生成个人日历ICS内容"""
    try:
        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Grace Irvine Ministry Scheduler//Personal Calendar//CN",
            "CALSCALE:GREGORIAN", 
            "METHOD:PUBLISH",
            f"X-WR-CALNAME:{worker_name} - Grace Irvine 个人服事日历",
            f"X-WR-CALDESC:{worker_name}的个人事工服事安排（自动更新）",
            "X-WR-TIMEZONE:America/Los_Angeles",
            f"X-WR-CALDESC:最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        
        today = date.today()
        future_assignments = [a for a in assignments if a.date >= today]
        
        for assignment in future_assignments:
            # 检查该同工是否参与此次服事
            worker_roles = []
            if assignment.audio_tech == worker_name:
                worker_roles.append(("音控", "09:00", "12:00"))
            if assignment.camera_operator == worker_name:
                worker_roles.append(("导播/摄影", "09:30", "12:00"))
            if assignment.propresenter == worker_name:
                worker_roles.append(("ProPresenter播放", "09:00", "12:00"))
            if assignment.video_editor == worker_name:
                worker_roles.append(("ProPresenter更新", "09:00", "12:00"))
            
            for role_name, start_time, end_time in worker_roles:
                try:
                    start_hour, start_minute = map(int, start_time.split(':'))
                    end_hour, end_minute = map(int, end_time.split(':'))
                    
                    event_ics = create_simple_ics_event(
                        uid=f"personal_{role_name}_{assignment.date.strftime('%Y%m%d')}_{worker_name}@graceirvine.org",
                        summary=f"我的服事 - {role_name}",
                        description=f"角色：{role_name}\n日期：{assignment.date}\n到场时间：{start_time}\n\n愿主同在，出入平安！",
                        start_dt=datetime.combine(assignment.date, datetime.min.time().replace(hour=start_hour, minute=start_minute)),
                        end_dt=datetime.combine(assignment.date, datetime.min.time().replace(hour=end_hour, minute=end_minute)),
                        location="Grace Irvine 教会"
                    )
                    ics_lines.append(event_ics)
                except Exception:
                    pass
        
        ics_lines.append("END:VCALENDAR")
        return "\n".join(ics_lines)
        
    except Exception as e:
        st.error(f"生成 {worker_name} 个人日历时出错: {e}")
        return None

def create_simple_ics_event(uid: str, summary: str, description: str, 
                           start_dt: datetime, end_dt: datetime, location: str = "") -> str:
    """创建简单的ICS事件"""
    def escape_ics_text(text: str) -> str:
        text = text.replace('\\', '\\\\')
        text = text.replace(',', '\\,')
        text = text.replace(';', '\\;')
        text = text.replace('\n', '\\n')
        return text
    
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

def get_worker_list(assignments) -> List[str]:
    """获取同工名单"""
    workers = set()
    for assignment in assignments:
        if assignment.audio_tech and assignment.audio_tech.strip():
            workers.add(assignment.audio_tech)
        if assignment.camera_operator and assignment.camera_operator.strip():
            workers.add(assignment.camera_operator)
        if assignment.propresenter and assignment.propresenter.strip():
            workers.add(assignment.propresenter)
        if assignment.video_editor and assignment.video_editor.strip():
            workers.add(assignment.video_editor)
    
    return list(workers)

if __name__ == "__main__":
    main()
