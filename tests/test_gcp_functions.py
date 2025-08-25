#!/usr/bin/env python3
"""
Google Cloud Functions 测试脚本
Test deployed Cloud Functions locally and remotely
"""

import requests
import json
import time
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GCPFunctionTester:
    """Google Cloud Functions 测试器"""
    
    def __init__(self, project_id: str, region: str = "us-central1"):
        self.project_id = project_id
        self.region = region
        
        # 构建函数URL
        self.weekly_url = f"https://{region}-{project_id}.cloudfunctions.net/send-weekly-confirmation"
        self.sunday_url = f"https://{region}-{project_id}.cloudfunctions.net/send-sunday-reminder"
    
    def test_function(self, url: str, function_name: str) -> bool:
        """测试单个Cloud Function"""
        try:
            logger.info(f"🧪 测试 {function_name} 函数")
            logger.info(f"URL: {url}")
            
            # 发送POST请求
            response = requests.post(url, timeout=300)  # 5分钟超时
            
            logger.info(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    logger.info(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    
                    if result.get('success'):
                        logger.info(f"✅ {function_name} 测试成功")
                        return True
                    else:
                        logger.warning(f"⚠️  {function_name} 执行完成但返回失败状态")
                        return False
                        
                except json.JSONDecodeError:
                    logger.info(f"响应内容: {response.text}")
                    logger.info(f"✅ {function_name} 测试成功（非JSON响应）")
                    return True
            else:
                logger.error(f"❌ {function_name} 测试失败")
                logger.error(f"响应内容: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ {function_name} 测试超时")
            return False
        except Exception as e:
            logger.error(f"❌ {function_name} 测试出错: {e}")
            return False
    
    def test_all_functions(self):
        """测试所有函数"""
        logger.info("=" * 60)
        logger.info("🚀 开始测试 Google Cloud Functions")
        logger.info("=" * 60)
        
        results = {}
        
        # 测试周三确认通知函数
        results['weekly'] = self.test_function(self.weekly_url, "周三确认通知")
        
        logger.info("")  # 空行分隔
        
        # 测试周六提醒通知函数
        results['sunday'] = self.test_function(self.sunday_url, "周六提醒通知")
        
        # 输出测试结果摘要
        logger.info("")
        logger.info("=" * 60)
        logger.info("📊 测试结果摘要")
        logger.info("=" * 60)
        
        success_count = sum(results.values())
        total_count = len(results)
        
        for name, success in results.items():
            status = "✅ 成功" if success else "❌ 失败"
            logger.info(f"  {name}: {status}")
        
        logger.info(f"\n总体结果: {success_count}/{total_count} 个函数测试成功")
        
        if success_count == total_count:
            logger.info("🎉 所有函数测试通过！")
        else:
            logger.warning("⚠️  部分函数测试失败，请检查日志")
        
        return success_count == total_count

def main():
    """主函数"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python test_gcp_functions.py <project_id> [region]")
        print("\n示例:")
        print("  python test_gcp_functions.py grace-irvine-scheduler")
        print("  python test_gcp_functions.py grace-irvine-scheduler us-west1")
        sys.exit(1)
    
    project_id = sys.argv[1]
    region = sys.argv[2] if len(sys.argv) > 2 else "us-central1"
    
    # 创建测试器并运行测试
    tester = GCPFunctionTester(project_id, region)
    success = tester.test_all_functions()
    
    # 根据测试结果设置退出码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
