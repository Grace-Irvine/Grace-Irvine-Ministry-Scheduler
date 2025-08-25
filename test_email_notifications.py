#!/usr/bin/env python3
"""
邮件通知测试脚本
Test script for email notifications
"""

import os
import sys
from datetime import datetime, date, timedelta
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from src.email_sender import EmailSender, EmailRecipient, EmailConfig, test_connection
from src.scheduler import GoogleSheetsExtractor, NotificationGenerator, MinistryAssignment

def setup_test_environment():
    """设置测试环境"""
    # 加载环境变量
    load_dotenv()
    
    # 检查必要的环境变量
    required_vars = ['EMAIL_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("⚠️  缺少必要的环境变量:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n请在 .env 文件中设置以上环境变量")
        print("\n示例 .env 文件内容:")
        print("EMAIL_PASSWORD=your_app_password_here")
        print("\n注意：对于Gmail，需要使用应用专用密码而不是账户密码")
        print("生成应用密码：https://myaccount.google.com/apppasswords")
        return False
    
    return True

def test_smtp_connection():
    """测试SMTP连接"""
    print("\n" + "="*60)
    print("📧 测试邮件服务器连接")
    print("="*60)
    
    if test_connection():
        print("✅ 邮件服务器连接成功！")
        return True
    else:
        print("❌ 邮件服务器连接失败")
        print("\n可能的原因：")
        print("1. EMAIL_PASSWORD 环境变量未设置或错误")
        print("2. 网络连接问题")
        print("3. SMTP服务器设置错误")
        return False

def test_send_simple_email():
    """测试发送简单邮件"""
    print("\n" + "="*60)
    print("📨 测试发送简单邮件")
    print("="*60)
    
    sender = EmailSender()
    
    # 创建测试收件人
    recipient = EmailRecipient(
        email="jonathanjing@graceirvine.org",
        name="Jonathan Jing"
    )
    
    # 准备邮件内容
    subject = "【测试】Grace Irvine 事工管理系统 - 邮件功能测试"
    
    html_content = """
    <html>
    <body style="font-family: 'Microsoft YaHei', sans-serif; padding: 20px;">
        <h2 style="color: #2E5984;">邮件功能测试</h2>
        <p>这是一封测试邮件，用于验证邮件发送功能是否正常工作。</p>
        <p>测试时间：{}</p>
        <hr>
        <p style="color: #666; font-size: 12px;">
            此邮件由 Grace Irvine 事工管理系统自动发送
        </p>
    </body>
    </html>
    """.format(datetime.now().strftime("%Y年%m月%d日 %H:%M:%S"))
    
    text_content = f"""
邮件功能测试

这是一封测试邮件，用于验证邮件发送功能是否正常工作。
测试时间：{datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}

此邮件由 Grace Irvine 事工管理系统自动发送
    """
    
    # 发送邮件
    print(f"发送测试邮件到: {recipient.email}")
    if sender.send_email(
        recipients=[recipient],
        subject=subject,
        html_content=html_content,
        text_content=text_content
    ):
        print("✅ 测试邮件发送成功！")
        print("   请检查收件箱确认邮件已收到")
        return True
    else:
        print("❌ 测试邮件发送失败")
        return False

def test_weekly_confirmation_email():
    """测试周三确认通知邮件"""
    print("\n" + "="*60)
    print("📅 测试周三确认通知邮件")
    print("="*60)
    
    sender = EmailSender()
    
    # 创建测试收件人
    recipient = EmailRecipient(
        email="jonathanjing@graceirvine.org",
        name="Jonathan Jing",
        role="事工协调员"
    )
    
    # 创建测试数据
    test_schedules = [
        {
            'date': date.today() + timedelta(days=3),  # 本周日
            'time': '10:00',
            'location': 'Grace Irvine 教会',
            'roles': {
                '音控': '张三',
                '屏幕': '李四',
                '摄像/导播': '王五',
                'ProPresenter制作': '赵六',
                '视频剪辑': '靖铮'
            },
            'notes': '请提前15分钟到场准备'
        }
    ]
    
    print(f"发送周三确认通知到: {recipient.email}")
    if sender.send_weekly_confirmation(
        recipients=[recipient],
        week_schedules=test_schedules
    ):
        print("✅ 周三确认通知邮件发送成功！")
        return True
    else:
        print("❌ 周三确认通知邮件发送失败")
        return False

def test_sunday_reminder_email():
    """测试周六提醒通知邮件"""
    print("\n" + "="*60)
    print("🔔 测试周六提醒通知邮件")
    print("="*60)
    
    sender = EmailSender()
    
    # 创建测试收件人
    recipient = EmailRecipient(
        email="jonathanjing@graceirvine.org",
        name="Jonathan Jing",
        role="音控"
    )
    
    # 创建测试数据
    test_schedule = {
        'date': date.today() + timedelta(days=1),  # 明天
        'roles': {
            '音控': 'Jonathan Jing',
            '屏幕': '李四',
            '摄像/导播': '王五',
            'ProPresenter制作': '赵六',
            '视频剪辑': '靖铮'
        },
        'notes': '请携带设备检查清单'
    }
    
    print(f"发送周六提醒通知到: {recipient.email}")
    if sender.send_sunday_reminder(
        recipients=[recipient],
        sunday_schedule=test_schedule
    ):
        print("✅ 周六提醒通知邮件发送成功！")
        return True
    else:
        print("❌ 周六提醒通知邮件发送失败")
        return False

def test_with_real_data():
    """使用真实数据测试"""
    print("\n" + "="*60)
    print("📊 使用真实数据测试（如果可用）")
    print("="*60)
    
    # 尝试连接Google Sheets
    spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
    if not spreadsheet_id:
        print("⚠️  未设置 GOOGLE_SPREADSHEET_ID，跳过真实数据测试")
        return False
    
    try:
        print("正在连接 Google Sheets...")
        extractor = GoogleSheetsExtractor(spreadsheet_id)
        generator = NotificationGenerator(extractor)
        
        # 获取本周安排
        assignment = extractor.get_current_week_assignment()
        if assignment:
            print(f"✅ 获取到本周日({assignment.date})的安排:")
            print(f"   - 音控: {assignment.audio_tech}")
            print(f"   - 屏幕: {assignment.screen_operator}")
            print(f"   - 摄像/导播: {assignment.camera_operator}")
            print(f"   - ProPresenter: {assignment.propresenter}")
            
            # 转换为邮件格式
            schedule = {
                'date': assignment.date,
                'time': '10:00',
                'location': 'Grace Irvine 教会',
                'roles': {
                    '音控': assignment.audio_tech,
                    '屏幕': assignment.screen_operator,
                    '摄像/导播': assignment.camera_operator,
                    'ProPresenter制作': assignment.propresenter,
                    '视频剪辑': assignment.video_editor
                }
            }
            
            # 发送测试邮件
            sender = EmailSender()
            recipient = EmailRecipient(
                email="jonathanjing@graceirvine.org",
                name="Jonathan Jing"
            )
            
            print(f"\n发送真实数据测试邮件到: {recipient.email}")
            if sender.send_weekly_confirmation(
                recipients=[recipient],
                week_schedules=[schedule]
            ):
                print("✅ 真实数据测试邮件发送成功！")
                return True
        else:
            print("⚠️  未找到本周的事工安排")
            return False
            
    except Exception as e:
        print(f"❌ 真实数据测试失败: {e}")
        return False

def main():
    """主测试流程"""
    print("\n" + "🚀 Grace Irvine 事工管理系统 - 邮件通知测试 🚀")
    print("="*60)
    
    # 设置测试环境
    if not setup_test_environment():
        print("\n❌ 测试环境设置失败，请检查配置后重试")
        sys.exit(1)
    
    print("\n✅ 测试环境设置成功")
    
    # 测试菜单
    tests = {
        '1': ('测试SMTP连接', test_smtp_connection),
        '2': ('发送简单测试邮件', test_send_simple_email),
        '3': ('发送周三确认通知', test_weekly_confirmation_email),
        '4': ('发送周六提醒通知', test_sunday_reminder_email),
        '5': ('使用真实数据测试', test_with_real_data),
        '6': ('运行所有测试', None)
    }
    
    print("\n请选择要运行的测试:")
    for key, (name, _) in tests.items():
        print(f"  {key}. {name}")
    print("  0. 退出")
    
    choice = input("\n请输入选项 (0-6): ").strip()
    
    if choice == '0':
        print("退出测试")
        sys.exit(0)
    elif choice == '6':
        # 运行所有测试
        print("\n开始运行所有测试...")
        results = []
        for key in ['1', '2', '3', '4', '5']:
            name, test_func = tests[key]
            if test_func:
                print(f"\n正在运行: {name}")
                success = test_func()
                results.append((name, success))
        
        # 显示测试结果总结
        print("\n" + "="*60)
        print("📊 测试结果总结")
        print("="*60)
        for name, success in results:
            status = "✅ 成功" if success else "❌ 失败"
            print(f"{status} - {name}")
            
    elif choice in tests:
        name, test_func = tests[choice]
        if test_func:
            test_func()
    else:
        print("无效的选项")
    
    print("\n" + "="*60)
    print("测试完成！")
    
    # 提供下一步建议
    print("\n📝 下一步建议:")
    print("1. 如果测试成功，可以将邮件功能集成到主系统中")
    print("2. 配置定时任务，自动发送通知邮件")
    print("3. 添加更多收件人和邮件模板")
    print("4. 考虑添加邮件发送日志和错误处理")

if __name__ == "__main__":
    main()
