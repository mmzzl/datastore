# AD9288 ADC使用指南

## 概述

AD9288是一款双通道8位模数转换器(ADC)，支持最高100 MSPS的采样率，具有475MHz的模拟带宽和低功耗特性。本指南介绍如何在RP2040微控制器上使用AD9288进行高速数据采集。

## 硬件特性

### 基本参数
- **分辨率**: 8位
- **通道数**: 双通道
- **最大采样率**: 100 MSPS
- **模拟带宽**: 475 MHz
- **输入范围**: 1.024 V p-p（可通过参考电压调整±5%）
- **电源电压**: 3.0 V（2.7 V至3.6 V）
- **功耗**: 90 mW（每通道，100 MSPS）

### 引脚功能

| 引脚号 | 名称 | 描述 |
|--------|------|------|
| 2, 3 | AINA, AINA- | 通道A模拟输入（差分） |
| 10, 11 | AINB, AINB- | 通道B模拟输入（差分） |
| 4 | DFS | 数据格式选择（低电平：偏移二进制；高电平：二进制补码） |
| 5, 7 | REFINA, REFINB | 通道A/B参考电压输入 |
| 6 | REFOUT | 内部参考电压输出（1.25V） |
| 8, 9 | S1, S2 | 用户选择引脚，控制工作模式 |
| 14, 47 | ENCB, ENCA | 通道B/A时钟输入 |
| 17-24 | D7B-D0B | 通道B数字输出 |
| 37-44 | D0A-D7A | 通道A数字输出 |
| 13, 30, 31, 48 | VCC | 模拟电源（3V） |
| 15, 28, 33, 46 | VDD | 数字电源（3V） |
| 1, 12, 16, 27, 29, 32, 34, 45 | GND | 地 |

## 硬件连接

### 基本连接方案

#### 1. 电源连接
```
VCC (3V) -> AD9288 VCC引脚
VDD (3V) -> AD9288 VDD引脚
GND -> AD9288 GND引脚
```

#### 2. 模拟输入连接
```
信号源 -> 耦合电容 -> AINA/AINB (或 AINA-/AINB-)
AINA-/AINB- -> 参考电压（通常为VCC×0.3）
```

#### 3. 时钟连接
```
RP2040 PWM输出 -> ENCA/ENCB
```

#### 4. 数据输出连接
```
AD9288 D0A-D7A -> RP2040 GP2-GP9（连续引脚）
AD9288 D0B-D7B -> RP2040 GP11-GP18（连续引脚，用于双通道）
```

### RP2040连接示例

```
AD9288引脚    ->    RP2040引脚
D0A-D7A      ->    GP2-GP9
ENCA         ->    GP10
D0B-D7B      ->    GP11-GP18（双通道使用）
DFS          ->    GND（偏移二进制模式）
S1, S2       ->    GND（正常工作模式）
VCC          ->    3.3V
VDD          ->    3.3V
GND          ->    GND
```

## 工作模式配置

### S1和S2引脚配置

| S1 | S2 | 工作模式 | 描述 |
|----|----|----------|------|
| 0  | 0  | 两通道待机 | 降低功耗 |
| 0  | 1  | 仅B通道待机 | 仅A通道工作 |
| 1  | 0  | 正常工作 | 数据对齐禁用 |
| 1  | 1  | 数据对齐 | B通道数据延迟1/2时钟周期 |

### 数据格式选择

- **DFS = 0**: 偏移二进制输出（推荐）
- **DFS = 1**: 二进制补码输出

## 软件使用

### 1. 基本初始化

```python
import micropython.ad9288_reader_rp2 as ad9288

# 创建单通道读取器
reader = ad9288.AD9288Reader(
    data_base_pin=2,      # D0连接到GP2
    enc_pin=10,           # ENCODE连接到GP10
    dfs_mode="offset-binary"  # 数据格式
)

# 创建双通道读取器
dual_reader = ad9288.AD9288DualReader(
    dataA_base_pin=2,     # 通道A数据引脚起始
    dataB_base_pin=11,    # 通道B数据引脚起始
    enc_pin=10,           # 时钟引脚
    dfs_mode="offset-binary"
)
```

