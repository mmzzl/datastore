import lvgl as lv
from hal.encoder import EH11Encoder

class Display_Driver:
    def __init__( self, lcd, width=240, height=320, tsc=None, fb_rows=64, encoder=None ):
        self.width = width
        self.height = height
        self.lcd = lcd
        self.tsc = tsc
        self.encoder = encoder
        self.fb_rows = fb_rows
        
        self.is_fb1 = True
        self.dma_running = False
        
        self.x = 0
        self.y = 0
        self.s = 0
        
        # 编码器相关状态
        self.encoder_events = {
            "rotation": 0,
            "button_pressed": False,
            "button_released": False
        }
        
        self.init_gui()
    
    def init_gui(self):
        lv.init()
        draw_buf_size = int((self.width * self.height) / 10 * (lv.COLOR_DEPTH / 8))
        self.fb1 = bytearray(draw_buf_size // 4 )
        self.fb2 = bytearray(draw_buf_size // 4 )
        print("len(fb1)", len(self.fb1))
        print("len(fb2)", len(self.fb2))
        # 2. 初始化显示驱动
        self.disp_drv = lv.display_create(self.width, self.height)
        self.disp_drv.set_flush_cb(self.disp_drv_flush_cb)
        self.disp_drv.set_buffers(self.fb1, self.fb2, len(self.fb1), lv.DISPLAY_RENDER_MODE.PARTIAL)
        # 4. 注册显示驱动
        self.disp_drv.flush_ready()
        
        # 初始化编码器输入设备
        if self.encoder:
            self.init_encoder()

    def disp_drv_flush_cb( self, disp_drv, area, color ):
        #print( "disp_drv_flush_cb", area.x1, area.x2, area.y1, area.y2 )
                    
        if( self.dma_running == True ):
            self.lcd.wait_dma()
            self.dma_running = False
        
        if( self.is_fb1 ):
            fb = memoryview( self.fb1 )
        else:
            fb = memoryview( self.fb2 )
        self.is_fb1 = not self.is_fb1
        
        x = area.x1
        y = area.y1
        w = area.x2 - area.x1 + 1
        h = area.y2 - area.y1 + 1
        self.lcd.draw_bitmap_dma( x, y, w, h, fb[0:w*h*lv.color_t.__SIZE__], is_blocking=False )
        self.dma_running = True
        
        disp_drv.flush_ready()
        
    def indev_drv_read_cb( self, indev_drv, data ):
        #print( "indev_drv_read_cb", self.x, self.y, self.s )
        
        if( self.dma_running == True ):
            self.lcd.wait_dma()
            self.dma_running = False     
        if self.tsc:
            self.tsc.spi_init()
            x, y = self.tsc.read()
        self.lcd.spi_init() # Reinit SPI with LCD settings
        
        if( x or y ):
            self.x = x
            self.y = y
            self.s = 1
            #print( "indev_drv_read_cb", self.x, self.y, self.s )
        else:
            self.s = 0
        
        data.point.x = self.x
        data.point.y = self.y
        data.state = self.s
        
        return False

    def init_encoder(self):
        """初始化编码器输入设备"""
        # 创建编码器输入设备
        self.indev_encoder = lv.indev_create()
        self.indev_encoder.set_type(lv.INDEV_TYPE.ENCODER)
        self.indev_encoder.set_read_cb(self.indev_encoder_read_cb)
        
        # 设置编码器回调
        self.encoder.set_rotation_callback(self._on_encoder_rotation)
        self.encoder.set_button_callback(self._on_encoder_button)
    
    def _on_encoder_rotation(self, direction):
        """编码器旋转回调"""
        self.encoder_events["rotation"] += direction
    
    def _on_encoder_button(self, event):
        """编码器按键回调"""
        if event == "pressed":
            self.encoder_events["button_pressed"] = True
            print(f"Button pressed event received")
        elif event == "released":
            self.encoder_events["button_released"] = True
            print(f"Button released event received")
    
    def indev_encoder_read_cb(self, indev_drv, data):
        """编码器输入设备读取回调"""
        # 获取编码器事件
        events = self.encoder.get_events() if self.encoder else {"rotation": 0, "button_state": 1}
        
        # 设置编码器值
        data.enc_diff = events["rotation"]
        data.state = 0 if events["button_state"] == 1 else 1
        
        # 重置旋转计数
        if events["rotation"] != 0:
            self.encoder.reset_counter()
        
        return False
    
    def get_encoder_events(self):
        """获取编码器事件并清除标志"""
        if not self.encoder:
            return {"rotation": 0, "button_pressed": False, "button_released": False}
        
        # 保存当前事件
        events = {
            "rotation": self.encoder_events["rotation"],
            "button_pressed": self.encoder_events["button_pressed"],
            "button_released": self.encoder_events["button_released"]
        }
        
        # 清除事件标志
        self.encoder_events["rotation"] = 0
        self.encoder_events["button_pressed"] = False
        self.encoder_events["button_released"] = False
        
        return events

print("done")