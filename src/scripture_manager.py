#!/usr/bin/env python3
"""
经文分享管理器
Scripture Sharing Manager

用于管理周三通知中的经文分享内容
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ScriptureManager:
    """经文分享管理器
    
    负责管理经文内容的读取、选择和更新
    """
    
    def __init__(self, storage_manager=None):
        """初始化经文管理器
        
        Args:
            storage_manager: 存储管理器实例，如果为None则创建新实例
        """
        if storage_manager:
            self.storage_manager = storage_manager
        else:
            from .cloud_storage_manager import get_storage_manager
            self.storage_manager = get_storage_manager()
        
        # 经文数据
        self.scriptures_data = {}
        
        # 加载经文配置
        self.load_scriptures()
    
    def load_scriptures(self) -> bool:
        """加载经文配置
        
        Returns:
            是否加载成功
        """
        try:
            # 使用存储管理器读取经文配置
            self.scriptures_data = self.storage_manager.read_scripture_config()
            
            if self.scriptures_data:
                logger.info("经文配置加载成功")
                return True
            else:
                logger.warning("经文配置加载失败，使用默认配置")
                self._create_default_scriptures()
                return False
                
        except Exception as e:
            logger.error(f"加载经文配置失败: {e}")
            self._create_default_scriptures()
            return False
    
    def save_scriptures(self) -> bool:
        """保存经文配置
        
        Returns:
            是否保存成功
        """
        try:
            # 更新元数据
            if 'metadata' not in self.scriptures_data:
                self.scriptures_data['metadata'] = {}
            
            self.scriptures_data['metadata']['last_updated'] = datetime.now().isoformat()
            self.scriptures_data['metadata']['total_count'] = len(self.scriptures_data.get('scriptures', []))
            
            # 使用存储管理器保存
            return self.storage_manager.write_scripture_config(self.scriptures_data)
            
        except Exception as e:
            logger.error(f"保存经文配置失败: {e}")
            return False
    
    def _create_default_scriptures(self):
        """创建默认经文配置"""
        self.scriptures_data = {
            "metadata": {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "description": "周三通知经文分享内容",
                "author": "事工协调员",
                "current_index": 0,
                "total_count": 3
            },
            "scriptures": [
                {
                    "id": 1,
                    "content": "看哪，弟兄和睦同居\n是何等地善，何等地美！\n(诗篇 133:1 和合本)"
                },
                {
                    "id": 2,
                    "content": "恩赐原有分别，圣灵却是一位。\n职事也有分别，主却是一位。\n(哥林多前书 12:4-5 和合本)"
                },
                {
                    "id": 3,
                    "content": "无论做什么，都要从心里做，\n像是给主做的，不是给人做的。\n(歌罗西书 3:23 和合本)"
                }
            ]
        }
    
    def get_next_scripture(self) -> Optional[Dict[str, Any]]:
        """获取下一段经文
        
        Returns:
            经文字典，包含verse、content、theme、note等字段
        """
        try:
            scriptures = self.scriptures_data.get('scriptures', [])
            if not scriptures:
                logger.warning("没有可用的经文")
                return None
            
            metadata = self.scriptures_data.get('metadata', {})
            current_index = metadata.get('current_index', 0)
            
            # 确保索引在有效范围内
            if current_index >= len(scriptures):
                current_index = 0
            
            # 获取当前经文
            current_scripture = scriptures[current_index]
            
            # 更新索引到下一个位置
            next_index = (current_index + 1) % len(scriptures)
            self.scriptures_data['metadata']['current_index'] = next_index
            
            # 保存更新后的配置
            self.save_scriptures()
            
            logger.info(f"选择经文: {current_scripture.get('verse', 'Unknown')} (索引: {current_index})")
            return current_scripture
            
        except Exception as e:
            logger.error(f"获取经文失败: {e}")
            return None
    
    def get_current_scripture(self) -> Optional[Dict[str, Any]]:
        """获取当前经文（不更新索引）
        
        Returns:
            经文字典
        """
        try:
            scriptures = self.scriptures_data.get('scriptures', [])
            if not scriptures:
                return None
            
            metadata = self.scriptures_data.get('metadata', {})
            current_index = metadata.get('current_index', 0)
            
            # 确保索引在有效范围内
            if current_index >= len(scriptures):
                current_index = 0
                self.scriptures_data['metadata']['current_index'] = current_index
                self.save_scriptures()
            
            return scriptures[current_index]
            
        except Exception as e:
            logger.error(f"获取当前经文失败: {e}")
            return None
    
    def get_all_scriptures(self) -> List[Dict[str, Any]]:
        """获取所有经文列表
        
        Returns:
            经文列表
        """
        return self.scriptures_data.get('scriptures', [])
    
    def add_scripture(self, content: str) -> bool:
        """添加新经文
        
        Args:
            content: 经文内容（包含出处）
            
        Returns:
            是否添加成功
        """
        try:
            scriptures = self.scriptures_data.get('scriptures', [])
            
            # 生成新ID
            new_id = max([s.get('id', 0) for s in scriptures], default=0) + 1
            
            new_scripture = {
                "id": new_id,
                "content": content
            }
            
            scriptures.append(new_scripture)
            self.scriptures_data['scriptures'] = scriptures
            
            # 保存配置
            success = self.save_scriptures()
            if success:
                # 提取经文标识用于日志
                first_line = content.split('\n')[0][:20] if content else "Unknown"
                logger.info(f"添加经文成功: {first_line}...")
            
            return success
            
        except Exception as e:
            logger.error(f"添加经文失败: {e}")
            return False
    
    def update_scripture(self, scripture_id: int, content: str) -> bool:
        """更新经文
        
        Args:
            scripture_id: 经文ID
            content: 经文内容（包含出处）
            
        Returns:
            是否更新成功
        """
        try:
            scriptures = self.scriptures_data.get('scriptures', [])
            
            # 查找要更新的经文
            for i, scripture in enumerate(scriptures):
                if scripture.get('id') == scripture_id:
                    scriptures[i] = {
                        "id": scripture_id,
                        "content": content
                    }
                    
                    self.scriptures_data['scriptures'] = scriptures
                    
                    # 保存配置
                    success = self.save_scriptures()
                    if success:
                        # 提取经文标识用于日志
                        first_line = content.split('\n')[0][:20] if content else "Unknown"
                        logger.info(f"更新经文成功: {first_line}...")
                    
                    return success
            
            logger.warning(f"未找到ID为 {scripture_id} 的经文")
            return False
            
        except Exception as e:
            logger.error(f"更新经文失败: {e}")
            return False
    
    def delete_scripture(self, scripture_id: int) -> bool:
        """删除经文
        
        Args:
            scripture_id: 经文ID
            
        Returns:
            是否删除成功
        """
        try:
            scriptures = self.scriptures_data.get('scriptures', [])
            
            # 查找并删除经文
            original_length = len(scriptures)
            scriptures = [s for s in scriptures if s.get('id') != scripture_id]
            
            if len(scriptures) < original_length:
                self.scriptures_data['scriptures'] = scriptures
                
                # 调整当前索引（如果需要）
                metadata = self.scriptures_data.get('metadata', {})
                current_index = metadata.get('current_index', 0)
                if current_index >= len(scriptures) and len(scriptures) > 0:
                    self.scriptures_data['metadata']['current_index'] = len(scriptures) - 1
                elif len(scriptures) == 0:
                    self.scriptures_data['metadata']['current_index'] = 0
                
                # 保存配置
                success = self.save_scriptures()
                if success:
                    logger.info(f"删除经文成功: ID {scripture_id}")
                
                return success
            else:
                logger.warning(f"未找到ID为 {scripture_id} 的经文")
                return False
            
        except Exception as e:
            logger.error(f"删除经文失败: {e}")
            return False
    
    def reset_index(self) -> bool:
        """重置经文索引到开头
        
        Returns:
            是否重置成功
        """
        try:
            self.scriptures_data['metadata']['current_index'] = 0
            success = self.save_scriptures()
            if success:
                logger.info("经文索引已重置")
            return success
            
        except Exception as e:
            logger.error(f"重置经文索引失败: {e}")
            return False
    
    def get_scripture_stats(self) -> Dict[str, Any]:
        """获取经文统计信息
        
        Returns:
            统计信息字典
        """
        try:
            scriptures = self.scriptures_data.get('scriptures', [])
            metadata = self.scriptures_data.get('metadata', {})
            
            return {
                'total_count': len(scriptures),
                'current_index': metadata.get('current_index', 0),
                'last_updated': metadata.get('last_updated', 'Unknown')
            }
            
        except Exception as e:
            logger.error(f"获取经文统计失败: {e}")
            return {}
    
    def format_scripture_for_template(self, scripture: Dict[str, Any]) -> str:
        """格式化经文用于模板
        
        Args:
            scripture: 经文字典
            
        Returns:
            格式化后的经文字符串
        """
        if not scripture:
            return ""
        
        content = scripture.get('content', '')
        
        # 简单格式，直接使用经文内容
        formatted = f"📖 {content}"
        
        return formatted

# 便捷函数
def get_scripture_manager() -> ScriptureManager:
    """获取经文管理器实例"""
    return ScriptureManager()

def test_scripture_manager():
    """测试经文管理器"""
    print("🧪 测试经文管理器...")
    
    manager = get_scripture_manager()
    
    # 测试加载经文
    stats = manager.get_scripture_stats()
    if stats.get('total_count', 0) > 0:
        print(f"✅ 成功加载 {stats['total_count']} 段经文")
    else:
        print("❌ 经文加载失败")
        return False
    
    # 测试获取经文
    current_scripture = manager.get_current_scripture()
    if current_scripture:
        # 提取经文标识（第一行）
        first_line = current_scripture.get('content', '').split('\n')[0][:30]
        print(f"✅ 当前经文: {first_line}...")
    else:
        print("❌ 获取当前经文失败")
        return False
    
    # 测试经文格式化
    formatted = manager.format_scripture_for_template(current_scripture)
    if formatted and "📖" in formatted:
        print("✅ 经文格式化正常")
    else:
        print("❌ 经文格式化失败")
        return False
    
    return True

if __name__ == "__main__":
    success = test_scripture_manager()
    print(f"\n{'✅ 测试通过' if success else '❌ 测试失败'}")
