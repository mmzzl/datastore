"""
简洁版EH11编码器集成示例
========================

这个版本保持原有的self.widgets结构，通过最小修改添加EH11编码器支持，
保持代码的简洁性。

使用方法：
1. 将以下代码添加到scope_example.py文件中
2. 在__init__方法中调用self.init_encoder()
3. 在主循环中调用self.process_encoder()

修改步骤：
1. 在文件开头添加导入
2. 在Scope类中添加编码器相关方法
3. 在__init__方法中初始化编码器
4. 在主循环中处理编码器事件
"""

# 1. 在文件开头添加导入
from hal.encoder import create_encoder_input_device, create_button_input_device
import asyncio

# 2. 在Scope类中添加以下方法
def init_encoder(self):
    """初始化EH11编码器和按键"""
    # 初始化EH11编码器
    self.encoder, self.encoder_indev = create_encoder_input_device(clk_pin=2, dt_pin=3, sw_pin=4)
    
    # 初始化功能按键
    button_pins = {
        'run': 5,      # 运行/停止
        'single': 6,   # 单次触发
        'save': 7,     # 保存
        'ok': 8        # 确认/重置
    }
    self.buttons, self.button_indev = create_button_input_device(button_pins)
    
    # 当前控制模式: "horizontal", "vertical", "trigger"
    self.control_mode = "horizontal"
    
    # 创建编码器任务
    self.encoder_task = asyncio.create_task(self.encoder_loop())

async def encoder_loop(self):
    """编码器处理循环"""
    last_encoder_dir = 0
    last_encoder_btn = False
    
    while True:
        # 更新编码器状态
        self.encoder.update()
        current_dir = self.encoder.get_direction()
        current_btn = self.encoder.is_switch_pressed()
        
        # 检测编码器旋转
        if current_dir != 0 and current_dir != last_encoder_dir:
            if self.control_mode == "horizontal":
                if current_dir > 0:
                    self.cb_horizontal_scale_inc(None)
                else:
                    self.cb_horizontal_scale_dec(None)
            elif self.control_mode == "vertical":
                if current_dir > 0:
                    self.cb_vertical_scale_inc(None)
                else:
                    self.cb_vertical_scale_dec(None)
            elif self.control_mode == "trigger":
                if current_dir > 0:
                    self.cb_trigger_position_inc(None)
                else:
                    self.cb_trigger_position_dec(None)
        
        # 检测编码器按钮 - 切换控制模式
        if current_btn and not last_encoder_btn:
            if self.control_mode == "horizontal":
                self.control_mode = "vertical"
                self.widgets["#Status"].set_text("Vertical")
            elif self.control_mode == "vertical":
                self.control_mode = "trigger"
                self.widgets["#Status"].set_text("Trigger")
            else:
                self.control_mode = "horizontal"
                self.widgets["#Status"].set_text("Horizontal")
        
        # 更新按键状态
        self.buttons.update()
        
        # 检查按键状态
        if self.buttons.is_pressed('run'):
            # 模拟点击Run按钮
            self.widgets["Run#M"].add_state(lv.STATE.CHECKED if not (self.widgets["Run#M"].get_state() & lv.STATE.CHECKED) else 0)
            self.cb_run(None)
        elif self.buttons.is_pressed('single'):
            self.cb_single(None)
        elif self.buttons.is_pressed('save'):
            self.cb_save(None)
        elif self.buttons.is_pressed('ok'):
            # 重置当前控制模式的参数
            if self.control_mode == "horizontal":
                self.cb_horizontal_position_set(None)
            elif self.control_mode == "vertical":
                self.cb_vertical_position_set(None)
            elif self.control_mode == "trigger":
                self.cb_trigger_position_set(None)
        
        last_encoder_dir = current_dir
        last_encoder_btn = current_btn
        
        await asyncio.sleep_ms(20)

# 3. 在Scope类的__init__方法末尾添加
# self.init_encoder()

# 4. 在主循环中添加事件循环
# 在文件末尾添加:
# asyncio.run()

# 或者，如果已有主循环，可以在循环中添加:
# await asyncio.sleep_ms(0)

"""
使用说明：
1. 编码器旋转：调整当前控制模式的参数值
2. 编码器按下：切换控制模式（水平/垂直/触发）
3. Run按键：切换运行/停止状态
4. Single按键：单次触发
5. Save按键：保存数据
6. OK按键：重置当前控制模式的参数

这种实现方式保持了原有的self.widgets结构，代码简洁，
同时添加了EH11编码器和按键支持。
"""