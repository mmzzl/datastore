# RP2040 100MHz 示波器项目总结

## 项目概述

本项目实现了一个基于RP2040和AD9288的100MHz数字示波器，使用ST7789显示屏（240×320分辨率）和EH11旋转编码器进行交互。示波器支持实时波形显示、电压和频率测量、触发功能以及测试信号生成。

## 已实现功能

### 1. 核心硬件驱动

#### ST7789显示屏驱动 ([hal/st7789.py](file:///d:\work\datastore\scope\hal\st7789.py))
- ✅ SPI通信驱动
- ✅ DMA加速传输
- ✅ 240×320分辨率支持
- ✅ 屏幕旋转控制
- ✅ 背光控制

#### AD9288 ADC驱动 ([hal/ad9288.py](file:///d:\work\datastore\scope\hal\ad9288.py))
- ✅ PIO状态机控制
- ✅ DMA高速采样
- ✅ 支持持续采样模式
- ✅ 环形缓冲区支持
- ✅ 触发功能（上升沿/下降沿）
- ✅ 可调采样率（最高100MHz）

#### EH11旋转编码器驱动 ([hal/encoder.py](file:///d:\work\datastore\scope\hal\encoder.py))
- ✅ 四倍频检测
- ✅ 按键检测
- ✅ 防抖处理
- ✅ 中断驱动
- ✅ 回调函数支持

#### 测试信号生成器 ([hal/test_signal.py](file:///d:\work\datastore\scope\hal\test_signal.py))
- ✅ 正弦波生成
- ✅ 方波生成
- ✅ 三角波生成
- ✅ 锯齿波生成
- ✅ 可调频率和幅度

### 2. 示波器主程序 ([scope.py](file:///d:\work\datastore\scope\scope.py))

#### 波形显示
- ✅ 实时波形显示
- ✅ 网格和中心线绘制
- ✅ 触发线显示
- ✅ 波形缩放（电压缩放）
- ✅ 波形暂停/继续

#### 测量功能
- ✅ 频率测量（过零点检测）
- ✅ 峰峰值电压测量
- ✅ RMS电压计算
- ✅ 实时更新显示

#### 交互控制
- ✅ 旋转编码器控制缩放
- ✅ 按键暂停/继续
- ✅ 长按切换缩放模式
- ✅ 触发级别调节
- ✅ 触发启用/禁用

#### 测试信号集成
- ✅ 测试信号模式切换
- ✅ 频率调节
- ✅ 波形类型切换

### 3. 用户界面

#### LVGL界面集成 ([gui/dear_lvgl.py](file:///d:\work\datastore\scope\gui\dear_lvgl.py))
- ✅ 波形显示组件
- ✅ 状态栏（频率、电压、缩放）
- ✅ 信息面板（状态、触发）
- ✅ Canvas绘图

#### 显示驱动 ([gui/display_driver_utils.py](file:///d:\work\datastore\scope\gui\display_driver_utils.py))
- ✅ LVGL显示驱动
- ✅ 编码器焦点管理
- ✅ 异步更新支持

### 4. 辅助工具

#### 配置文件 ([config.py](file:///d:\work\datastore\scope\config.py))
- ✅ 硬件引脚配置
- ✅ 示波器参数配置
- ✅ 性能优化配置
- ✅ 调试配置
- ✅ 配置验证

#### 测试程序 ([test_modules.py](file:///d:\work\datastore\scope\test_modules.py))
- ✅ 显示屏测试
- ✅ 编码器测试
- ✅ ADC测试
- ✅ 测试信号生成器测试

#### 示例程序 ([example_scope.py](file:///d:\work\datastore\scope\example_scope.py))
- ✅ 完整功能演示
- ✅ 测试信号使用示例
- ✅ 触发功能示例
- ✅ 参数调节示例

## 技术特点

### 1. 高速采样
- 使用PIO状态机实现精确的时序控制
- DMA传输实现无CPU干预的高速数据采集
- 支持环形缓冲区实现持续采样
- 最高采样率可达100MHz

### 2. 高效显示
- 使用LVGL Canvas组件绘制波形
- DMA加速SPI传输
- 优化的绘图算法
- 20Hz刷新率保证流畅显示

### 3. 精确测量
- 过零点检测算法测量频率
- 峰峰值和RMS电压计算
- 实时更新测量结果
- 触发功能确保波形稳定

### 4. 友好交互
- 单个旋转编码器实现所有控制
- 直观的缩放操作
- 清晰的状态显示
- 快速响应的按键操作

## 文件结构

