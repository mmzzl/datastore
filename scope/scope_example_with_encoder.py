"""
scope_example_with_encoder.py
==============================

这是原始scope_example.py的修改版本，添加了EH11编码器支持，
同时保持了原有的self.widgets结构和代码简洁性。

主要修改：
1. 添加了编码器和按键初始化
2. 添加了编码器事件处理循环
3. 保持了原有的UI结构和回调函数
"""

import lvgl
import gc
import time
import uctypes
import micropython
import asyncio
from gui.dear_lvgl import *
from hal.st7789 import *
from hal.ad9288 import *
from hal.dma import *
from hal.pio_pwm import *
from gui.asm_set_pixel2 import asm_set_pixel2
from hal.encoder import create_encoder_input_device, create_button_input_device

class Scope:
    def __init__( self, parent ):
        self.parent = parent
        self.context = []
        self.widgets = {}
        
        # 示波器参数
        self.horizontal_scale = 0
        self.horizontal_position = 0
        self.trigger_position = 0
        self.channel1_scale = 1
        self.channel2_scale = 1
        self.channel1_position = 0
        self.channel2_position = 0
        self.channel1_selected = True
        self.single = False
        self.adc_used = 0
        
        # 缓冲区
        self.buf_adc_a = bytearray( 512 )
        self.buf_adc_b = bytearray( 512 )
        self.buf_adc = self.buf_adc_a
        self.trigger_pos_a = 0
        self.trigger_pos_b = 0
        
        # 初始化硬件
        self.init_hardware()
        
        # 初始化UI
        self.build_ui( parent )
        
        # 初始化编码器 - 新增
        self.init_encoder()
        
        # 启动数据采集任务
        self.start_data_acquisition()
    
    def init_hardware(self):
        """初始化硬件"""
        # 初始化ADC
        self.adc = AD9288()
        
        # 初始化DMA
        self.dma = DMA()
        
        # 初始化PWM
        self.trig = PWM( 28 )
        self.trig.duty_u16( int( 0xFFFF*1.024/3.3 ) )
        self.trig.freq( 1000 )
    
    def init_encoder(self):
        """初始化EH11编码器和按键 - 新增"""
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
        """编码器处理循环 - 新增"""
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
    
    def start_data_acquisition(self):
        """启动数据采集任务"""
        asyncio.create_task(self.data_acquisition_loop())
    
    async def data_acquisition_loop(self):
        """数据采集循环"""
        while True:
            if not (self.widgets["Run#M"].get_state() & lv.STATE.CHECKED) and not self.single:
                await asyncio.sleep_ms(50)
                continue
            
            self.single = False
            self.adc_used = 1 - self.adc_used
            
            if self.adc_used == 1:
                self.buf_adc = self.buf_adc_a
                self.trigger_pos_a = self.dma.capture( self.buf_adc_a )
                self.trigger_pos = self.trigger_pos_a
            else:
                self.buf_adc = self.buf_adc_b
                self.trigger_pos_b = self.dma.capture( self.buf_adc_b )
                self.trigger_pos = self.trigger_pos_b
            
            self.update_display()
            await asyncio.sleep_ms(10)
    
    def update_display(self):
        """更新显示"""
        t0 = time.ticks_us()
        
        self.params = bytearray( 13*4 )
        
        self.params[0] = 480-160-12
        self.params[1] = 300-5-50-10
        self.params[2] = 0
        self.params[3] = 0
        self.params[4] = 8
        self.params[5] = 10
        
        self.params[6] = uctypes.addressof( self.buf_adc )
        self.params[7] = ((uctypes.addressof( self.buf_adc )+0xFF)&0xFFFFFF00)-uctypes.addressof( self.buf_adc )
        self.params[8] = self.trigger_pos
        self.params[9] = 0xFFFF
        
        self.params[10] = 256
        self.params[11] = 0xFF
        
        self.params[12] = 12
        asm_set_pixel2( uctypes.addressof( self.params ) )
        t1 = time.ticks_us()
        print( "display update time:", t1-t0 )
    
    # 以下是原始的回调函数，保持不变
    def cb_run( self, evt ):
        if( self.widgets["Run#M"].get_state() & lv.STATE.CHECKED ):
            self.widgets["#Status"].set_text( "Running" )
            self.widgets["Run#M"].get_child(0).set_text( lv.SYMBOL.STOP )
        else:
            self.widgets["#Status"].set_text( "Stop" )  
            self.widgets["Run#M"].get_child(0).set_text( lv.SYMBOL.PLAY )
    
    def cb_single( self, evt ):
        self.single = True
        self.widgets["Run#M"].clear_state( lv.STATE.CHECKED )
        self.widgets["Run#M"].get_child(0).set_text( lv.SYMBOL.PLAY )
        self.widgets["#Status"].set_text( "Single" )
    
    def cb_save( self, evt ):
        idx = len( [name for name in os.listdir() if "data" in name] )
        fl_name = "data{}.txt".format( idx )
        
        if( self.adc_used == 1 ):
            buf_adc = self.buf_adc_a
            addr = uctypes.addressof( self.buf_adc_a )
            align = ((addr+0xFF)&0xFFFFFF00)-addr
            trigger = self.trigger_pos_a
        else:
            buf_adc = self.buf_adc_b
            addr = uctypes.addressof( self.buf_adc_b )
            align = ((addr+0xFF)&0xFFFFFF00)-addr
            trigger = self.trigger_pos_b
        
        with open( fl_name, "w" ) as fl:
            for i in range( 256 ):
                fl.write( "{}\n".format( buf_adc[ align + ((trigger + i)&0xFF) ] ) )
        
        self.widgets["#Status"].set_text( fl_name )

    def cb_horizontal_scale_inc( self, evt ):
        if( self.horizontal_scale < 6 ):
            self.horizontal_scale += 1
        sps = [ "1 M", "2 M", "5 M", "10 M", "20 M", "50 M", "100 M" ][self.horizontal_scale]
        self.widgets[ "#lHS" ].set_text( "HS {} Sps".format( sps ) )

    def cb_horizontal_scale_dec( self, evt ):
        if( self.horizontal_scale > 0 ):
            self.horizontal_scale -= 1
        sps = [ "1 M", "2 M", "5 M", "10 M", "20 M", "50 M", "100 M" ][self.horizontal_scale]
        self.widgets[ "#lHS" ].set_text( "HS {} Sps".format( sps ) )

    def cb_horizontal_position_inc( self, evt ):
        if( self.horizontal_position < 1024 ):
            self.horizontal_position += 1
        self.widgets[ "#lHP" ].set_text( "HP {} S".format( self.horizontal_position ) )

    def cb_horizontal_position_set( self, evt ):
        self.horizontal_position = 0
        self.widgets[ "#lHP" ].set_text( "HP {} S".format( self.horizontal_position ) )

    def cb_horizontal_position_dec( self, evt ):
        if( self.horizontal_position > -127 ):
            self.horizontal_position -= 1
        self.widgets[ "#lHP" ].set_text( "HP {} S".format( self.horizontal_position ) )

    def cb_channel_select( self, evt ):
        self.channel1_selected = not self.channel1_selected
        self.widgets["CHS#VS"].get_child(0).set_text( "CH1" if self.channel1_selected else "CH2" )
        print( "channel1_selected", self.channel1_selected )

    def cb_vertical_scale_inc( self, evt ):
        if( self.channel1_selected ):
            self.channel1_scale += 1
            self.widgets[ "#lVS1" ].set_text( "VS1 {} V/D".format( self.channel1_scale ) )
        else:
            self.channel2_scale += 1
            self.widgets[ "#lVS2" ].set_text( "VS2 {} V/D".format( self.channel2_scale ) )
        
    def cb_vertical_scale_dec( self, evt ):
        if( self.channel1_selected ):
            self.channel1_scale -= 1
            self.widgets[ "#lVS1" ].set_text( "VS1 {} V/D".format( self.channel1_scale ) )
        else:
            self.channel2_scale -= 1
            self.widgets[ "#lVS2" ].set_text( "VS2 {} V/D".format( self.channel2_scale ) )

    def cb_vertical_position_inc( self, evt ):
        if( self.channel1_selected ):
            self.channel1_position += 1
            self.widgets[ "#lVP1" ].set_text( "VP1 {} V".format( self.channel1_position ) )
        else:
            self.channel2_position += 1
            self.widgets[ "#lVP2" ].set_text( "VP2 {} V".format( self.channel2_position ) )

    def cb_vertical_position_set( self, evt ):
        if( self.channel1_selected ):
            self.channel1_position = 1
            self.widgets[ "#lVP1" ].set_text( "VP1 {} V".format( self.channel1_position ) )
        else:
            self.channel2_position = 1
            self.widgets[ "#lVP2" ].set_text( "VP2 {} V".format( self.channel2_position ) )

    def cb_vertical_position_dec( self, evt ):
        if( self.channel1_selected ):
            self.channel1_position -= 1
            self.widgets[ "#lVP1" ].set_text( "VP1 {} V".format( self.channel1_position ) )
        else:
            self.channel2_position -= 1
            self.widgets[ "#lVP2" ].set_text( "VP2 {} V".format( self.channel2_position ) )

    def cb_trigger_position_inc( self, evt ):
        self.trigger_position += 1
        self.widgets[ "#lTP" ].set_text( "TP {} V".format( self.trigger_position ) )
        self.trig.duty_u16( int( 0xFFFF*1.024/3.3 ) + self.trigger_position*256 )

    def cb_trigger_position_set( self, evt ):
        self.trigger_position = 0
        self.widgets[ "#lTP" ].set_text( "TP {} V".format( self.trigger_position ) )
        self.trig.duty_u16( int( 0xFFFF*1.024/3.3 ) + self.trigger_position*256 )

    def cb_trigger_position_dec( self, evt ):
        self.trigger_position -= 1
        self.widgets[ "#lTP" ].set_text( "TP {} V".format( self.trigger_position ) )
        self.trig.duty_u16( int( 0xFFFF*1.024/3.3 ) + self.trigger_position*256 )

    # UI构建方法 - 保持不变
    def build_ui( self, parent ):
        width = 160
        point_count = 480-width
        
        self.context.append( parent )
        set_context( self.context )
        set_widgets( self.widgets )
        
        with Cont():
            with Cont( 0, 0, 480-width, 320-15 ):
                with Column():
                    lblw= 74
                    with Row():
                        add_label( "#Status", w=lblw )
                        add_label( "#lHS", w=lblw ).set_text( "1 S/D" )
                        add_label( "#lHP", w=lblw ).set_text( "0 S" )
                        add_label( "#lTP", w=lblw ).set_text( "0 V" )

                    self.chart = lv.chart( self.context[-1] )
                    self.chart.set_size( 480-160-12, 300-5-50-10 )
                    self.chart.set_div_line_count( 8, 10 )
                    with Row():
                        add_label( "#lVS1", w=lblw ).set_text( "1 V/D" )
                        add_label( "#lVP1", w=lblw ).set_text( "0 V" )
                        add_label( "#lVS2", w=lblw ).set_text( "1 V/D" )
                        add_label( "#lVP2", w=lblw ).set_text( "0 V" )
            with Cont( 480-width, 0, width-15, 320-15 ):
                with Column():
                    with Row():
                        add_button( "Run#M" ).add_event_cb( self.cb_run, lv.EVENT.VALUE_CHANGED, None )
                        self.widgets["Run#M"].add_flag( lv.obj.FLAG.CHECKABLE )
                        self.widgets["Run#M"].get_child(0).set_text( lv.SYMBOL.PLAY )
                        add_button( "Sing#M" ).add_event_cb( self.cb_single, lv.EVENT.CLICKED, None )
                        self.widgets["Sing#M"].get_child(0).set_text( lv.SYMBOL.NEXT )
                        add_button( "#Save" ).add_event_cb( self.cb_save, lv.EVENT.CLICKED, None )
                        self.widgets["#Save"].get_child(0).set_text( lv.SYMBOL.SAVE )
                    add_line( 0, 2, 120+2*4, 1 )

                    add_label( "Horizontal", w=100 )
                    with Row():
                        add_button( "+#HT" ).add_event_cb( self.cb_horizontal_scale_inc, lv.EVENT.CLICKED, None )
                        self.widgets["+#HT"].get_child(0).set_text( lv.SYMBOL.PLUS )
                        add_button( "Time" ).add_event_cb( self.cb_horizontal_scale_set, lv.EVENT.CLICKED, None )
                        add_button( "-#HT" ).add_event_cb( self.cb_horizontal_scale_dec, lv.EVENT.CLICKED, None )
                        self.widgets["-#HT"].get_child(0).set_text( lv.SYMBOL.MINUS )
                    with Row():
                        add_button( "+#HP" ).add_event_cb( self.cb_horizontal_position_inc, lv.EVENT.CLICKED, None )
                        self.widgets["+#HP"].get_child(0).set_text( lv.SYMBOL.PLUS )
                        add_button( "Pos#H").add_event_cb( self.cb_horizontal_position_set, lv.EVENT.CLICKED, None )
                        add_button( "-#HP" ).add_event_cb( self.cb_horizontal_position_dec, lv.EVENT.CLICKED, None )
                        self.widgets["-#HP"].get_child(0).set_text( lv.SYMBOL.MINUS )
                        self.widgets["+#HP"].add_event_cb( self.cb_horizontal_position_inc, lv.EVENT.LONG_PRESSED_REPEAT, None )
                        self.widgets["-#HP"].add_event_cb( self.cb_horizontal_position_dec, lv.EVENT.LONG_PRESSED_REPEAT, None )
                    add_line( 0, 2, 120+2*4, 1 )

                    add_label( "Vertical", w=80 )
                    with Row():
                        add_button( "CH1#V" ).add_flag( lv.obj.FLAG.CHECKABLE )
                        add_button( "CH2#V" ).add_flag( lv.obj.FLAG.CHECKABLE )
                        self.widgets["CH1#V"].set_style_bg_color( lv.palette_lighten( lv.PALETTE.RED, 1 ), 1 )
                        self.widgets["CH2#V"].set_style_bg_color( lv.palette_lighten( lv.PALETTE.BLUE, 1 ), 1 )
                        
                        add_button( "CHS#VS" ).add_flag( lv.obj.FLAG.CHECKABLE )
                        self.widgets["CHS#VS"].set_style_bg_color( lv.palette_lighten( lv.PALETTE.RED, 1 ), 0 )
                        self.widgets["CHS#VS"].set_style_bg_color( lv.palette_lighten( lv.PALETTE.BLUE, 1 ), 1 )
                        self.widgets["CHS#VS"].add_event_cb( self.cb_channel_select, lv.EVENT.CLICKED, None )
                        self.widgets["CHS#VS"].get_child(0).set_text( "CH1" )
                        
                    with Row():
                        add_button( "+#VV" ).add_event_cb( self.cb_vertical_scale_inc, lv.EVENT.CLICKED, None )
                        self.widgets["+#VV"].get_child(0).set_text( lv.SYMBOL.PLUS )
                        add_button( "Volt" ).add_event_cb( self.cb_vertical_scale_set, lv.EVENT.CLICKED, None )
                        add_button( "-#VV" ).add_event_cb( self.cb_vertical_scale_dec, lv.EVENT.CLICKED, None )
                        self.widgets["-#VV"].get_child(0).set_text( lv.SYMBOL.MINUS )
                    with Row():
                        add_button( "+#VP" ).add_event_cb( self.cb_vertical_position_inc, lv.EVENT.CLICKED, None )
                        self.widgets["+#VP"].get_child(0).set_text( lv.SYMBOL.PLUS )
                        add_button( "Pos#V").add_event_cb( self.cb_vertical_position_set, lv.EVENT.CLICKED, None )
                        add_button( "-#VP" ).add_event_cb( self.cb_vertical_position_dec, lv.EVENT.CLICKED, None )
                        self.widgets["-#VP"].get_child(0).set_text( lv.SYMBOL.MINUS )
                    add_line( 0, 2, 120+2*4, 1 )

                    add_label( "Trigger", w=80 )
                    with Row():
                        add_button( "CH12#T"  ).add_flag( lv.obj.FLAG.CHECKABLE )
                        self.widgets["CH12#T"].get_child(0).set_text( "CH1" )
                        self.widgets["CH12#T"].set_style_bg_color( lv.palette_lighten( lv.PALETTE.RED, 1 ), 0 )
                        self.widgets["CH12#T"].set_style_bg_color( lv.palette_lighten( lv.PALETTE.BLUE, 1 ), 1 )
                        add_button( "Edge#T" ).add_flag( lv.obj.FLAG.CHECKABLE )
                        add_button( "Auto#T" ).add_flag( lv.obj.FLAG.CHECKABLE )
                    with Row():
                        add_button( "+#TP" ).add_event_cb( self.cb_trigger_position_inc, lv.EVENT.CLICKED, None )
                        self.widgets["+#TP"].get_child(0).set_text( lv.SYMBOL.PLUS )
                        add_button( "Pos#T").add_event_cb( self.cb_trigger_position_set, lv.EVENT.CLICKED, None )
                        add_button( "-#TP" ).add_event_cb( self.cb_trigger_position_dec, lv.EVENT.CLICKED, None )
                        self.widgets["-#TP"].get_child(0).set_text( lv.SYMBOL.MINUS )
                        self.widgets["+#TP"].add_event_cb( self.cb_trigger_position_inc, lv.EVENT.LONG_PRESSED_REPEAT, None )
                        self.widgets["-#TP"].add_event_cb( self.cb_trigger_position_dec, lv.EVENT.LONG_PRESSED_REPEAT, None )

# 初始化和主循环
def foo2():
    # 初始化LVGL
    lv.init()
    
    # 初始化显示驱动
    scr = lv.scr_act()
    disp = DisplayDriver( scr )
    
    # 创建示波器实例
    scope = Scope( scr )
    
    # 启动事件循环
    asyncio.run()

if __name__ == "__main__":
    foo2()