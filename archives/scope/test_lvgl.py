import machine
import time
import lvgl as lv
import uasyncio as asyncio
from hal.st7789 import ST7789
from gui.display_driver_utils import Display_Driver
from gui.async_utils import Lv_Async
from scope import Scope
from hal.encoder import EH11Encoder
from clock import Clock
from example.example import (show_hello_world, get_started_2)

def main():
     # 引脚定义 - 根据实际硬件连接调整
    baudrate = 40_000_000  # ST7789支持更高波特率
    sck = machine.Pin(10, machine.Pin.OUT)
    mosi = machine.Pin(11, machine.Pin.OUT)
    rst = machine.Pin(12, machine.Pin.OUT)
    dc = machine.Pin(13, machine.Pin.OUT)
    cs = machine.Pin(14, machine.Pin.OUT)
    bl = machine.Pin(15, machine.Pin.OUT)
    miso = None
    # 创建ST7789实例 (240x320分辨率)
    lcd = ST7789(baudrate, cs, sck, mosi, miso, dc, rst, bl, 
                    rotation=3)
    encoder = EH11Encoder()
    
    # 检查is_connected方法是否存在
    if hasattr(encoder, 'is_connected'):
        print("✓ is_connected method found")
        # 检查连接状态
        if encoder.is_connected():
            print("✓ Encoder connected successfully")
        else:
            print("Warning: Encoder may not be properly connected")
    else:
        print("✗ is_connected method not found")
        print("Available methods:", [method for method in dir(encoder) if not method.startswith('_')])
    
    # 设置防抖时间（可选）
    encoder.set_debounce_time(30)  # 30ms防抖时间
    
    # 控制调试输出（生产环境中可以关闭）
    encoder.set_debug(True)  # 设置为False可以禁用调试输出
    
    display_driver = Display_Driver(lcd, 320, 240, encoder=encoder)
    scr = lv.screen_active()
    scr.set_style_bg_color(lv.color_hex(0x003a57), lv.PART.MAIN)
    
    # clock = Clock(scr, display_driver)
    
    # display_driver_utils.py中已经设置了全局焦点组
    # 不需要在这里重复设置
    
#     show_hello_world(scr)
    # btn = get_started_2(scr)
    
    # # 将按钮手动添加到全局焦点组
    # display_driver.add_obj_to_focus_group(btn)
    
    # # 确保按钮获得焦点
    # lv.group_focus_obj(btn)
    # print("Button added to focus group and focused")
    
    my_scope = Scope(scr, display_driver)
    
    def scope_update(tmr):
        my_scope.process()
    
    timer = lv.timer_create_basic()
    timer.set_period(50)
    timer.set_cb(scope_update)
    print("示波器定时器已启动")
    
    lva = Lv_Async( refresh_rate=20 )
    asyncio.Loop.run_forever()