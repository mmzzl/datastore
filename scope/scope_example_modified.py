"""
修改后的scope_example.py，添加EH11编码器支持，保持原有的self.widgets结构
"""

import lvgl
import utime
import uasyncio as asyncio
import machine
from hal.st7789 import ST7789
from hal.ad9288 import AD9288
from hal.encoder import create_encoder_input_device, create_button_input_device
import micropython

class Scope:
    def __init__(self):
        # 初始化硬件
        self.init_hardware()
        
        # 初始化UI
        self.init_ui()
        
        # 初始化编码器
        self.init_encoder()
        
        # 初始化数据
        self.init_data()
        
        # 启动数据采集任务
        self.data_task = asyncio.create_task(self.data_loop())
    
    def init_hardware(self):
        """初始化硬件"""
        # 初始化显示屏
        self.disp = ST7789()
        
        # 初始化ADC
        self.adc = AD9288()
        
        # 设置采样率
        machine.freq(240_000_000)  # 240MHz
        
        # 配置GPIO引脚
        self.db = machine.Pin(0, machine.Pin.OUT)
        self.sck = machine.Pin(1, machine.Pin.OUT)
        self.mux = machine.Pin(2, machine.Pin.OUT)
        self.trig = machine.Pin(3, machine.Pin.OUT)
        
        # 初始状态
        self.db.value(0)
        self.sck.value(0)
        self.mux.value(0)
        self.trig.value(0)
    
    def init_ui(self):
        """初始化UI"""
        # 创建UI组件
        self.widgets = {}
        
        # 创建屏幕
        self.scr = lv.obj()
        lv.scr_load(self.scr)
        
        # 创建图表
        self.chart = lv.chart(self.scr)
        self.chart.set_size(240, 120)
        self.chart.align(lv.ALIGN.TOP_MID, 0, 10)
        self.chart.set_type(lv.chart.TYPE.LINE)
        self.chart.set_div_line_count(6, 10)
        self.chart.set_range(lv.chart.AXIS.PRIMARY_Y, 0, 255)
        
        # 添加数据系列
        self.ch1_series = self.chart.add_series(lv.color_hex(0x00FF00), lv.chart.AXIS.PRIMARY_Y)
        self.ch2_series = self.chart.add_series(lv.color_hex(0xFF0000), lv.chart.AXIS.PRIMARY_Y)
        
        # 创建按钮
        self.create_buttons()
        
        # 创建标签
        self.create_labels()
    
    def create_buttons(self):
        """创建按钮"""
        # Run按钮
        btn_run = lv.btn(self.scr)
        btn_run.align(lv.ALIGN.BOTTOM_LEFT, 10, -10)
        btn_run.set_size(50, 30)
        btn_run.add_event_cb(self.cb_run, lv.EVENT.CLICKED, None)
        label_run = lv.label(btn_run)
        label_run.set_text("Run")
        label_run.center()
        self.widgets["Run#M"] = btn_run
        
        # Single按钮
        btn_single = lv.btn(self.scr)
        btn_single.align(lv.ALIGN.BOTTOM_LEFT, 70, -10)
        btn_single.set_size(50, 30)
        btn_single.add_event_cb(self.cb_single, lv.EVENT.CLICKED, None)
        label_single = lv.label(btn_single)
        label_single.set_text("Single")
        label_single.center()
        self.widgets["Single#M"] = btn_single
        
        # Save按钮
        btn_save = lv.btn(self.scr)
        btn_save.align(lv.ALIGN.BOTTOM_LEFT, 130, -10)
        btn_save.set_size(50, 30)
        btn_save.add_event_cb(self.cb_save, lv.EVENT.CLICKED, None)
        label_save = lv.label(btn_save)
        label_save.set_text("Save")
        label_save.center()
        self.widgets["Save#M"] = btn_save
        
        # 水平缩放按钮
        btn_h_inc = lv.btn(self.scr)
        btn_h_inc.align(lv.ALIGN.BOTTOM_RIGHT, -60, -10)
        btn_h_inc.set_size(30, 30)
        btn_h_inc.add_event_cb(self.cb_horizontal_scale_inc, lv.EVENT.CLICKED, None)
        label_h_inc = lv.label(btn_h_inc)
        label_h_inc.set_text("H+")
        label_h_inc.center()
        self.widgets["HInc#M"] = btn_h_inc
        
        btn_h_dec = lv.btn(self.scr)
        btn_h_dec.align(lv.ALIGN.BOTTOM_RIGHT, -25, -10)
        btn_h_dec.set_size(30, 30)
        btn_h_dec.add_event_cb(self.cb_horizontal_scale_dec, lv.EVENT.CLICKED, None)
        label_h_dec = lv.label(btn_h_dec)
        label_h_dec.set_text("H-")
        label_h_dec.center()
        self.widgets["HDec#M"] = btn_h_dec
    
    def create_labels(self):
        """创建标签"""
        # 状态标签
        label_status = lv.label(self.scr)
        label_status.align(lv.ALIGN.TOP_MID, 0, 140)
        label_status.set_text("Ready")
        self.widgets["#Status"] = label_status
        
        # 水平缩放标签
        label_h_scale = lv.label(self.scr)
        label_h_scale.align(lv.ALIGN.TOP_LEFT, 10, 140)
        label_h_scale.set_text("H: 1ms")
        self.widgets["#lHS"] = label_h_scale
        
        # 垂直缩放标签
        label_v_scale = lv.label(self.scr)
        label_v_scale.align(lv.ALIGN.TOP_RIGHT, -10, 140)
        label_v_scale.set_text("V: 1V")
        self.widgets["#lVS"] = label_v_scale
    
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
    
    def init_data(self):
        """初始化数据"""
        # 数据缓冲区
        self.data_buffer = [0] * 240
        self.trigger_index = 0
        
        # 示波器参数
        self.horizontal_scale = 1.0  # ms/div
        self.vertical_scale = 1.0     # V/div
        self.trigger_level = 128      # 触发电平
        self.trigger_mode = "auto"    # 触发模式: auto, normal, single
        
        # 运行状态
        self.running = False
        self.single_trigger = False
    
    async def data_loop(self):
        """数据采集循环"""
        while True:
            if self.running or self.single_trigger:
                # 采集数据
                self.adc.read_data(self.data_buffer)
                
                # 触发处理
                if self.find_trigger():
                    # 更新图表
                    self.update_chart()
                    
                    # 重置单次触发标志
                    if self.single_trigger:
                        self.single_trigger = False
                        self.widgets["#Status"].set_text("Single Done")
            
            await asyncio.sleep_ms(50)
    
    def find_trigger(self):
        """查找触发点"""
        # 简单的上升沿触发
        for i in range(1, len(self.data_buffer)):
            if self.data_buffer[i-1] < self.trigger_level and self.data_buffer[i] >= self.trigger_level:
                self.trigger_index = i
                return True
        return False
    
    def update_chart(self):
        """更新图表"""
        # 清除旧数据
        self.chart.clear_series(self.ch1_series)
        self.chart.clear_series(self.ch2_series)
        
        # 添加新数据
        for i, value in enumerate(self.data_buffer):
            self.chart.set_next_value(self.ch1_series, value)
            self.chart.set_next_value(self.ch2_series, value // 2)  # 模拟第二通道
    
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
    
    # 按钮回调函数
    def cb_run(self, event):
        """运行/停止回调"""
        self.running = not self.running
        if self.running:
            self.widgets["#Status"].set_text("Running")
            self.widgets["Run#M"].add_state(lv.STATE.CHECKED)
        else:
            self.widgets["#Status"].set_text("Stopped")
            self.widgets["Run#M"].clear_state(lv.STATE.CHECKED)
    
    def cb_single(self, event):
        """单次触发回调"""
        self.single_trigger = True
        self.widgets["#Status"].set_text("Single")
    
    def cb_save(self, event):
        """保存回调"""
        # 保存数据到文件
        with open("scope_data.txt", "w") as f:
            for value in self.data_buffer:
                f.write(f"{value}\n")
        self.widgets["#Status"].set_text("Saved")
    
    def cb_horizontal_scale_inc(self, event):
        """水平缩放增加"""
        self.horizontal_scale *= 2
        self.widgets["#lHS"].set_text(f"H: {self.horizontal_scale}ms")
    
    def cb_horizontal_scale_dec(self, event):
        """水平缩放减少"""
        self.horizontal_scale /= 2
        self.widgets["#lHS"].set_text(f"H: {self.horizontal_scale}ms")
    
    def cb_vertical_scale_inc(self, event):
        """垂直缩放增加"""
        self.vertical_scale *= 2
        self.widgets["#lVS"].set_text(f"V: {self.vertical_scale}V")
    
    def cb_vertical_scale_dec(self, event):
        """垂直缩放减少"""
        self.vertical_scale /= 2
        self.widgets["#lVS"].set_text(f"V: {self.vertical_scale}V")
    
    def cb_trigger_position_inc(self, event):
        """触发电平增加"""
        self.trigger_level += 10
        if self.trigger_level > 255:
            self.trigger_level = 255
    
    def cb_trigger_position_dec(self, event):
        """触发电平减少"""
        self.trigger_level -= 10
        if self.trigger_level < 0:
            self.trigger_level = 0
    
    def cb_horizontal_position_set(self, event):
        """水平位置重置"""
        self.horizontal_scale = 1.0
        self.widgets["#lHS"].set_text(f"H: {self.horizontal_scale}ms")
    
    def cb_vertical_position_set(self, event):
        """垂直位置重置"""
        self.vertical_scale = 1.0
        self.widgets["#lVS"].set_text(f"V: {self.vertical_scale}V")
    
    def cb_trigger_position_set(self, event):
        """触发电平重置"""
        self.trigger_level = 128

def foo2():
    """主函数"""
    # 创建Scope实例
    scope = Scope()
    
    # 启动事件循环
    asyncio.run()

if __name__ == "__main__":
    foo2()