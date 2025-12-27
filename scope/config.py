"""
示波器配置文件
用户可以在此修改硬件连接和参数设置
"""

# ============== 硬件引脚配置 ==============

# ST7789显示屏引脚
LCD_CONFIG = {
    'baudrate': 40_000_000,      # SPI波特率
    'sck': 10,                   # 时钟引脚
    'mosi': 11,                  # 数据输出引脚
    'miso': None,                # 数据输入引脚（可选）
    'rst': 12,                   # 复位引脚
    'dc': 13,                    # 数据/命令选择引脚
    'cs': 14,                    # 片选引脚
    'bl': 15,                    # 背光引脚
    'rotation': 3,               # 屏幕旋转 (0-3)
    'x_offset': 0,               # X轴偏移
    'y_offset': 0                # Y轴偏移
}

# AD9288 ADC引脚
ADC_CONFIG = {
    'db_pins': [0, 1, 2, 3, 4, 5, 6, 7],  # 数据引脚 DB0-DB7
    'sck': 21,                   # 采样时钟引脚
    'sample_rate': 100_000_000,  # 采样率 (Hz)
    'buffer_size': 240,          # 采样缓冲区大小
    'pio_sm': 0,                 # PIO状态机编号
    'dma_channel': 1             # DMA通道编号
}

# EH11旋转编码器引脚
ENCODER_CONFIG = {
    'pin_a': 18,                 # A相引脚
    'pin_b': 19,                 # B相引脚
    'pin_btn': 20,               # 按键引脚
    'debounce_time': 30,         # 防抖时间 (ms)
    'debug': False               # 调试输出
}

# 测试信号生成器引脚
TEST_SIGNAL_CONFIG = {
    'output_pin': 2,             # 输出引脚
    'default_frequency': 1000,  # 默认频率 (Hz)
    'default_amplitude': 64,     # 默认幅度 (0-128)
    'default_offset': 128,       # 默认偏置 (0-255)
    'default_waveform': 'sine'  # 默认波形类型
}

# ============== 示波器参数配置 ==============

SCOPE_CONFIG = {
    # 显示参数
    'width': 320,                # 显示宽度
    'height': 240,               # 显示高度
    'waveform_height': 180,      # 波形显示区域高度
    'waveform_y': 30,            # 波形显示区域Y坐标
    
    # 刷新参数
    'refresh_rate': 20,          # 刷新率 (Hz)
    'timer_period': 50,          # 定时器周期 (ms)
    
    # 缩放参数
    'voltage_scale_min': 0.1,    # 最小电压缩放
    'voltage_scale_max': 10.0,   # 最大电压缩放
    'voltage_scale_step': 0.1,  # 电压缩放步长
    'time_scale_min': 0.1,       # 最小时间缩放
    'time_scale_max': 10.0,      # 最大时间缩放
    'time_scale_step': 0.1,      # 时间缩放步长
    
    # 触发参数
    'trigger_level_min': 0,      # 最小触发级别
    'trigger_level_max': 255,    # 最大触发级别
    'default_trigger_level': 128, # 默认触发级别
    'trigger_edge': 'rising',    # 触发边沿 ('rising' 或 'falling')
    
    # 测量参数
    'voltage_ref': 3.3,          # 参考电压 (V)
    'adc_resolution': 8,         # ADC分辨率 (位)
    
    # 颜色配置
    'waveform_color': 0x00ff00,  # 波形颜色 (绿色)
    'grid_color': 0x1a1a2e,      # 网格颜色
    'center_color': 0x333333,    # 中心线颜色
    'trigger_color': 0xff0000,   # 触发线颜色 (红色)
    'bg_color': 0x000000,        # 背景颜色
    'status_bar_bg': 0x1a1a2e,   # 状态栏背景色
    'info_panel_bg': 0x1a1a2e,   # 信息面板背景色
    
    # 文本颜色
    'freq_color': 0x00ff00,      # 频率文本颜色
    'vpp_color': 0xffff00,       # 电压文本颜色
    'scale_color': 0x00ffff,     # 缩放文本颜色
    'status_color': 0xffffff,    # 状态文本颜色
    'trigger_text_color': 0xff9900 # 触发文本颜色
}

# ============== 性能优化配置 ==============

PERFORMANCE_CONFIG = {
    # DMA配置
    'use_ring_buffer': True,     # 使用环形缓冲区
    'ring_size_pow2': 8,         # 环形缓冲区大小幂次
    
    # 波形绘制优化
    'optimize_drawing': True,    # 优化波形绘制
    'batch_draw_lines': True,    # 批量绘制线条
    
    # 内存优化
    'reuse_buffers': True,       # 重用缓冲区
    'buffer_pool_size': 2        # 缓冲区池大小
}

# ============== 调试配置 ==============

DEBUG_CONFIG = {
    'enable_debug': False,       # 启用调试输出
    'log_adc_data': False,       # 记录ADC数据
    'log_performance': False,    # 记录性能数据
    'log_encoder_events': False, # 记录编码器事件
    'log_trigger_events': False  # 记录触发事件
}

