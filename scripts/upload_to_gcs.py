#!/usr/bin/env python3
"""
直接上传ICS文件到Google Cloud Storage
Upload ICS files directly to GCS bucket

用法:
  python upload_to_gcs.py
"""

import sys
import os
from pathlib import Path
from datetime import date, datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

def main():
    """主函数"""
    print("🔄 生成并上传ICS文件到Google Cloud Storage")
    print("=" * 60)
    
    # 加载环境变量
    load_dotenv()
    
    # 检查环境变量
    spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
    bucket_name = os.getenv('GCP_STORAGE_BUCKET', 'grace-irvine-ministry-scheduler')
    
    if not spreadsheet_id:
        print("❌ 错误: 请在 .env 文件中设置 GOOGLE_SPREADSHEET_ID")
        return 1
    
    print(f"📦 目标Bucket: {bucket_name}")
    
    try:
        # 导入Google Cloud Storage
        print("\n📦 导入Google Cloud Storage...")
        from google.cloud import storage
        print("✅ Google Cloud Storage导入成功")
        
        # 导入其他模块
        print("📦 导入项目模块...")
        from src.data_cleaner import FocusedDataCleaner
        from src.dynamic_template_manager import get_dynamic_template_manager
        
        print("✅ 模块导入成功")
        
        # 获取数据
        print("\n📊 获取Google Sheets数据...")
        cleaner = FocusedDataCleaner()
        raw_df = cleaner.download_data()
        focused_df = cleaner.extract_focused_columns(raw_df)
        schedules = cleaner.clean_focused_data(focused_df)
        
        if not schedules:
            print("❌ 未找到排程数据")
            return 1
        
        print(f"✅ 成功获取 {len(schedules)} 条事工安排")
        
        # 获取模板管理器
        print("\n📝 初始化模板管理器...")
        template_manager = get_dynamic_template_manager()
        print("✅ 模板管理器初始化成功")
        
        # 生成ICS内容
        print("\n📅 生成ICS日历内容...")
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
        # 保留过去4周到未来15周的事件
        cutoff_date = today - timedelta(days=28)
        relevant_schedules = [s for s in schedules if s.date >= cutoff_date][:19]
        events_created = 0
        
        print(f"📋 准备生成 {len(relevant_schedules)} 周的日历事件...")
        
        # 生成事件
        for schedule in relevant_schedules:
            # 周三确认通知
            wednesday = schedule.date - timedelta(days=4)
            if wednesday >= today - timedelta(days=7):
                try:
                    notification_content = template_manager.render_weekly_confirmation(
                        schedule.date, schedule, for_ics_generation=True
                    )
                    
                    event_lines = create_ics_event(
                        uid=f"weekly_confirmation_{wednesday.strftime('%Y%m%d')}@graceirvine.org",
                        summary=f"发送周末确认通知 ({schedule.date.month}/{schedule.date.day})",
                        description=f"发送内容：\n\n{notification_content}",
                        start_dt=datetime.combine(wednesday, datetime.min.time().replace(hour=20, minute=0)),
                        end_dt=datetime.combine(wednesday, datetime.min.time().replace(hour=20, minute=30))
                    )
                    ics_lines.append(event_lines)
                    events_created += 1
                except Exception as e:
                    print(f"  ⚠️ 创建周三事件失败 ({schedule.date}): {e}")
            
            # 周六提醒通知
            saturday = schedule.date - timedelta(days=1)
            if saturday >= today - timedelta(days=7):
                try:
                    notification_content = template_manager.render_saturday_reminder(
                        schedule.date, schedule
                    )
                    
                    event_lines = create_ics_event(
                        uid=f"sunday_reminder_{saturday.strftime('%Y%m%d')}@graceirvine.org",
                        summary=f"发送主日提醒通知 ({schedule.date.month}/{schedule.date.day})",
                        description=f"发送内容：\n\n{notification_content}",
                        start_dt=datetime.combine(saturday, datetime.min.time().replace(hour=20, minute=0)),
                        end_dt=datetime.combine(saturday, datetime.min.time().replace(hour=20, minute=30))
                    )
                    ics_lines.append(event_lines)
                    events_created += 1
                except Exception as e:
                    print(f"  ⚠️ 创建周六事件失败 ({schedule.date}): {e}")
        
        ics_lines.append("END:VCALENDAR")
        ics_content = "\n".join(ics_lines)
        
        print(f"✅ 成功生成 {events_created} 个日历事件")
        
        # 上传到GCS
        print(f"\n☁️  上传到Google Cloud Storage...")
        print(f"   Bucket: gs://{bucket_name}")
        
        # 初始化GCS客户端
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        
        # 上传ICS文件
        blob_path = "calendars/grace_irvine_coordinator.ics"
        blob = bucket.blob(blob_path)
        
        # 设置内容类型和缓存控制
        blob.content_type = "text/calendar; charset=utf-8"
        blob.cache_control = "public, max-age=3600"  # 1小时缓存
        
        # 上传内容
        blob.upload_from_string(ics_content, content_type="text/calendar; charset=utf-8")
        
        # 设置为公开访问
        blob.make_public()
        
        # 获取公开URL
        public_url = f"https://storage.cloud.google.com/{bucket_name}/{blob_path}"
        
        print(f"✅ ICS文件已成功上传到Google Cloud Storage！")
        print(f"\n🔗 公开订阅URL:")
        print(f"   {public_url}")
        print(f"\n📊 文件信息:")
        print(f"   - 事件数量: {events_created}")
        print(f"   - 文件大小: {len(ics_content.encode('utf-8')) / 1024:.1f} KB")
        print(f"   - 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   - GCS路径: gs://{bucket_name}/{blob_path}")
        
        return 0
            
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("   请确保已安装 google-cloud-storage:")
        print("   pip install google-cloud-storage")
        return 1
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

def escape_ics_text(text: str) -> str:
    """转义ICS文本中的特殊字符"""
    text = text.replace('\\', '\\\\')
    text = text.replace(',', '\\,')
    text = text.replace(';', '\\;')
    text = text.replace('\n', '\\n')
    return text

def create_ics_event(uid: str, summary: str, description: str, 
                    start_dt, end_dt, location: str = "Grace Irvine 教会") -> str:
    """创建ICS事件字符串"""
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

if __name__ == "__main__":
    sys.exit(main())

