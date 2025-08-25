#!/usr/bin/env python3
"""
简化版 Google Sheets 数据清洗工具
Simplified Google Sheets Data Cleaning Tool

这个版本使用公开的 Google Sheets CSV 导出功能，无需复杂的 API 认证
This version uses public Google Sheets CSV export, no complex API authentication needed
"""
import pandas as pd
import re
import json
import ssl
import urllib.request
from datetime import datetime, date
from typing import Optional, Dict, Any, List
import argparse
import sys
from pathlib import Path

# 项目根目录
project_root = Path(__file__).parent


class SimpleDataCleaner:
    """简化版数据清洗器"""
    
    def __init__(self, spreadsheet_id: str):
        self.spreadsheet_id = spreadsheet_id
        self.csv_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid=0"
        self.stats = {
            'total_rows': 0,
            'valid_rows': 0,
            'cleaned_names': 0,
            'invalid_dates': 0,
            'empty_rows_removed': 0
        }
    
    def download_data(self) -> pd.DataFrame:
        """下载 Google Sheets 数据"""
        try:
            print(f"正在从 Google Sheets 下载数据...")
            print(f"URL: {self.csv_url}")
            
            # 创建不验证 SSL 证书的上下文（用于解决证书问题）
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # 使用 pandas 读取 CSV，并指定 SSL 上下文
            try:
                df = pd.read_csv(self.csv_url, encoding='utf-8')
            except Exception as ssl_error:
                print(f"SSL 错误，尝试使用不安全连接: {ssl_error}")
                # 如果 SSL 有问题，尝试使用 requests 或其他方法
                import urllib.request
                import io
                
                # 创建请求，忽略 SSL 验证
                req = urllib.request.Request(self.csv_url)
                with urllib.request.urlopen(req, context=ssl_context) as response:
                    csv_data = response.read().decode('utf-8')
                
                # 使用 StringIO 创建 DataFrame
                df = pd.read_csv(io.StringIO(csv_data))
            
            self.stats['total_rows'] = len(df)
            print(f"成功下载 {len(df)} 行数据")
            print(f"列名: {list(df.columns)}")
            
            return df
            
        except Exception as e:
            print(f"下载数据失败: {e}")
            print("请确保：")
            print("1. Google Sheets 链接是公开可访问的")
            print("2. 网络连接正常")
            print("3. Spreadsheet ID 正确")
            print("4. 如果是私有表格，请将其设置为 '知道链接的任何人都可以查看'")
            raise
    
    def clean_person_name(self, name: Any) -> Optional[str]:
        """清洗人名"""
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
        
        for pattern, replacement in cleaning_patterns:
            name = re.sub(pattern, replacement, name).strip()
        
        if len(name) < 1 or len(name) > 50:
            return None
        
        if name != str(name).strip():
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
    
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗 DataFrame"""
        print("开始数据清洗...")
        
        # 复制数据
        cleaned_df = df.copy()
        
        # 1. 移除完全空白的行
        before_empty = len(cleaned_df)
        cleaned_df = cleaned_df.dropna(how='all')
        self.stats['empty_rows_removed'] = before_empty - len(cleaned_df)
        
        # 2. 清洗日期列（假设第一列是日期）
        if len(cleaned_df.columns) > 0:
            date_col = cleaned_df.columns[0]
            print(f"清洗日期列: {date_col}")
            
            cleaned_df[f'{date_col}_parsed'] = cleaned_df[date_col].apply(self.parse_date)
            
            # 移除无效日期的行
            valid_date_mask = cleaned_df[f'{date_col}_parsed'].notna()
            cleaned_df = cleaned_df[valid_date_mask]
        
        # 3. 识别和清洗人名列
        name_columns = self.identify_name_columns(cleaned_df)
        print(f"识别到人名列: {name_columns}")
        
        for col in name_columns:
            if col in cleaned_df.columns:
                print(f"清洗人名列: {col}")
                cleaned_df[f'{col}_cleaned'] = cleaned_df[col].apply(self.clean_person_name)
        
        # 4. 移除重复行（基于日期）
        if len(cleaned_df.columns) > 0:
            date_cols = [col for col in cleaned_df.columns if 'parsed' in col or '日期' in col]
            if date_cols:
                before_dup = len(cleaned_df)
                cleaned_df = cleaned_df.drop_duplicates(subset=[date_cols[0]])
                print(f"移除重复行: {before_dup - len(cleaned_df)} 行")
        
        self.stats['valid_rows'] = len(cleaned_df)
        
        print(f"清洗完成，剩余 {len(cleaned_df)} 行有效数据")
        return cleaned_df
    
    def identify_name_columns(self, df: pd.DataFrame) -> List[str]:
        """识别人名列"""
        name_keywords = [
            '讲员', '敬拜', '司琴', '音控', '导播', '摄影', 
            '儿童', '助教', '简餐', '祷告', '服侍', '打扫', 
            '财务', '场地', '外展', '协调'
        ]
        
        name_columns = []
        for col in df.columns:
            if any(keyword in str(col) for keyword in name_keywords):
                name_columns.append(col)
        
        return name_columns
    
    def validate_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """验证数据质量"""
        if df.empty:
            return {'quality_score': 0, 'issues': ['数据集为空']}
        
        validation_report = {
            'total_rows': len(df),
            'quality_score': 0,
            'issues': []
        }
        
        # 日期完整性
        date_cols = [col for col in df.columns if 'parsed' in col or '日期' in col]
        if date_cols:
            valid_dates = df[date_cols[0]].notna().sum()
            date_completeness = valid_dates / len(df) * 100
            validation_report['date_completeness'] = date_completeness
            
            if date_completeness < 90:
                validation_report['issues'].append(f"日期完整性较低: {date_completeness:.1f}%")
        
        # 人名完整性
        name_cols = [col for col in df.columns if 'cleaned' in col]
        if name_cols:
            total_assignments = len(df) * len(name_cols)
            filled_assignments = sum(df[col].notna().sum() for col in name_cols)
            assignment_completeness = filled_assignments / total_assignments * 100
            validation_report['assignment_completeness'] = assignment_completeness
            
            if assignment_completeness < 70:
                validation_report['issues'].append(f"事工安排完整性较低: {assignment_completeness:.1f}%")
        
        # 计算质量分数
        scores = []
        if 'date_completeness' in validation_report:
            scores.append(validation_report['date_completeness'])
        if 'assignment_completeness' in validation_report:
            scores.append(validation_report['assignment_completeness'])
        
        validation_report['quality_score'] = sum(scores) / len(scores) if scores else 0
        
        return validation_report
    
    def export_data(self, df: pd.DataFrame, output_path: str):
        """导出数据"""
        try:
            if output_path.endswith('.xlsx'):
                df.to_excel(output_path, index=False, engine='openpyxl')
            else:
                if not output_path.endswith('.csv'):
                    output_path += '.csv'
                df.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            print(f"数据已导出到: {output_path}")
            
        except Exception as e:
            print(f"导出失败: {e}")
            raise
    
    def generate_report(self, validation_report: Dict[str, Any] = None) -> Dict[str, Any]:
        """生成清洗报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'spreadsheet_id': self.spreadsheet_id,
            'cleaning_stats': self.stats,
            'data_quality': validation_report or {}
        }
        
        return report


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="简化版 Google Sheets 数据清洗工具")
    
    parser.add_argument(
        '--spreadsheet-id',
        type=str,
        default='1wescUQe9rIVLNcKdqmSLpzlAw9BGXMZmkFvjEF296nM',
        help='Google Sheets ID'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='输出文件路径 (支持 .csv 和 .xlsx)'
    )
    
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='只验证数据质量'
    )
    
    args = parser.parse_args()
    
    try:
        # 创建清洗器
        cleaner = SimpleDataCleaner(args.spreadsheet_id)
        
        # 下载数据
        df = cleaner.download_data()
        
        if args.validate_only:
            # 只验证
            validation_report = cleaner.validate_data(df)
            print("\n=== 数据质量报告 ===")
            print(f"总行数: {validation_report['total_rows']}")
            print(f"质量分数: {validation_report['quality_score']:.1f}/100")
            
            if validation_report.get('date_completeness'):
                print(f"日期完整性: {validation_report['date_completeness']:.1f}%")
            
            if validation_report.get('assignment_completeness'):
                print(f"事工安排完整性: {validation_report['assignment_completeness']:.1f}%")
            
            if validation_report['issues']:
                print("\n发现的问题:")
                for issue in validation_report['issues']:
                    print(f"  - {issue}")
        
        else:
            # 完整清洗流程
            cleaned_df = cleaner.clean_dataframe(df)
            validation_report = cleaner.validate_data(cleaned_df)
            
            print("\n=== 清洗统计 ===")
            print(f"原始行数: {cleaner.stats['total_rows']}")
            print(f"有效行数: {cleaner.stats['valid_rows']}")
            print(f"移除空行: {cleaner.stats['empty_rows_removed']}")
            print(f"无效日期: {cleaner.stats['invalid_dates']}")
            print(f"清洗人名: {cleaner.stats['cleaned_names']}")
            
            print(f"\n数据质量分数: {validation_report['quality_score']:.1f}/100")
            
            if validation_report['issues']:
                print("发现的问题:")
                for issue in validation_report['issues']:
                    print(f"  - {issue}")
            
            # 导出数据
            if args.output:
                cleaner.export_data(cleaned_df, args.output)
            else:
                # 默认导出路径
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                default_output = project_root / "data" / f"cleaned_data_{timestamp}.xlsx"
                default_output.parent.mkdir(exist_ok=True)
                cleaner.export_data(cleaned_df, str(default_output))
            
            # 保存报告
            report = cleaner.generate_report(validation_report)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = project_root / "data" / f"cleaning_report_{timestamp}.json"
            report_file.parent.mkdir(exist_ok=True)
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"\n详细报告已保存到: {report_file}")
    
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(0)
    
    except Exception as e:
        print(f"处理失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
