"""
EH11 旋转编码器驱动程序
支持旋转和按键输入
"""

import machine
import time
from micropython import const

# 编码器引脚定义
ENCODER_A_PIN = const(18)  # 编码器A相
ENCODER_B_PIN = const(19)  # 编码器B相
ENCODER_BTN_PIN = const(20)  # 编码器按键

class EH11Encoder:
    def __init__(self, pin_a=ENCODER_A_PIN, pin_b=ENCODER_B_PIN, pin_btn=ENCODER_BTN_PIN):
        """
        初始化EH11编码器
        
        Args:
            pin_a: A相引脚号
            pin_b: B相引脚号
            pin_btn: 按键引脚号
        """
        self.pin_a = machine.Pin(pin_a, machine.Pin.IN, machine.Pin.PULL_UP)
        self.pin_b = machine.Pin(pin_b, machine.Pin.IN, machine.Pin.PULL_UP)
        self.pin_btn = machine.Pin(pin_btn, machine.Pin.IN, machine.Pin.PULL_UP)
        
        # 编码器状态
        self.last_a = 1
        self.last_b = 1
        self.counter = 0
        self.button_state = 1
        self.last_button_state = 1
        self.button_pressed = False
        self.button_released = False
        
        # 按键防抖相关
        self.debounce_time = 50  # 防抖时间（毫秒）
        self.last_button_time = 0
        
        # 调试输出控制
        self.debug_enabled = True
        
        # 回调函数
        self.rotation_callback = None
        self.button_callback = None
        
        # 初始化中断
        self._init_interrupts()
    
    def _init_interrupts(self):
        """初始化GPIO中断"""
        # 使用A相和B相中断来检测旋转
        self.pin_a.irq(trigger=machine.Pin.IRQ_RISING | machine.Pin.IRQ_FALLING, 
                       handler=self._encoder_isr)
        self.pin_b.irq(trigger=machine.Pin.IRQ_RISING | machine.Pin.IRQ_FALLING, 
                       handler=self._encoder_isr)
        # 按键中断 - 检测下降沿（按下）和上升沿（释放）
        self.pin_btn.irq(trigger=machine.Pin.IRQ_RISING | machine.Pin.IRQ_FALLING, 
                        handler=self._button_isr)
        
        print("编码器中断已初始化（A相和B相中断）")
    
    def _encoder_isr(self, pin):
        """编码器中断服务程序"""
        try:
            # 读取当前状态
            current_a = self.pin_a.value()
            current_b = self.pin_b.value()
            
            # 使用更稳定的四倍频检测方法
            # 检测A相变化
            if pin == self.pin_a and self.last_a != current_a:
                # 添加小延时防止抖动
                time.sleep_ms(1)
                
                # 重新读取状态确认
                current_a = self.pin_a.value()
                current_b = self.pin_b.value()
                
                if current_a != current_b:
                    self.counter += 1  # 顺时针旋转
                    direction = 1
                else:
                    self.counter -= 1  # 逆时针旋转
                    direction = -1
                    
                # 如果有回调函数，调用它
                if self.rotation_callback:
                    self.rotation_callback(direction)
                
                # 调试输出
                if self.debug_enabled:
                    print(f"Encoder rotation: {direction}, counter: {self.counter}")
            
            # 更新上次状态
            self.last_a = current_a
            self.last_b = current_b
        except Exception as e:
            if self.debug_enabled:
                print(f"Error in encoder ISR: {e}")
    
    def _button_isr(self, pin):
        """按键中断服务程序"""
        current_time = time.ticks_ms()
        
        # 防抖处理
        if time.ticks_diff(current_time, self.last_button_time) < self.debounce_time:
            return
        
        self.button_state = self.pin_btn.value()
        self.last_button_time = current_time
        
        # 检测按键按下（下降沿）
        if self.last_button_state == 1 and self.button_state == 0:
            self.button_pressed = True
            if self.button_callback:
                self.button_callback("pressed")
            if self.debug_enabled:
                print("Button pressed")
        
        # 检测按键释放（上升沿）
        elif self.last_button_state == 0 and self.button_state == 1:
            self.button_released = True
            if self.button_callback:
                self.button_callback("released")
            if self.debug_enabled:
                print("Button released")
        
        self.last_button_state = self.button_state
    
    def set_rotation_callback(self, callback):
        """设置旋转回调函数"""
        self.rotation_callback = callback
    
    def set_button_callback(self, callback):
        """设置按键回调函数"""
        self.button_callback = callback
    
    def set_debounce_time(self, debounce_ms):
        """设置按键防抖时间（毫秒）"""
        self.debounce_time = debounce_ms
    
    def set_debug(self, enabled):
        """启用或禁用调试输出"""
        self.debug_enabled = enabled
    
    def get_counter(self):
        """获取当前计数值"""
        return self.counter
    
    def reset_counter(self):
        """重置计数器"""
        self.counter = 0
    
    def is_button_pressed(self):
        """检查按键是否被按下"""
        return self.button_state == 0
    
    def get_events(self):
        """获取所有事件并清除标志"""
        events = {
            "rotation": self.counter,
            "button_pressed": self.button_pressed,
            "button_released": self.button_released,
            "button_state": self.button_state
        }
        
        # 清除事件标志
        self.button_pressed = False
        self.button_released = False
        
        return events
    
    def is_connected(self):
        """检查编码器是否正确连接"""
        # 读取引脚状态
        a_state = self.pin_a.value()
        b_state = self.pin_b.value()
        btn_state = self.pin_btn.value()
        
        # 检查引脚是否都处于上拉状态（未按下时为高电平）
        return a_state == 1 and b_state == 1 and btn_state == 1