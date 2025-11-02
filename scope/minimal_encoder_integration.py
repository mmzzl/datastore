"""
最小修改示例：在scope_example中添加EH11编码器支持
===============================================

这个示例展示如何在现有的scope_example基础上进行最小修改，
添加EH11编码器和按键支持，而不需要完全重写UI。

1. 在scope_example文件开头添加以下导入：
```python
from hal.encoder import create_encoder_input_device, create_button_input_device
import asyncio
```

2. 在初始化LVGL和显示驱动后，添加编码器和按键初始化：
```python
# 初始化EH11编码器
encoder, encoder_indev = create_encoder_input_device(clk_pin=2, dt_pin=3, sw_pin=4)

# 初始化功能按键
button_pins = {
    'run': 5,      # 运行/停止
    'single': 6,   # 单次触发
    'save': 7,     # 保存
    'up': 9,       # 向上
    'down': 10,    # 向下
    'left': 11,    # 向左
    'right': 12,    # 向右
    'ok': 13       # 确认
}
buttons, button_indev = create_button_input_device(button_pins)
```

3. 在Scope类的__init__方法中添加以下代码：
```python
# 在__init__方法末尾添加
self.current_control = "horizontal"  # 当前控制的参数: horizontal, vertical, trigger
self.start_encoder_task()
```

4. 在Scope类中添加以下方法：
```python
def start_encoder_task(self):
    """启动编码器任务"""
    asyncio.create_task(self.encoder_task())

async def encoder_task(self):
    """编码器处理任务"""
    last_encoder_dir = 0
    last_encoder_btn = False
    
    while True:
        # 更新编码器状态
        encoder.update()
        current_dir = encoder.get_direction()
        current_btn = encoder.is_switch_pressed()
        
        # 检测编码器旋转
        if current_dir != 0 and current_dir != last_encoder_dir:
            if self.current_control == "horizontal":
                if current_dir > 0:
                    self.cb_horizontal_scale_inc(None)
                else:
                    self.cb_horizontal_scale_dec(None)
            elif self.current_control == "vertical":
                if current_dir > 0:
                    self.cb_vertical_scale_inc(None)
                else:
                    self.cb_vertical_scale_dec(None)
            elif self.current_control == "trigger":
                if current_dir > 0:
                    self.cb_trigger_position_inc(None)
                else:
                    self.cb_trigger_position_dec(None)
        
        # 检测编码器按钮
        if current_btn and not last_encoder_btn:
            # 切换控制参数
            if self.current_control == "horizontal":
                self.current_control = "vertical"
                print("Switched to vertical control")
            elif self.current_control == "vertical":
                self.current_control = "trigger"
                print("Switched to trigger control")
            else:
                self.current_control = "horizontal"
                print("Switched to horizontal control")
        
        # 更新按键状态
        buttons.update()
        
        # 检查按键状态
        if buttons.is_pressed('run'):
            self.cb_run(None)
        elif buttons.is_pressed('single'):
            self.cb_single(None)
        elif buttons.is_pressed('save'):
            self.cb_save(None)
        elif buttons.is_pressed('left'):
            if self.current_control == "horizontal":
                self.cb_horizontal_position_dec(None)
            elif self.current_control == "vertical":
                self.cb_vertical_position_dec(None)
        elif buttons.is_pressed('right'):
            if self.current_control == "horizontal":
                self.cb_horizontal_position_inc(None)
            elif self.current_control == "vertical":
                self.cb_vertical_position_inc(None)
        elif buttons.is_pressed('up'):
            # 切换到上一个控制参数
            if self.current_control == "vertical":
                self.current_control = "horizontal"
            elif self.current_control == "trigger":
                self.current_control = "vertical"
            print(f"Current control: {self.current_control}")
        elif buttons.is_pressed('down'):
            # 切换到下一个控制参数
            if self.current_control == "horizontal":
                self.current_control = "vertical"
            elif self.current_control == "vertical":
                self.current_control = "trigger"
            print(f"Current control: {self.current_control}")
        elif buttons.is_pressed('ok'):
            # 重置当前参数
            if self.current_control == "horizontal":
                self.cb_horizontal_position_set(None)
            elif self.current_control == "vertical":
                self.cb_vertical_position_set(None)
            elif self.current_control == "trigger":
                self.cb_trigger_position_set(None)
        
        last_encoder_dir = current_dir
        last_encoder_btn = current_btn
        
        await asyncio.sleep_ms(20)
```

5. 在文件末尾添加事件循环：
```python
# 启动事件循环
asyncio.run()
```

使用说明：
1. 编码器旋转：调整当前选中的参数值
2. 编码器按下：切换控制参数（水平/垂直/触发）
3. 上/下按键：切换控制参数
4. 左/右按键：调整水平或垂直位置
5. OK按键：重置当前参数
6. 专用按键：运行/停止、单次触发、保存

这种最小修改方式保留了原有的UI，同时添加了编码器和按键支持，
用户可以通过编码器和按键来控制示波器，而不需要触摸屏。
"""