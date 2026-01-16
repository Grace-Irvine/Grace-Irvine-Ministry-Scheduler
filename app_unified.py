#!/usr/bin/env python3
"""
Grace Irvine Ministry Scheduler - ICS 专用界面
只保留 ICS 生成与查看功能（媒体部 / 儿童部）
"""

import logging
from datetime import datetime
from pathlib import Path

import streamlit as st

from dotenv import load_dotenv
from src.cloud_storage_manager import get_storage_manager
from src.multi_calendar_generator import generate_all_calendars


# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def write_calendars_to_storage(results):
    """写入生成的ICS文件到存储（本地/云端）"""
    storage_manager = get_storage_manager()
    saved = []

    for calendar_type, calendar_result in results.get('calendars', {}).items():
        if not calendar_result.get('success') or not calendar_result.get('content'):
            continue

        filename = f"{calendar_type}.ics"
        ok = storage_manager.write_ics_calendar(calendar_result['content'], filename)
        if ok:
            saved.append({
                "filename": filename,
                "events": calendar_result.get("events", 0),
                "size_kb": f"{len(calendar_result['content'].encode('utf-8')) / 1024:.1f}"
            })

    return saved


def read_calendar_content(filename):
    """读取ICS内容（本地/云端）"""
    storage_manager = get_storage_manager()
    return storage_manager.read_ics_calendar(filename)


def get_calendar_status():
    """获取日历状态"""
    storage_manager = get_storage_manager()
    calendar_files = ["media-team.ics", "children-team.ics"]
    status = []

    for filename in calendar_files:
        content = storage_manager.read_ics_calendar(filename)
        if content:
            status.append({
                "filename": filename,
                "events": content.count("BEGIN:VEVENT"),
                "size_kb": f"{len(content.encode('utf-8')) / 1024:.1f}",
                "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        else:
            status.append({
                "filename": filename,
                "events": 0,
                "size_kb": "-",
                "updated": "-"
            })

    return status


def main():
    st.set_page_config(
        page_title="Grace Irvine ICS",
        page_icon="📅",
        layout="wide"
    )

    st.title("📅 Grace Irvine ICS")
    st.caption("仅保留媒体部 / 儿童部周三确认与周六提醒日历")

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("🔄 生成/更新 ICS", use_container_width=True):
            with st.spinner("正在生成ICS日历..."):
                results = generate_all_calendars()
                saved_files = write_calendars_to_storage(results)
            if saved_files:
                st.success(f"✅ 已更新 {len(saved_files)} 个日历文件")
                st.json(saved_files)
            else:
                st.error("❌ 未生成任何日历文件")

    with col2:
        if st.button("📊 刷新日历状态", use_container_width=True):
            st.rerun()

    st.markdown("---")
    st.subheader("📁 日历状态")
    st.table(get_calendar_status())

    st.markdown("---")
    st.subheader("🔍 查看 ICS 内容")
    filename = st.selectbox(
        "选择日历文件",
        ["media-team.ics", "children-team.ics"]
    )
    content = read_calendar_content(filename)
    if content:
        st.text_area("ICS 原始内容", content, height=420)
    else:
        st.warning("未找到该日历文件，请先生成。")


if __name__ == "__main__":
    main()
