"""
示波器功能示例程序
演示如何使用示波器的各种功能
"""

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
    print("=== RP2040 100MHz 示波器 ===")
    
    # 初始化显示屏
    print("初始化ST7789显示屏...")
    baudrate = 40_000_000
    sck = machine.Pin(10, machine.Pin.OUT)
    mosi = machine.Pin(11, machine.Pin.OUT)
    rst = machine.Pin(12, machine.Pin.OUT)
    dc = machine.Pin(13, machine.Pin.OUT)
    cs = machine.Pin(14, machine.Pin.OUT)
    bl = machine.Pin(15, machine.Pin.OUT)
    miso = None
    
    lcd = ST7789(baudrate, cs, sck, mosi, miso, dc, rst, bl, rotation=3)
    print("✓ 显示屏初始化成功")
    
    # 初始化编码器
    print("初始化EH11编码器...")
    encoder = EH11Encoder()
    encoder.set_debounce_time(30)
    encoder.set_debug(False)
    print("✓ 编码器初始化成功")
    
    # 初始化显示驱动
    print("初始化显示驱动...")
    display_driver = Display_Driver(lcd, 320, 240, encoder=encoder)
    scr = lv.screen_active()
    scr.set_style_bg_color(lv.color_hex(0x003a57), lv.PART.MAIN)
    print("✓ 显示驱动初始化成功")
    
    # 创建示波器
    print("初始化示波器...")
    my_scope = Scope(scr, display_driver)
    print("✓ 示波器初始化成功")
    
    # 示例1: 使用测试信号
    print("\n示例1: 启用测试信号")
    my_scope.toggle_test_signal()
    my_scope.set_test_signal_frequency(1000)  # 1kHz正弦波
    print("✓ 测试信号已启用 (1kHz)")
    
    # 等待5秒观察测试信号
    print("观察测试信号中...")
    time.sleep(5)
    
    # 示例2: 调整测试信号频率
    print("\n示例2: 调整测试信号频率")
    for freq in [100, 500, 1000, 5000, 10000]:
        my_scope.set_test_signal_frequency(freq)
        print(f"  频率设置为: {freq} Hz")
        time.sleep(2)
    
    # 示例3: 启用触发功能
    print("\n示例3: 启用触发功能")
    my_scope.set_trigger_level(128)
    my_scope.set_trigger_enabled(True)
    print("✓ 触发已启用 (级别: 128)")
    time.sleep(3)
    
    # 示例4: 调整触发级别
    print("\n示例4: 调整触发级别")
    for level in [64, 128, 192]:
        my_scope.set_trigger_level(level)
        print(f"  触发级别设置为: {level}")
        time.sleep(2)
    
    # 示例5: 关闭触发
    print("\n示例5: 关闭触发功能")
    my_scope.toggle_trigger()
    print("✓ 触发已关闭")
    time.sleep(2)
    
    # 示例6: 暂停波形
    print("\n示例6: 暂停波形显示")
    print("  当前状态: 运行中")
    time.sleep(2)
    print("  暂停波形...")
    my_scope.is_paused = True
    my_scope.status_label.set_text("Status: Paused")
    time.sleep(3)
    print("  继续波形...")
    my_scope.is_paused = False
    my_scope.status_label.set_text("Status: Running")
    time.sleep(2)
    
    # 示例7: 切换到真实ADC采样
    print("\n示例7: 切换到真实ADC采样")
    my_scope.toggle_test_signal()
    print("✓ 已切换到AD9288采样模式")
    print("  请连接测试信号到AD9288输入")
    time.sleep(5)
    
    # 示例8: 调整电压缩放
    print("\n示例8: 调整电压缩放")
    for scale in [0.5, 1.0, 2.0, 5.0]:
        my_scope.voltage_scale = scale
        my_scope._update_ui()
        print(f"  电压缩放设置为: {scale}x")
        time.sleep(2)
    
    # 示例9: 恢复默认设置
    print("\n示例9: 恢复默认设置")
    my_scope.voltage_scale = 1.0
    my_scope.time_scale = 1.0
    my_scope.trigger_level = 128
    my_scope.trigger_enabled = False
    my_scope.is_paused = False
    my_scope._update_ui()
    print("✓ 已恢复默认设置")
    
    # 示例10: 重新启用测试信号
    print("\n示例10: 重新启用测试信号")
    my_scope.toggle_test_signal()
    my_scope.set_test_signal_frequency(1000)
    print("✓ 测试信号已重新启用")
    
    print("\n=== 示例演示完成 ===")
    print("示波器现在处于正常运行状态")
    print("使用旋转编码器可以:")
    print("  - 旋转: 调节波形缩放")
    print("  - 短按: 暂停/继续")
    print("  - 长按: 切换缩放模式")
    
    # 设置定时器持续更新波形
    def scope_update(tmr):
        my_scope.process()
    
    timer = lv.timer_create_basic()
    timer.set_period(50)
    timer.set_cb(scope_update)
    print("✓ 示波器定时器已启动")
    
    # 运行主循环
    lva = Lv_Async(refresh_rate=20)
    asyncio.Loop.run_forever()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()
