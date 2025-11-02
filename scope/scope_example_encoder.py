import lvgl as lv
import time
import math
import array
import micropython
import gc
import sys
import machine
import asyncio

from hal import st7789, dma, ad9288, pio_pwm
from hal.encoder import create_encoder_input_device, create_button_input_device
from gui.dear_lvgl import set_context, set_widgets, get_widgets
from gui import asm_set_pixel2
from gui import display_driver_utils

# 初始化LVGL
lv.init()

# 初始化显示驱动
disp = st7789.ST7789(
    width=480,
    height=320,
    spihost=1,
    mosi=35,
    clk=36,
    cs=34,
    dc=33,
    rst=32,
    backlight=38,
    rotation=0,
    power=-1,
    debug=False
)

# 注册显示驱动
disp_drv = lv.disp_create(480, 320)
display_driver_utils.register_flush_cb(disp_drv, disp)
display_driver_utils.register_flush_wait_cb(disp_drv)

# 初始化EH11编码器和按键
# 编码器用于导航和选择
encoder, encoder_indev = create_encoder_input_device(clk_pin=2, dt_pin=3, sw_pin=4)

# 功能按键
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

# 全局变量
scr = None
scope = None

# 初始化硬件
def foo2():
    global db, sck, mux, trig, pio, sm, dma, dma_ch, adc, trig_pwm
    
    # 初始化引脚
    db = machine.Pin(21, machine.Pin.OUT)
    sck = machine.Pin(20, machine.Pin.OUT)
    mux = machine.Pin(19, machine.Pin.OUT)
    trig = machine.Pin(18, machine.Pin.OUT)
    
    # 初始化PIO PWM
    pio = pio_pwm.PIO_PWM(0, 17, 125_000_000)
    sm = pio.add_sm(16, 125_000_000)
    
    # 初始化DMA
    dma = dma.DMA()
    dma_ch = dma.add_channel()
    
    # 初始化ADC
    adc = ad9288.AD9288(sck, db, mux)
    
    # 初始化触发PWM
    trig_pwm = machine.PWM(machine.Pin(18))
    trig_pwm.freq(1_000_000)
    trig_pwm.duty_u16(int(0xFFFF*1.024/3.3))

