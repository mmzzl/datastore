# -*- coding: utf-8 -*-
"""
收服策略模块 - 实现收服判断逻辑
"""

from config import RARE_BEAST_KEYWORDS, TARGET_ATTRIBUTES


class CaptureStrategy:
    """收服策略"""
    
    def __init__(self, attribute_parser, logger=None):
        """
        初始化收服策略
        Args:
            attribute_parser: 属性解析器实例
            logger: 日志实例
        """
        self.attribute_parser = attribute_parser
        self.logger = logger
    
    def compare_special_attributes(self, new_beast, current_beast):
        """
        比较两个异兽的特殊属性
        Args:
            new_beast: 新异兽属性
            current_beast: 当前异兽属性
        Returns:
            int: 1表示新异兽更好，-1表示当前异兽更好，0表示相同
        """
        # 特殊属性优先级（数字越小优先级越高）
        priority_map = {
            '暴击': 1,
            '闪避': 2,
            '连击': 3,
            '吸血': 4,
            '反击': 5,
            '击晕': 6
        }
        
        new_attr = new_beast.get('special_attribute', '')
        current_attr = current_beast.get('special_attribute', '')
        
        # 如果新异兽没有特殊属性，当前异兽更好
        if not new_attr:
            return -1
        
        # 如果当前异兽没有特殊属性，新异兽更好
        if not current_attr:
            return 1
        
        # 比较特殊属性优先级
        new_priority = priority_map.get(new_attr, 999)
        current_priority = priority_map.get(current_attr, 999)
        
        if new_priority < current_priority:
            return 1
        elif new_priority > current_priority:
            return -1
        else:
            # 优先级相同，比较特殊属性数值
            new_value = new_beast.get('special_value', 0)
            current_value = current_beast.get('special_value', 0)
            
            if new_value > current_value:
                return 1
            elif new_value < current_value:
                return -1
            else:
                return 0
    
    def compare_basic_attributes(self, new_beast, current_beast):
        """
        比较两个异兽的基础属性（生命、攻击、防御、速度）
        Args:
            new_beast: 新异兽属性
            current_beast: 当前异兽属性
        Returns:
            int: 1表示新异兽更好，-1表示当前异兽更好，0表示相同
        """
        # 获取基础属性
        new_hp = new_beast.get('hp', 0)
        new_attack = new_beast.get('attack', 0)
        new_defense = new_beast.get('defense', 0)
        new_speed = new_beast.get('speed', 0)
        
        current_hp = current_beast.get('hp', 0)
        current_attack = current_beast.get('attack', 0)
        current_defense = current_beast.get('defense', 0)
        current_speed = current_beast.get('speed', 0)
        
        # 计算基础属性总和
        new_total = new_hp + new_attack + new_defense + new_speed
        current_total = current_hp + current_attack + current_defense + current_speed
        
        if new_total > current_total:
            return 1
        elif new_total < current_total:
            return -1
        else:
            return 0

    def is_rare_beast(self, beast):
        """
        判断是否是稀有异兽（神兽及以上）
        Args:
            beast: 异兽属性字典
        Returns:
            bool: 是否是稀有异兽
        """
        beast_type = beast.get("name", "")
        return any(keyword in beast_type for keyword in RARE_BEAST_KEYWORDS)

    def is_target_beast(self, beast):
        """
        判断是否是目标异兽（稀有异兽）
        Args:
            beast: 异兽属性字典
        Returns:
            bool: 是否是目标异兽
        """
        special_attr = beast.get("special_attribute", "")
        return any(keyword in special_attr for keyword in TARGET_ATTRIBUTES)

    def should_capture(self, new_beast, current_beast, strategy="balanced", attribute_slots=None):
        """
        判断是否应该收服新异兽（简化版）
        Args:
            new_beast: 新异兽属性
            current_beast: 当前异兽属性
            strategy: 收服策略（保留参数兼容性，暂不使用）
            attribute_slots: 属性格子字典（保留参数兼容性，暂不使用）
        Returns:
            bool: 是否收服            
        """
        # 如果没有当前异兽，直接收服
        if not current_beast:
            if self.logger:
                self.logger.info("当前没有异兽，收服新异兽")
            return True
        
        if not self.is_rare_beast(new_beast):
            if self.logger:
                self.logger.info(f"当前异兽不是稀有异兽（{new_beast.get('type', '未知')}），不收服")
            return False
    
        # 记录当前异兽属性
        if self.logger:
            self.logger.info(f"当前异兽: {current_beast.get('name', '未知')} "
                          f"类型: {current_beast.get('type', '未知')} "
                          f"生命: {current_beast.get('hp', 0)} "
                          f"攻击: {current_beast.get('attack', 0)} "
                          f"防御: {current_beast.get('defense', 0)} "
                          f"速度: {current_beast.get('speed', 0)} "
                          f"特殊属性: {current_beast.get('special_attribute', '')}")
        
        # 记录新异兽属性
        if self.logger:
            self.logger.info(f"新异兽: {new_beast.get('name', '未知')} "
                          f"类型: {new_beast.get('type', '未知')} "
                          f"生命: {new_beast.get('hp', 0)} "
                          f"攻击: {new_beast.get('attack', 0)} "
                          f"防御: {new_beast.get('defense', 0)} "
                          f"速度: {new_beast.get('speed', 0)} "
                          f"特殊属性: {new_beast.get('special_attribute', '')}")
        
        # 判断是否是目标异兽
        current_is_target = self.is_target_beast(current_beast)
        new_is_target = self.is_target_beast(new_beast)
        
        if self.logger:
            self.logger.info(f"当前异兽是目标异兽: {current_is_target}")
            self.logger.info(f"新异兽是目标异兽: {new_is_target}")
        
        # 情况1: 新异兽是目标异兽，当前异兽也是目标异兽，比较基础属性
        if new_is_target and current_is_target:
            comparison = self.compare_basic_attributes(new_beast, current_beast)
            
            if self.logger:
                self.logger.info(f"新异兽基础属性总和: {new_beast.get('hp', 0) + new_beast.get('attack', 0) + new_beast.get('defense', 0) + new_beast.get('speed', 0)}")
                self.logger.info(f"当前异兽基础属性总和: {current_beast.get('hp', 0) + current_beast.get('attack', 0) + current_beast.get('defense', 0) + current_beast.get('speed', 0)}")
            
            if comparison > 0:
                if self.logger:
                    self.logger.info(f"两个都是目标异兽，新异兽基础属性更高，收服")
                return True
            else:
                if self.logger:
                    self.logger.info(f"两个都是目标异兽，新异兽基础属性不更高，不收服")
                return False
        
        # 情况2: 新异兽不是目标异兽，当前异兽也不是目标异兽，比较基础属性
        if not new_is_target and not current_is_target:
            comparison = self.compare_basic_attributes(new_beast, current_beast)
            
            if self.logger:
                self.logger.info(f"新异兽基础属性总和: {new_beast.get('hp', 0) + new_beast.get('attack', 0) + new_beast.get('defense', 0) + new_beast.get('speed', 0)}")
                self.logger.info(f"当前异兽基础属性总和: {current_beast.get('hp', 0) + current_beast.get('attack', 0) + current_beast.get('defense', 0) + current_beast.get('speed', 0)}")
            
            if comparison > 0:
                if self.logger:
                    self.logger.info(f"两个都不是目标异兽，新异兽基础属性更高，收服")
                return True
            else:
                if self.logger:
                    self.logger.info(f"两个都不是目标异兽，新异兽基础属性不更高，不收服")
                return False
        
        # 情况3: 新异兽不是目标异兽，当前异兽是目标异兽，不收服
        if not new_is_target and current_is_target:
            if self.logger:
                self.logger.info(f"新异兽不是目标异兽，当前异兽是目标异兽，不收服")
            return False
        
        # 情况4: 新异兽是目标异兽，当前异兽不是目标异兽，收服
        if new_is_target and not current_is_target:
            # 判断当前异兽是否是神兽及以上
            if self.logger:
                self.logger.info(f"新异兽是目标异兽，当前异兽不是目标异兽且不是稀有异兽，收服")
            return True
        
        # 默认不收服
        if self.logger:
            self.logger.info(f"默认不收服")
        return False










