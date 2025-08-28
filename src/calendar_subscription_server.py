#!/usr/bin/env python3
"""
ICS日历订阅服务器
提供HTTP服务，支持日历应用通过URL订阅ICS日历

功能：
1. 提供固定URL的ICS日历订阅服务
2. 自动更新日历内容
3. 支持多种日历类型的订阅
4. 处理日历应用的定期刷新请求

部署方式：
1. 本地HTTP服务器
2. 云端部署（推荐）
3. Streamlit集成
"""

import os
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse
import threading
import time

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ICSSubscriptionHandler(SimpleHTTPRequestHandler):
    """ICS订阅请求处理器"""
    
    def __init__(self, *args, calendar_manager=None, **kwargs):
        self.calendar_manager = calendar_manager
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """处理GET请求"""
        try:
            path = urllib.parse.unquote(self.path)
            
            # 处理不同的日历订阅请求
            if path == '/coordinator.ics' or path == '/coordinator':
                self.serve_coordinator_calendar()
            elif path == '/workers.ics' or path == '/workers':
                self.serve_workers_calendar()
            elif path.startswith('/worker/') and path.endswith('.ics'):
                # 个人日历订阅 /worker/张三.ics
                worker_name = path.split('/')[-1].replace('.ics', '')
                self.serve_personal_calendar(worker_name)
            elif path == '/status':
                self.serve_status()
            elif path == '/' or path == '/index.html':
                self.serve_index()
            else:
                self.send_error(404, "Calendar not found")
                
        except Exception as e:
            logger.error(f"处理请求时出错: {e}")
            self.send_error(500, f"Internal server error: {e}")
    
    def serve_coordinator_calendar(self):
        """提供负责人日历"""
        try:
            # 生成最新的负责人日历
            ics_content = self.calendar_manager.get_fresh_coordinator_calendar()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/calendar; charset=utf-8')
            self.send_header('Content-Disposition', 'attachment; filename="grace_irvine_coordinator.ics"')
            self.send_header('Cache-Control', 'no-cache, must-revalidate')
            self.send_header('Expires', 'Thu, 01 Jan 1970 00:00:00 GMT')
            self.end_headers()
            
            self.wfile.write(ics_content.encode('utf-8'))
            logger.info("提供负责人日历订阅")
            
        except Exception as e:
            logger.error(f"生成负责人日历时出错: {e}")
            self.send_error(500, f"Calendar generation error: {e}")
    
    def serve_workers_calendar(self):
        """提供综合同工日历"""
        try:
            ics_content = self.calendar_manager.get_fresh_workers_calendar()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/calendar; charset=utf-8')
            self.send_header('Content-Disposition', 'attachment; filename="grace_irvine_workers.ics"')
            self.send_header('Cache-Control', 'no-cache, must-revalidate')
            self.send_header('Expires', 'Thu, 01 Jan 1970 00:00:00 GMT')
            self.end_headers()
            
            self.wfile.write(ics_content.encode('utf-8'))
            logger.info("提供同工日历订阅")
            
        except Exception as e:
            logger.error(f"生成同工日历时出错: {e}")
            self.send_error(500, f"Calendar generation error: {e}")
    
    def serve_personal_calendar(self, worker_name: str):
        """提供个人日历"""
        try:
            ics_content = self.calendar_manager.get_fresh_personal_calendar(worker_name)
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/calendar; charset=utf-8')
            self.send_header('Content-Disposition', f'attachment; filename="grace_irvine_{worker_name}.ics"')
            self.send_header('Cache-Control', 'no-cache, must-revalidate')
            self.send_header('Expires', 'Thu, 01 Jan 1970 00:00:00 GMT')
            self.end_headers()
            
            self.wfile.write(ics_content.encode('utf-8'))
            logger.info(f"提供 {worker_name} 的个人日历订阅")
            
        except Exception as e:
            logger.error(f"生成 {worker_name} 个人日历时出错: {e}")
            self.send_error(500, f"Personal calendar generation error: {e}")
    
    def serve_status(self):
        """提供系统状态"""
        try:
            status = self.calendar_manager.get_status()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            
            import json
            self.wfile.write(json.dumps(status, indent=2, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"获取状态时出错: {e}")
            self.send_error(500, f"Status error: {e}")
    
    def serve_index(self):
        """提供主页"""
        html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Grace Irvine 事工日历订阅</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .calendar-link { display: block; margin: 10px 0; padding: 15px; background: #f0f0f0; text-decoration: none; border-radius: 5px; }
        .calendar-link:hover { background: #e0e0e0; }
        h1 { color: #333; }
        .description { color: #666; margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>🕊️ Grace Irvine 事工日历订阅</h1>
    <p class="description">点击下面的链接订阅相应的日历，日历会自动更新最新的事工安排。</p>
    
    <h2>📅 可用的日历订阅</h2>
    
    <a href="/coordinator.ics" class="calendar-link">
        <strong>👨‍💼 负责人日历</strong><br>
        事工通知发送提醒（周三、周六、月初）
    </a>
    
    <a href="/workers.ics" class="calendar-link">
        <strong>👥 综合同工日历</strong><br>
        所有同工的服事安排
    </a>
    
    <h2>🔗 订阅方法</h2>
    <ul>
        <li><strong>Google Calendar:</strong> 添加日历 → 通过URL → 复制上面的链接</li>
        <li><strong>Apple Calendar:</strong> 文件 → 新建日历订阅 → 输入URL</li>
        <li><strong>Outlook:</strong> 添加日历 → 从Internet订阅</li>
    </ul>
    
    <h2>📊 系统状态</h2>
    <a href="/status" class="calendar-link">查看系统状态 (JSON格式)</a>
    
    <p><small>最后更新: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</small></p>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))

class CalendarSubscriptionManager:
    """日历订阅管理器"""
    
    def __init__(self, config_path: str = "configs/calendar_config.yaml"):
        self.config_path = config_path
        self.config = None
        self.sheets_extractor = None
        self.template_manager = None
        self.last_update = None
        self.cache_duration = 300  # 5分钟缓存
        self.cached_assignments = None
        
        self.load_config()
        self.initialize_components()
    
    def load_config(self):
        """加载配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
    
    def initialize_components(self):
        """初始化组件"""
        try:
            from src.scheduler import GoogleSheetsExtractor
            from src.template_manager import get_default_template_manager
            
            spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID') or self.config.get('sync_settings', {}).get('google_sheets_id', '')
            
            if spreadsheet_id:
                self.sheets_extractor = GoogleSheetsExtractor(spreadsheet_id)
                self.template_manager = get_default_template_manager()
                logger.info("✅ 订阅管理器组件初始化成功")
            else:
                logger.error("❌ 未配置Google Sheets ID")
                
        except Exception as e:
            logger.error(f"初始化组件失败: {e}")
    
    def get_fresh_data(self) -> List:
        """获取最新数据（带缓存）"""
        try:
            now = datetime.now()
            
            # 检查缓存
            if (self.cached_assignments and self.last_update and 
                (now - self.last_update).total_seconds() < self.cache_duration):
                logger.info("使用缓存数据")
                return self.cached_assignments
            
            # 获取新数据
            logger.info("从Google Sheets获取最新数据...")
            assignments = self.sheets_extractor.parse_ministry_data()
            
            # 更新缓存
            self.cached_assignments = assignments
            self.last_update = now
            
            logger.info(f"✅ 获取到 {len(assignments)} 条最新事工安排")
            return assignments
            
        except Exception as e:
            logger.error(f"获取数据失败: {e}")
            return self.cached_assignments or []
    
    def get_fresh_coordinator_calendar(self) -> str:
        """生成最新的负责人日历ICS内容"""
        try:
            assignments = self.get_fresh_data()
            
            if not assignments:
                return self._create_empty_calendar("Grace Irvine 事工协调日历")
            
            # 使用简化的ICS生成逻辑
            return self._generate_coordinator_ics_content(assignments)
            
        except Exception as e:
            logger.error(f"生成负责人日历失败: {e}")
            return self._create_empty_calendar("Grace Irvine 事工协调日历")
    
    def get_fresh_workers_calendar(self) -> str:
        """生成最新的同工日历ICS内容"""
        try:
            assignments = self.get_fresh_data()
            
            if not assignments:
                return self._create_empty_calendar("Grace Irvine 同工服事日历")
            
            return self._generate_workers_ics_content(assignments)
            
        except Exception as e:
            logger.error(f"生成同工日历失败: {e}")
            return self._create_empty_calendar("Grace Irvine 同工服事日历")
    
    def get_fresh_personal_calendar(self, worker_name: str) -> str:
        """生成最新的个人日历ICS内容"""
        try:
            assignments = self.get_fresh_data()
            
            if not assignments:
                return self._create_empty_calendar(f"{worker_name} - Grace Irvine 个人服事日历")
            
            return self._generate_personal_ics_content(assignments, worker_name)
            
        except Exception as e:
            logger.error(f"生成 {worker_name} 个人日历失败: {e}")
            return self._create_empty_calendar(f"{worker_name} - Grace Irvine 个人服事日历")
    
    def _generate_coordinator_ics_content(self, assignments: List) -> str:
        """生成负责人日历ICS内容"""
        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Grace Irvine Ministry Scheduler//Coordinator Calendar//CN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:Grace Irvine 事工协调日历",
            "X-WR-CALDESC:事工通知发送提醒日历（自动更新）",
            "X-WR-TIMEZONE:America/Los_Angeles",
            "REFRESH-INTERVAL;VALUE=DURATION:PT1H"  # 1小时刷新一次
        ]
        
        today = date.today()
        future_assignments = [a for a in assignments if a.date >= today][:10]
        
        for assignment in future_assignments:
            # 周三确认通知事件
            wednesday = assignment.date - timedelta(days=4)
            if wednesday >= today - timedelta(days=7):
                try:
                    notification_content = self.template_manager.render_weekly_confirmation(assignment)
                    event_ics = self._create_ics_event(
                        uid=f"weekly_confirmation_{wednesday.strftime('%Y%m%d')}@graceirvine.org",
                        summary=f"发送周末确认通知 ({assignment.date.month}/{assignment.date.day})",
                        description=f"发送内容：\n\n{notification_content}",
                        start_dt=datetime.combine(wednesday, datetime.min.time().replace(hour=20, minute=0)),
                        end_dt=datetime.combine(wednesday, datetime.min.time().replace(hour=20, minute=30)),
                        location="Grace Irvine 教会"
                    )
                    ics_lines.append(event_ics)
                except Exception as e:
                    logger.error(f"创建周三事件失败: {e}")
            
            # 周六提醒通知事件
            saturday = assignment.date - timedelta(days=1)
            if saturday >= today - timedelta(days=7):
                try:
                    notification_content = self.template_manager.render_sunday_reminder(assignment)
                    event_ics = self._create_ics_event(
                        uid=f"sunday_reminder_{saturday.strftime('%Y%m%d')}@graceirvine.org",
                        summary=f"发送主日提醒通知 ({assignment.date.month}/{assignment.date.day})",
                        description=f"发送内容：\n\n{notification_content}",
                        start_dt=datetime.combine(saturday, datetime.min.time().replace(hour=20, minute=0)),
                        end_dt=datetime.combine(saturday, datetime.min.time().replace(hour=20, minute=30)),
                        location="Grace Irvine 教会"
                    )
                    ics_lines.append(event_ics)
                except Exception as e:
                    logger.error(f"创建周六事件失败: {e}")
        
        ics_lines.append("END:VCALENDAR")
        return "\n".join(ics_lines)
    
    def _generate_workers_ics_content(self, assignments: List) -> str:
        """生成同工日历ICS内容"""
        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Grace Irvine Ministry Scheduler//Workers Calendar//CN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:Grace Irvine 同工服事日历",
            "X-WR-CALDESC:同工事工服事安排日历（自动更新）",
            "X-WR-TIMEZONE:America/Los_Angeles",
            "REFRESH-INTERVAL;VALUE=DURATION:PT1H"
        ]
        
        today = date.today()
        future_assignments = [a for a in assignments if a.date >= today][:10]
        
        for assignment in future_assignments:
            # 为每个角色创建服事事件
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
                        
                        event_ics = self._create_ics_event(
                            uid=f"service_{role_name}_{assignment.date.strftime('%Y%m%d')}_{person_name}@graceirvine.org",
                            summary=f"主日服事 - {role_name}",
                            description=f"角色：{role_name}\n负责人：{person_name}\n到场时间：{start_time}\n\n愿主同在，出入平安！",
                            start_dt=datetime.combine(assignment.date, datetime.min.time().replace(hour=start_hour, minute=start_minute)),
                            end_dt=datetime.combine(assignment.date, datetime.min.time().replace(hour=end_hour, minute=end_minute)),
                            location="Grace Irvine 教会"
                        )
                        ics_lines.append(event_ics)
                    except Exception as e:
                        logger.error(f"创建 {person_name} 服事事件失败: {e}")
        
        ics_lines.append("END:VCALENDAR")
        return "\n".join(ics_lines)
    
    def _generate_personal_ics_content(self, assignments: List, worker_name: str) -> str:
        """生成个人日历ICS内容"""
        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Grace Irvine Ministry Scheduler//Personal Calendar//CN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            f"X-WR-CALNAME:{worker_name} - Grace Irvine 个人服事日历",
            f"X-WR-CALDESC:{worker_name}的个人事工服事安排（自动更新）",
            "X-WR-TIMEZONE:America/Los_Angeles",
            "REFRESH-INTERVAL;VALUE=DURATION:PT1H"
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
                    
                    event_ics = self._create_ics_event(
                        uid=f"personal_{role_name}_{assignment.date.strftime('%Y%m%d')}_{worker_name}@graceirvine.org",
                        summary=f"我的服事 - {role_name}",
                        description=f"角色：{role_name}\n日期：{assignment.date}\n到场时间：{start_time}\n\n愿主同在，出入平安！",
                        start_dt=datetime.combine(assignment.date, datetime.min.time().replace(hour=start_hour, minute=start_minute)),
                        end_dt=datetime.combine(assignment.date, datetime.min.time().replace(hour=end_hour, minute=end_minute)),
                        location="Grace Irvine 教会"
                    )
                    ics_lines.append(event_ics)
                except Exception as e:
                    logger.error(f"创建 {worker_name} 个人事件失败: {e}")
        
        ics_lines.append("END:VCALENDAR")
        return "\n".join(ics_lines)
    
    def _create_ics_event(self, uid: str, summary: str, description: str, 
                         start_dt: datetime, end_dt: datetime, location: str = "") -> str:
        """创建ICS事件字符串"""
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
    
    def _create_empty_calendar(self, calendar_name: str) -> str:
        """创建空日历"""
        return f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Grace Irvine Ministry Scheduler//Empty Calendar//CN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:{calendar_name}
X-WR-CALDESC:暂无事工安排数据
X-WR-TIMEZONE:America/Los_Angeles
END:VCALENDAR"""
    
    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'cache_duration_seconds': self.cache_duration,
            'components_initialized': {
                'sheets_extractor': self.sheets_extractor is not None,
                'template_manager': self.template_manager is not None
            },
            'cached_assignments_count': len(self.cached_assignments) if self.cached_assignments else 0
        }

def create_subscription_handler(calendar_manager):
    """创建订阅处理器工厂"""
    class CustomHandler(ICSSubscriptionHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, calendar_manager=calendar_manager, **kwargs)
    return CustomHandler

def start_subscription_server(port: int = 8080):
    """启动订阅服务器"""
    try:
        # 初始化日历管理器
        calendar_manager = CalendarSubscriptionManager()
        
        # 创建HTTP服务器
        handler_class = create_subscription_handler(calendar_manager)
        httpd = HTTPServer(('', port), handler_class)
        
        print(f"🚀 Grace Irvine ICS订阅服务器启动")
        print(f"📡 监听端口: {port}")
        print(f"🔗 订阅地址:")
        print(f"   负责人日历: http://localhost:{port}/coordinator.ics")
        print(f"   同工日历: http://localhost:{port}/workers.ics")
        print(f"   个人日历: http://localhost:{port}/worker/姓名.ics")
        print(f"   管理页面: http://localhost:{port}/")
        print(f"📊 系统状态: http://localhost:{port}/status")
        print("\n按 Ctrl+C 停止服务器")
        
        # 启动服务器
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        print("\n🛑 正在停止服务器...")
        httpd.shutdown()
        print("✅ 服务器已停止")
    except Exception as e:
        print(f"❌ 启动服务器失败: {e}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Grace Irvine ICS订阅服务器")
    parser.add_argument('--port', type=int, default=8080, help='服务器端口 (默认: 8080)')
    
    args = parser.parse_args()
    
    # 检查环境
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv('GOOGLE_SPREADSHEET_ID'):
        print("❌ 错误: 请在 .env 文件中设置 GOOGLE_SPREADSHEET_ID")
        return
    
    start_subscription_server(args.port)

if __name__ == "__main__":
    main()
