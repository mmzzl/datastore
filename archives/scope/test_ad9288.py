"""
AD9288驱动测试程序
测试ADC的基本功能，包括采样、触发和DMA传输
"""

import machine
import time
from hal.ad9288 import Adc9288
from hal.test_signal import TestSignalGenerator

def test_ad9288_basic():
    """测试AD9288基本采样功能"""
    print("\n=== 测试AD9288基本采样功能 ===")
    
    db_pins = [machine.Pin(i, machine.Pin.IN) for i in range(8)]
    sck = machine.Pin(21, machine.Pin.OUT)
    
    adc = Adc9288(
        sample_rate=10_000_000,
        sck_pin=sck,
        db_pins=db_pins,
        pio_sm=0,
        dma_channel=1
    )
    
    buffer_size = 240
    buffer = bytearray(buffer_size)
    
    print(f"采样率: {adc.get_sample_rate() / 1_000_000:.1f} MHz")
    print(f"缓冲区大小: {buffer_size} 字节")
    
    print("\n开始采样...")
    start_time = time.ticks_ms()
    
    adc.read(buffer)
    
    end_time = time.ticks_ms()
    elapsed = time.ticks_diff(end_time, start_time)
    
    print(f"采样完成，耗时: {elapsed} ms")
    print(f"采样速度: {buffer_size / elapsed * 1000:.0f} samples/s")
    
    print("\n前20个采样值:")
    for i in range(min(20, len(buffer))):
        print(f"  [{i:3d}]: {buffer[i]:3d} ({buffer[i] / 255.0 * 3.3:.2f} V)")
    
    print("\n统计信息:")
    min_val = min(buffer)
    max_val = max(buffer)
    avg_val = sum(buffer) / len(buffer)
    
    print(f"  最小值: {min_val} ({min_val / 255.0 * 3.3:.2f} V)")
    print(f"  最大值: {max_val} ({max_val / 255.0 * 3.3:.2f} V)")
    print(f"  平均值: {avg_val:.1f} ({avg_val / 255.0 * 3.3:.2f} V)")
    print(f"  峰峰值: {max_val - min_val} ({(max_val - min_val) / 255.0 * 3.3:.2f} V)")
    
    return True

def test_ad9288_with_test_signal():
    """使用测试信号测试AD9288"""
    print("\n=== 使用测试信号测试AD9288 ===")
    
    db_pins = [machine.Pin(i, machine.Pin.IN) for i in range(8)]
    sck = machine.Pin(21, machine.Pin.OUT)
    
    adc = Adc9288(
        sample_rate=10_000_000,
        sck_pin=sck,
        db_pins=db_pins,
        pio_sm=0,
        dma_channel=1
    )
    
    output_pin = machine.Pin(2, machine.Pin.OUT)
    test_signal = TestSignalGenerator(output_pin, frequency=1000)
    
    buffer_size = 240
    buffer = bytearray(buffer_size)
    
    print("启动测试信号...")
    test_signal.start()
    time.sleep(0.1)
    
    print("开始采样...")
    adc.read(buffer)
    
    print("停止测试信号...")
    test_signal.stop()
    
    print("\n采样结果:")
    print(f"  最小值: {min(buffer)}")
    print(f"  最大值: {max(buffer)}")
    print(f"  平均值: {sum(buffer) / len(buffer):.1f}")
    
    print("\n波形数据 (每10个采样点):")
    for i in range(0, len(buffer), 10):
        values = buffer[i:i+10]
        print(f"  [{i:3d}]: {[f'{v:3d}' for v in values]}")
    
    return True

