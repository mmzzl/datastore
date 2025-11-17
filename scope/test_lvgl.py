import machine
import time
import lvgl as lv
import uasyncio as asyncio
from hal.st7789 import ST7789
from gui.display_driver_utils import Display_Driver
from gui.async_utils import Lv_Async
from scope import Scope
from hal.encoder import EH11Encoder

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
    display_driver = Display_Driver(lcd, 320, 240, encoder=encoder)
    scr = lv.screen_active()
    my_scope = Scope(scr, display_driver)
    timer = lv.timer_create_basic()
    timer.set_period( 50 )
    timer.set_cb(lambda tmr: my_scope.process())
    print( "run" )
    lva = Lv_Async( refresh_rate=20 )
    asyncio.Loop.run_forever()