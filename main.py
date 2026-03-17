#!/usr/bin/env python3
"""
Grace Irvine ICS Generator - 精简重构版
Cloud Function / Cloud Run 入口

功能:
1. 从 Google Sheets 读取排程数据（智能列匹配）
2. 结合预设经文生成通知内容
3. 生成 ICS 文件（周三/周六通知）
4. 上传到 Cloud Storage

环境变量:
- GOOGLE_SPREADSHEET_ID: Google Sheets ID
- GCP_STORAGE_BUCKET: 存储桶名称 (默认: grace-irvine-ministry-scheduler)
- SERVICE_ACCOUNT_KEY: 服务账号 JSON (可选，Cloud Run 默认凭据)
"""

import os
import sys
import re
import json
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# =============================================================================
# 配置
# =============================================================================

class Config:
    """应用配置"""
    
    def __init__(self):
        # 必需配置
        self.spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
        if not self.spreadsheet_id:
            raise ValueError("GOOGLE_SPREADSHEET_ID environment variable is required")
        
        self.bucket_name = os.getenv('GCP_STORAGE_BUCKET', 'grace-irvine-ministry-scheduler')
        
        # ICS 生成配置
        self.weeks_ahead = int(os.getenv('ICS_WEEKS_AHEAD', '4'))
        
        # 周三通知配置: 周三 19:00-21:00 (晚上7点到9点)
        self.wednesday_enabled = os.getenv('WEDNESDAY_ENABLED', 'true').lower() == 'true'
        self.wednesday_weekday = int(os.getenv('WEDNESDAY_WEEKDAY', '2'))  # 周三 (0=周一, 2=周三, 6=周日)
        self.wednesday_hour = int(os.getenv('WEDNESDAY_HOUR', '19'))  # 19:00
        self.wednesday_minute = int(os.getenv('WEDNESDAY_MINUTE', '0'))
        self.wednesday_duration = int(os.getenv('WEDNESDAY_DURATION', '120'))  # 2小时
        # 计算周日到周三的天数差 (周日=6, 周三=2, 差值为 2-6 = -4, 即往前推4天)
        self.wednesday_days_before_sunday = (6 - self.wednesday_weekday) % 7
        
        # 周六通知配置: 周六 09:00-10:00 (早上9点到10点)
        self.saturday_enabled = os.getenv('SATURDAY_ENABLED', 'true').lower() == 'true'
        self.saturday_weekday = int(os.getenv('SATURDAY_WEEKDAY', '5'))  # 周六 (0=周一, 5=周六, 6=周日)
        self.saturday_hour = int(os.getenv('SATURDAY_HOUR', '9'))  # 09:00
        self.saturday_minute = int(os.getenv('SATURDAY_MINUTE', '0'))
        self.saturday_duration = int(os.getenv('SATURDAY_DURATION', '60'))  # 1小时
        # 计算周日到周六的天数差 (周日=6, 周六=5, 差值为 5-6 = -1, 即往前推1天)
        self.saturday_days_before_sunday = (6 - self.saturday_weekday) % 7
        
        # 经文轮换
        self.scripture_rotation = os.getenv('SCRIPTURE_ROTATION', 'true').lower() == 'true'
    
    @classmethod
    def from_env(cls) -> 'Config':
        """从环境变量加载配置"""
        return cls()


# =============================================================================
# 数据模型
# =============================================================================

@dataclass
class MinistryAssignment:
    """事工安排数据模型"""
    date: date
    audio_tech: Optional[str] = None          # 音控
    video_director: Optional[str] = None      # 导播/摄影
    propresenter_play: Optional[str] = None   # ProPresenter播放
    propresenter_update: Optional[str] = None # ProPresenter更新
    video_editor: Optional[str] = None        # 视频剪辑
    
    def get_all_assignments(self, show_empty: bool = True) -> Dict[str, str]:
        """获取所有事工安排，空缺显示'待安排'"""
        assignments = {}
        assignments['音控'] = self.audio_tech if self.audio_tech else '待安排'
        assignments['导播/摄影'] = self.video_director if self.video_director else '待安排'
        assignments['ProPresenter播放'] = self.propresenter_play if self.propresenter_play else '待安排'
        assignments['ProPresenter更新'] = self.propresenter_update if self.propresenter_update else '待安排'
        assignments['视频剪辑'] = self.video_editor if self.video_editor else '待安排'
        return assignments


# =============================================================================
# 预设经文
# =============================================================================

