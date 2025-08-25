#!/usr/bin/env python3
"""
Grace Irvine Ministry Scheduler - 专注数据清洗器
Focused Data Cleaner for specific columns (A, Q, S, T, U)

根据 configs/config.yaml 配置，只提取指定的列：
- A: 日期 (主日日期)
- Q: 音控
- S: 导播/摄影  
- T: ProPresenter播放
- U: ProPresenter更新
"""
import pandas as pd
import re
import json
import ssl
import urllib.request
import io
import yaml
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path
from dataclasses import dataclass

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent


@dataclass
class MinistrySchedule:
    """事工排程数据结构"""
    date: date
    audio_tech: Optional[str] = None          # 音控 (Q列)
    video_director: Optional[str] = None      # 导播/摄影 (S列)
    propresenter_play: Optional[str] = None   # ProPresenter播放 (T列)
    propresenter_update: Optional[str] = None # ProPresenter更新 (U列)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'date': self.date.strftime('%Y-%m-%d'),
            'audio_tech': self.audio_tech,
            'video_director': self.video_director,
            'propresenter_play': self.propresenter_play,
            'propresenter_update': self.propresenter_update
        }
    
    def get_all_assignments(self) -> Dict[str, str]:
        """获取所有非空的事工安排"""
        assignments = {}
        if self.audio_tech:
            assignments['音控'] = self.audio_tech
        if self.video_director:
            assignments['导播/摄影'] = self.video_director
        if self.propresenter_play:
            assignments['ProPresenter播放'] = self.propresenter_play
        if self.propresenter_update:
            assignments['ProPresenter更新'] = self.propresenter_update
        return assignments


