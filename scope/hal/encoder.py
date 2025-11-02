import machine
import time
import lvgl as lv

class EH11_Encoder:
    """EH11旋转编码器驱动类"""
    
    def __init__(self, clk_pin, dt_pin, sw_pin=None, steps_per_notch=1):
        """
        初始化EH11编码器
        
        参数:
            clk_pin: 时钟引脚
            dt_pin: 数据引脚
            sw_pin: 开关引脚(可选)
            steps_per_notch: 每个刻度的步数(默认为1)
        """
        self.clk = machine.Pin(clk_pin, machine.Pin.IN, machine.Pin.PULL_UP)
        self.dt = machine.Pin(dt_pin, machine.Pin.IN, machine.Pin.PULL_UP)
        
        self.clk_state = 0
        self.dt_state = 0
        self.last_clk_state = 0
        self.counter = 0
        self.steps_per_notch = steps_per_notch
        self.direction = 0  # 0: 无转动, 1: 顺时针, -1: 逆时针
        
        # 初始化状态
        self.last_clk_state = self.clk.value()
        
        # 如果有开关引脚，初始化它
        self.sw = None
        self.sw_pressed = False
        self.last_sw_state = 1  # 默认为高电平(未按下)
        
        if sw_pin is not None:
            self.sw = machine.Pin(sw_pin, machine.Pin.IN, machine.Pin.PULL_UP)
            self.last_sw_state = self.sw.value()
        
        # LVGL输入设备
        self.indev = None
        
    def update(self):
        """更新编码器状态，应该在主循环中定期调用"""
        current_clk = self.clk.value()
        current_dt = self.dt.value()
        
        # 检测旋转
        if current_clk != self.last_clk_state:
            # CLK状态改变
            if current_clk != current_dt:
                # 顺时针旋转
                self.direction = 1
                self.counter += self.steps_per_notch
            else:
                # 逆时针旋转
                self.direction = -1
                self.counter -= self.steps_per_notch
                
            self.last_clk_state = current_clk
            return True
        
        # 检测开关
        if self.sw is not None:
            current_sw = self.sw.value()
            if current_sw != self.last_sw_state:
                # 开关状态改变
                if current_sw == 0:  # 低电平表示按下
                    self.sw_pressed = True
                else:  # 高电平表示释放
                    self.sw_pressed = False
                self.last_sw_state = current_sw
                return True
        
        # 无变化
        self.direction = 0
        return False
    
    def get_direction(self):
        """获取旋转方向"""
        return self.direction
    
    def get_counter(self):
        """获取计数器值"""
        return self.counter
    
    def is_switch_pressed(self):
        """检查开关是否被按下"""
        return self.sw_pressed
    
    def reset_counter(self):
        """重置计数器"""
        self.counter = 0
    
    def register_lvgl_indev(self):
        """注册为LVGL输入设备"""
        # 创建编码器输入设备
        self.indev = lv.indev_create()
        self.indev.set_type(lv.INDEV_TYPE.ENCODER)
        self.indev.set_read_cb(self._encoder_read_cb)
        return self.indev
    
    def _encoder_read_cb(self, indev_drv, data):
        """LVGL编码器读取回调函数"""
        # 更新编码器状态
        self.update()
        
        # 设置编码器差值
        data.enc_diff = self.direction
        
        # 设置按键状态
        if self.sw_pressed:
            data.state = lv.INDEV_STATE.PRESSED
        else:
            data.state = lv.INDEV_STATE.RELEASED


class Button_Handler:
    """按键处理类"""
    
    def __init__(self, pin_map):
        """
        初始化按键处理器
        
        参数:
            pin_map: 字典，键为按键名称，值为引脚号
                    例如: {'up': 2, 'down': 3, 'left': 4, 'right': 5, 'ok': 6}
        """
        self.buttons = {}
        self.last_states = {}
        self.current_states = {}
        
        # 初始化所有按键
        for name, pin in pin_map.items():
            self.buttons[name] = machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_UP)
            self.last_states[name] = 1  # 默认为高电平(未按下)
            self.current_states[name] = 1
        
        # LVGL输入设备
        self.indev = None
    
    def update(self):
        """更新所有按键状态，应该在主循环中定期调用"""
        changed = False
        for name, button in self.buttons.items():
            current = button.value()
            if current != self.last_states[name]:
                # 按键状态改变
                self.current_states[name] = current
                changed = True
            self.last_states[name] = current
        return changed
    
    def is_pressed(self, name):
        """检查指定按键是否被按下"""
        return self.current_states.get(name, 1) == 0  # 低电平表示按下
    
    def get_pressed_buttons(self):
        """获取所有被按下的按键名称列表"""
        return [name for name, state in self.current_states.items() if state == 0]
    
    def register_lvgl_keypad_indev(self):
        """注册为LVGL键盘输入设备"""
        # 创建键盘输入设备
        self.indev = lv.indev_create()
        self.indev.set_type(lv.INDEV_TYPE.KEYPAD)
        self.indev.set_read_cb(self._keypad_read_cb)
        return self.indev
    
    def _keypad_read_cb(self, indev_drv, data):
        """LVGL键盘读取回调函数"""
        # 更新按键状态
        self.update()
        
        # 检查是否有按键被按下
        pressed = self.get_pressed_buttons()
        if pressed:
            # 根据按键名称映射到LVGL键码
            key_map = {
                'up': lv.KEY.UP,
                'down': lv.KEY.DOWN,
                'left': lv.KEY.LEFT,
                'right': lv.KEY.RIGHT,
                'ok': lv.KEY.ENTER,
                'enter': lv.KEY.ENTER,
                'esc': lv.KEY.ESC,
                'back': lv.KEY.BACKSPACE,
                'prev': lv.KEY.PREV,
                'next': lv.KEY.NEXT
            }
            
            # 使用第一个被按下的按键
            button_name = pressed[0]
            if button_name in key_map:
                data.key = key_map[button_name]
                data.state = lv.INDEV_STATE.PRESSED
            else:
                data.state = lv.INDEV_STATE.RELEASED
        else:
            data.state = lv.INDEV_STATE.RELEASED


def create_encoder_input_device(clk_pin=2, dt_pin=3, sw_pin=4):
    """
    创建并注册EH11编码器输入设备
    
    参数:
        clk_pin: 时钟引脚(默认为2)
        dt_pin: 数据引脚(默认为3)
        sw_pin: 开关引脚(默认为4)
    
    返回:
        encoder: EH11_Encoder实例
        indev: LVGL输入设备
    """
    encoder = EH11_Encoder(clk_pin, dt_pin, sw_pin)
    indev = encoder.register_lvgl_indev()
    return encoder, indev


def create_button_input_device(pin_map):
    """
    创建并注册按键输入设备
    
    参数:
        pin_map: 字典，键为按键名称，值为引脚号
    
    返回:
        button_handler: Button_Handler实例
        indev: LVGL输入设备
    """
    button_handler = Button_Handler(pin_map)
    indev = button_handler.register_lvgl_keypad_indev()
    return button_handler, indev