class Scope:
    """示波器类，使用EH11编码器和按键控制"""
    
    def __init__(self):
        self.context = []
        self.widgets = {}
        self.chart = None
        
        # 示波器参数
        self.running = False
        self.single = False
        self.channel1_selected = True
        self.horizontal_scale = 3  # 0:1M, 1:2M, 2:5M, 3:10M, 4:20M, 5:50M, 6:100M
        self.horizontal_position = 0
        self.channel1_scale = 1
        self.channel2_scale = 1
        self.channel1_position = 0
        self.channel2_position = 0
        self.trigger_position = 0
        
        # UI焦点管理
        self.focused_group = None
        self.focused_item = 0
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
        
        # 初始化硬件
        foo2()
        
        # 构建UI
        self.build_ui()
        
        # 设置按键回调
        buttons.set_callbacks(
            cb_run=self.cb_run,
            cb_single=self.cb_single,
            cb_save=self.cb_save,
            cb_mode=self.cb_mode_change
        )
        
        # 创建对象组用于管理焦点
        self.focused_group = lv.group_create()
        lv.indev_set_group(encoder_indev, self.focused_group)
        
        # 添加UI元素到焦点组
        self._setup_focus_navigation()
        
        # 启动任务
        self.start_tasks()
    
    def _setup_focus_navigation(self):
        """设置焦点导航"""
        # 将主要UI元素添加到焦点组
        if self.chart:
            lv.group_add_obj(self.focused_group, self.chart)
        
        # 添加按钮到焦点组
        for name, widget in self.widgets.items():
            if isinstance(widget, lv.obj) and "Button" in str(type(widget)):
                lv.group_add_obj(self.focused_group, widget)
    
    def cb_mode_change(self, evt):
        """模式切换回调"""
        self.current_menu = (self.current_menu + 1) % len(self.menu_items)
        self.update_status_display()
    
    def update_status_display(self):
        """更新状态显示"""
        if "#Status" in self.widgets:
            self.widgets["#Status"].set_text(self.menu_items[self.current_menu])
    
    def cb_run(self, evt):
        """运行/停止回调"""
        self.running = not self.running
        if self.running:
            self.widgets["Run#M"].get_child(0).set_text(lv.SYMBOL.PAUSE)
            self.widgets["#Status"].set_text("Running")
        else:
            self.widgets["Run#M"].get_child(0).set_text(lv.SYMBOL.PLAY)
            self.widgets["#Status"].set_text("Stopped")
    
    def cb_single(self, evt):
        """单次触发回调"""
        self.single = True
        self.widgets["#Status"].set_text("Single")
    
    def cb_save(self, evt):
        """保存回调"""
        self.widgets["#Status"].set_text("Saved")
        # 这里可以添加保存数据的代码
    
    def cb_encoder_turn(self, direction):
        """编码器旋转回调"""
        if self.current_menu == 0:  # Run/Stop
            # 不使用编码器控制
            pass
        elif self.current_menu == 1:  # Single
            # 不使用编码器控制
            pass
        elif self.current_menu == 2:  # Save
            # 不使用编码器控制
            pass
        elif self.current_menu == 3:  # H-Scale
            if direction > 0:
                self.cb_horizontal_scale_inc(None)
            else:
                self.cb_horizontal_scale_dec(None)
        elif self.current_menu == 4:  # H-Position
            if direction > 0:
                self.cb_horizontal_position_inc(None)
            else:
                self.cb_horizontal_position_dec(None)
        elif self.current_menu == 5:  # V-Scale
            if direction > 0:
                self.cb_vertical_scale_inc(None)
            else:
                self.cb_vertical_scale_dec(None)
        elif self.current_menu == 6:  # V-Position
            if direction > 0:
                self.cb_vertical_position_inc(None)
            else:
                self.cb_vertical_position_dec(None)
        elif self.current_menu == 7:  # Trigger
            if direction > 0:
                self.cb_trigger_position_inc(None)
            else:
                self.cb_trigger_position_dec(None)
        elif self.current_menu == 8:  # Channel
            # 不使用编码器控制
            pass
    
    def cb_encoder_press(self):
        """编码器按下回调"""
        if self.current_menu == 0:  # Run/Stop
            self.cb_run(None)
        elif self.current_menu == 1:  # Single
            self.cb_single(None)
        elif self.current_menu == 2:  # Save
            self.cb_save(None)
        elif self.current_menu == 3:  # H-Scale
            self.cb_horizontal_scale_set(None)
        elif self.current_menu == 4:  # H-Position
            self.cb_horizontal_position_set(None)
        elif self.current_menu == 5:  # V-Scale
            self.cb_vertical_scale_set(None)
        elif self.current_menu == 6:  # V-Position
            self.cb_vertical_position_set(None)
        elif self.current_menu == 7:  # Trigger
            self.cb_trigger_position_set(None)
        elif self.current_menu == 8:  # Channel
            self.cb_channel_select(None)
    
    def cb_button_press(self, button_name):
        """按键按下回调"""
        if button_name == 'up':
            if self.current_menu in [3, 4, 5, 6, 7]:  # 有增减功能的菜单
                if self.current_menu == 3:
                    self.cb_horizontal_scale_inc(None)
                elif self.current_menu == 4:
                    self.cb_horizontal_position_inc(None)
                elif self.current_menu == 5:
                    self.cb_vertical_scale_inc(None)
                elif self.current_menu == 6:
                    self.cb_vertical_position_inc(None)
                elif self.current_menu == 7:
                    self.cb_trigger_position_inc(None)
        elif button_name == 'down':
            if self.current_menu in [3, 4, 5, 6, 7]:  # 有增减功能的菜单
                if self.current_menu == 3:
                    self.cb_horizontal_scale_dec(None)
                elif self.current_menu == 4:
                    self.cb_horizontal_position_dec(None)
                elif self.current_menu == 5:
                    self.cb_vertical_scale_dec(None)
                elif self.current_menu == 6:
                    self.cb_vertical_position_dec(None)
                elif self.current_menu == 7:
                    self.cb_trigger_position_dec(None)
        elif button_name == 'left':
            self.current_menu = (self.current_menu - 1) % len(self.menu_items)
            self.update_status_display()
        elif button_name == 'right':
            self.current_menu = (self.current_menu + 1) % len(self.menu_items)
            self.update_status_display()
        elif button_name == 'ok':
            self.cb_encoder_press()
    
    def cb_horizontal_scale_inc(self, evt):
        if self.horizontal_scale < 6:
            self.horizontal_scale += 1
        sps = ["1 M", "2 M", "5 M", "10 M", "20 M", "50 M", "100 M"][self.horizontal_scale]
        self.widgets["#lHS"].set_text("HS {} Sps".format(sps))

    def cb_horizontal_scale_dec(self, evt):
        if self.horizontal_scale > 0:
            self.horizontal_scale -= 1
        sps = ["1 M", "2 M", "5 M", "10 M", "20 M", "50 M", "100 M"][self.horizontal_scale]
        self.widgets["#lHS"].set_text("HS {} Sps".format(sps))

    def cb_horizontal_position_inc(self, evt):
        if self.horizontal_position < 1024:
            self.horizontal_position += 1
        self.widgets["#lHP"].set_text("HP {} S".format(self.horizontal_position))

    def cb_horizontal_position_set(self, evt):
        self.horizontal_position = 0
        self.widgets["#lHP"].set_text("HP {} S".format(self.horizontal_position))

    def cb_horizontal_position_dec(self, evt):
        if self.horizontal_position > -127:
            self.horizontal_position -= 1
        self.widgets["#lHP"].set_text("HP {} S".format(self.horizontal_position))

    def cb_channel_select(self, evt):
        self.channel1_selected = not self.channel1_selected
        self.widgets["CHS#VS"].get_child(0).set_text("CH1" if self.channel1_selected else "CH2")
        print("channel1_selected", self.channel1_selected)

    def cb_vertical_scale_inc(self, evt):
        if self.channel1_selected:
            self.channel1_scale += 1
            self.widgets["#lVS1"].set_text("VS1 {} V/D".format(self.channel1_scale))
        else:
            self.channel2_scale += 1
            self.widgets["#lVS2"].set_text("VS2 {} V/D".format(self.channel2_scale))
        
    def cb_vertical_scale_set(self, evt):
        if self.channel1_selected:
            self.channel1_scale = 1
            self.widgets["#lVS1"].set_text("VS1 {} V/D".format(self.channel1_scale))
        else:
            self.channel2_scale = 1
            self.widgets["#lVS2"].set_text("VS2 {} V/D".format(self.channel2_scale))

    def cb_vertical_scale_dec(self, evt):
        if self.channel1_selected:
            self.channel1_scale -= 1
            self.widgets["#lVS1"].set_text("VS1 {} V/D".format(self.channel1_scale))
        else:
            self.channel2_scale -= 1
            self.widgets["#lVS2"].set_text("VS2 {} V/D".format(self.channel2_scale))

    def cb_vertical_position_inc(self, evt):
        if self.channel1_selected:
            self.channel1_position += 1
            self.widgets["#lVP1"].set_text("VP1 {} V".format(self.channel1_position))
        else:
            self.channel2_position += 1
            self.widgets["#lVP2"].set_text("VP2 {} V".format(self.channel2_position))

    def cb_vertical_position_set(self, evt):
        if self.channel1_selected:
            self.channel1_position = 1
            self.widgets["#lVP1"].set_text("VP1 {} V".format(self.channel1_position))
        else:
            self.channel2_position = 1
            self.widgets["#lVP2"].set_text("VP2 {} V".format(self.channel2_position))

    def cb_vertical_position_dec(self, evt):
        if self.channel1_selected:
            self.channel1_position -= 1
            self.widgets["#lVP1"].set_text("VP1 {} V".format(self.channel1_position))
        else:
            self.channel2_position -= 1
            self.widgets["#lVP2"].set_text("VP2 {} V".format(self.channel2_position))

    def cb_trigger_position_inc(self, evt):
        self.trigger_position += 1
        self.widgets["#lTP"].set_text("TP {} V".format(self.trigger_position))
        trig_pwm.duty_u16(int(0xFFFF*1.024/3.3) + self.trigger_position*256)

    def cb_trigger_position_set(self, evt):
        self.trigger_position = 0
        self.widgets["#lTP"].set_text("TP {} V".format(self.trigger_position))
        trig_pwm.duty_u16(int(0xFFFF*1.024/3.3) + self.trigger_position*256)

    def cb_trigger_position_dec(self, evt):
        self.trigger_position -= 1
        self.widgets["#lTP"].set_text("TP {} V".format(self.trigger_position))
        trig_pwm.duty_u16(int(0xFFFF*1.024/3.3) + self.trigger_position*256)

    def build_ui(self, parent=None):
        """构建UI界面"""
        width = 160
        point_count = 480 - width
        
        if parent is None:
            parent = lv.scr_act()
        
        self.context.append(parent)
        set_context(self.context)
        set_widgets(self.widgets)
        
        with lv.obj(parent) as cont:
            cont.set_size(480, 320)
            cont.set_pos(0, 0)
            
            # 左侧区域 - 显示区域
            with lv.obj(cont) as left_panel:
                left_panel.set_size(480-width, 320-15)
                left_panel.set_pos(0, 0)
                
                with lv.obj(left_panel) as status_row:
                    status_row.set_size(480-width, 30)
                    status_row.set_pos(0, 0)
                    status_row.set_flex_flow(lv.FLEX_FLOW.ROW)
                    
                    # 状态标签
                    lblw = 74
                    self.widgets["#Status"] = lv.label(status_row)
                    self.widgets["#Status"].set_text(self.menu_items[self.current_menu])
                    self.widgets["#Status"].set_width(lblw)
                    
                    self.widgets["#lHS"] = lv.label(status_row)
                    self.widgets["#lHS"].set_text("1 S/D")
                    self.widgets["#lHS"].set_width(lblw)
                    
                    self.widgets["#lHP"] = lv.label(status_row)
                    self.widgets["#lHP"].set_text("0 S")
                    self.widgets["#lHP"].set_width(lblw)
                    
                    self.widgets["#lTP"] = lv.label(status_row)
                    self.widgets["#lTP"].set_text("0 V")
                    self.widgets["#lTP"].set_width(lblw)
                
                # 图表区域
                self.chart = lv.chart(left_panel)
                self.chart.set_size(480-160-12, 300-5-50-10)
                self.chart.set_pos(0, 35)
                self.chart.set_div_line_count(8, 10)
                
                # 通道状态行
                with lv.obj(left_panel) as channel_row:
                    channel_row.set_size(480-width, 30)
                    channel_row.set_pos(0, 270)
                    channel_row.set_flex_flow(lv.FLEX_FLOW.ROW)
                    
                    self.widgets["#lVS1"] = lv.label(channel_row)
                    self.widgets["#lVS1"].set_text("1 V/D")
                    self.widgets["#lVS1"].set_width(lblw)
                    
                    self.widgets["#lVP1"] = lv.label(channel_row)
                    self.widgets["#lVP1"].set_text("0 V")
                    self.widgets["#lVP1"].set_width(lblw)
                    
                    self.widgets["#lVS2"] = lv.label(channel_row)
                    self.widgets["#lVS2"].set_text("1 V/D")
                    self.widgets["#lVS2"].set_width(lblw)
                    
                    self.widgets["#lVP2"] = lv.label(channel_row)
                    self.widgets["#lVP2"].set_text("0 V")
                    self.widgets["#lVP2"].set_width(lblw)
            
            # 右侧区域 - 控制区域
            with lv.obj(cont) as right_panel:
                right_panel.set_size(width-15, 320-15)
                right_panel.set_pos(480-width, 0)
                
                # 控制按钮区域
                with lv.obj(right_panel) as control_row:
                    control_row.set_size(width-15, 40)
                    control_row.set_pos(0, 0)
                    control_row.set_flex_flow(lv.FLEX_FLOW.ROW)
                    
                    self.widgets["Run#M"] = lv.btn(control_row)
                    self.widgets["Run#M"].set_size(40, 35)
                    label = lv.label(self.widgets["Run#M"])
                    label.set_text(lv.SYMBOL.PLAY)
                    label.center()
                    
                    self.widgets["Sing#M"] = lv.btn(control_row)
                    self.widgets["Sing#M"].set_size(40, 35)
                    label = lv.label(self.widgets["Sing#M"])
                    label.set_text(lv.SYMBOL.NEXT)
                    label.center()
                    
                    self.widgets["#Save"] = lv.btn(control_row)
                    self.widgets["#Save"].set_size(40, 35)
                    label = lv.label(self.widgets["#Save"])
                    label.set_text(lv.SYMBOL.SAVE)
                    label.center()
                
                # 分隔线
                line = lv.line(right_panel)
                line.set_pos(0, 45)
                line_points = [0, 0, 120+2*4, 0]
                line.set_points(line_points, 2)
                
                # 水平控制区域
                with lv.obj(right_panel) as h_control:
                    h_control.set_size(width-15, 80)
                    h_control.set_pos(0, 50)
                    
                    h_label = lv.label(h_control)
                    h_label.set_text("Horizontal")
                    h_label.set_pos(0, 0)
                    
                    with lv.obj(h_control) as h_buttons:
                        h_buttons.set_size(width-15, 25)
                        h_buttons.set_pos(0, 20)
                        h_buttons.set_flex_flow(lv.FLEX_FLOW.ROW)
                        
                        self.widgets["+#HT"] = lv.btn(h_buttons)
                        self.widgets["+#HT"].set_size(35, 25)
                        label = lv.label(self.widgets["+#HT"])
                        label.set_text(lv.SYMBOL.PLUS)
                        label.center()
                        
                        h_time_btn = lv.btn(h_buttons)
                        h_time_btn.set_size(50, 25)
                        label = lv.label(h_time_btn)
                        label.set_text("Time")
                        label.center()
                        
                        self.widgets["-#HT"] = lv.btn(h_buttons)
                        self.widgets["-#HT"].set_size(35, 25)
                        label = lv.label(self.widgets["-#HT"])
                        label.set_text(lv.SYMBOL.MINUS)
                        label.center()
                    
                    with lv.obj(h_control) as h_pos_buttons:
                        h_pos_buttons.set_size(width-15, 25)
                        h_pos_buttons.set_pos(0, 45)
                        h_pos_buttons.set_flex_flow(lv.FLEX_FLOW.ROW)
                        
                        self.widgets["+#HP"] = lv.btn(h_pos_buttons)
                        self.widgets["+#HP"].set_size(35, 25)
                        label = lv.label(self.widgets["+#HP"])
                        label.set_text(lv.SYMBOL.PLUS)
                        label.center()
                        
                        h_pos_btn = lv.btn(h_pos_buttons)
                        h_pos_btn.set_size(50, 25)
                        label = lv.label(h_pos_btn)
                        label.set_text("Pos")
                        label.center()
                        
                        self.widgets["-#HP"] = lv.btn(h_pos_buttons)
                        self.widgets["-#HP"].set_size(35, 25)
                        label = lv.label(self.widgets["-#HP"])
                        label.set_text(lv.SYMBOL.MINUS)
                        label.center()
                
                # 分隔线
                line2 = lv.line(right_panel)
                line2.set_pos(0, 130)
                line2_points = [0, 0, 120+2*4, 0]
                line2.set_points(line2_points, 2)
                
                # 垂直控制区域
                with lv.obj(right_panel) as v_control:
                    v_control.set_size(width-15, 80)
                    v_control.set_pos(0, 135)
                    
                    v_label = lv.label(v_control)
                    v_label.set_text("Vertical")
                    v_label.set_pos(0, 0)
                    
                    with lv.obj(v_control) as v_buttons:
                        v_buttons.set_size(width-15, 25)
                        v_buttons.set_pos(0, 20)
                        v_buttons.set_flex_flow(lv.FLEX_FLOW.ROW)
                        
                        self.widgets["+#VV"] = lv.btn(v_buttons)
                        self.widgets["+#VV"].set_size(35, 25)
                        label = lv.label(self.widgets["+#VV"])
                        label.set_text(lv.SYMBOL.PLUS)
                        label.center()
                        
                        v_volt_btn = lv.btn(v_buttons)
                        v_volt_btn.set_size(50, 25)
                        label = lv.label(v_volt_btn)
                        label.set_text("Volt")
                        label.center()
                        
                        self.widgets["-#VV"] = lv.btn(v_buttons)
                        self.widgets["-#VV"].set_size(35, 25)
                        label = lv.label(self.widgets["-#VV"])
                        label.set_text(lv.SYMBOL.MINUS)
                        label.center()
                    
                    with lv.obj(v_control) as v_pos_buttons:
                        v_pos_buttons.set_size(width-15, 25)
                        v_pos_buttons.set_pos(0, 45)
                        v_pos_buttons.set_flex_flow(lv.FLEX_FLOW.ROW)
                        
                        self.widgets["+#VP"] = lv.btn(v_pos_buttons)
                        self.widgets["+#VP"].set_size(35, 25)
                        label = lv.label(self.widgets["+#VP"])
                        label.set_text(lv.SYMBOL.PLUS)
                        label.center()
                        
                        v_pos_btn = lv.btn(v_pos_buttons)
                        v_pos_btn.set_size(50, 25)
                        label = lv.label(v_pos_btn)
                        label.set_text("Pos")
                        label.center()
                        
                        self.widgets["-#VP"] = lv.btn(v_pos_buttons)
                        self.widgets["-#VP"].set_size(35, 25)
                        label = lv.label(self.widgets["-#VP"])
                        label.set_text(lv.SYMBOL.MINUS)
                        label.center()
                
                # 分隔线
                line3 = lv.line(right_panel)
                line3.set_pos(0, 215)
                line3_points = [0, 0, 120+2*4, 0]
                line3.set_points(line3_points, 2)
                
                # 触发控制区域
                with lv.obj(right_panel) as t_control:
                    t_control.set_size(width-15, 80)
                    t_control.set_pos(0, 220)
                    
                    t_label = lv.label(t_control)
                    t_label.set_text("Trigger")
                    t_label.set_pos(0, 0)
                    
                    with lv.obj(t_control) as t_buttons:
                        t_buttons.set_size(width-15, 25)
                        t_buttons.set_pos(0, 20)
                        t_buttons.set_flex_flow(lv.FLEX_FLOW.ROW)
                        
                        self.widgets["+#TP"] = lv.btn(t_buttons)
                        self.widgets["+#TP"].set_size(35, 25)
                        label = lv.label(self.widgets["+#TP"])
                        label.set_text(lv.SYMBOL.PLUS)
                        label.center()
                        
                        t_pos_btn = lv.btn(t_buttons)
                        t_pos_btn.set_size(50, 25)
                        label = lv.label(t_pos_btn)
                        label.set_text("Pos")
                        label.center()
                        
                        self.widgets["-#TP"] = lv.btn(t_buttons)
                        self.widgets["-#TP"].set_size(35, 25)
                        label = lv.label(self.widgets["-#TP"])
                        label.set_text(lv.SYMBOL.MINUS)
                        label.center()
    
    def start_tasks(self):
        """启动任务"""
        # 创建数据采集任务
        asyncio.create_task(self.data_acquisition_task())
        # 创建UI更新任务
        asyncio.create_task(self.ui_update_task())
    
    async def data_acquisition_task(self):
        """数据采集任务"""
        while True:
            if self.running or self.single:
                # 这里添加数据采集代码
                # ...
                
                if self.single:
                    self.single = False
                    self.widgets["#Status"].set_text("Single Done")
            
            await asyncio.sleep_ms(50)
    
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

# 创建屏幕
scr = lv.scr_act()
scr.set_style_bg_color(lv.color_hex(0x000000), 0)

# 创建示波器实例
scope = Scope()

# 启动事件循环
asyncio.run()