# 默认经文列表 - 格式与原来一致
DEFAULT_SCRIPTURES = [
    """看哪，弟兄和睦同居
是何等地善，何等地美！
(诗篇 133:1 和合本)""",
    """又要彼此相顾，激发爱心，勉励行善。
你们不可停止聚会，好像那些停止惯了的人，
(希伯来书 10:24-25 和合本)""",
    """用诗章、颂词、灵歌彼此对说，
口唱心和地赞美主。
(以弗所书 5:19 和合本)""",
    """凡你们所做的，都要凭爱心而做。
(哥林多前书 16:14 和合本)""",
    """所以，你们或吃或喝，无论做什么，
都要为荣耀神而行。
(哥林多前书 10:31 和合本)""",
    """愿主我们神的荣美归于我们身上。
愿你坚立我们手所做的工。
(诗篇 90:17 和合本)""",
    """你们当乐意事奉耶和华，
当来向他歌唱！
(诗篇 100:2 和合本)""",
    """按我们所得的恩赐，各有不同。
或说预言，就当照着信心的程度说预言；
或作执事，就当专一执事；
或作教导的，就当专一教导；
或作劝化的，就当专一劝化；
施舍的，就当诚实；
治理的，就当殷勤；
怜悯人的，就当甘心。
(罗马书 12:6-8 和合本)""",
]


def load_scriptures_from_env() -> List[str]:
    """从环境变量加载经文列表
    
    环境变量 SCRIPTURES 格式（JSON 数组字符串）:
    '["经文1", "经文2", ...]'
    
    或使用 SCRIPTURE_1, SCRIPTURE_2, ... 单独设置
    """
    # 方法1: 从 JSON 数组加载
    scriptures_json = os.getenv('SCRIPTURES')
    if scriptures_json:
        try:
            scriptures = json.loads(scriptures_json)
            if isinstance(scriptures, list) and len(scriptures) > 0:
                logger.info(f"✅ 从环境变量加载 {len(scriptures)} 条经文")
                return scriptures
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ SCRIPTURES 环境变量格式错误: {e}")
    
    # 方法2: 从单独的环境变量加载 (SCRIPTURE_1, SCRIPTURE_2, ...)
    scriptures = []
    for i in range(1, 100):  # 最多支持 99 条经文
        scripture = os.getenv(f'SCRIPTURE_{i}')
        if scripture:
            scriptures.append(scripture)
    
    if scriptures:
        logger.info(f"✅ 从 SCRIPTURE_N 环境变量加载 {len(scriptures)} 条经文")
        return scriptures
    
    # 使用默认经文
    logger.info(f"✅ 使用默认经文列表 ({len(DEFAULT_SCRIPTURES)} 条)")
    return DEFAULT_SCRIPTURES


class ScriptureStore:
    """预设经文存储"""
    
    def __init__(self, scriptures: Optional[List[str]] = None):
        # 优先使用传入的经文列表，否则从环境变量加载
        self.scriptures = scriptures if scriptures else load_scriptures_from_env()
        self._current_index = 0
    
    def get_scripture_for_date(self, target_date: date) -> str:
        """根据日期获取经文（轮换）"""
        # 使用日期作为种子，确保同一日期总是返回相同经文
        days_since_epoch = (target_date - date(2024, 1, 1)).days
        index = days_since_epoch % len(self.scriptures)
        return self.scriptures[index]
    
    def get_all_scriptures(self) -> List[str]:
        """获取所有经文"""
        return self.scriptures.copy()
    
    def get_scripture_count(self) -> int:
        """获取经文数量"""
        return len(self.scriptures)


# =============================================================================
# Google Sheets 读取（智能列匹配）
# =============================================================================