### 2. 单次采样

```python
# 采集1024个样本，采样率10kHz
raw_data = reader.capture_dma(
    n_samples=1024,
    sample_rate_hz=10000,
    pio_freq=2000000
)

# 转换为电压值
volts = reader.samples_to_volts(raw_data)
print(f"前10个样本电压: {volts[:10]}")
```

### 3. 流式采样

```python
# 定义数据块处理回调函数
def chunk_callback(chunk, idx):
    print(f"接收到块 {idx}, 大小: {len(chunk)}")
    # 在这里处理数据块

# 启动流式采样
handle = reader.start_stream_dma(
    chunk_size=256,       # 每块256个样本
    num_chunks=4,         # 总共4块
    sample_rate_hz=10000, # 采样率10kHz
    on_chunk=chunk_callback
)

# 等待采样完成
while handle.completed_chunks < 4:
    time.sleep_ms(10)

# 停止采样
handle.stop()
```

### 4. 双通道同步采样

```python
# 同时采集两个通道
dataA, dataB = dual_reader.capture_dma_dual(
    n_samples=1024,
    sample_rate_hz=10000
)

# 转换为电压值
voltsA = dual_reader.samples_to_volts(dataA)
voltsB = dual_reader.samples_to_volts(dataB)

print(f"通道A前5个样本: {voltsA[:5]}")
print(f"通道B前5个样本: {voltsB[:5]}")
```

### 5. 频率测量

```python
# 测量实际采样频率
measured_freq = reader.measure_rate_dma(
    n_edges=2000,
    start_clock_hz=10000  # 目标频率10kHz
)

print(f"测量频率: {measured_freq:.2f} Hz")
```

## 应用示例

### 1. 简单示波器

```python
import time
import math
from machine import Pin
import micropython.ad9288_reader_rp2 as ad9288

# 初始化ADC
reader = ad9288.AD9288Reader(data_base_pin=2, enc_pin=10)

# 采集数据
sample_rate = 10000  # 10kHz
n_samples = 1000

raw_data = reader.capture_dma(n_samples=n_samples, sample_rate_hz=sample_rate)
volts = reader.samples_to_volts(raw_data)

# 找到最大值和最小值
v_max = max(volts)
v_min = min(volts)
v_pp = v_max - v_min

# 计算频率（简单的过零检测）
zero_crossings = 0
threshold = (v_max + v_min) / 2
for i in range(1, len(volts)):
    if (volts[i-1] < threshold and volts[i] >= threshold) or \
       (volts[i-1] >= threshold and volts[i] < threshold):
        zero_crossings += 1

frequency = (zero_crossings / 2) * (sample_rate / n_samples)

print(f"峰峰值: {v_pp:.3f} V")
print(f"频率: {frequency:.2f} Hz")
```

### 2. 频谱分析

```python
import math
import micropython.ad9288_reader_rp2 as ad9288

# 简单的DFT实现
def dft(samples, sample_rate):
    n = len(samples)
    freqs = []
    mags = []
    
    for k in range(n // 2):  # 只计算正频率部分
        freq = k * sample_rate / n
        real = sum(samples[i] * math.cos(2 * math.pi * k * i / n) for i in range(n))
        imag = -sum(samples[i] * math.sin(2 * math.pi * k * i / n) for i in range(n))
        mag = math.sqrt(real**2 + imag**2) / n
        
        freqs.append(freq)
        mags.append(mag)
    
    return freqs, mags

# 采集数据
reader = ad9288.AD9288Reader(data_base_pin=2, enc_pin=10)
sample_rate = 50000  # 50kHz
n_samples = 1024

raw_data = reader.capture_dma(n_samples=n_samples, sample_rate_hz=sample_rate)
volts = reader.samples_to_volts(raw_data)

# 执行DFT
freqs, mags = dft(volts, sample_rate)

# 找到主要频率分量
max_idx = mags.index(max(mags))
dominant_freq = freqs[max_idx]
dominant_mag = mags[max_idx]

print(f"主要频率分量: {dominant_freq:.2f} Hz, 幅度: {dominant_mag:.3f} V")
```

