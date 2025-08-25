#!/usr/bin/env python3
"""
事工通知生成器 - 专用脚本

用法:
  python generate_notifications.py weekly     # 生成周三确认通知
  python generate_notifications.py sunday     # 生成周六提醒通知
  python generate_notifications.py monthly    # 生成月度总览通知
  python generate_notifications.py all        # 生成所有通知
"""

import sys
import os
from datetime import datetime, date
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from simple_scheduler import GoogleSheetsExtractor, NotificationGenerator
from dotenv import load_dotenv

def main():
    # 加载环境变量
    load_dotenv()
    
    # 检查参数
    if len(sys.argv) < 2:
        print("用法: python generate_notifications.py [weekly|sunday|monthly|all]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # 获取配置
    spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
    if not spreadsheet_id:
        print("❌ 错误: 请在 .env 文件中设置 GOOGLE_SPREADSHEET_ID")
        sys.exit(1)
    
    try:
        # 初始化
        print("🔗 正在连接 Google Sheets...")
        extractor = GoogleSheetsExtractor(spreadsheet_id)
        generator = NotificationGenerator(extractor)
        
        print("✅ 连接成功!")
        print("=" * 60)
        
        if command == "weekly" or command == "all":
            print("\n📅 【周三确认通知】")
            print("-" * 40)
            weekly_msg = generator.generate_weekly_confirmation()
            print(weekly_msg)
            
            # 保存到文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(f"weekly_notification_{timestamp}.txt", "w", encoding="utf-8") as f:
                f.write(weekly_msg)
            print(f"\n💾 已保存到: weekly_notification_{timestamp}.txt")
        
        if command == "sunday" or command == "all":
            print("\n🔔 【周六提醒通知】")
            print("-" * 40)
            sunday_msg = generator.generate_sunday_reminder()
            print(sunday_msg)
            
            # 保存到文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(f"sunday_reminder_{timestamp}.txt", "w", encoding="utf-8") as f:
                f.write(sunday_msg)
            print(f"\n💾 已保存到: sunday_reminder_{timestamp}.txt")
        
        if command == "monthly" or command == "all":
            print("\n📊 【月度总览通知】")
            print("-" * 40)
            monthly_msg = generator.generate_monthly_overview()
            print(monthly_msg)
            
            # 保存到文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(f"monthly_overview_{timestamp}.txt", "w", encoding="utf-8") as f:
                f.write(monthly_msg)
            print(f"\n💾 已保存到: monthly_overview_{timestamp}.txt")
        
        if command not in ["weekly", "sunday", "monthly", "all"]:
            print(f"❌ 未知命令: {command}")
            print("支持的命令: weekly, sunday, monthly, all")
            sys.exit(1)
        
        print("\n" + "=" * 60)
        print("✅ 通知生成完成!")
        print("\n📋 使用提示:")
        print("1. 复制生成的文本到微信群")
        print("2. 检查日期和人员信息是否正确")
        print("3. 如有需要，可以手动调整内容")
        
    except FileNotFoundError as e:
        print(f"❌ 文件未找到: {e}")
        print("请确保 configs/service_account.json 文件存在")
    except Exception as e:
        print(f"❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