def test_ad9288_trigger():
    """测试AD9288触发功能"""
    print("\n=== 测试AD9288触发功能 ===")
    
    db_pins = [machine.Pin(i, machine.Pin.IN) for i in range(8)]
    sck = machine.Pin(21, machine.Pin.OUT)
    
    adc = Adc9288(
        sample_rate=10_000_000,
        sck_pin=sck,
        db_pins=db_pins,
        pio_sm=0,
        dma_channel=1
    )
    
    buffer_size = 240
    buffer = bytearray(buffer_size)
    
    print("测试上升沿触发...")
    adc.set_trigger_level(128)
    adc.set_trigger_edge('rising')
    adc.set_trigger_enabled(True)
    
    print(f"  触发级别: {adc.trigger_level}")
    print(f"  触发边沿: {adc.trigger_edge}")
    print(f"  触发状态: {'启用' if adc.trigger_enabled else '禁用'}")
    
    adc.read_triggered(buffer)
    
    print("\n采样完成")
    print(f"  最小值: {min(buffer)}")
    print(f"  最大值: {max(buffer)}")
    
    print("\n测试下降沿触发...")
    adc.set_trigger_edge('falling')
    adc.set_trigger_level(128)
    
    print(f"  触发级别: {adc.trigger_level}")
    print(f"  触发边沿: {adc.trigger_edge}")
    
    adc.read_triggered(buffer)
    
    print("\n采样完成")
    print(f"  最小值: {min(buffer)}")
    print(f"  最大值: {max(buffer)}")
    
    adc.set_trigger_enabled(False)
    print("\n触发已禁用")
    
    return True

def test_ad9288_sample_rates():
    """测试不同采样率"""
    print("\n=== 测试不同采样率 ===")
    
    db_pins = [machine.Pin(i, machine.Pin.IN) for i in range(8)]
    sck = machine.Pin(21, machine.Pin.OUT)
    
    sample_rates = [1_000_000, 5_000_000, 10_000_000, 50_000_000, 100_000_000]
    buffer_size = 240
    
    for rate in sample_rates:
        print(f"\n测试采样率: {rate / 1_000_000:.1f} MHz")
        
        adc = Adc9288(
            sample_rate=rate,
            sck_pin=sck,
            db_pins=db_pins,
            pio_sm=0,
            dma_channel=1
        )
        
        buffer = bytearray(buffer_size)
        
        start_time = time.ticks_ms()
        adc.read(buffer)
        end_time = time.ticks_ms()
        
        elapsed = time.ticks_diff(end_time, start_time)
        actual_rate = buffer_size / elapsed * 1000
        
        print(f"  理论采样率: {rate / 1_000_000:.1f} MHz")
        print(f"  实际采样率: {actual_rate / 1_000_000:.1f} MHz")
        print(f"  采样耗时: {elapsed} ms")
        print(f"  采样值范围: {min(buffer)} - {max(buffer)}")
    
    return True

def test_ad9288_continuous():
    """测试连续采样"""
    print("\n=== 测试连续采样 ===")
    
    db_pins = [machine.Pin(i, machine.Pin.IN) for i in range(8)]
    sck = machine.Pin(21, machine.Pin.OUT)
    
    adc = Adc9288(
        sample_rate=10_000_000,
        sck_pin=sck,
        db_pins=db_pins,
        pio_sm=0,
        dma_channel=1
    )
    
    buffer_size = 240
    buffer = bytearray(buffer_size)
    
    print("连续采样10次...")
    for i in range(10):
        start_time = time.ticks_ms()
        adc.read(buffer)
        end_time = time.ticks_ms()
        
        elapsed = time.ticks_diff(end_time, start_time)
        
        print(f"  [{i+1:2d}] 耗时: {elapsed:3d} ms, "
              f"范围: {min(buffer):3d}-{max(buffer):3d}, "
              f"平均: {sum(buffer)/len(buffer):.1f}")
        
        time.sleep(0.01)
    
    print("\n连续采样测试完成")
    return True

def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*50)
    print("AD9288驱动测试套件")
    print("="*50)
    
    tests = [
        ("基本采样功能", test_ad9288_basic),
        ("测试信号采样", test_ad9288_with_test_signal),
        ("触发功能", test_ad9288_trigger),
        ("不同采样率", test_ad9288_sample_rates),
        ("连续采样", test_ad9288_continuous)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result, None))
            print(f"\n✓ {name} 测试通过")
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"\n✗ {name} 测试失败: {e}")
    
    print("\n" + "="*50)
    print("测试结果汇总")
    print("="*50)
    
    passed = sum(1 for _, result, _ in results if result)
    total = len(results)
    
    for name, result, error in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status} - {name}")
        if error:
            print(f"  错误: {error}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    
    if success:
        print("\n🎉 所有测试通过!")
    else:
        print("\n⚠ 部分测试失败")