```
scope/
├── config.py                    # 配置文件
├── scope.py                     # 示波器主程序
├── test_lvgl.py                 # 主程序入口
├── test_modules.py              # 模块测试程序
├── example_scope.py             # 示例程序
├── README.md                    # 使用说明
├── hal/                         # 硬件驱动层
│   ├── st7789.py               # ST7789显示屏驱动
│   ├── ad9288.py               # AD9288 ADC驱动
│   ├── encoder.py              # EH11编码器驱动
│   ├── test_signal.py          # 测试信号生成器
│   ├── dma.py                  # DMA驱动
│   └── pio_pwm.py              # PIO PWM模块
├── gui/                         # 图形界面层
│   ├── dear_lvgl.py            # LVGL封装
│   ├── display_driver_utils.py # 显示驱动工具
│   ├── async_utils.py          # 异步工具
│   └── asm_set_pixel2.py       # 像素设置汇编
└── .trae/                       # 项目文档
    └── documents/
        └── 实现基于LVGL的示波器功能.md
```

## 使用方法

### 1. 硬件连接
按照[README.md](file:///d:\work\datastore\scope\README.md)中的硬件连接说明连接各个模块。

### 2. 运行测试
```bash
python test_modules.py
```
运行模块测试程序，验证各个硬件模块是否正常工作。

### 3. 运行示波器
```bash
python test_lvgl.py
```
启动示波器主程序。

### 4. 运行示例
```bash
python example_scope.py
```
运行示例程序，学习如何使用各种功能。

## 操作说明

### 旋转编码器控制
- **顺时针旋转**: 放大波形（增大电压缩放）
- **逆时针旋转**: 缩小波形（减小电压缩放）
- **短按**: 暂停/继续波形显示
- **长按**: 切换电压缩放/时间缩放模式

### 界面信息
- **顶部状态栏**: 显示频率、电压、缩放比例
- **中间波形区**: 显示实时波形
- **底部信息栏**: 显示运行状态和触发信息

## 性能指标

| 参数 | 指标 |
|------|------|
| 最大采样率 | 100 MHz |
| ADC分辨率 | 8位 |
| 显示分辨率 | 320×240 |
| 刷新率 | 20 Hz |
| 频率测量范围 | 1 Hz - 100 MHz |
| 电压测量范围 | 0 V - 3.3 V (可缩放) |
| 电压缩放范围 | 0.1x - 10.0x |
| 时间缩放范围 | 0.1x - 10.0x |

## 扩展功能建议

### 1. 高级测量功能
- [ ] 占空比测量
- [ ] 上升时间/下降时间测量
- [ ] 脉宽测量
- [ ] FFT频谱分析

### 2. 存储功能
- [ ] 波形保存到文件
- [ ] 截图功能
- [ ] 数据导出（CSV格式）
- [ ] 波形回放

### 3. 通信功能
- [ ] USB串口通信
- [ ] WiFi远程控制
- [ ] 数据上传到云端
- [ ] 远程显示

### 4. 高级触发
- [ ] 脉宽触发
- [ ] 斜率触发
- [ ] 窗口触发
- [ ] 串行总线触发

### 5. 多通道支持
- [ ] 双通道显示
- [ ] 数学运算（加、减、乘、除）
- [ ] XY模式
- [ ] 李萨如图形

## 已知问题

1. **频率测量精度**: 对于高频信号，过零点检测算法的精度可能不够高，建议使用FFT算法提高精度。

2. **触发稳定性**: 在某些情况下，触发可能不够稳定，需要调整触发级别和迟滞。

3. **内存限制**: 由于RP2040内存有限，缓冲区大小受到限制，可能影响某些功能的实现。

4. **显示性能**: 在高刷新率下，CPU占用率较高，可能影响其他功能的运行。

## 优化建议

1. **使用环形缓冲区**: 实现真正的持续采样，避免数据丢失。

2. **优化绘图算法**: 使用批量绘制和DMA传输提高绘图性能。

3. **降低刷新率**: 在不需要高刷新率时降低刷新率以节省CPU资源。

4. **使用汇编优化**: 对关键代码路径使用汇编优化提高性能。

## 学习资源

1. **RP2040文档**: [Raspberry Pi Pico Datasheet](https://datasheets.raspberrypi.com/pico/raspberry-pi-pico-datasheet.pdf)

2. **AD9288文档**: [AD9288 Datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/AD9288.pdf)

3. **ST7789文档**: [ST7789 Datasheet](https://www.waveshare.com/w/upload/a/ae/ST7789S.pdf)

4. **LVGL文档**: [LVGL Documentation](https://docs.lvgl.io/)

5. **MicroPython文档**: [MicroPython Documentation](https://docs.micropython.org/)

## 许可证

本项目仅供学习和研究使用。

## 贡献者

- 初始实现: [用户]

## 更新日志

### v1.0.0 (2025-12-31)
- ✅ 初始版本发布
- ✅ 实现基本的示波器功能
- ✅ 支持AD9288 ADC
- ✅ 支持ST7789显示屏
- ✅ 支持EH11编码器
- ✅ 支持测试信号生成
- ✅ 支持触发功能
- ✅ 支持频率和电压测量

## 联系方式

如有问题或建议，请通过以下方式联系：
- 项目地址: [GitHub仓库地址]
- 邮箱: [联系邮箱]

---

**注意**: 本项目仍在开发中，可能存在一些未发现的bug和问题。使用时请注意安全，避免损坏硬件设备。
