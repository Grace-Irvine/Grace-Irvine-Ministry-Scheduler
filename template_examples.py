#!/usr/bin/env python3
"""
模板修改示例

这个文件展示了如何修改通知模板的具体例子。
您可以复制这些代码片段到 simple_scheduler.py 中替换原有的模板。
"""

from datetime import date

# 示例数据
class ExampleAssignment:
    def __init__(self):
        self.date = date(2024, 1, 14)
        self.audio_tech = "张三"
        self.screen_operator = "李四"
        self.camera_operator = "王五"
        self.propresenter = "赵六"
        self.video_editor = "靖铮"

assignment = ExampleAssignment()

# ============================================================================
# 1. 周三确认通知的不同样式
# ============================================================================

def example_weekly_simple():
    """简洁版周三通知"""
    month = assignment.date.month
    day = assignment.date.day
    
    template = f"""【{month}/{day} 主日事工】🕊️

音控:{assignment.audio_tech or 'TBD'} | 屏幕:{assignment.screen_operator or 'TBD'}
摄像:{assignment.camera_operator or 'TBD'} | 制作:{assignment.propresenter or 'TBD'}
剪辑:{assignment.video_editor}

有冲突请私信 🙏"""
    
    return template

def example_weekly_detailed():
    """详细版周三通知"""
    month = assignment.date.month
    day = assignment.date.day
    
    template = f"""🎵【恩典尔湾长老教会】🎵
═══════════════════════════

📅 {assignment.date.year}年{month}月{day}日主日事工安排

👥 服事团队：
🎤 音控：{assignment.audio_tech or '❌待安排'}
📺 屏幕：{assignment.screen_operator or '❌待安排'}  
📹 摄像/导播：{assignment.camera_operator or '❌待安排'}
💻 Propresenter：{assignment.propresenter or '❌待安排'}
✂️ 视频剪辑：{assignment.video_editor}

⏰ 重要时间：
• 周三晚 8:00 - 最终确认截止
• 主日上午 9:00 - 同工到场时间
• 主日上午 10:00 - 正式敬拜

请大家及时确认，若有冲突请尽快私信协调
感谢各位忠心的服事！🙏✨

═══════════════════════════"""
    
    return template

def example_weekly_table():
    """表格版周三通知"""
    month = assignment.date.month
    day = assignment.date.day
    
    template = f"""【本周{month}月{day}日主日事工安排提醒】🕊️

┌─────────────┬──────────────┐
│   服事项目   │   负责同工    │
├─────────────┼──────────────┤
│     音控     │ {assignment.audio_tech or '待安排':^10} │
│     屏幕     │ {assignment.screen_operator or '待安排':^10} │
│   摄像/导播   │ {assignment.camera_operator or '待安排':^10} │
│ PP制作       │ {assignment.propresenter or '待安排':^10} │
│   视频剪辑    │ {assignment.video_editor:^10} │
└─────────────┴──────────────┘

请大家确认时间，若有冲突请尽快私信我
感谢摆上 🙏"""
    
    return template

# ============================================================================
# 2. 周六提醒通知的不同样式  
# ============================================================================

def example_sunday_urgent():
    """紧急版周六通知"""
    template = f"""🚨【明日主日紧急提醒】🚨

⏰ 明天 8:30开始布置，请准时到场！

服事同工：
{assignment.audio_tech or 'TBD'}(音控) ➜ 9:00到
{assignment.screen_operator or 'TBD'}(屏幕) ➜ 9:00到  
{assignment.camera_operator or 'TBD'}(摄像) ➜ 9:30到

⚠️ 有急事请立即联系协调员！
🙏 为明天的敬拜祷告"""
    
    return template

def example_sunday_formal():
    """正式版周六通知"""
    template = f"""【恩典尔湾长老教会 - 主日服事提醒】✨

亲爱的事工团队同工们，主内平安！

📅 明日主日聚会安排：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
日期：{assignment.date.strftime('%Y年%m月%d日')} (主日)
地点：主堂
时间：上午 10:00 正式开始

⏰ 详细时间安排：
• 8:30-9:00  会场布置，设备准备
• 9:00-9:45  敬拜团队彩排
• 9:45-10:00 最后检查，预备心灵
• 10:00      正式敬拜开始

👥 明日服事同工：
🎤 音控同工：{assignment.audio_tech or '待确认'} 
   ↳ 请 9:00 准时到场，配合敬拜团排练
   
📺 屏幕同工：{assignment.screen_operator or '待确认'}
   ↳ 请 9:00 准时到场，测试投影设备
   
📹 摄像同工：{assignment.camera_operator or '待确认'}
   ↳ 请 9:30 到场，检查和调整机位
   
💻 制作同工：{assignment.propresenter or '待确认'}
   ↳ 请提前准备好 PPT 和相关材料

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🙏 祷告事项：
• 为明日的敬拜时光祷告
• 为讲员和敬拜团队祷告  
• 为会众的心预备祷告
• 为技术设备顺利运行祷告

愿主耶稣亲自与我们同在，出入平安！
若临时有事无法服事，请第一时间私信告知。

神祝福您！🌟"""
    
    return template

