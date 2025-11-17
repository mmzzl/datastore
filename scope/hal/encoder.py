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
        
        # 回调函数
        self.rotation_callback = None
        self.button_callback = None
        
        # 初始化中断
        self._init_interrupts()
    
    def _init_interrupts(self):
        """初始化GPIO中断"""
        # 尝试只使用A相中断来检测旋转
        self.pin_a.irq(trigger=machine.Pin.IRQ_RISING | machine.Pin.IRQ_FALLING, 
                       handler=self._encoder_isr)
        # B相变化中断 - 暂时禁用
        # self.pin_b.irq(trigger=machine.Pin.IRQ_RISING | machine.Pin.IRQ_FALLING, 
        #                handler=self._encoder_isr)
        # 按键中断 - 只检测下降沿（按下）
        self.pin_btn.irq(trigger=machine.Pin.IRQ_FALLING, 
                        handler=self._button_isr)
        
        print("编码器中断已初始化（仅A相中断）")
    
    def _encoder_isr(self, pin):
        """编码器中断服务程序"""
        try:
            # 读取当前状态
            current_a = self.pin_a.value()
            current_b = self.pin_b.value()
            
            # 添加调试输出
            print(f"Encoder ISR: A={current_a}, B={current_b}, last_A={self.last_a}, last_B={self.last_b}")
            
            # 检测旋转方向
            if self.last_a != current_a:
                if current_a != current_b:
                    self.counter += 1  # 顺时针旋转
                    print(f"顺时针旋转，计数器: {self.counter}")
                else:
                    self.counter -= 1  # 逆时针旋转
                    print(f"逆时针旋转，计数器: {self.counter}")
                    
                # 如果有回调函数，调用它
                if self.rotation_callback:
                    direction = 1 if current_a != current_b else -1
                    self.rotation_callback(direction)
            
            # 更新上次状态
            self.last_a = current_a
            self.last_b = current_b
        except Exception as e:
            print(f"Error in encoder ISR: {e}")
    
    def _button_isr(self, pin):
        """按键中断服务程序"""
        self.button_state = self.pin_btn.value()
        
        # 检测按键按下（下降沿）
        if self.last_button_state == 1 and self.button_state == 0:
            self.button_pressed = True
            if self.button_callback:
                self.button_callback("pressed")
        
        # 检测按键释放（上升沿）
        elif self.last_button_state == 0 and self.button_state == 1:
            self.button_released = True
            if self.button_callback:
                self.button_callback("released")
        
        self.last_button_state = self.button_state
        
        # 添加调试输出
        print(f"Button ISR: state={self.button_state}, pressed={self.button_pressed}, released={self.button_released}")
    
    def set_rotation_callback(self, callback):
        """设置旋转回调函数"""
        self.rotation_callback = callback
    
    def set_button_callback(self, callback):
        """设置按键回调函数"""
        self.button_callback = callback
    
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