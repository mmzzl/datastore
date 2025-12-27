"""
AD9288驱动使用示例
演示如何使用AD9288驱动程序进行高速ADC采样
"""

import machine
import time
from hal.ad9288 import Adc9288

def example_basic_sampling():
    """示例1: 基本采样"""
    print("\n=== 示例1: 基本采样 ===")
    
    # 配置硬件引脚
    db_pins = [machine.Pin(i, machine.Pin.IN) for i in range(8)]
    sck = machine.Pin(21, machine.Pin.OUT)
    
    # 创建ADC实例
    adc = Adc9288(
        sample_rate=10_000_000,  # 10 MHz采样率
        sck_pin=sck,
        db_pins=db_pins,
        pio_sm=0,
        dma_channel=1
    )
    
    # 创建采样缓冲区
    buffer_size = 240
    buffer = bytearray(buffer_size)
    
    # 执行采样
    print("开始采样...")
    adc.read(buffer)
    print("采样完成")
    
    # 显示结果
    print(f"采样值范围: {min(buffer)} - {max(buffer)}")
    print(f"平均值: {sum(buffer) / len(buffer):.1f}")
    
    return buffer

def example_triggered_sampling():
    """示例2: 触发采样"""
    print("\n=== 示例2: 触发采样 ===")
    
    # 配置硬件引脚
    db_pins = [machine.Pin(i, machine.Pin.IN) for i in range(8)]
    sck = machine.Pin(21, machine.Pin.OUT)
    
    # 创建ADC实例
    adc = Adc9288(
        sample_rate=10_000_000,
        sck_pin=sck,
        db_pins=db_pins,
        pio_sm=0,
        dma_channel=1
    )
    
    # 配置触发
    adc.set_trigger_level(128)        # 触发级别
    adc.set_trigger_edge('rising')     # 上升沿触发
    adc.set_trigger_enabled(True)       # 启用触发
    
    # 创建采样缓冲区
    buffer = bytearray(240)
    
    # 执行触发采样
    print("开始触发采样...")
    adc.read_triggered(buffer)
    print("采样完成")
    
    # 显示结果
    print(f"采样值范围: {min(buffer)} - {max(buffer)}")
    
    # 禁用触发
    adc.set_trigger_enabled(False)
    
    return buffer

def example_variable_sample_rate():
    """示例3: 可变采样率"""
    print("\n=== 示例3: 可变采样率 ===")
    
    # 配置硬件引脚
    db_pins = [machine.Pin(i, machine.Pin.IN) for i in range(8)]
    sck = machine.Pin(21, machine.Pin.OUT)
    
    # 创建ADC实例
    adc = Adc9288(
        sample_rate=1_000_000,  # 初始1 MHz
        sck_pin=sck,
        db_pins=db_pins,
        pio_sm=0,
        dma_channel=1
    )
    
    # 测试不同采样率
    sample_rates = [1_000_000, 5_000_000, 10_000_000, 50_000_000]
    
    for rate in sample_rates:
        # 设置采样率
        adc.set_sample_rate(rate)
        
        # 执行采样
        buffer = bytearray(240)
        start_time = time.ticks_ms()
        adc.read(buffer)
        elapsed = time.ticks_diff(start_time, time.ticks_ms())
        
        # 显示结果
        print(f"采样率: {rate/1_000_000:.1f} MHz, "
              f"耗时: {elapsed} ms, "
              f"范围: {min(buffer)}-{max(buffer)}")
    
    return True

def example_continuous_sampling():
    """示例4: 连续采样"""
    print("\n=== 示例4: 连续采样 ===")
    
    # 配置硬件引脚
    db_pins = [machine.Pin(i, machine.Pin.IN) for i in range(8)]
    sck = machine.Pin(21, machine.Pin.OUT)
    
    # 创建ADC实例
    adc = Adc9288(
        sample_rate=10_000_000,
        sck_pin=sck,
        db_pins=db_pins,
        pio_sm=0,
        dma_channel=1
    )
    
    # 创建采样缓冲区
    buffer = bytearray(240)
    
    # 连续采样
    print("开始连续采样 (按Ctrl+C停止)...")
    count = 0
    
    try:
        while True:
            adc.read(buffer)
            count += 1
            
            # 每10次采样显示一次统计
            if count % 10 == 0:
                avg = sum(buffer) / len(buffer)
                print(f"[{count:3d}] 范围: {min(buffer):3d}-{max(buffer):3d}, "
                      f"平均: {avg:.1f}")
            
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print(f"\n采样停止，共采样 {count} 次")
    
    return True

