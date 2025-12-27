import machine
import rp2
import uctypes
from hal.dma import DMA

class Adc9288:
    """AD9288 8位 100MSPS ADC驱动程序
    
    特性:
    - 使用PIO进行高速并行采样
    - 使用DMA进行数据传输
    - 支持触发功能
    - 可配置采样率
    """
    
    def __init__(self, sample_rate, sck_pin, db_pins, pio_sm=0, dma_channel=1):
        """初始化AD9288驱动
        
        Args:
            sample_rate: 采样率 (Hz)
            sck_pin: 采样时钟引脚
            db_pins: 数据引脚列表 [DB0, DB1, ..., DB7]
            pio_sm: PIO状态机编号
            dma_channel: DMA通道编号
        """
        self.sample_rate = sample_rate
        self.sck_pin = sck_pin
        self.db_pins = db_pins
        self.pio_sm = pio_sm
        self.dma_channel = dma_channel
        
        self.trigger_enabled = False
        self.trigger_level = 128
        self.trigger_edge = 'rising'
        
        self.sm = None
        self.dma = None
        self._init_pio()
        self._init_dma()
        
    def _init_pio(self):
        """初始化PIO状态机"""
        @rp2.asm_pio(
            sideset_init=rp2.PIO.OUT_LOW,
            out_shiftdir=rp2.PIO.SHIFT_LEFT,
            in_shiftdir=rp2.PIO.SHIFT_RIGHT,
            autopush=True,
            push_thresh=8
        )
        def ad9288_capture():
            """AD9288数据捕获PIO程序"""
            label("capture_loop")
            mov(pins, null)          .side(0)
            mov(x, osr)              .side(0)
            label("delay_loop")
            jmp(x_dec, "delay_loop") .side(0)
            in_(pins, 8)             .side(1)
            jmp("capture_loop")      .side(0)
        
        self.sm = rp2.StateMachine(self.pio_sm, ad9288_capture, freq=self.sample_rate * 2,
                                  sideset_base=self.sck_pin, in_base=self.db_pins[0])
        
    def _init_dma(self):
        """初始化DMA"""
        self.dma = DMA(self.dma_channel)
        
    def set_sample_rate(self, sample_rate):
        """设置采样率
        
        Args:
            sample_rate: 采样率 (Hz)
        """
        self.sample_rate = sample_rate
        self.sm.active(False)
        self.sm = rp2.StateMachine(self.pio_sm, self.sm.program, freq=self.sample_rate * 2,
                                  sideset_base=self.sck_pin, in_base=self.db_pins[0])
        
    def dma_config(self, buf, count):
        """配置DMA传输
        
        Args:
            buf: 目标缓冲区
            count: 传输字节数
        """
        buf_addr = uctypes.addressof(buf)
        rx_fifo_addr = 0x50200010 + self.pio_sm * 0x20
        
        self.dma.config(
            src_addr=rx_fifo_addr,
            dst_addr=buf_addr,
            count=count,
            src_inc=False,
            dst_inc=True,
            trig_dreq=DMA.DREQ_PIO0_RX0 + self.pio_sm,
            ring_sel=False,
            ring_size_pow2=0
        )
        
    def read(self, buf, dma_config=True):
        """读取ADC数据
        
        Args:
            buf: 目标缓冲区
            dma_config: 是否配置DMA
            
        Returns:
            读取的数据缓冲区
        """
        if dma_config:
            self.dma_config(buf, len(buf))
        
        self.dma.enable()
        self.sm.active(1)
        
        while self.dma.is_busy():
            pass
        
        self.sm.active(False)
        self.dma.disable()
        
        return buf
        
    def read_triggered(self, buf, dma_config=True):
        """带触发的采样
        
        Args:
            buf: 目标缓冲区
            dma_config: 是否配置DMA
            
        Returns:
            读取的数据缓冲区
        """
        if not self.trigger_enabled:
            return self.read(buf, dma_config)
        
        if dma_config:
            self.dma_config(buf, len(buf))
        
        self.dma.enable()
        self.sm.active(1)
        
        while self.dma.is_busy():
            pass
        
        self.sm.active(False)
        self.dma.disable()
        
        if self._find_trigger_point(buf):
            pass
        
        return buf
        
    def _find_trigger_point(self, buf):
        """在缓冲区中查找触发点
        
        Args:
            buf: 数据缓冲区
            
        Returns:
            是否找到触发点
        """
        if len(buf) < 2:
            return False
        
        for i in range(1, len(buf) // 2):
            prev_val = buf[i - 1]
            curr_val = buf[i]
            
            if self.trigger_edge == 'rising':
                if prev_val <= self.trigger_level and curr_val > self.trigger_level:
                    return True
            else:
                if prev_val >= self.trigger_level and curr_val < self.trigger_level:
                    return True
        
        return False
        
    def set_trigger_level(self, level):
        """设置触发级别
        
        Args:
            level: 触发级别 (0-255)
        """
        self.trigger_level = max(0, min(255, level))
        
    def set_trigger_enabled(self, enabled):
        """启用或禁用触发
        
        Args:
            enabled: 是否启用触发
        """
        self.trigger_enabled = enabled
        
    def set_trigger_edge(self, edge):
        """设置触发边沿
        
        Args:
            edge: 触发边沿 ('rising' 或 'falling')
        """
        if edge in ['rising', 'falling']:
            self.trigger_edge = edge
            
    def start(self):
        """启动采样"""
        self.sm.active(1)
        
    def stop(self):
        """停止采样"""
        self.sm.active(0)
        
    def is_running(self):
        """检查是否正在采样
        
        Returns:
            是否正在采样
        """
        return self.sm.active() == 1
        
    def get_sample_rate(self):
        """获取当前采样率
        
        Returns:
            采样率 (Hz)
        """
        return self.sample_rate
