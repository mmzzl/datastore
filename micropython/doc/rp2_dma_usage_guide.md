# RP2 DMA使用指南

## 概述

RP2040芯片的DMA（Direct Memory Access）控制器可以在不占用CPU的情况下，在内存和外设之间传输数据。RP2040有12个独立的DMA通道，可以同时运行。

## 基本使用步骤

### 1. 创建DMA实例

```python
import rp2

dma = rp2.DMA()
```

### 2. 配置控制寄存器

```python
ctrl = dma.pack_ctrl(size=0, inc_read=False, inc_write=True, treq_sel=dreq_index)
```

控制参数说明：
- `size`: 传输大小 (0=字节, 1=半字, 2=字)
- `inc_read`: 是否递增读地址
- `inc_write`: 是否递增写地址
- `treq_sel`: 数据请求信号，用于控制传输速率

### 3. 配置DMA传输

```python
dma.config(read=source, write=destination, count=transfer_count, ctrl=ctrl, trigger=True)
```

参数说明：
- `read`: 数据源地址或对象
- `write`: 目标地址或对象
- `count`: 传输次数（注意：不是字节数，取决于传输大小）
- `ctrl`: 控制寄存器配置
- `trigger`: 是否立即开始传输

### 4. 等待传输完成

```python
while dma.active():
    pass
```

### 5. 释放DMA资源

```python
dma.close()
```

## 常见应用场景

### 1. 内存到内存的简单传输

```python
a = bytearray(32*1024)
b = bytearray(32*1024)
d = rp2.DMA()
c = d.pack_ctrl()  # 使用默认控制值
d.config(read=a, write=b, count=len(a)//4, ctrl=c, trigger=True)
while d.active():
    pass
```

### 2. 内存到外设的传输（如PIO状态机）

```python
# 计算DREQ索引
dreq_index = (pio_num << 3) + sm_id

src_data = bytearray(1024)
d = rp2.DMA()

# 配置为字节传输，不递增写地址，控制传输速率
c = d.pack_ctrl(size=0, inc_write=False, treq_sel=dreq_index)

d.config(
    read=src_data,
    write=state_machine,
    count=len(src_data),
    ctrl=c,
    trigger=True
)
```

### 3. 外设到内存的流式传输（带中断）

```python
# 创建多个缓冲区用于流式传输
buffers = [bytearray(chunk_size) for _ in range(num_chunks)]

# 配置DMA
dma = rp2.DMA()
ctrl = dma.pack_ctrl(size=0, inc_read=False, inc_write=True, treq_sel=dreq_index)

# 定义中断处理函数
def _on_irq(_dma=dma):
    idx = state["i"]
    handle.completed_chunks += 1
    if on_chunk:
        try:
            on_chunk(buffers[idx], idx)
        except Exception:
            pass
    state["i"] += 1
    if state["i"] < num_chunks:
        _dma.config(read=sm, write=buffers[state["i"]], count=chunk_size, ctrl=ctrl, trigger=True)
    else:
        handle.stop()

# 设置中断处理
if hasattr(dma, "irq"):
    dma.irq(_on_irq)

# 启动第一次传输
dma.config(read=sm, write=buffers[0], count=chunk_size, ctrl=ctrl, trigger=True)
```

## 高级功能

### 1. DMA通道链接

```python
# 当一个通道完成时，自动触发另一个通道
ctrl = dma.pack_ctrl(chain_to=other_channel_number)
```

### 2. 地址循环

```python
# 使地址在特定边界处循环
ctrl = dma.pack_ctrl(ring_size=3, ring_sel=True)  # 在8字节边界循环
```

## 实际应用示例：AD9288 ADC数据采集

以下是一个完整的AD9288 ADC数据采集示例，展示了如何使用DMA进行高速数据采集：

```python
class AD9288Reader:
    def start_stream_dma(self, num_chunks, chunk_size, on_chunk=None):
        """启动DMA流式传输"""
        # 创建状态机和DMA
        sm = rp2.StateMachine(self.sm_id, self.adc_sm, freq=self.freq)
        dma = rp2.DMA()
        
        # 配置DMA控制寄存器
        ctrl = dma.pack_ctrl(
            size=0,  # 字节传输
            inc_read=False,  # 不递增读地址（固定读取ADC数据）
            inc_write=True,   # 递增写地址
            treq_sel=self.dreq  # 使用ADC数据请求信号
        )
        
        # 创建缓冲区
        buffers = [bytearray(chunk_size) for _ in range(num_chunks)]
        
        # 创建流处理句柄
        handle = StreamHandle(
            dma=dma,
            sm=sm,
            buffers=buffers,
            on_chunk=on_chunk,
            completed_chunks=0,
            active=True
        )
        
        # 定义中断处理状态
        state = {"i": 0}
        
        # 定义DMA中断处理函数
        def _on_irq(_dma=dma):
            idx = state["i"]
            handle.completed_chunks += 1
            
            # 调用回调函数处理数据块
            if on_chunk:
                try:
                    on_chunk(buffers[idx], idx)
                except Exception:
                    pass
            
            state["i"] += 1
            
            # 配置下一个数据块传输
            if state["i"] < num_chunks:
                _dma.config(
                    read=sm,
                    write=buffers[state["i"]],
                    count=chunk_size,
                    ctrl=ctrl,
                    trigger=True
                )
            else:
                handle.stop()
        
        # 设置中断处理
        if hasattr(dma, "irq"):
            dma.irq(_on_irq)
        
        # 启动状态机
        sm.active(1)
        
        # 启动第一次DMA传输
        dma.config(
            read=sm,
            write=buffers[0],
            count=chunk_size,
            ctrl=ctrl,
            trigger=True
        )
        
        return handle
```

## 注意事项

1. **传输计数**：`count`参数是传输次数，不是字节数。如果传输字（4字节），则实际传输字节数为`count * 4`。

2. **DREQ信号**：当与外设交互时，需要正确设置`treq_sel`以控制传输速率，避免数据丢失。

3. **中断处理**：对于流式传输，通常需要设置中断处理函数来处理每个数据块。

4. **资源管理**：使用完毕后记得调用`dma.close()`释放DMA通道资源。

5. **同步**：在多DMA通道应用中，可能需要使用`dma.active()`或中断来同步传输完成。

6. **数据一致性**：在DMA传输期间，确保CPU不会修改源数据或读取目标数据，以避免数据不一致。

7. **中断优先级**：DMA中断优先级较高，中断处理函数应尽可能简短，避免影响系统性能。

## 常见问题与解决方案

### 1. DMA传输不完整

**问题**：DMA传输提前结束或数据不完整。

**解决方案**：
- 检查`count`参数是否正确
- 确认`treq_sel`设置是否正确
- 验证源地址和目标地址是否有效

### 2. 中断处理函数未被调用

**问题**：设置了中断处理函数但未被调用。

**解决方案**：
- 确认DMA对象是否支持中断（使用`hasattr(dma, "irq")`检查）
- 检查中断处理函数签名是否正确
- 验证DMA传输是否真正完成

### 3. 数据丢失

**问题**：高速数据采集时出现数据丢失。

**解决方案**：
- 使用双缓冲或多缓冲技术
- 调整`treq_sel`以匹配外设数据速率
- 优化中断处理函数，减少处理时间

## 总结

RP2的DMA控制器是一个强大的工具，可以显著提高数据传输效率，特别是在高速数据采集场景中。正确配置DMA参数、合理设计中断处理流程以及注意资源管理是使用DMA的关键。通过本文档提供的示例和注意事项，您可以更好地利用RP2的DMA功能来实现高效的数据传输。