# ============== 用户界面配置 ==============

UI_CONFIG = {
    # 状态栏配置
    'show_frequency': True,      # 显示频率
    'show_voltage': True,        # 显示电压
    'show_scale': True,          # 显示缩放
    
    # 信息面板配置
    'show_status': True,         # 显示状态
    'show_trigger': True,        # 显示触发信息
    
    # 波形显示配置
    'show_grid': True,           # 显示网格
    'show_center_line': True,    # 显示中心线
    'show_trigger_line': True,   # 显示触发线
    
    # 文本格式
    'freq_format': 'auto',       # 频率格式 ('auto', 'hz', 'khz', 'mhz')
    'voltage_format': '.2f',     # 电压格式
    'scale_format': '.1f'        # 缩放格式
}

# ============== 高级配置 ==============

ADVANCED_CONFIG = {
    # 采样配置
    'oversampling': 1,           # 过采样倍数
    'averaging': False,          # 平均采样
    'average_count': 4,          # 平均采样次数
    
    # 触发配置
    'trigger_hysteresis': 2,      # 触发迟滞
    'trigger_timeout': 1000,      # 触发超时 (ms)
    
    # 测量配置
    'frequency_method': 'zero_crossing',  # 频率测量方法 ('zero_crossing', 'fft')
    'voltage_method': 'peak_to_peak',     # 电压测量方法 ('peak_to_peak', 'rms')
    
    # 滤波配置
    'enable_filter': False,      # 启用滤波
    'filter_type': 'none',       # 滤波类型 ('none', 'lowpass', 'highpass')
    'filter_cutoff': 1000        # 滤波截止频率 (Hz)
}

# ============== 配置验证函数 ==============

def validate_config():
    """验证配置参数"""
    errors = []
    
    # 验证引脚配置
    if not (0 <= LCD_CONFIG['sck'] <= 29):
        errors.append("LCD SCK引脚超出范围")
    
    if not (0 <= ADC_CONFIG['sck'] <= 29):
        errors.append("ADC SCK引脚超出范围")
    
    if not (0 <= ENCODER_CONFIG['pin_a'] <= 29):
        errors.append("编码器A相引脚超出范围")
    
    # 验证采样率
    if ADC_CONFIG['sample_rate'] > 100_000_000:
        errors.append("采样率超过100MHz")
    
    # 验证缓冲区大小
    if ADC_CONFIG['buffer_size'] > 4096:
        errors.append("缓冲区大小过大")
    
    # 验证缩放范围
    if SCOPE_CONFIG['voltage_scale_min'] >= SCOPE_CONFIG['voltage_scale_max']:
        errors.append("电压缩放范围无效")
    
    # 验证触发级别
    if not (0 <= SCOPE_CONFIG['default_trigger_level'] <= 255):
        errors.append("默认触发级别超出范围")
    
    return errors

def print_config():
    """打印当前配置"""
    print("\n=== 示波器配置 ===")
    print("\n硬件引脚配置:")
    print(f"  LCD SCK: GPIO{LCD_CONFIG['sck']}")
    print(f"  ADC SCK: GPIO{ADC_CONFIG['sck']}")
    print(f"  编码器 A相: GPIO{ENCODER_CONFIG['pin_a']}")
    print(f"  编码器 B相: GPIO{ENCODER_CONFIG['pin_b']}")
    print(f"  编码器按键: GPIO{ENCODER_CONFIG['pin_btn']}")
    
    print("\n示波器参数:")
    print(f"  采样率: {ADC_CONFIG['sample_rate']/1_000_000:.1f} MHz")
    print(f"  缓冲区大小: {ADC_CONFIG['buffer_size']}")
    print(f"  刷新率: {SCOPE_CONFIG['refresh_rate']} Hz")
    print(f"  显示分辨率: {SCOPE_CONFIG['width']}x{SCOPE_CONFIG['height']}")
    
    print("\n缩放范围:")
    print(f"  电压缩放: {SCOPE_CONFIG['voltage_scale_min']}x - {SCOPE_CONFIG['voltage_scale_max']}x")
    print(f"  时间缩放: {SCOPE_CONFIG['time_scale_min']}x - {SCOPE_CONFIG['time_scale_max']}x")
    
    print("\n触发配置:")
    print(f"  默认触发级别: {SCOPE_CONFIG['default_trigger_level']}")
    print(f"  触发边沿: {SCOPE_CONFIG['trigger_edge']}")
    
    print("\n性能配置:")
    print(f"  使用环形缓冲区: {PERFORMANCE_CONFIG['use_ring_buffer']}")
    print(f"  优化波形绘制: {PERFORMANCE_CONFIG['optimize_drawing']}")
    
    print("\n调试配置:")
    print(f"  启用调试: {DEBUG_CONFIG['enable_debug']}")
    
    # 验证配置
    errors = validate_config()
    if errors:
        print("\n⚠ 配置错误:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✓ 配置验证通过")

if __name__ == "__main__":
    print_config()
