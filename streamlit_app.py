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

# 导入我们的数据清洗模块
from focused_data_cleaner import FocusedDataCleaner

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
    
    # 保存模板到文件
    if st.button("💾 保存模板到文件"):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"notification_template_{timestamp}.txt"
        filepath = PROJECT_ROOT / "data" / filename
        
        # 确保目录存在
        filepath.parent.mkdir(exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(template)
        
        st.success(f"✅ 模板已保存到: {filepath}")

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
        
        page = st.selectbox(
            "选择页面",
            ["📊 数据概览", "🔍 数据查看器", "📝 模板生成器", "⚙️ 系统设置"]
        )
        
        st.markdown("---")
        
        # 快速操作
        st.markdown("### ⚡ 快速操作")
        
        if st.button("🔄 刷新数据", use_container_width=True):
            st.cache_data.clear()
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

if __name__ == "__main__":
    main()
