#!/usr/bin/env python3
"""
Grace Irvine Ministry Scheduler - 数据清洗执行脚本
Data Cleaning Execution Script

一键运行数据清洗流程的便捷脚本
Convenient script for one-click data cleaning workflow
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# 项目根目录
project_root = Path(__file__).parent.parent


def print_banner():
    """打印欢迎横幅"""
    print("=" * 60)
    print("  Grace Irvine Ministry Scheduler - 数据清洗工具")
    print("  Grace Irvine Ministry Scheduler - Data Cleaning Tool")
    print("=" * 60)
    print()


def print_summary():
    """打印功能摘要"""
    print("🔧 功能特性 / Features:")
    print("  ✅ 自动连接 Google Sheets / Auto connect to Google Sheets")
    print("  ✅ 智能数据清洗 / Intelligent data cleaning")
    print("  ✅ 人名标准化 / Name standardization")
    print("  ✅ 日期格式解析 / Date format parsing")
    print("  ✅ 数据质量验证 / Data quality validation")
    print("  ✅ Excel/CSV 导出 / Excel/CSV export")
    print()


def check_dependencies():
    """检查依赖项"""
    print("🔍 检查依赖项 / Checking dependencies...")
    
    required_packages = ['pandas', 'openpyxl']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ❌ {package} (缺失 / Missing)")
    
    if missing_packages:
        print(f"\n⚠️  请安装缺失的依赖项 / Please install missing dependencies:")
        print(f"   pip3 install {' '.join(missing_packages)}")
        return False
    
    print("  ✅ 所有依赖项已安装 / All dependencies installed")
    return True


def run_data_cleaning():
    """运行数据清洗"""
    print("\n🚀 开始数据清洗流程 / Starting data cleaning process...")
    
    # 确保输出目录存在
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)
    
    # 生成输出文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = data_dir / f"cleaned_schedule_{timestamp}.xlsx"
    
    # 运行清洗脚本
    import subprocess
    
    try:
        cmd = [
            sys.executable, 
            str(project_root / "simple_data_cleaner.py"),
            "--output", str(output_file)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ 数据清洗完成 / Data cleaning completed successfully!")
            return True, output_file
        else:
            print("❌ 数据清洗失败 / Data cleaning failed!")
            print(f"错误信息 / Error: {result.stderr}")
            return False, None
            
    except Exception as e:
        print(f"❌ 执行失败 / Execution failed: {e}")
        return False, None


def show_results(output_file):
    """显示结果"""
    if not output_file or not output_file.exists():
        return
    
    print(f"\n📊 清洗结果 / Cleaning Results:")
    print(f"  📄 清洗后数据文件 / Cleaned data file: {output_file}")
    
    # 查找最新的报告文件
    data_dir = project_root / "data"
    report_files = list(data_dir.glob("cleaning_report_*.json"))
    
    if report_files:
        latest_report = max(report_files, key=lambda x: x.stat().st_mtime)
        print(f"  📋 清洗报告文件 / Cleaning report: {latest_report}")
        
        # 显示报告摘要
        try:
            with open(latest_report, 'r', encoding='utf-8') as f:
                report = json.load(f)
            
            stats = report.get('cleaning_stats', {})
            quality = report.get('data_quality', {})
            
            print(f"\n📈 清洗统计 / Cleaning Statistics:")
            print(f"  • 原始行数 / Original rows: {stats.get('total_rows', 'N/A')}")
            print(f"  • 有效行数 / Valid rows: {stats.get('valid_rows', 'N/A')}")
            print(f"  • 清洗人名 / Names cleaned: {stats.get('cleaned_names', 'N/A')}")
            print(f"  • 无效日期 / Invalid dates: {stats.get('invalid_dates', 'N/A')}")
            
            print(f"\n🎯 数据质量 / Data Quality:")
            print(f"  • 质量分数 / Quality score: {quality.get('quality_score', 'N/A'):.1f}/100")
            print(f"  • 日期完整性 / Date completeness: {quality.get('date_completeness', 'N/A'):.1f}%")
            print(f"  • 事工安排完整性 / Assignment completeness: {quality.get('assignment_completeness', 'N/A'):.1f}%")
            
            if quality.get('issues'):
                print(f"\n⚠️  发现的问题 / Issues found:")
                for issue in quality['issues']:
                    print(f"    - {issue}")
        
        except Exception as e:
            print(f"  ⚠️  无法读取报告文件 / Cannot read report file: {e}")


def show_next_steps():
    """显示后续步骤"""
    print(f"\n🎯 后续步骤 / Next Steps:")
    print(f"  1. 查看清洗后的 Excel 文件 / Review the cleaned Excel file")
    print(f"  2. 检查数据质量报告 / Check the data quality report")
    print(f"  3. 根据需要进行手动调整 / Make manual adjustments if needed")
    print(f"  4. 将清洗后的数据用于通知系统 / Use cleaned data for notification system")
    
    print(f"\n📚 更多信息 / More Information:")
    print(f"  • 详细指南 / Detailed guide: DATA_CLEANING_GUIDE.md")
    print(f"  • 配置文件 / Configuration: configs/data_cleaning_config.yaml")
    print(f"  • 高级工具 / Advanced tool: clean_sheets_data.py")


def main():
    """主函数"""
    print_banner()
    print_summary()
    
    # 检查依赖项
    if not check_dependencies():
        print(f"\n❌ 请先安装缺失的依赖项，然后重新运行此脚本")
        print(f"❌ Please install missing dependencies and run this script again")
        sys.exit(1)
    
    # 运行数据清洗
    success, output_file = run_data_cleaning()
    
    if success:
        show_results(output_file)
        show_next_steps()
        
        print(f"\n🎉 数据清洗流程完成！/ Data cleaning workflow completed!")
        print("=" * 60)
    else:
        print(f"\n💡 故障排除建议 / Troubleshooting suggestions:")
        print(f"  1. 检查网络连接 / Check network connection")
        print(f"  2. 确认 Google Sheets 为公开访问 / Ensure Google Sheets is publicly accessible")
        print(f"  3. 验证 Spreadsheet ID 正确 / Verify correct Spreadsheet ID")
        print(f"  4. 查看详细错误信息 / Check detailed error messages above")
        print(f"\n📖 更多帮助请参考 / For more help, see: DATA_CLEANING_GUIDE.md")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
