"""
如何将scope_example从触摸控制改为EH11编码器和按键控制
=====================================

1. 初始化EH11编码器和按键
------------------------

首先，导入encoder模块并初始化编码器和按键：

```python
from hal.encoder import create_encoder_input_device, create_button_input_device

# 初始化EH11编码器 (用于导航和选择)
encoder, encoder_indev = create_encoder_input_device(clk_pin=2, dt_pin=3, sw_pin=4)

# 初始化功能按键
button_pins = {
    'run': 5,      # 运行/停止
    'single': 6,   # 单次触发
    'save': 7,     # 保存
    'mode': 8,     # 模式切换
    'up': 9,       # 向上
    'down': 10,    # 向下
    'left': 11,    # 向左
    'right': 12,    # 向右
    'ok': 13       # 确认
}
buttons, button_indev = create_button_input_device(button_pins)
```

2. 修改Scope类
--------------

在Scope类中添加以下方法来处理编码器和按键输入：

```python
class Scope:
    def __init__(self):
        # ... 原有初始化代码 ...
        
        # 添加编码器和按键相关变量
        self.focused_group = None
        self.menu_items = [
            "Run/Stop",
            "Single", 
            "Save",
            "H-Scale",
            "H-Position",
            "V-Scale",
            "V-Position",
            "Trigger",
            "Channel"
        ]
        self.current_menu = 0
        
        # 创建对象组用于管理焦点
        self.focused_group = lv.group_create()
        lv.indev_set_group(encoder_indev, self.focused_group)
        
        # 启动UI更新任务
        self.start_ui_update_task()
    
    def cb_encoder_turn(self, direction):
        """编码器旋转回调"""
        if self.current_menu == 3:  # H-Scale
            if direction > 0:
                self.cb_horizontal_scale_inc(None)
            else:
                self.cb_horizontal_scale_dec(None)
        elif self.current_menu == 4:  # H-Position
            if direction > 0:
                self.cb_horizontal_position_inc(None)
            else:
                self.cb_horizontal_position_dec(None)
        # ... 其他菜单项的处理 ...
    
    def cb_encoder_press(self):
        """编码器按下回调"""
        if self.current_menu == 0:  # Run/Stop
            self.cb_run(None)
        elif self.current_menu == 1:  # Single
            self.cb_single(None)
        # ... 其他菜单项的处理 ...
    
    def cb_button_press(self, button_name):
        """按键按下回调"""
        if button_name == 'run':
            self.cb_run(None)
        elif button_name == 'single':
            self.cb_single(None)
        elif button_name == 'left':
            self.current_menu = (self.current_menu - 1) % len(self.menu_items)
        elif button_name == 'right':
            self.current_menu = (self.current_menu + 1) % len(self.menu_items)
        # ... 其他按键的处理 ...
    
    async def ui_update_task(self):
        """UI更新任务"""
        last_encoder_dir = 0
        last_encoder_btn = False
        
        while True:
            # 更新编码器状态
            encoder.update()
            current_dir = encoder.get_direction()
            current_btn = encoder.is_switch_pressed()
            
            # 检测编码器旋转
            if current_dir != 0 and current_dir != last_encoder_dir:
                self.cb_encoder_turn(current_dir)
            
            # 检测编码器按钮
            if current_btn and not last_encoder_btn:
                self.cb_encoder_press()
            
            # 更新按键状态
            buttons.update()
            
            # 检查按键状态
            for button_name in button_pins.keys():
                if buttons.is_pressed(button_name):
                    self.cb_button_press(button_name)
            
            last_encoder_dir = current_dir
            last_encoder_btn = current_btn
            
            await asyncio.sleep_ms(20)
    
    def start_ui_update_task(self):
        """启动UI更新任务"""
        asyncio.create_task(self.ui_update_task())
```

3. 修改build_ui方法
------------------

可以简化UI，减少按钮数量，因为大部分操作将通过编码器和按键完成：

```python
def build_ui(self, parent=None):
    """构建简化的UI界面"""
    # ... 基本UI布局代码 ...
    
    # 添加状态显示，显示当前选中的菜单项
    self.widgets["#Status"] = lv.label(...)
    self.widgets["#Status"].set_text(self.menu_items[self.current_menu])
    
    # 保留图表和必要的显示元素
    self.chart = lv.chart(...)
    
    # 可以移除大部分按钮，因为功能通过编码器和按键实现
```

4. 主要交互方式
--------------

使用EH11编码器和按键的主要交互方式：

1. 左右按键：切换菜单项
2. 编码器旋转：调整当前菜单项的值
3. 编码器按下：执行当前菜单项的功能
4. 专用按键：直接执行特定功能（如运行/停止、单次触发等）

5. 硬件连接
----------

EH11编码器和按键的硬件连接：

```
EH11编码器:
- A相 -> GPIO2
- B相 -> GPIO3  
- 开关 -> GPIO4

功能按键:
- 运行/停止 -> GPIO5
- 单次触发 -> GPIO6
- 保存 -> GPIO7
- 模式切换 -> GPIO8
- 向上 -> GPIO9
- 向下 -> GPIO10
- 向左 -> GPIO11
- 向右 -> GPIO12
- 确认 -> GPIO13
```

6. 注意事项
----------

1. 编码器和按键需要上拉电阻，或使用内部上拉
2. 编码器旋转可能会产生抖动，可以在软件中添加去抖动逻辑
3. 按键检测需要适当的防抖处理
4. 菜单导航逻辑应该直观易用
5. 状态显示应该清晰，用户知道当前操作的是哪个参数

这种实现方式将原本需要触摸操作的功能转换为通过编码器和按键操作，更适合没有触摸屏或者需要精确控制的应用场景。
"""