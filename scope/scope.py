import lvgl as lv
import machine
import time
import math
from hal.ad9288 import Adc9288
from hal.encoder import EH11Encoder
from hal.test_signal import TestSignalGenerator

class Scope:
    def __init__(self, parent, display_driver):
        self.parent = parent
        self.display_driver = display_driver
        
        self.width = 320
        self.height = 240
        
        self.sample_rate = 100_000_000
        self.buffer_size = 240
        self.sample_buffer = bytearray(self.buffer_size)
        
        self.voltage_scale = 1.0
        self.time_scale = 1.0
        self.trigger_level = 128
        self.trigger_mode = 'auto'
        self.trigger_enabled = False
        
        self.is_paused = False
        self.waveform_data = []
        
        self.frequency = 0
        self.voltage_pp = 0
        self.voltage_rms = 0
        
        self.use_test_signal = False
        self.test_signal_freq = 1000
        
        self._init_adc()
        self._init_test_signal()
        self._init_ui()
        self._init_encoder()
        
    def _init_adc(self):
        db = machine.Pin(0, machine.Pin.IN)
        sck = machine.Pin(21, machine.Pin.OUT)
        self.adc = Adc9288(self.sample_rate, sck, db)
    
    def _init_test_signal(self):
        output_pin = machine.Pin(2, machine.Pin.OUT)
        self.test_signal = TestSignalGenerator(output_pin, frequency=self.test_signal_freq)
    
    def toggle_test_signal(self):
        """切换测试信号模式"""
        self.use_test_signal = not self.use_test_signal
        if self.use_test_signal:
            self.test_signal.start()
        else:
            self.test_signal.stop()
        return self.use_test_signal
    
    def set_test_signal_frequency(self, frequency):
        """设置测试信号频率"""
        self.test_signal_freq = frequency
        self.test_signal.set_frequency(frequency)
    
    def set_trigger_level(self, level):
        """设置触发级别"""
        self.trigger_level = max(0, min(255, level))
        self.adc.set_trigger_level(level)
    
    def set_trigger_enabled(self, enabled):
        """启用或禁用触发"""
        self.trigger_enabled = enabled
        self.adc.set_trigger_enabled(enabled)
    
    def toggle_trigger(self):
        """切换触发状态"""
        self.trigger_enabled = not self.trigger_enabled
        self.adc.set_trigger_enabled(self.trigger_enabled)
        return self.trigger_enabled
        
    def _init_ui(self):
        self.main_container = lv.obj(self.parent)
        self.main_container.set_size(self.width, self.height)
        self.main_container.set_pos(0, 0)
        self.main_container.set_style_bg_color(lv.color_hex(0x000000), 0)
        self.main_container.set_style_border_width(0, 0)
        self.main_container.set_style_pad_all(0, 0)
        
        self._create_status_bar()
        self._create_waveform_display()
        self._create_info_panel()
        
    def _create_status_bar(self):
        self.status_bar = lv.obj(self.main_container)
        self.status_bar.set_size(self.width, 30)
        self.status_bar.set_pos(0, 0)
        self.status_bar.set_style_bg_color(lv.color_hex(0x1a1a2e), 0)
        self.status_bar.set_style_border_width(0, 0)
        self.status_bar.set_style_pad_all(5, 0)
        
        self.freq_label = lv.label(self.status_bar)
        self.freq_label.set_text("Freq: -- Hz")
        self.freq_label.set_style_text_color(lv.color_hex(0x00ff00), 0)
        self.freq_label.set_pos(5, 5)
        
        self.vpp_label = lv.label(self.status_bar)
        self.vpp_label.set_text("Vpp: -- V")
        self.vpp_label.set_style_text_color(lv.color_hex(0xffff00), 0)
        self.vpp_label.set_pos(120, 5)
        
        self.scale_label = lv.label(self.status_bar)
        self.scale_label.set_text("Scale: 1.0x")
        self.scale_label.set_style_text_color(lv.color_hex(0x00ffff), 0)
        self.scale_label.set_pos(220, 5)
        
    def _create_waveform_display(self):
        self.waveform_height = 180
        self.waveform_y = 30
        
        self.waveform_canvas = lv.canvas(self.main_container)
        self.waveform_canvas.set_size(self.width, self.waveform_height)
        self.waveform_canvas.set_pos(0, self.waveform_y)
        
        buf_size = self.width * self.waveform_height
        self.waveform_buffer = bytearray(buf_size * lv.COLOR_FORMAT.NATIVE.size)
        self.waveform_canvas.set_buffer(self.waveform_buffer, self.width, self.waveform_height, lv.COLOR_FORMAT.NATIVE)
        
        self._clear_waveform()
        self._draw_grid()
        
    def _clear_waveform(self):
        self.waveform_canvas.fill_bg(lv.color_hex(0x000000), lv.OPA.COVER)
        
    def _draw_grid(self):
        grid_color = lv.color_hex(0x1a1a2e)
        
        center_y = self.waveform_height // 2
        
        for x in range(0, self.width, 20):
            self.waveform_canvas.draw_line(x, 0, x, self.waveform_height, grid_color, 1)
        
        for y in range(0, self.waveform_height, 20):
            self.waveform_canvas.draw_line(0, y, self.width, y, grid_color, 1)
        
        center_color = lv.color_hex(0x333333)
        self.waveform_canvas.draw_line(0, center_y, self.width, center_y, center_color, 2)
        
    def _create_info_panel(self):
        self.info_panel = lv.obj(self.main_container)
        self.info_panel.set_size(self.width, 30)
        self.info_panel.set_pos(0, 210)
        self.info_panel.set_style_bg_color(lv.color_hex(0x1a1a2e), 0)
        self.info_panel.set_style_border_width(0, 0)
        self.info_panel.set_style_pad_all(5, 0)
        
        self.status_label = lv.label(self.info_panel)
        self.status_label.set_text("Status: Running")
        self.status_label.set_style_text_color(lv.color_hex(0xffffff), 0)
        self.status_label.set_pos(5, 5)
        
        self.trigger_label = lv.label(self.info_panel)
        self.trigger_label.set_text("Trigger: Auto")
        self.trigger_label.set_style_text_color(lv.color_hex(0xff9900), 0)
        self.trigger_label.set_pos(150, 5)
        
    def _init_encoder(self):
        self.encoder = self.display_driver.encoder
        
        self.encoder_state = 'normal'
        self.encoder_counter = 0
        self.last_encoder_value = 0
        
        self.encoder.set_rotation_callback(self._on_encoder_rotation)
        self.encoder.set_button_callback(self._on_encoder_button)
        
    def _on_encoder_rotation(self, direction):
        if self.encoder_state == 'normal':
            self.voltage_scale += direction * 0.1
            if self.voltage_scale < 0.1:
                self.voltage_scale = 0.1
            elif self.voltage_scale > 10.0:
                self.voltage_scale = 10.0
        elif self.encoder_state == 'time':
            self.time_scale += direction * 0.1
            if self.time_scale < 0.1:
                self.time_scale = 0.1
            elif self.time_scale > 10.0:
                self.time_scale = 10.0
        
        self._update_ui()
        
    def _on_encoder_button(self, event):
        if event == 'pressed':
            if self.is_paused:
                self.is_paused = False
                self.status_label.set_text("Status: Running")
            else:
                self.is_paused = True
                self.status_label.set_text("Status: Paused")
            
            if self.encoder_state == 'normal':
                self.encoder_state = 'time'
                self.trigger_label.set_text("Mode: Time Scale")
            else:
                self.encoder_state = 'normal'
                self.trigger_label.set_text("Mode: Voltage Scale")
        
    def _update_ui(self):
        self.scale_label.set_text(f"Scale: {self.voltage_scale:.1f}x")
        
    def _acquire_waveform(self):
        if self.is_paused:
            return
        
        if self.use_test_signal:
            self.test_signal.generate_buffer(self.sample_buffer, self.sample_rate)
        else:
            self.adc.read(self.sample_buffer)
        
        self.waveform_data = list(self.sample_buffer)
        
        self._calculate_measurements()
        self._draw_waveform()
        
    def _calculate_measurements(self):
        if not self.waveform_data:
            return
            
        data = self.waveform_data
        
        min_val = min(data)
        max_val = max(data)
        
        self.voltage_pp = (max_val - min_val) / 255.0 * 3.3 * self.voltage_scale
        
        sum_sq = sum((x - 128) ** 2 for x in data)
        self.voltage_rms = math.sqrt(sum_sq / len(data)) / 255.0 * 3.3 * self.voltage_scale
        
        self.frequency = self._calculate_frequency(data)
        
    def _calculate_frequency(self, data):
        zero_crossings = 0
        threshold = 128
        
        prev_above = data[0] > threshold
        
        for i in range(1, len(data)):
            curr_above = data[i] > threshold
            
            if curr_above != prev_above:
                zero_crossings += 1
                prev_above = curr_above
        
        if zero_crossings > 0:
            period_samples = len(data) / (zero_crossings / 2)
            frequency = self.sample_rate / period_samples
            return frequency
        
        return 0
        
    def _draw_waveform(self):
        self._clear_waveform()
        self._draw_grid()
        
        if not self.waveform_data:
            return
            
        center_y = self.waveform_height // 2
        wave_color = lv.color_hex(0x00ff00)
        
        points = []
        
        for i, val in enumerate(self.waveform_data):
            if i >= self.width:
                break
                
            normalized = (val - 128) / 128.0
            y = int(center_y - normalized * self.waveform_height * 0.4 * self.voltage_scale)
            y = max(0, min(y, self.waveform_height - 1))
            points.append((i, y))
        
        if len(points) > 1:
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                self.waveform_canvas.draw_line(x1, y1, x2, y2, wave_color, 2)
        
        self._draw_trigger_line()
        self._update_info_labels()
    
    def _draw_trigger_line(self):
        if not self.trigger_enabled:
            return
            
        center_y = self.waveform_height // 2
        normalized = (self.trigger_level - 128) / 128.0
        trigger_y = int(center_y - normalized * self.waveform_height * 0.4 * self.voltage_scale)
        trigger_y = max(0, min(trigger_y, self.waveform_height - 1))
        
        trigger_color = lv.color_hex(0xff0000)
        self.waveform_canvas.draw_line(0, trigger_y, self.width, trigger_y, trigger_color, 1)
        
    def _update_info_labels(self):
        if self.frequency > 1000:
            freq_str = f"{self.frequency/1000:.2f} kHz"
        else:
            freq_str = f"{self.frequency:.1f} Hz"
        
        self.freq_label.set_text(f"Freq: {freq_str}")
        self.vpp_label.set_text(f"Vpp: {self.voltage_pp:.2f} V")
        
    def process(self):
        self._acquire_waveform()
