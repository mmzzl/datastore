import os
import time
import machine
import rp2
import array
import uctypes

import lvgl as lv
from gui.dear_lvgl import *
from gui.display_driver_utils import Display_Driver
from hal.encoder import EH11Encoder

# 缩放系数
SCALE = 0.4

def scale(v):
    return int(v * SCALE)

class Scope:
    def __init__(self, parent, display_driver: Display_Driver):
        self.display_driver = display_driver
        self.widgets = {}
        self.context = []
        
        # 编码器相关变量
        self.encoder_value = 0
        self.encoder_button_pressed = False
        
        self.build_ui(parent)
        
        # 启动编码器事件处理
        self.process_encoder_events()
    
    def process( self ):
        pass
    
    def process_encoder_events(self):
        """处理编码器事件"""
        events = self.display_driver.get_encoder_events()
        
        # 处理旋转事件
        if events["rotation"] != 0:
            self.encoder_value += events["rotation"]
            self.update_encoder_display()
            print(f"Encoder rotation: {events['rotation']}, new value: {self.encoder_value}")
        
        # 处理按键事件
        if events["button_pressed"]:
            self.encoder_button_pressed = True
            self.update_encoder_display()
            print("Encoder button pressed")
        
        if events["button_released"]:
            self.encoder_button_pressed = False
            self.update_encoder_display()
            print("Encoder button released")
        
        # 继续处理事件
        lv.timer_create(lambda timer: self.process_encoder_events(), 50)
    
    def update_encoder_display(self):
        """更新编码器显示"""
        if "encoder_value" in self.widgets:
            self.widgets["encoder_value"].set_text(f"值: {self.encoder_value}")
        
        if "encoder_status" in self.widgets:
            status = "按下" if self.encoder_button_pressed else "释放"
            self.widgets["encoder_status"].set_text(f"按键: {status}")
    
    def test_button_cb(self, event):
        """测试按钮回调"""
        print("测试按钮被点击")
        self.encoder_value = 0
        self.update_encoder_display()
    
    def build_ui( self, parent ):
        """构建UI界面"""
        width = scale(160)
        self.context.append( parent )
        set_context( self.context )
        set_widgets( self.widgets )
        
        with Cont():
            with Cont( 0, 0, 320-50, 240-15):
                with Column():
                    # 标题
                    add_label("encoder test", w=scale(200))
                    
                    # 测试按钮
                    with Row():
                        add_button("test button").add_event_cb(self.test_button_cb, lv.EVENT.CLICKED, None)
                    
                    # 编码器值显示
                    with Row():
                        add_label("encoder value:", w=scale(80))
                        add_label("v: 0")
                    
                    # 按键状态显示
                    with Row():
                        add_label("status:", w=scale(80))
                        add_label("button: ")

    