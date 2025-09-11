#!/usr/bin/env python3
"""
ICS日历生成器启动脚本
ICS Calendar Generator Launcher

这是一个便捷的启动脚本，用于运行ICS日历生成器。
"""

import sys
import subprocess
from pathlib import Path

def main():
    """主函数"""
    print("🚀 启动ICS日历生成器...")
    
    try:
        # 运行日历生成器模块
        result = subprocess.run([
            sys.executable, '-m', 'src.calendar_generator'
        ], cwd=Path(__file__).parent)
        
        return result.returncode
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