def example_voltage_measurement():
    """示例5: 电压测量"""
    print("\n=== 示例5: 电压测量 ===")
    
    # 配置硬件引脚
    db_pins = [machine.Pin(i, machine.Pin.IN) for i in range(8)]
    sck = machine.Pin(21, machine.Pin.OUT)
    
    # 创建ADC实例
    adc = Adc9288(
        sample_rate=10_000_000,
        sck_pin=sck,
        db_pins=db_pins,
        pio_sm=0,
        dma_channel=1
    )
    
    # 创建采样缓冲区
    buffer = bytearray(240)
    
    # 执行采样
    adc.read(buffer)
    
    # 计算电压参数
    voltage_ref = 3.3  # 参考电压
    
    min_val = min(buffer)
    max_val = max(buffer)
    avg_val = sum(buffer) / len(buffer)
    
    # 转换为电压值
    min_voltage = min_val / 255.0 * voltage_ref
    max_voltage = max_val / 255.0 * voltage_ref
    avg_voltage = avg_val / 255.0 * voltage_ref
    vpp_voltage = (max_val - min_val) / 255.0 * voltage_ref
    
    # 计算RMS电压
    sum_sq = sum((x - avg_val) ** 2 for x in buffer)
    rms_val = (sum_sq / len(buffer)) ** 0.5
    rms_voltage = rms_val / 255.0 * voltage_ref
    
    # 显示结果
    print("电压测量结果:")
    print(f"  最小电压: {min_voltage:.3f} V")
    print(f"  最大电压: {max_voltage:.3f} V")
    print(f"  平均电压: {avg_voltage:.3f} V")
    print(f"  峰峰值电压: {vpp_voltage:.3f} V")
    print(f"  RMS电压: {rms_voltage:.3f} V")
    
    return {
        'min': min_voltage,
        'max': max_voltage,
        'avg': avg_voltage,
        'vpp': vpp_voltage,
        'rms': rms_voltage
    }

def example_frequency_measurement():
    """示例6: 频率测量"""
    print("\n=== 示例6: 频率测量 ===")
    
    # 配置硬件引脚
    db_pins = [machine.Pin(i, machine.Pin.IN) for i in range(8)]
    sck = machine.Pin(21, machine.Pin.OUT)
    
    # 创建ADC实例
    adc = Adc9288(
        sample_rate=10_000_000,
        sck_pin=sck,
        db_pins=db_pins,
        pio_sm=0,
        dma_channel=1
    )
    
    # 创建采样缓冲区
    buffer = bytearray(240)
    
    # 执行采样
    adc.read(buffer)
    
    # 使用过零检测法计算频率
    threshold = 128
    zero_crossings = 0
    prev_above = buffer[0] > threshold
    
    for i in range(1, len(buffer)):
        curr_above = buffer[i] > threshold
        
        if curr_above != prev_above:
            zero_crossings += 1
            prev_above = curr_above
    
    # 计算频率
    if zero_crossings > 0:
        period_samples = len(buffer) / (zero_crossings / 2)
        frequency = adc.get_sample_rate() / period_samples
        
        print(f"过零点数量: {zero_crossings}")
        print(f"周期采样点数: {period_samples:.1f}")
        print(f"信号频率: {frequency:.1f} Hz")
        
        if frequency > 1000:
            print(f"信号频率: {frequency/1000:.2f} kHz")
        
        return frequency
    else:
        print("未检测到过零点，无法计算频率")
        return 0

def example_advanced_trigger():
    """示例7: 高级触发功能"""
    print("\n=== 示例7: 高级触发功能 ===")
    
    # 配置硬件引脚
    db_pins = [machine.Pin(i, machine.Pin.IN) for i in range(8)]
    sck = machine.Pin(21, machine.Pin.OUT)
    
    # 创建ADC实例
    adc = Adc9288(
        sample_rate=10_000_000,
        sck_pin=sck,
        db_pins=db_pins,
        pio_sm=0,
        dma_channel=1
    )
    
    # 测试不同的触发级别
    trigger_levels = [64, 128, 192]
    
    for level in trigger_levels:
        # 设置触发参数
        adc.set_trigger_level(level)
        adc.set_trigger_edge('rising')
        adc.set_trigger_enabled(True)
        
        # 执行触发采样
        buffer = bytearray(240)
        adc.read_triggered(buffer)
        
        # 显示结果
        print(f"触发级别: {level}, "
              f"采样范围: {min(buffer)}-{max(buffer)}")
    
    # 测试不同的触发边沿
    edges = ['rising', 'falling']
    
    for edge in edges:
        adc.set_trigger_level(128)
        adc.set_trigger_edge(edge)
        adc.set_trigger_enabled(True)
        
        buffer = bytearray(240)
        adc.read_triggered(buffer)
        
        print(f"触发边沿: {edge}, "
              f"采样范围: {min(buffer)}-{max(buffer)}")
    
    # 禁用触发
    adc.set_trigger_enabled(False)
    
    return True

def main():
    """运行所有示例"""
    print("\n" + "="*50)
    print("AD9288驱动使用示例")
    print("="*50)
    
    examples = [
        ("基本采样", example_basic_sampling),
        ("触发采样", example_triggered_sampling),
        ("可变采样率", example_variable_sample_rate),
        ("电压测量", example_voltage_measurement),
        ("频率测量", example_frequency_measurement),
        ("高级触发", example_advanced_trigger)
    ]
    
    print("\n可用示例:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\n运行所有示例...")
    
    for name, func in examples:
        try:
            print(f"\n{'='*50}")
            func()
            print(f"✓ {name} 示例完成")
        except Exception as e:
            print(f"✗ {name} 示例失败: {e}")
    
    print("\n" + "="*50)
    print("所有示例运行完成")
    print("="*50)

if __name__ == "__main__":
    main()