### 3. 实时数据监控

```python
import time
import micropython.ad9288_reader_rp2 as ad9288

# 实时监控函数
def monitor_signal(duration_sec=10, sample_rate=10000, chunk_size=256):
    reader = ad9288.AD9288Reader(data_base_pin=2, enc_pin=10)
    
    # 计算需要的块数
    total_samples = duration_sec * sample_rate
    num_chunks = (total_samples + chunk_size - 1) // chunk_size
    
    chunks_processed = 0
    max_val = -float('inf')
    min_val = float('inf')
    
    def process_chunk(chunk, idx):
        nonlocal chunks_processed, max_val, min_val
        volts = reader.samples_to_volts(chunk)
        chunk_max = max(volts)
        chunk_min = min(volts)
        
        max_val = max(max_val, chunk_max)
        min_val = min(min_val, chunk_min)
        
        chunks_processed += 1
        print(f"块 {idx+1}/{num_chunks}: 最大={chunk_max:.3f}V, 最小={chunk_min:.3f}V")
    
    # 启动流式采样
    handle = reader.start_stream_dma(
        chunk_size=chunk_size,
        num_chunks=num_chunks,
        sample_rate_hz=sample_rate,
        on_chunk=process_chunk
    )
    
    # 等待完成
    start_time = time.time()
    while handle.completed_chunks < num_chunks and (time.time() - start_time) < duration_sec + 2:
        time.sleep_ms(100)
    
    # 停止采样
    handle.stop()
    
    print(f"\n监控完成:")
    print(f"处理块数: {chunks_processed}/{num_chunks}")
    print(f"最大值: {max_val:.3f} V")
    print(f"最小值: {min_val:.3f} V")
    print(f"峰峰值: {max_val - min_val:.3f} V")

# 运行监控
monitor_signal(duration_sec=5, sample_rate=5000)
```

## 性能优化建议

### 1. 采样率选择

- **低频信号**: 1-10 kHz采样率通常足够
- **音频信号**: 20-50 kHz采样率
- **高频信号**: 根据奈奎斯特定理，至少为信号频率的2倍

### 2. 内存管理

- 对于长时间采样，使用流式采样模式而非一次性采集
- 合理设置块大小，平衡内存使用和处理延迟

### 3. 数据处理

- 在回调函数中尽快处理数据，避免阻塞DMA传输
- 考虑使用环形缓冲区处理连续数据流

### 4. 时钟质量

- 使用低抖动时钟源以提高信噪比
- 对于高精度应用，考虑使用外部时钟源

## 故障排除

### 1. 数据不稳定或噪声大

- 检查电源去耦电容是否正确安装
- 确保模拟输入阻抗匹配
- 验证时钟信号质量

### 2. 采样率不准确

- 检查PWM配置是否正确
- 验证时钟源稳定性
- 使用measure_rate_dma函数测量实际采样率

### 3. 数据格式不正确

- 确认DFS引脚电平设置
- 检查samples_to_volts函数是否与当前数据格式匹配

### 4. DMA传输失败

- 确保DMA通道可用
- 检查缓冲区大小是否合理
- 验证DREQ索引计算是否正确

## 注意事项

1. **电源去耦**: 确保所有电源引脚都有适当的去耦电容（0.1μF高频电容和10μF低频电容）
2. **信号完整性**: 高频信号走线应尽可能短，避免长距离并行布线
3. **时序考虑**: 考虑ADC输出延迟和系统时序要求
4. **温度影响**: ADC性能可能随温度变化，关键应用应考虑温度补偿
5. **输入保护**: 确保模拟输入电压在规格范围内，避免损坏芯片

## 总结

AD9288是一款功能强大的双通道ADC，结合RP2040的PIO和DMA功能，可以实现高速数据采集系统。通过合理配置硬件连接和软件参数，可以满足从简单的电压测量到复杂信号分析的各种应用需求。