def example_sunday_checklist():
    """清单版周六通知"""
    template = f"""【明日主日服事清单】✅

📋 {assignment.audio_tech or '音控同工'}，您明天需要：
☐ 9:00 到场
☐ 检查音响设备
☐ 配合敬拜团彩排  
☐ 调试麦克风音量

📋 {assignment.screen_operator or '屏幕同工'}，您明天需要：
☐ 9:00 到场
☐ 测试投影仪
☐ 检查PPT播放
☐ 准备歌词显示

📋 {assignment.camera_operator or '摄像同工'}，您明天需要：  
☐ 9:30 到场
☐ 检查摄像设备
☐ 调整机位角度
☐ 测试录制功能

🕘 重要提醒：提前10分钟到场更佳！
🙏 愿主使用我们的服事"""
    
    return template

# ============================================================================
# 3. 月度通知的不同样式
# ============================================================================

def example_monthly_statistics():
    """统计版月度通知"""
    year = 2024
    month = 1
    
    # 模拟统计数据
    total_services = 4
    total_volunteers = 8
    
    template = f"""📊【{year}年{month:02d}月事工统计报告】📊

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 本月数据一览：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 基本统计：
• 主日聚会：{total_services} 次
• 参与同工：{total_volunteers} 位  
• 服事岗位：4 个类别
• 服事频次：平均每人 2.1 次

🏆 服事排行（按次数）：
🥇 张三 - 4次 (音控专家)
🥈 李四 - 3次 (屏幕能手)  
🥉 王五 - 3次 (摄像达人)
   赵六 - 2次 (制作高手)

📅 详细排班表：
https://docs.google.com/spreadsheets/d/your_sheet_id

📋 本月具体安排：
• 1/7: 张三(音控), 李四(屏幕), 王五(摄像), 赵六(制作)
• 1/14: 钱七(音控), 孙八(屏幕), 周九(摄像), 吴十(制作)
• 1/21: 张三(音控), 孙八(屏幕), 王五(摄像), 赵六(制作)
• 1/28: 钱七(音控), 李四(屏幕), 周九(摄像), 吴十(制作)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 温馨提示：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ 周三晚 8:00 发布当周安排确认
✓ 周六晚 8:00 发布主日服事提醒  
✓ 如有冲突请提前2周告知
✓ 临时调换请自行找到替补同工
✓ 感谢各位的忠心摆上和配搭

🙏 愿神纪念每一份服事的心，赐福每一位同工！"""
    
    return template

def example_monthly_simple():
    """简洁版月度通知"""
    year = 2024
    month = 1
    
    template = f"""【{month}月排班】📅

1/7: 张三(音控), 李四(屏幕), 王五(摄像), 赵六(制作)
1/14: 钱七(音控), 孙八(屏幕), 周九(摄像), 吴十(制作)  
1/21: 张三(音控), 孙八(屏幕), 王五(摄像), 赵六(制作)
1/28: 钱七(音控), 李四(屏幕), 周九(摄像), 吴十(制作)

📋 完整表格：
https://docs.google.com/spreadsheets/d/your_sheet_id

有冲突请提前告知 🙏"""
    
    return template

# ============================================================================
# 4. 特殊情况的模板
# ============================================================================

def example_special_holiday():
    """节日特殊通知"""
    month = 12
    day = 25
    
    template = f"""🎄【圣诞节主日特别安排】🎄

亲爱的同工们，圣诞快乐！

📅 12月25日圣诞节主日特别提醒：

🎵 今日安排：
• 音控：{assignment.audio_tech or '待安排'} 
• 屏幕：{assignment.screen_operator or '待安排'}
• 摄像/导播：{assignment.camera_operator or '待安排'}
• Propresenter：{assignment.propresenter or '待安排'}
• 视频剪辑：{assignment.video_editor}

⏰ 特别时间安排：
• 8:00 - 会场布置（圣诞装饰）
• 8:30 - 设备调试  
• 9:00 - 敬拜团彩排
• 10:00 - 圣诞节特别敬拜

🎁 特别注意：
• 今天有圣诞节特别节目，可能需要额外技术支持
• 预计会众较多，请提前调试音响
• 有圣诞装饰，注意摄像角度调整
• 准备录制圣诞节特别信息

🙏 让我们以喜乐的心迎接救主降生的日子！
感谢各位在这特别的日子里的摆上！

以马内利！🌟"""
    
    return template

def example_emergency_replacement():
    """紧急替补通知"""
    template = f"""🚨【紧急通知 - 需要替补】🚨

各位同工注意！

由于 {assignment.audio_tech} 临时有急事，
明日主日 音控 岗位急需替补！

📅 时间：明日主日 9:00-11:30
📍 地点：主堂音控台
🔧 要求：熟悉基本音响操作

已确认的其他同工：
• 屏幕：{assignment.screen_operator} ✅
• 摄像：{assignment.camera_operator} ✅  
• 制作：{assignment.propresenter} ✅

🙏 请有经验的同工紧急支援！
能够帮忙的请立即回复！

感谢理解与配合！🙇‍♂️"""
    
    return template

# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("模板修改示例")
    print("=" * 60)
    
    print("\n📅 周三确认通知 - 简洁版：")
    print("-" * 40)
    print(example_weekly_simple())
    
    print("\n📅 周三确认通知 - 详细版：") 
    print("-" * 40)
    print(example_weekly_detailed())
    
    print("\n🔔 周六提醒通知 - 紧急版：")
    print("-" * 40) 
    print(example_sunday_urgent())
    
    print("\n📊 月度通知 - 统计版：")
    print("-" * 40)
    print(example_monthly_statistics())
    
    print("\n🎄 特殊节日通知：")
    print("-" * 40)
    print(example_special_holiday())
    
    print("\n" + "=" * 60)
    print("您可以将喜欢的模板复制到 simple_scheduler.py 中！")
    print("=" * 60)