class FocusedDataCleaner:
    """
    专注的数据清洗器
    只提取和处理配置文件中指定的列 (A, Q, S, T, U)
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化数据清洗器
        
        Args:
            config_path: 配置文件路径，默认使用 configs/config.yaml
        """
        if config_path is None:
            config_path = PROJECT_ROOT / "configs" / "config.yaml"
        
        self.config = self._load_config(config_path)
        self.spreadsheet_id = self.config['spreadsheet_id']
        self.sheet_name = self.config.get('sheet_name', '总表')
        self.csv_url = f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/export?format=csv&gid=0"
        
        self.stats = {
            'total_rows': 0,
            'valid_rows': 0,
            'cleaned_names': 0,
            'invalid_dates': 0,
            'empty_rows_removed': 0
        }
    
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"⚠️  无法加载配置文件 {config_path}: {e}")
            # 使用默认配置
            return {
                'spreadsheet_id': '1wescUQe9rIVLNcKdqmSLpzlAw9BGXMZmkFvjEF296nM',
                'sheet_name': '总表',
                'columns': {
                    'date': 'A',
                    'roles': [
                        {'key': 'Q', 'service_type': '音控'},
                        {'key': 'S', 'service_type': '导播/摄影'},
                        {'key': 'T', 'service_type': 'ProPresenter播放'},
                        {'key': 'U', 'service_type': 'ProPresenter更新'}
                    ]
                }
            }
    
    def download_data(self) -> pd.DataFrame:
        """下载 Google Sheets 数据"""
        try:
            print(f"📥 正在从 Google Sheets 下载数据...")
            print(f"📊 表格ID: {self.spreadsheet_id}")
            print(f"📋 工作表: {self.sheet_name}")
            
            # 创建 SSL 上下文
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # 下载数据
            try:
                df = pd.read_csv(self.csv_url, encoding='utf-8')
            except Exception as ssl_error:
                print(f"🔒 SSL 错误，使用不安全连接: {ssl_error}")
                req = urllib.request.Request(self.csv_url)
                with urllib.request.urlopen(req, context=ssl_context) as response:
                    csv_data = response.read().decode('utf-8')
                df = pd.read_csv(io.StringIO(csv_data))
            
            self.stats['total_rows'] = len(df)
            print(f"✅ 成功下载 {len(df)} 行数据")
            
            return df
            
        except Exception as e:
            print(f"❌ 下载数据失败: {e}")
            raise
    
    def extract_focused_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """提取指定的列 (A, Q, S, T, U)"""
        print("🎯 提取指定列: A, Q, S, T, U")
        
        # 列名映射 (基于位置)
        column_mapping = {
            'A': 0,   # 日期列
            'Q': 16,  # 音控 (第17列)
            'S': 18,  # 导播/摄影 (第19列)
            'T': 19,  # ProPresenter播放 (第20列)
            'U': 20   # ProPresenter更新 (第21列)
        }
        
        focused_data = {}
        
        for col_letter, col_index in column_mapping.items():
            if col_index < len(df.columns):
                focused_data[col_letter] = df.iloc[:, col_index]
                print(f"  ✅ {col_letter}列 ({df.columns[col_index]})")
            else:
                print(f"  ⚠️  {col_letter}列不存在 (索引 {col_index})")
                focused_data[col_letter] = pd.Series([None] * len(df))
        
        # 创建新的 DataFrame
        focused_df = pd.DataFrame(focused_data)
        
        # 重命名列
        focused_df.columns = ['日期', '音控', '导播/摄影', 'ProPresenter播放', 'ProPresenter更新']
        
        print(f"🎯 成功提取 {len(focused_df)} 行，{len(focused_df.columns)} 列")
        return focused_df
    
    def clean_person_name(self, name: Any) -> Optional[str]:
        """清洗人名数据"""
        if pd.isna(name) or name is None:
            return None
        
        name = str(name).strip()
        
        # 检查无效模式
        invalid_patterns = [
            r'^$',  # 空字符串
            r'^-+$',  # 只有短横线
            r'^[?？]+$',  # 只有问号
            r'^(待定|TBD|tbd|N/A|n/a|NA|na)$',  # 待定标记
            r'^[0-9]+$',  # 纯数字
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, name, re.IGNORECASE):
                return None
        
        # 清洗规则
        cleaning_patterns = [
            (r'\s+', ' '),  # 多个空格合并
            (r'^[0-9]+\s*', ''),  # 移除开头数字
            (r'\s*[0-9]+$', ''),  # 移除结尾数字
            (r'[（(].*?[）)]', ''),  # 移除括号内容
            (r'[，,].*$', ''),  # 移除逗号后内容
        ]
        
        original_name = name
        for pattern, replacement in cleaning_patterns:
            name = re.sub(pattern, replacement, name).strip()
        
        if len(name) < 1 or len(name) > 50:
            return None
        
        if name != original_name:
            self.stats['cleaned_names'] += 1
        
        return name
    
    def parse_date(self, date_str: Any) -> Optional[date]:
        """解析日期"""
        if pd.isna(date_str) or date_str is None:
            return None
        
        date_str = str(date_str).strip()
        if not date_str:
            return None
        
        # 日期格式模式
        patterns = [
            (r'(\d{1,2})/(\d{1,2})/(\d{4})', 'mdy'),  # MM/DD/YYYY
            (r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', 'ymd'),  # YYYY/MM/DD
            (r'(\d{1,2})月(\d{1,2})日', 'md_chinese'),  # X月Y日
        ]
        
        for pattern, format_type in patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    if format_type == 'mdy':
                        month, day, year = map(int, match.groups())
                    elif format_type == 'ymd':
                        year, month, day = map(int, match.groups())
                    elif format_type == 'md_chinese':
                        month, day = map(int, match.groups())
                        year = datetime.now().year
                        if month < datetime.now().month:
                            year += 1
                    
                    return date(year, month, day)
                except ValueError:
                    continue
        
        # 使用 pandas 解析
        try:
            parsed_date = pd.to_datetime(date_str, infer_datetime_format=True)
            return parsed_date.date()
        except:
            self.stats['invalid_dates'] += 1
            return None
    
    def clean_focused_data(self, df: pd.DataFrame) -> List[MinistrySchedule]:
        """清洗专注的数据并转换为 MinistrySchedule 对象"""
        print("🧹 开始清洗数据...")
        
        schedules = []
        
        for index, row in df.iterrows():
            # 解析日期
            parsed_date = self.parse_date(row['日期'])
            if not parsed_date:
                continue
            
            # 清洗人名
            audio_tech = self.clean_person_name(row['音控'])
            video_director = self.clean_person_name(row['导播/摄影'])
            propresenter_play = self.clean_person_name(row['ProPresenter播放'])
            propresenter_update = self.clean_person_name(row['ProPresenter更新'])
            
            # 只有当至少有一个角色有人时才创建记录
            if any([audio_tech, video_director, propresenter_play, propresenter_update]):
                schedule = MinistrySchedule(
                    date=parsed_date,
                    audio_tech=audio_tech,
                    video_director=video_director,
                    propresenter_play=propresenter_play,
                    propresenter_update=propresenter_update
                )
                schedules.append(schedule)
        
        self.stats['valid_rows'] = len(schedules)
        print(f"✅ 清洗完成，生成 {len(schedules)} 个有效排程记录")
        
        return schedules
    
    def generate_summary_report(self, schedules: List[MinistrySchedule]) -> Dict[str, Any]:
        """生成汇总报告"""
        if not schedules:
            return {
                'total_schedules': 0,
                'date_range': None,
                'role_statistics': {},
                'volunteer_statistics': {}
            }
        
        # 统计信息
        dates = [s.date for s in schedules]
        date_range = f"{min(dates)} 至 {max(dates)}"
        
        # 角色统计
        role_stats = {
            '音控': sum(1 for s in schedules if s.audio_tech),
            '导播/摄影': sum(1 for s in schedules if s.video_director),
            'ProPresenter播放': sum(1 for s in schedules if s.propresenter_play),
            'ProPresenter更新': sum(1 for s in schedules if s.propresenter_update)
        }
        
        # 志愿者统计
        all_volunteers = set()
        for schedule in schedules:
            if schedule.audio_tech:
                all_volunteers.add(schedule.audio_tech)
            if schedule.video_director:
                all_volunteers.add(schedule.video_director)
            if schedule.propresenter_play:
                all_volunteers.add(schedule.propresenter_play)
            if schedule.propresenter_update:
                all_volunteers.add(schedule.propresenter_update)
        
        return {
            'total_schedules': len(schedules),
            'date_range': date_range,
            'role_statistics': role_stats,
            'volunteer_statistics': {
                'total_volunteers': len(all_volunteers),
                'volunteer_list': sorted(list(all_volunteers))
            }
        }
    
    def export_to_excel(self, schedules: List[MinistrySchedule], output_path: str):
        """导出到 Excel 文件"""
        try:
            # 转换为 DataFrame
            data = []
            for schedule in schedules:
                data.append({
                    '日期': schedule.date.strftime('%Y-%m-%d'),
                    '星期': ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][schedule.date.weekday()],
                    '音控': schedule.audio_tech or '',
                    '导播/摄影': schedule.video_director or '',
                    'ProPresenter播放': schedule.propresenter_play or '',
                    'ProPresenter更新': schedule.propresenter_update or ''
                })
            
            df = pd.DataFrame(data)
            df.to_excel(output_path, index=False, engine='openpyxl')
            print(f"✅ 数据已导出到: {output_path}")
            
        except Exception as e:
            print(f"❌ 导出失败: {e}")
            raise
    
    def find_next_sunday_schedule(self, schedules: List[MinistrySchedule]) -> Optional[MinistrySchedule]:
        """查找下周主日的排程"""
        today = date.today()
        days_until_sunday = (6 - today.weekday()) % 7
        if days_until_sunday == 0:  # 如果今天是周日
            days_until_sunday = 7
        next_sunday = today + timedelta(days=days_until_sunday)
        
        for schedule in schedules:
            if schedule.date == next_sunday:
                return schedule
        
        return None
    
    def process_complete_workflow(self) -> Dict[str, Any]:
        """执行完整的数据处理工作流"""
        try:
            print("🚀 开始完整数据处理工作流...")
            print("=" * 50)
            
            # 1. 下载原始数据
            raw_df = self.download_data()
            
            # 2. 提取指定列
            focused_df = self.extract_focused_columns(raw_df)
            
            # 3. 清洗数据
            schedules = self.clean_focused_data(focused_df)
            
            # 4. 生成报告
            summary_report = self.generate_summary_report(schedules)
            
            # 5. 导出数据
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            data_dir = PROJECT_ROOT / "data"
            data_dir.mkdir(exist_ok=True)
            
            excel_file = data_dir / f"focused_schedule_{timestamp}.xlsx"
            self.export_to_excel(schedules, str(excel_file))
            
            # 6. 保存处理报告
            report = {
                'timestamp': datetime.now().isoformat(),
                'config': self.config,
                'processing_stats': self.stats,
                'summary_report': summary_report,
                'output_files': {
                    'excel_file': str(excel_file)
                }
            }
            
            report_file = data_dir / f"processing_report_{timestamp}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            
            print("\n📊 处理统计:")
            print(f"  • 原始行数: {self.stats['total_rows']}")
            print(f"  • 有效排程: {self.stats['valid_rows']}")
            print(f"  • 清洗人名: {self.stats['cleaned_names']}")
            print(f"  • 无效日期: {self.stats['invalid_dates']}")
            
            print(f"\n📋 汇总报告:")
            print(f"  • 排程总数: {summary_report['total_schedules']}")
            print(f"  • 日期范围: {summary_report['date_range']}")
            print(f"  • 志愿者总数: {summary_report['volunteer_statistics']['total_volunteers']}")
            
            print(f"\n🎯 角色统计:")
            for role, count in summary_report['role_statistics'].items():
                print(f"  • {role}: {count} 次")
            
            print(f"\n📁 输出文件:")
            print(f"  • Excel文件: {excel_file}")
            print(f"  • 报告文件: {report_file}")
            
            # 7. 查找下周主日
            next_sunday_schedule = self.find_next_sunday_schedule(schedules)
            if next_sunday_schedule:
                print(f"\n📅 下周主日 ({next_sunday_schedule.date.strftime('%Y-%m-%d')}) 安排:")
                assignments = next_sunday_schedule.get_all_assignments()
                if assignments:
                    for role, person in assignments.items():
                        print(f"  • {role}: {person}")
                else:
                    print("  • 暂无安排")
            else:
                today = date.today()
                days_until_sunday = (6 - today.weekday()) % 7
                if days_until_sunday == 0:
                    days_until_sunday = 7
                next_sunday = today + timedelta(days=days_until_sunday)
                print(f"\n⚠️  未找到下周主日 ({next_sunday.strftime('%Y-%m-%d')}) 的安排")
            
            print("\n🎉 数据处理完成！")
            print("=" * 50)
            
            return {
                'success': True,
                'schedules': schedules,
                'summary_report': summary_report,
                'output_files': {
                    'excel_file': str(excel_file),
                    'report_file': str(report_file)
                }
            }
            
        except Exception as e:
            print(f"\n❌ 处理失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }


def main():
    """主函数"""
    print("🎯 Grace Irvine Ministry Scheduler - 专注数据清洗器")
    print("📋 只提取列: A(日期), Q(音控), S(导播/摄影), T(ProPresenter播放), U(ProPresenter更新)")
    print("=" * 70)
    
    try:
        # 创建数据清洗器
        cleaner = FocusedDataCleaner()
        
        # 执行完整工作流
        result = cleaner.process_complete_workflow()
        
        if result['success']:
            print("\n✅ 所有任务完成！您现在可以:")
            print("  1. 查看生成的 Excel 文件")
            print("  2. 检查处理报告")
            print("  3. 使用清洗后的数据生成通知模板")
        else:
            print(f"\n❌ 处理失败: {result['error']}")
            return 1
            
    except KeyboardInterrupt:
        print("\n👋 用户中断操作")
        return 0
    except Exception as e:
        print(f"\n💥 意外错误: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
