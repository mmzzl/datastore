# -*- coding: utf-8 -*-
"""
属性格子管理模块 - 管理属性格子数据
"""

import json
import os
from config import SLOTS_FILE


class SlotManager:
    """属性格子管理器"""
    
    def __init__(self, logger=None):
        """
        初始化属性格子管理器
        Args:
            logger: 日志实例
        """
        self.logger = logger
        self.attribute_slots = {}
        self.load_attribute_slots()
    
    def load_attribute_slots(self):
        """加载属性格子数据"""
        try:
            if os.path.exists(SLOTS_FILE):
                with open(SLOTS_FILE, "r", encoding="utf-8") as f:
                    self.attribute_slots = json.load(f)
                if self.logger:
                    self.logger.info(f"属性格子数据已加载: {self.attribute_slots}")
            else:
                # 初始化默认属性格子
                self.attribute_slots = {
                    "神兽": 0,
                    "神灵": 0,
                    "圣兽": 0,
                    "神兽": 0,
                    "神灵": 0,
                    "圣兽": 0
                }
                self.save_attribute_slots()
                if self.logger:
                    self.logger.info("属性格子数据已初始化")
        except Exception as e:
            if self.logger:
                self.logger.error(f"加载属性格子数据出错: {e}")
            self.attribute_slots = {}
    
    def save_attribute_slots(self):
        """保存属性格子数据"""
        try:
            with open(SLOTS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.attribute_slots, f, ensure_ascii=False, indent=2)
            if self.logger:
                self.logger.info(f"属性格子数据已保存: {self.attribute_slots}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"保存属性格子数据出错: {e}")
    
    def update_attribute_slots(self, attributes):
        """
        更新属性格子数据
        Args:
            attributes: 异兽属性字典
        """
        if not attributes or "special_attributes" not in attributes:
            return
        
        for attr in attributes["special_attributes"]:
            if attr in self.attribute_slots:
                self.attribute_slots[attr] += 1
            else:
                self.attribute_slots[attr] = 1
        
        self.save_attribute_slots()
    
    def get_attribute_slots(self):
        """
        获取属性格子数据
        Returns:
            dict: 属性格子字典
        """
        return self.attribute_slots
    
    def get_slot_count(self, attribute):
        """
        获取指定属性的格子数量
        Args:
            attribute: 属性名称
        Returns:
            int: 格子数量
        """
        return self.attribute_slots.get(attribute, 0)