class SheetsReader:
    """Google Sheets 读取器 - 智能列匹配"""
    
    # 列名匹配模式 - 支持多种可能的列名变体
    COLUMN_PATTERNS = {
        'date': [
            '日期', 'date', '主日日期', '时间', '礼拜日期', '主日', 'sunday', 'date',
            r'\d{1,2}/\d{1,2}/\d{4}',
        ],
        'audio_tech': [
            '音控', 'audio', 'sound', '音响', '音频', 'audio tech', 'sound control', 'audio_tech',
        ],
        'video_director': [
            '导播/摄影', '摄影/导播', 'video/camera', 'camera/video',
            '导播', '摄影', 'video', 'camera', '直播', 'stream', 'video director',
            'video_director', '导播摄影', '摄影导播',
        ],
        'propresenter_play': [
            'propresenter播放', 'propresenter play', 'ppt播放', '幻灯片播放',
            'pro presenter播放', 'pro presenter play', 'presentation播放',
            'propresenter', 'ppt', '幻灯片', 'presentation', 'propresenter_play',
            '播放', 'play',
        ],
        'propresenter_update': [
            'propresenter更新', 'propresenter update', 'ppt更新', '幻灯片更新',
            'pro presenter更新', 'pro presenter update', 'presentation更新',
            '更新', 'update', 'propresenter_update',
        ],
        'video_editor': [
            '视频剪辑', 'video editor', '剪辑', 'editor', 'video_editor', 'video editing',
        ],
    }
    
    def __init__(self, spreadsheet_id: str):
        self.spreadsheet_id = spreadsheet_id
        self.client = None
        self._setup_client()
    
    def _setup_client(self):
        """初始化 Google Sheets 客户端"""
        try:
            from google.oauth2.service_account import Credentials
            import gspread
            
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets.readonly',
                'https://www.googleapis.com/auth/drive.readonly'
            ]
            
            # 尝试从环境变量读取服务账号
            service_account_key = os.getenv('SERVICE_ACCOUNT_KEY')
            
            if service_account_key:
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    f.write(service_account_key)
                    temp_path = f.name
                credentials = Credentials.from_service_account_file(temp_path, scopes=scopes)
            else:
                # 使用默认凭据（Cloud Run 环境）
                from google.auth import default
                credentials, _ = default(scopes=scopes)
            
            self.client = gspread.authorize(credentials)
            logger.info("✅ Google Sheets 客户端初始化成功")
            
        except Exception as e:
            logger.error(f"❌ Google Sheets 客户端初始化失败: {e}")
            raise
    
    def read_data(self, sheet_name: str = '总表') -> List[MinistryAssignment]:
        """读取并解析数据"""
        try:
            import pandas as pd
            
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            worksheet = spreadsheet.worksheet(sheet_name)
            values = worksheet.get_all_values()
            
            if len(values) < 2:
                logger.warning("表格数据不足（至少需要2行：部门标题+列名）")
                return []
            
            # 调试：打印前5行原始数据
            logger.info(f"🔍 原始数据前5行:")
            for i in range(min(5, len(values))):
                logger.info(f"  行 {i}: {values[i][:5]}...")  # 只打印前5列
            
            # 跳过第一行（部门标题），使用第二行作为实际列名
            headers = values[1]
            df = pd.DataFrame(values[2:], columns=headers)
            
            logger.info(f"📊 读取到 {len(df)} 行数据，{len(df.columns)} 列")
            logger.info(f"📋 所有列名: {list(df.columns)}")
            
            # 智能匹配列
            column_mapping = self._match_columns(df)
            logger.info(f"🔍 列映射结果: {column_mapping}")
            
            # 解析数据 - 过滤掉旧数据和无效日期
            assignments = []
            skipped_rows = 0
            
            for idx, row in df.iterrows():
                assignment = self._parse_row(row, column_mapping)
                
                # 过滤：只保留 2026 年以后的排程
                if assignment and assignment.date.year >= 2026:
                    assignments.append(assignment)
                else:
                    skipped_rows += 1
            
            logger.info(f"✅ 成功解析 {len(assignments)} 条 2026 年以后排程 (跳过 {skipped_rows} 行旧数据/无效行)")
            return assignments
            
        except Exception as e:
            logger.error(f"❌ 读取数据失败: {e}")
            raise
    
    def _match_columns(self, df) -> Dict[str, Optional[int]]:
        """智能匹配列名 - 优先匹配更长的精确列名"""
        mapping = {}
        available_columns = {i: str(col).strip().lower() for i, col in enumerate(df.columns)}
        
        for field, patterns in self.COLUMN_PATTERNS.items():
            best_match = None
            best_match_length = 0
            
            for col_index, col_name_lower in available_columns.items():
                for pattern in patterns:
                    if isinstance(pattern, str):
                        pattern_lower = pattern.lower()
                        if pattern_lower in col_name_lower:
                            # 优先选择更长的匹配（更精确）
                            if len(pattern_lower) > best_match_length:
                                best_match = col_index
                                best_match_length = len(pattern_lower)
                                break
                    else:
                        if re.search(pattern, col_name_lower, re.IGNORECASE):
                            best_match = col_index
                            best_match_length = 999  # 正则表达式视为高优先级
                            break
            
            if best_match is not None:
                mapping[field] = best_match
                original_name = df.columns[best_match]
                logger.info(f"  ✅ {field} → '{original_name}' (索引 {best_match})")
            else:
                logger.warning(f"  ⚠️ {field} 未找到匹配的列")
                mapping[field] = None
        
        return mapping
    
    def _parse_row(self, row, column_mapping: Dict[str, Optional[int]], row_idx: int = -1) -> Optional[MinistryAssignment]:
        """解析单行数据"""
        # 解析日期
        date_col_idx = column_mapping.get('date')
        date_value = self._get_column_value(row, date_col_idx)
        
        # 调试：打印前3行的日期解析过程
        if row_idx >= 0 and row_idx < 3:
            logger.info(f"  [DEBUG] 行 {row_idx}: date_col_idx={date_col_idx}, date_value='{date_value}'")
        
        parsed_date = self._parse_date(date_value)
        if not parsed_date:
            return None
        
        # 解析人员
        audio_tech = self._clean_name(self._get_column_value(row, column_mapping.get('audio_tech')))
        video_director = self._clean_name(self._get_column_value(row, column_mapping.get('video_director')))
        propresenter_play = self._clean_name(self._get_column_value(row, column_mapping.get('propresenter_play')))
        propresenter_update = self._clean_name(self._get_column_value(row, column_mapping.get('propresenter_update')))
        video_editor = self._clean_name(self._get_column_value(row, column_mapping.get('video_editor')))
        
        # 只有当至少有一个角色有人时才创建记录
        if any([audio_tech, video_director, propresenter_play, propresenter_update, video_editor]):
            return MinistryAssignment(
                date=parsed_date,
                audio_tech=audio_tech,
                video_director=video_director,
                propresenter_play=propresenter_play,
                propresenter_update=propresenter_update,
                video_editor=video_editor
            )
        return None
    
    def _get_column_value(self, row, col_index: Optional[int]) -> Optional[str]:
        """获取列值"""
        if col_index is None:
            return None
        try:
            import pandas as pd
            value = row.iloc[col_index] if hasattr(row, 'iloc') else row[col_index]
            # 调试：打印原始值类型和内容
            # logger.info(f"  [DEBUG] col_index={col_index}, value={repr(value)}, type={type(value)}")
            if pd.notna(value) and str(value).strip():
                return str(value).strip()
            return None
        except Exception as e:
            logger.warning(f"  [DEBUG] 获取列值失败: {e}")
            return None
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """解析日期"""
        if not date_str:
            return None
        
        date_str = str(date_str).strip()
        if not date_str:
            return None
        
        # 尝试多种日期格式
        patterns = [
            (r'(\d{1,2})/(\d{1,2})/(\d{4})', lambda m: date(int(m.group(3)), int(m.group(1)), int(m.group(2)))),
            (r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', lambda m: date(int(m.group(1)), int(m.group(2)), int(m.group(3)))),
            (r'(\d{1,2})月(\d{1,2})日', lambda m: date(date.today().year, int(m.group(1)), int(m.group(2)))),
        ]
        
        for pattern, parser in patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    return parser(match)
                except ValueError:
                    continue
        
        # 使用 pandas 解析
        try:
            import pandas as pd
            parsed = pd.to_datetime(date_str, infer_datetime_format=True)
            return parsed.date()
        except:
            return None
    
    def _clean_name(self, name: Optional[str]) -> Optional[str]:
        """清洗人名 - 过滤无效值"""
        if not name:
            return None
        
        name = str(name).strip()
        
        # 无效模式（包含"待安排"）
        invalid_patterns = [
            r'^$', r'^-+$', r'^[?？]+$', 
            r'^(待定|待安排|TBD|N/A|NA|待定中|待确认|暂无|无)$',
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, name, re.IGNORECASE):
                return None
        
        # 清洗
        name = re.sub(r'\s+', ' ', name)
        name = re.sub(r'^[0-9]+\s*', '', name)
        name = re.sub(r'\s*[0-9]+$', '', name)
        name = re.sub(r'[（(].*?[）)]', '', name)
        name = re.sub(r'[，,].*$', '', name)
        
        return name.strip() if name else None


# =============================================================================
# ICS 生成器
# =============================================================================

class ICSGenerator:
    """ICS 日历生成器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.scripture_store = ScriptureStore()
    
    def generate(self, assignments: List[MinistryAssignment]) -> str:
        """生成 ICS 文件内容"""
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Grace Irvine Ministry Scheduler//Coordinator Calendar//CN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:Grace Irvine 事工协调日历",
            "X-WR-CALDESC:事工通知发送提醒日历（Cloud Scheduler自动更新）",
            "X-WR-TIMEZONE:America/Los_Angeles",
            f"X-WR-CALDESC:最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        
        today = date.today()
        future_assignments = [a for a in assignments if a.date >= today][:self.config.weeks_ahead * 2]
        
        events_count = 0
        
        for assignment in future_assignments:
            # 周三通知事件
            if self.config.wednesday_enabled:
                event = self._create_wednesday_event(assignment)
                if event:
                    lines.append(event)
                    events_count += 1
            
            # 周六通知事件
            if self.config.saturday_enabled:
                event = self._create_saturday_event(assignment)
                if event:
                    lines.append(event)
                    events_count += 1
        
        lines.append("END:VCALENDAR")
        
        logger.info(f"✅ 生成 ICS: {events_count} 个事件")
        return "\n".join(lines)
    
    def _create_wednesday_event(self, assignment: MinistryAssignment) -> Optional[str]:
        """创建周三通知事件"""
        try:
            # 计算周三日期
            days_before = self.config.wednesday_days_before_sunday
            event_date = assignment.date - timedelta(days=days_before)
            
            # 如果事件日期已经过去，跳过
            if event_date < date.today() - timedelta(days=7):
                return None
            
            # 获取经文
            scripture = self.scripture_store.get_scripture_for_date(event_date)
            
            # 生成通知内容
            notification = self._render_wednesday_notification(assignment, scripture)
            
            # 创建事件
            return self._create_ics_event(
                uid=f"weekly_confirmation_{event_date.strftime('%Y%m%d')}@graceirvine.org",
                summary=f"发送周末确认通知 ({assignment.date.month}/{assignment.date.day})",
                description=notification,
                event_date=event_date,
                hour=self.config.wednesday_hour,
                minute=self.config.wednesday_minute,
                duration=self.config.wednesday_duration
            )
            
        except Exception as e:
            logger.error(f"创建周三事件失败: {e}")
            return None
    
    def _create_saturday_event(self, assignment: MinistryAssignment) -> Optional[str]:
        """创建周六通知事件"""
        try:
            # 计算周六日期
            days_before = self.config.saturday_days_before_sunday
            event_date = assignment.date - timedelta(days=days_before)
            
            # 如果事件日期已经过去，跳过
            if event_date < date.today() - timedelta(days=7):
                return None
            
            # 生成通知内容
            notification = self._render_saturday_notification(assignment)
            
            # 创建事件
            return self._create_ics_event(
                uid=f"sunday_reminder_{event_date.strftime('%Y%m%d')}@graceirvine.org",
                summary=f"发送主日提醒通知 ({assignment.date.month}/{assignment.date.day})",
                description=notification,
                event_date=event_date,
                hour=self.config.saturday_hour,
                minute=self.config.saturday_minute,
                duration=self.config.saturday_duration
            )
            
        except Exception as e:
            logger.error(f"创建周六事件失败: {e}")
            return None
    
    def _render_wednesday_notification(self, assignment: MinistryAssignment, scripture: str) -> str:
        """渲染周三通知内容 - 匹配原有格式，使用真实换行符"""
        assignments = assignment.get_all_assignments()
        
        lines = [
            f"【本周{assignment.date.month}月{assignment.date.day}日主日事工安排提醒】🕊️",
            "",
        ]
        
        for role, person in assignments.items():
            lines.append(f"• {role}：{person}")
        
        lines.extend([
            "",
            f"📖 {scripture}",
            "",
            "请大家确认时间，若有冲突请尽快私信我，感谢摆上 🙏"
        ])
        
        # 使用真实换行符，ICS 会正确处理
        return "\n".join(lines)
    
    def _render_saturday_notification(self, assignment: MinistryAssignment) -> str:
        """渲染周六通知内容 - 匹配原有格式，使用真实换行符"""
        assignments = assignment.get_all_assignments()
        
        lines = [
            f"【明天{assignment.date.month}月{assignment.date.day}日主日事工提醒】🕊️",
            "",
        ]
        
        for role, person in assignments.items():
            lines.append(f"• {role}：{person}")
        
        lines.extend([
            "",
            "请提前做好准备，按时到场。",
            "",
            "愿神祝福！"
        ])
        
        # 使用真实换行符，ICS 会正确处理
        return "\n".join(lines)
    
    def _create_ics_event(self, uid: str, summary: str, description: str, 
                         event_date: date, hour: int, minute: int, duration: int = 30) -> str:
        """创建单个 ICS 事件"""
        start_dt = datetime.combine(event_date, datetime.min.time().replace(hour=hour, minute=minute))
        end_dt = start_dt + timedelta(minutes=duration)
        dtstamp = datetime.now()
        
        # 转义特殊字符
        summary_escaped = summary.replace('\\', '\\\\').replace(',', '\\,').replace(';', '\\;').replace('\n', '\\n')
        description_escaped = description.replace('\\', '\\\\').replace(',', '\\,').replace(';', '\\;').replace('\n', '\\n')
        
        lines = [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{dtstamp.strftime('%Y%m%dT%H%M%S')}",
            f"DTSTART:{start_dt.strftime('%Y%m%dT%H%M%S')}",
            f"DTEND:{end_dt.strftime('%Y%m%dT%H%M%S')}",
            f"SUMMARY:{summary_escaped}",
            f"DESCRIPTION:{description_escaped}",
            "LOCATION:Grace Irvine 教会",
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            f"DESCRIPTION:提醒：{summary_escaped}",
            "TRIGGER:-PT30M",
            "END:VALARM",
            "END:VEVENT"
        ]
        
        return "\n".join(lines)


# =============================================================================
# Cloud Storage 上传
# =============================================================================

class StorageUploader:
    """Cloud Storage 上传器"""
    
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self.client = None
        self._setup_client()
    
    def _setup_client(self):
        """初始化 Storage 客户端"""
        try:
            from google.cloud import storage
            self.client = storage.Client()
            logger.info("✅ Cloud Storage 客户端初始化成功")
        except Exception as e:
            logger.error(f"❌ Cloud Storage 客户端初始化失败: {e}")
            raise
    
    def upload(self, content: str, filename: str) -> str:
        """上传文件到 Cloud Storage"""
        try:
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(f"calendars/{filename}")
            
            blob.upload_from_string(
                content,
                content_type='text/calendar; charset=utf-8'
            )
            
            # 设置公开访问
            blob.make_public()
            
            logger.info(f"✅ 文件已上传: {blob.public_url}")
            return blob.public_url
            
        except Exception as e:
            logger.error(f"❌ 上传失败: {e}")
            raise


# =============================================================================
# HTTP 入口
# =============================================================================

def generate_ics(request):
    """Cloud Function / Cloud Run HTTP 入口
    
    支持 GET 和 POST 请求
    """
    try:
        logger.info("🚀 开始生成 ICS 日历...")
        
        # 加载配置
        config = Config.from_env()
        
        # 读取数据
        reader = SheetsReader(config.spreadsheet_id)
        assignments = reader.read_data()
        
        if not assignments:
            return {
                'success': False,
                'error': '未找到事工安排数据'
            }, 400
        
        # 生成 ICS
        generator = ICSGenerator(config)
        ics_content = generator.generate(assignments)
        
        # 上传
        uploader = StorageUploader(config.bucket_name)
        public_url = uploader.upload(ics_content, 'grace_irvine_coordinator.ics')
        
        # 获取经文信息
        scripture_count = generator.scripture_store.get_scripture_count()
        
        # 返回结果
        result = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'calendar_url': public_url,
            'events_count': ics_content.count('BEGIN:VEVENT'),
            'assignments_processed': len(assignments),
            'scriptures': {
                'count': scripture_count,
                'source': 'env' if os.getenv('SCRIPTURES') or os.getenv('SCRIPTURE_1') else 'default'
            },
            'config': {
                'weeks_ahead': config.weeks_ahead,
                'wednesday': {
                    'enabled': config.wednesday_enabled,
                    'weekday': config.wednesday_weekday,
                    'time': f"{config.wednesday_hour:02d}:{config.wednesday_minute:02d}",
                    'duration': config.wednesday_duration,
                },
                'saturday': {
                    'enabled': config.saturday_enabled,
                    'weekday': config.saturday_weekday,
                    'time': f"{config.saturday_hour:02d}:{config.saturday_minute:02d}",
                    'duration': config.saturday_duration,
                },
            }
        }
        
        logger.info("✅ ICS 生成完成")
        return result, 200
        
    except Exception as e:
        logger.error(f"❌ 生成失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, 500


# 本地测试入口
if __name__ == "__main__":
    from flask import Flask, request
    
    app = Flask(__name__)
    
    @app.route('/generate-ics', methods=['GET', 'POST'])
    def handle_generate():
        result, status_code = generate_ics(request)
        return result, status_code
    
    print("🧪 本地测试服务器: http://localhost:8080")
    app.run(host='0.0.0.0', port=8080, debug=True)
