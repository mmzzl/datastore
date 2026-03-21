"""
示波器模块测试程序
测试各个硬件模块的功能
"""

import machine
import time
from hal.st7789 import ST7789
from hal.ad9288 import Adc9288
from hal.encoder import EH11Encoder
from hal.test_signal import TestSignalGenerator

def test_display():
    """测试显示屏"""
    print("\n=== 测试ST7789显示屏 ===")
    
    try:
        baudrate = 40_000_000
        sck = machine.Pin(10, machine.Pin.OUT)
        mosi = machine.Pin(11, machine.Pin.OUT)
        rst = machine.Pin(12, machine.Pin.OUT)
        dc = machine.Pin(13, machine.Pin.OUT)
        cs = machine.Pin(14, machine.Pin.OUT)
        bl = machine.Pin(15, machine.Pin.OUT)
        miso = None
        
        lcd = ST7789(baudrate, cs, sck, mosi, miso, dc, rst, bl, rotation=3)
        print(f"✓ 显示屏初始化成功 ({lcd.width}x{lcd.height})")
        
        # 测试颜色显示
        colors = [
            (0xF800, "红色"),
            (0x07E0, "绿色"),
            (0x001F, "蓝色"),
            (0xFFE0, "黄色"),
            (0x0000, "黑色")
        ]
        
        for color, name in colors:
            print(f"  显示{name}...")
            lcd.fill(color)
            time.sleep_ms(500)
        
        print("✓ 显示屏测试完成")
        return True
        
    except Exception as e:
        print(f"✗ 显示屏测试失败: {e}")
        return False

def test_encoder():
    """测试编码器"""
    print("\n=== 测试EH11编码器 ===")
    
    try:
        encoder = EH11Encoder()
        encoder.set_debounce_time(30)
        encoder.set_debug(True)
        
        print("✓ 编码器初始化成功")
        
        # 检查连接状态
        if encoder.is_connected():
            print("✓ 编码器连接正常")
        else:
            print("⚠ 编码器可能未正确连接")
        
        # 测试旋转
        print("\n请旋转编码器 (5秒)...")
        start_time = time.time()
        initial_counter = encoder.get_counter()
        
        while time.time() - start_time < 5:
            time.sleep_ms(100)
        
        final_counter = encoder.get_counter()
        rotation_count = final_counter - initial_counter
        
        if rotation_count != 0:
            print(f"✓ 检测到旋转: {rotation_count} 步")
        else:
            print("⚠ 未检测到旋转")
        
        # 测试按键
        print("\n请按下编码器按键 (5秒)...")
        start_time = time.time()
        button_pressed = False
        
        while time.time() - start_time < 5:
            events = encoder.get_events()
            if events['button_pressed']:
                button_pressed = True
                print("✓ 检测到按键按下")
                break
            time.sleep_ms(100)
        
        if not button_pressed:
            print("⚠ 未检测到按键按下")
        
        print("✓ 编码器测试完成")
        return True
        
    except Exception as e:
        print(f"✗ 编码器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_adc():
    """测试ADC"""
    print("\n=== 测试AD9288 ADC ===")
    
    try:
        db = machine.Pin(0, machine.Pin.IN)
        sck = machine.Pin(21, machine.Pin.OUT)
        
        # 测试不同采样率
        sample_rates = [1_000_000, 10_000_000, 50_000_000, 100_000_000]
        buffer_size = 1000
        
        for rate in sample_rates:
            print(f"\n测试采样率: {rate/1_000_000:.1f} MHz")
            
            adc = Adc9288(rate, sck, db)
            buf = bytearray(buffer_size)
            
            # 测试采样速度
            t0 = time.ticks_us()
            adc.read(buf)
            t1 = time.ticks_us()
            
            elapsed_time = (t1 - t0) / 1e6
            actual_rate = buffer_size / elapsed_time
            
            print(f"  采样时间: {elapsed_time*1000:.2f} ms")
            print(f"  实际采样率: {actual_rate/1_000_000:.2f} MHz")
            print(f"  前10个采样值: {list(buf[:10])}")
            
            # 分析采样数据
            min_val = min(buf)
            max_val = max(buf)
            avg_val = sum(buf) / len(buf)
            
            print(f"  最小值: {min_val}, 最大值: {max_val}, 平均值: {avg_val:.1f}")
            
            # 测试触发功能
            print("\n  测试触发功能...")
            adc.set_trigger_level(128)
            adc.set_trigger_enabled(True)
            adc.read(buf)
            print(f"  ✓ 触发采样完成")
            
            time.sleep_ms(100)
        
        print("\n✓ ADC测试完成")
        return True
        
    except Exception as e:
        print(f"✗ ADC测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_test_signal():
    """测试测试信号生成器"""
    print("\n=== 测试测试信号生成器 ===")
    
    try:
        output_pin = machine.Pin(2, machine.Pin.OUT)
        generator = TestSignalGenerator(output_pin, frequency=1000)
        
        print("✓ 测试信号生成器初始化成功")
        
        # 测试不同波形类型
        waveforms = ['sine', 'square', 'triangle', 'sawtooth']
        
        for waveform in waveforms:
            print(f"\n测试波形: {waveform}")
            generator.set_waveform_type(waveform)
            
            # 生成测试缓冲区
            test_buffer = bytearray(256)
            generator.generate_buffer(test_buffer, 100000)
            
            min_val = min(test_buffer)
            max_val = max(test_buffer)
            avg_val = sum(test_buffer) / len(test_buffer)
            
            print(f"  最小值: {min_val}, 最大值: {max_val}, 平均值: {avg_val:.1f}")
        
        # 测试不同频率
        print("\n测试不同频率...")
        frequencies = [100, 1000, 10000, 50000]
        
        for freq in frequencies:
            print(f"  频率: {freq} Hz")
            generator.set_frequency(freq)
            generator.generate_buffer(test_buffer, 100000)
            print(f"  ✓ 生成完成")
        
        print("\n✓ 测试信号生成器测试完成")
        return True
        
    except Exception as e:
        print(f"✗ 测试信号生成器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("RP2040 示波器模块测试")
    print("=" * 50)
    
    results = {}
    
    # 运行各项测试
    results['display'] = test_display()
    results['encoder'] = test_encoder()
    results['adc'] = test_adc()
    results['test_signal'] = test_test_signal()
    
    # 打印测试结果
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    
    for test_name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name:20s}: {status}")
    
    # 统计结果
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("✓ 所有测试通过！")
    else:
        print("⚠ 部分测试失败，请检查硬件连接和配置")

if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
