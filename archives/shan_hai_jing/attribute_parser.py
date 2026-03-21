# -*- coding: utf-8 -*-
"""
属性解析模块 - 解析异兽属性
"""

from config import SPECIAL_ATTRIBUTES, ATTRIBUTE_WEIGHTS


class AttributeParser:
    """属性解析器"""
    
    def __init__(self, logger=None):
        """
        初始化属性解析器
        Args:
            logger: 日志实例
        """
        self.logger = logger
    
    def parse_beast_attributes(self, text_list):
        """
        解析异兽属性
        Args:
            text_list: OCR识别到的文字列表
        Returns:
            dict: 异兽属性字典
        """
        if not text_list:
            return None
        
        # 将文本列表合并为一个字符串
        text = " ".join(text_list)
        
        # 分割上下两部分
        parts = text.split("属性")
        
        if len(parts) < 2:
            return None
        
        # 解析第一部分（名称、类型、基础属性）
        first_part = parts[0]
        attributes = self._parse_first_part(first_part)
        
        # 解析第二部分（特殊属性）
        second_part = parts[1]
        special_attrs = self._parse_second_part(second_part)
        
        # 合并属性
        if attributes:
            attributes["special_attributes"] = special_attrs
            return attributes
        
        return None
    
    def _parse_first_part(self, text):
        """
        解析第一部分（名称、类型、基础属性）
        Args:
            text: 文本
        Returns:
            dict: 属性字典
        """
        attributes = {}
        
        # 提取名称和类型
        lines = text.split()
        if len(lines) >= 2:
            attributes["name"] = lines[0]
            attributes["type"] = lines[1]
        
        # 提取基础属性
        attr_keywords = ["生命", "攻击", "防御", "速度"]
        for keyword in attr_keywords:
            # 查找关键词后面的数字
            idx = text.find(keyword)
            if idx != -1:
                # 提取数字
                start = idx + len(keyword)
                end = start
                while end < len(text) and text[end].isdigit():
                    end += 1
                if end > start:
                    attributes[keyword] = int(text[start:end])
        
        return attributes if attributes else None
    
    def _parse_second_part(self, text):
        """
        解析第二部分（特殊属性）
        Args:
            text: 文本
        Returns:
            list: 特殊属性列表
        """
        special_attrs = []
        
        # 检查每个特殊属性关键词
        for attr in SPECIAL_ATTRIBUTES:
            if attr in text:
                special_attrs.append(attr)
        
        return special_attrs
    
    def calculate_comprehensive_score(self, attributes):
        """
        计算综合评分
        Args:
            attributes: 属性字典
        Returns:
            float: 综合评分
        """
        if not attributes:
            return 0.0
        
        # 属性映射（中文到英文）
        attr_map = {
            "生命": ("hp", ATTRIBUTE_WEIGHTS.get("hp", 1.0)),
            "攻击": ("attack", ATTRIBUTE_WEIGHTS.get("attack", 1.0)),
            "防御": ("defense", ATTRIBUTE_WEIGHTS.get("defense", 1.0)),
            "速度": ("speed", ATTRIBUTE_WEIGHTS.get("speed", 1.0))
        }
        
        # 计算基础属性得分
        base_score = 0.0
        for attr_cn, (attr_en, weight) in attr_map.items():
            # 优先使用英文键名，如果没有则使用中文键名
            value = attributes.get(attr_en, attributes.get(attr_cn, 0))
            base_score += value * weight
        
        # 计算特殊属性得分
        special_score = 0.0
        special_attr = attributes.get("special_attribute", attributes.get("special_attributes", ""))
        
        if isinstance(special_attr, str):
            # 处理单个特殊属性（字符串）
            if special_attr in ["神兽", "神灵", "圣兽"]:
                special_score += 15
            elif special_attr:
                special_score += 10
        elif isinstance(special_attr, list):
            # 处理多个特殊属性（列表）
            for attr in special_attr:
                if attr in ["神兽", "神灵", "圣兽"]:
                    special_score += 15
                else:
                    special_score += 10
        
        # 综合评分
        comprehensive_score = base_score + special_score
        
        return comprehensive_score
    
    def get_optimal_target_attribute(self, attribute_slots):
        """
        获取最优目标属性（格子数量最多的属性）
        Args:
            attribute_slots: 属性格子字典
        Returns:
            str: 最优目标属性
        """
        if not attribute_slots:
            return None
        
        # 找出格子数量最多的属性
        max_count = 0
        optimal_attr = None
        for attr, count in attribute_slots.items():
            if count > max_count:
                max_count = count
                optimal_attr = attr
        
        return optimal_attr

