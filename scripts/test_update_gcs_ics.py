#!/usr/bin/env python3
"""
测试更新 GCS 上的 ICS 文件
生成媒体部/儿童部日历并上传到 GCS，然后读取验证。
"""

import os
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.cloud_storage_manager import get_storage_manager
from src.multi_calendar_generator import generate_all_calendars


def require_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise RuntimeError(f"缺少环境变量: {var_name}")
    return value


def main():
    print("=" * 60)
    print("🧪 测试更新 GCS ICS 文件")
    print("=" * 60)

    # 确保云端模式
    os.environ["STORAGE_MODE"] = "cloud"

    # 基础环境检查
    require_env("GOOGLE_CLOUD_PROJECT")
    require_env("GCP_STORAGE_BUCKET")

    storage_manager = get_storage_manager()
    if not storage_manager.is_cloud_mode:
        print("❌ 当前不是云端模式，请设置 STORAGE_MODE=cloud")
        return 1

    print(f"✅ GCS Bucket: {storage_manager.config.bucket_name}")

    results = generate_all_calendars()
    if not results or not results.get("calendars"):
        print("❌ 未生成任何日历内容")
        return 1

    uploaded = []
    for calendar_type, calendar_result in results["calendars"].items():
        if not calendar_result.get("success") or not calendar_result.get("content"):
            print(f"⚠️ 跳过 {calendar_type}：生成失败")
            continue

        filename = f"{calendar_type}.ics"
        content = calendar_result["content"]
        if storage_manager.write_ics_calendar(content, filename):
            uploaded.append(filename)
            print(f"✅ 已上传: {filename} (事件数: {calendar_result.get('events', 0)})")
        else:
            print(f"❌ 上传失败: {filename}")

    if not uploaded:
        print("❌ 没有任何文件上传成功")
        return 1

    print("\n🔍 回读验证:")
    for filename in uploaded:
        content = storage_manager.read_ics_calendar(filename)
        if content:
            events = content.count("BEGIN:VEVENT")
            print(f"  ✅ {filename}: {events} events")
        else:
            print(f"  ❌ {filename}: 回读失败")

    print("\n✅ 测试完成")
    print(f"🕒 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
