#!/usr/bin/env python3
"""
Grace Irvine Ministry Scheduler - 简化版实现
专门针对微信群通知的三个模板

使用方法:
1. 将 service account JSON 文件放在 configs/service_account.json
2. 在 .env 文件中设置 GOOGLE_SPREADSHEET_ID
3. 运行: python simple_scheduler.py
"""

import os
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from dataclasses import dataclass
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MinistryAssignment:
    """事工安排数据结构"""
    date: date
    audio_tech: str = ""      # 音控
    screen_operator: str = ""  # 屏幕
    camera_operator: str = ""  # 摄像/导播
    propresenter: str = ""     # Propresenter 制作
    video_editor: str = "靖铮"  # 视频剪辑（固定）

class GoogleSheetsExtractor:
    """Google Sheets 数据提取器"""
    
    def __init__(self, spreadsheet_id: str, service_account_path: str = "configs/service_account.json"):
        self.spreadsheet_id = spreadsheet_id
        self.service_account_path = service_account_path
        self.client = None
        self.spreadsheet = None
        self._setup_client()
    
    def _setup_client(self):
        """初始化 Google Sheets 客户端"""
        try:
            if not Path(self.service_account_path).exists():
                raise FileNotFoundError(f"Service account file not found: {self.service_account_path}")
            
            # 设置认证范围
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets.readonly',
                'https://www.googleapis.com/auth/drive.readonly'
            ]
            
            # 创建认证凭据
            credentials = Credentials.from_service_account_file(
                self.service_account_path, 
                scopes=scopes
            )
            
            # 初始化客户端
            self.client = gspread.authorize(credentials)
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            
            logger.info(f"Successfully connected to Google Sheets: {self.spreadsheet.title}")
            
        except Exception as e:
            logger.error(f"Failed to setup Google Sheets client: {e}")
            raise
    
    def get_raw_data(self, sheet_name: str = "总表") -> List[List[str]]:
        """获取原始表格数据"""
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            values = worksheet.get_all_values()
            logger.info(f"Retrieved {len(values)} rows from sheet '{sheet_name}'")
            return values
        except Exception as e:
            logger.error(f"Failed to get data from sheet '{sheet_name}': {e}")
            raise
    
    def parse_ministry_data(self, sheet_name: str = "总表") -> List[MinistryAssignment]:
        """解析事工数据
        
        假设表格结构（根据实际情况调整列索引）:
        A: 日期
        B: 音控
        C: 屏幕
        D: 摄像/导播
        E: Propresenter制作
        """
        raw_data = self.get_raw_data(sheet_name)
        
        if not raw_data:
            logger.warning("No data found in spreadsheet")
            return []
        
        assignments = []
        
        # 跳过标题行，从第二行开始处理
        for i, row in enumerate(raw_data[1:], start=2):
            try:
                # 确保行有足够的列
                while len(row) < 6:
                    row.append("")
                
                # 解析日期 (A列)
                date_str = row[0].strip() if row[0] else ""
                if not date_str:
                    continue
                
                parsed_date = self._parse_date(date_str)
                if not parsed_date:
                    logger.warning(f"Could not parse date in row {i}: {date_str}")
                    continue
                
                # 解析各个角色 (根据实际列位置调整)
                assignment = MinistryAssignment(
                    date=parsed_date,
                    audio_tech=self._clean_name(row[1]),        # B列 - 音控
                    screen_operator=self._clean_name(row[2]),   # C列 - 屏幕
                    camera_operator=self._clean_name(row[3]),   # D列 - 摄像/导播
                    propresenter=self._clean_name(row[4]),      # E列 - Propresenter制作
                    video_editor="靖铮"  # 固定值
                )
                
                # 只添加有实际安排的记录
                if any([assignment.audio_tech, assignment.screen_operator, 
                       assignment.camera_operator, assignment.propresenter]):
                    assignments.append(assignment)
                    
            except Exception as e:
                logger.warning(f"Error processing row {i}: {e}")
                continue
        
        # 按日期排序
        assignments.sort(key=lambda x: x.date)
        logger.info(f"Successfully parsed {len(assignments)} ministry assignments")
        return assignments
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """解析各种日期格式"""
        if not date_str:
            return None
        
        date_str = date_str.strip()
        
        # 常见日期格式
        formats = [
            "%Y-%m-%d",     # 2024-01-14
            "%Y/%m/%d",     # 2024/01/14
            "%Y-%m-%d",     # 2024-1-14
            "%Y/%m/%d",     # 2024/1/14
            "%m/%d/%Y",     # 1/14/2024
            "%m-%d-%Y",     # 1-14-2024
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        # 尝试 pandas 解析
        try:
            return pd.to_datetime(date_str).date()
        except:
            return None
    
    def _clean_name(self, name: str) -> str:
        """清理姓名"""
        if not name:
            return ""
        
        name = str(name).strip()
        if name.lower() in ['', '-', 'n/a', 'tbd', '待定', '无']:
            return ""
        
        return name
    
    def get_current_week_assignment(self) -> Optional[MinistryAssignment]:
        """获取本周主日的事工安排"""
        assignments = self.parse_ministry_data()
        
        # 计算本周日的日期
        today = date.today()
        days_until_sunday = (6 - today.weekday()) % 7  # 0=周一, 6=周日
        if days_until_sunday == 0 and today.weekday() == 6:  # 今天是周日
            this_sunday = today
        else:
            this_sunday = today + timedelta(days=days_until_sunday)
        
        # 查找本周日的安排
        for assignment in assignments:
            if assignment.date == this_sunday:
                return assignment
        
        return None
    
    def get_next_sunday_assignment(self) -> Optional[MinistryAssignment]:
        """获取下个主日的事工安排"""
        assignments = self.parse_ministry_data()
        
        # 计算下个主日的日期
        today = date.today()
        days_until_next_sunday = (6 - today.weekday()) % 7
        if days_until_next_sunday == 0:  # 今天是周日
            days_until_next_sunday = 7
        next_sunday = today + timedelta(days=days_until_next_sunday)
        
        # 查找下个主日的安排
        for assignment in assignments:
            if assignment.date == next_sunday:
                return assignment
        
        return None
    
    def get_monthly_assignments(self, year: int = None, month: int = None) -> List[MinistryAssignment]:
        """获取指定月份的所有事工安排"""
        assignments = self.parse_ministry_data()
        
        if year is None:
            year = date.today().year
        if month is None:
            month = date.today().month
        
        monthly_assignments = [
            assignment for assignment in assignments
            if assignment.date.year == year and assignment.date.month == month
        ]
        
        return monthly_assignments

class NotificationGenerator:
    """通知生成器"""
    
    def __init__(self, extractor: GoogleSheetsExtractor):
        self.extractor = extractor
    
    def generate_weekly_confirmation(self) -> str:
        """生成周三晚上的确认通知 (模板1)"""
        assignment = self.extractor.get_current_week_assignment()
        
        if not assignment:
            return "【本周主日事工安排提醒】🕊️\n\n暂无本周事工安排，请联系协调员确认。"
        
        # 格式化日期
        month = assignment.date.month
        day = assignment.date.day
        
        template = f"""【本周{month}月{day}日主日事工安排提醒】🕊️

• 音控：{assignment.audio_tech or '待安排'}
• 屏幕：{assignment.screen_operator or '待安排'}
• 摄像/导播：{assignment.camera_operator or '待安排'}
• Propresenter 制作：{assignment.propresenter or '待安排'}
• 视频剪辑：{assignment.video_editor}

请大家确认时间，若有冲突请尽快私信我，感谢摆上 🙏"""
        
        return template
    
    def generate_sunday_reminder(self) -> str:
        """生成周六晚上的提醒通知 (模板2)"""
        # 周六发送时应该获取下个主日的安排
        assignment = self.extractor.get_next_sunday_assignment()
        
        if not assignment:
            return "【主日服事提醒】✨\n\n暂无明日事工安排，请联系协调员确认。"
        
        template = f"""【主日服事提醒】✨
明天 8:30布置/ 9:00彩排 / 10:00 正式敬拜  
请各位同工提前到场：  
- 音控：{assignment.audio_tech or '待安排'} 9:00到，随敬拜团排练
- 屏幕：{assignment.screen_operator or '待安排'} 9:00到，随敬拜团排练
- 摄像/导播: {assignment.camera_operator or '待安排'} 9:30到，检查预设机位

愿主同在，出入平安。若临时不适请第一时间私信我。🙌"""
        
        return template
    
    def generate_monthly_overview(self, year: int = None, month: int = None) -> str:
        """生成月初的排班一览通知 (模板3)"""
        if year is None:
            year = date.today().year
        if month is None:
            month = date.today().month
        
        assignments = self.extractor.get_monthly_assignments(year, month)
        
        # 构建月度安排表格
        schedule_text = ""
        if assignments:
            schedule_text = "\n当月安排预览：\n"
            for assignment in assignments:
                month_day = f"{assignment.date.month}/{assignment.date.day}"
                roles = []
                if assignment.audio_tech:
                    roles.append(f"音控:{assignment.audio_tech}")
                if assignment.screen_operator:
                    roles.append(f"屏幕:{assignment.screen_operator}")
                if assignment.camera_operator:
                    roles.append(f"摄像:{assignment.camera_operator}")
                if assignment.propresenter:
                    roles.append(f"制作:{assignment.propresenter}")
                
                if roles:
                    schedule_text += f"• {month_day}: {', '.join(roles)}\n"
        
        # 获取 Google Sheets 链接
        sheet_url = f"https://docs.google.com/spreadsheets/d/{self.extractor.spreadsheet_id}"
        
        template = f"""【{year}年{month:02d}月事工排班一览】📅
请各位同工先行预留时间，如有冲突尽快与我沟通：
{sheet_url}
{schedule_text}
温馨提示：
- 周三晚发布当周安排（确认/调换）
- 周六晚发布主日提醒（到场时间）
感谢大家同心配搭！🙏"""
        
        return template

def main():
    """主函数 - 测试和演示"""
    
    # 从环境变量获取配置
    from dotenv import load_dotenv
    load_dotenv()
    
    spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
    if not spreadsheet_id:
        logger.error("请在 .env 文件中设置 GOOGLE_SPREADSHEET_ID")
        return
    
    try:
        # 初始化数据提取器
        logger.info("正在连接 Google Sheets...")
        extractor = GoogleSheetsExtractor(spreadsheet_id)
        
        # 初始化通知生成器
        generator = NotificationGenerator(extractor)
        
        # 测试数据提取
        logger.info("正在测试数据提取...")
        assignments = extractor.parse_ministry_data()
        logger.info(f"成功获取 {len(assignments)} 条事工安排")
        
        # 显示最近的几条记录
        if assignments:
            logger.info("最近的事工安排:")
            for assignment in assignments[:3]:
                logger.info(f"  {assignment.date}: 音控={assignment.audio_tech}, 屏幕={assignment.screen_operator}")
        
        print("\n" + "="*50)
        print("通知模板测试")
        print("="*50)
        
        # 生成并显示三个模板
        print("\n【模板1 - 周三确认通知】")
        print("-" * 30)
        weekly_notification = generator.generate_weekly_confirmation()
        print(weekly_notification)
        
        print("\n【模板2 - 周六提醒通知】")
        print("-" * 30)
        sunday_notification = generator.generate_sunday_reminder()
        print(sunday_notification)
        
        print("\n【模板3 - 月度总览通知】")
        print("-" * 30)
        monthly_notification = generator.generate_monthly_overview()
        print(monthly_notification)
        
        print("\n" + "="*50)
        print("测试完成！")
        print("="*50)
        
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
