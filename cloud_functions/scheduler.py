# 这个文件是 src/scheduler.py 的符号链接或副本
# 用于Cloud Functions部署

# 在实际部署时，需要将 src/ 目录下的相关文件复制到这里
# 或者在部署脚本中处理文件依赖关系

# 临时解决方案：直接复制源文件内容
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from scheduler import *
