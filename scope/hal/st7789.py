import time
import machine
import uctypes
from hal.dma import DMA

class ST7789:
    """ST7789显示屏驱动"""
    
    # ST7789命令定义
    NOP = 0x00
    SWRESET = 0x01
    RDDID = 0x04
    RDDST = 0x09
    SLPIN = 0x10
    SLPOUT = 0x11
    PTLON = 0x12
    NORON = 0x13
    INVOFF = 0x20
    INVON = 0x21
    GAMSET = 0x26
    DISPOFF = 0x28
    DISPON = 0x29
    CASET = 0x2A
    RASET = 0x2B
    RAMWR = 0x2C
    RAMRD = 0x2E
    PTLAR = 0x30
    VSCRDEF = 0x33
    TEOFF = 0x34
    TEON = 0x35
    MADCTL = 0x36
    VSCSAD = 0x37
    IDMOFF = 0x38
    IDMON = 0x39
    COLMOD = 0x3A
    RAMWRC = 0x3C
    RAMRDC = 0x3E
    TESCAN = 0x44
    RDTE = 0x45
    WRDISBV = 0x51
    RDDISBV = 0x52
    WRCTRLD = 0x53
    RDCTRLD = 0x54
    WRCACE = 0x55
    RDCABC = 0x56
    WRCABCMB = 0x5E
    RDCABCMB = 0x5F
    RDABCSDR = 0x68
    RDID1 = 0xDA
    RDID2 = 0xDB
    RDID3 = 0xDC
    
    # 屏幕参数 - ST7789标准分辨率为240×320
    LCD_WIDTH = 240
    LCD_HEIGHT = 320
    
    def __init__(self, baudrate, cs, sck, mosi, miso, dc, rst, bl, 
                 rotation=0, x_offset=0, y_offset=0):
        """
        初始化ST7789驱动
        
        Args:
            baudrate: SPI波特率
            cs: 片选引脚
            sck: 时钟引脚
            mosi: 主出从入引脚
            miso: 主入从出引脚
            dc: 数据/命令选择引脚
            rst: 复位引脚
            bl: 背光引脚
            rotation: 屏幕旋转 (0-3)
            x_offset: X轴偏移
            y_offset: Y轴偏移
        """
        self.buf1 = bytearray(1)
        self.buf2 = bytearray(2)
        self.buf4 = bytearray(4)
        
        self.baudrate = baudrate
        self.cs = cs
        self.sck = sck
        self.mosi = mosi
        self.miso = miso
        self.dc = dc
        self.rst = rst
        self.bl = bl
        self.rotation = rotation
        self.x_offset = x_offset
        self.y_offset = y_offset
        
        # 设置分辨率 - ST7789标准分辨率为240×320
        self.width = self.LCD_WIDTH
        self.height = self.LCD_HEIGHT
        
        # 初始化引脚
        self.cs.value(1)
        self.dc.value(1)
        if self.rst:
            self.rst.value(1)
        if self.bl:
            self.bl.value(0)  # 默认关闭背光
        
        # 初始化SPI和DMA
        self.spi_init()
        self.dma = DMA(0)
        
        # 配置显示屏
        self.config()
    
    def _set_rotation(self, rotation):
        """设置屏幕旋转方向"""
        self.rotation = rotation % 4
        
        # MADCTL寄存器配置
        madctl = 0x00
        
        if self.rotation == 0:  # 纵向
            madctl = 0x00
        elif self.rotation == 1:  # 横向（右转90度）
            madctl = 0x60
        elif self.rotation == 2:  # 纵向（翻转）
            madctl = 0xC0
        elif self.rotation == 3:  # 横向（左转90度）
            madctl = 0xA0
        
        # 设置RGB顺序 (0x08 BGR顺序, 0x00 RGB顺序)
        madctl |= 0x00  # RGB顺序
        
        self._write_cmd_data(self.MADCTL, madctl)
        
        # 根据旋转方向调整宽高
        if self.rotation in [1, 3]:
            self.width, self.height = self.height, self.width
    
    def _write_cmd(self, cmd):
        """写入命令"""
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytearray([cmd]))
        self.cs.value(1)
    
    def _write_data(self, data):
        """写入数据"""
        self.dc.value(1)
        self.cs.value(0)
        if isinstance(data, int):
            self.spi.write(bytearray([data]))
        else:
            self.spi.write(data)
        self.cs.value(1)
    
    def _write_cmd_data(self, cmd, data):
        """写入命令和数据"""
        self._write_cmd(cmd)
        self._write_data(data)
    
    def _write_cmd_data_list(self, cmd, data_list):
        """写入命令和数据列表"""
        self._write_cmd(cmd)
        for data in data_list:
            self._write_data(data)

    def spi_init(self):
        """初始化SPI"""
        try:
            if self.miso is not None:
                self.spi = machine.SPI(
                    1,
                    baudrate=self.baudrate,
                    polarity=0,
                    phase=0,
                    bits=8,
                    sck=self.sck,
                    mosi=self.mosi,
                    miso=self.miso
                )
            else:
                self.spi = machine.SPI(
                    1,
                    baudrate=self.baudrate,
                    polarity=0,
                    phase=0,
                    bits=8,
                    sck=self.sck,
                    mosi=self.mosi
                )
            print("✓ SPI初始化成功")
        except Exception as e:
            print(f"✗ SPI初始化失败: {e}")
            raise e
    
    def reset(self):
        """硬件复位"""
        if self.rst:
            self.rst.value(0)
            time.sleep_ms(10)
            self.rst.value(1)
            time.sleep_ms(120)
    
    def config(self):
        """配置ST7789显示屏"""
        print("配置ST7789显示屏...")
        
        try:
            # 硬件复位
            self.reset()
            
            # 软件复位
            self._write_cmd(self.SWRESET)
            time.sleep_ms(150)
            
            # 退出睡眠模式
            self._write_cmd(self.SLPOUT)
            time.sleep_ms(120)
            
            # 设置颜色模式为16位RGB565 <mcreference link="https://wenku.csdn.net/answer/4h8ky7sf9q" index="2">2</mcreference>
            self._write_cmd_data(self.COLMOD, 0x05)  # 16-bit/pixel RGB565格式
            time.sleep_ms(10)
            
            # 设置内存访问控制
            self._set_rotation(self.rotation)
            
            # 设置显示反转
            self._write_cmd(self.INVOFF)  # 关闭显示反转
            time.sleep_ms(10)
            
            # 设置正常显示模式
            self._write_cmd(self.NORON)
            time.sleep_ms(10)
            
            # 开启显示
            self._write_cmd(self.DISPON)
            time.sleep_ms(120)
            
            # 开启背光
            if self.bl:
                self.bl.value(1)
            
            print("✓ ST7789配置完成")
            
        except Exception as e:
            print(f"✗ ST7789配置失败: {e}")
            raise e
    
    def _set_rotation(self, rotation):
        """设置屏幕旋转方向"""
        self.rotation = rotation % 4
        
        # MADCTL寄存器配置
        madctl = 0x00
        
        if self.rotation == 0:  # 纵向
            madctl = 0x00
        elif self.rotation == 1:  # 横向（右转90度）
            madctl = 0x60
        elif self.rotation == 2:  # 纵向（翻转）
            madctl = 0xC0
        elif self.rotation == 3:  # 横向（左转90度）
            madctl = 0xA0
        
        # 设置RGB顺序 (0x08 BGR顺序, 0x00 RGB顺序)
        madctl |= 0x00  # RGB顺序
        
        self._write_cmd_data(self.MADCTL, madctl)
        
        # 根据旋转方向调整宽高
        if self.rotation in [1, 3]:
            self.width, self.height = self.height, self.width
    
    def set_window(self, x, y, width, height):
        """设置显示窗口"""
        # 应用偏移量
        x += self.x_offset
        y += self.y_offset
        
        x_end = x + width - 1
        y_end = y + height - 1
        
        # 设置列地址
        self._write_cmd(self.CASET)
        self._write_data(bytearray([x >> 8, x & 0xFF, x_end >> 8, x_end & 0xFF]))
        
        # 设置行地址
        self._write_cmd(self.RASET)
        self._write_data(bytearray([y >> 8, y & 0xFF, y_end >> 8, y_end & 0xFF]))
    
    def write_pixel(self, x, y, color):
        """写入单个像素"""
        self.set_window(x, y, 1, 1)
        self._write_cmd(self.RAMWR)
        self._write_data(bytearray([color >> 8, color & 0xFF]))
    
    def fill_rect(self, x, y, width, height, color):
        """填充矩形区域"""
        if width <= 0 or height <= 0:
            return
            
        self.set_window(x, y, width, height)
        self._write_cmd(self.RAMWR)
        
        # 准备颜色数据
        color_high = color >> 8
        color_low = color & 0xFF
        
        # 批量写入像素数据
        total_pixels = width * height
        buffer_size = min(total_pixels, 256)  # 最大256像素的缓冲区
        buffer = bytearray(buffer_size * 2)
        
        # 填充缓冲区
        for i in range(0, buffer_size * 2, 2):
            buffer[i] = color_high
            buffer[i + 1] = color_low
        
        # 分批写入数据
        for i in range(0, total_pixels, buffer_size):
            pixels_to_write = min(buffer_size, total_pixels - i)
            if pixels_to_write < buffer_size:
                # 最后一批数据可能小于缓冲区大小
                partial_buffer = bytearray(pixels_to_write * 2)
                for j in range(0, pixels_to_write * 2, 2):
                    partial_buffer[j] = color_high
                    partial_buffer[j + 1] = color_low
                self._write_data(partial_buffer)
            else:
                self._write_data(buffer)
    
    def fill(self, color):
        """填充整个屏幕"""
        self.fill_rect(0, 0, self.width, self.height, color)
    
    def draw_bitmap(self, x, y, bitmap, width, height):
        """绘制位图"""
        self.set_window(x, y, width, height)
        self._write_cmd(self.RAMWR)
        self._write_data(bitmap)
    
    def draw_bitmap_dma(self, x, y, w, h, buf, is_blocking=True):
        """使用DMA绘制位图"""
        if w <= 0 or h <= 0:
            return
        self.set_window(x, y, w, h)
        self.write_register_dma(self.RAMWR, buf, is_blocking)
    
    def write_register_dma(self, reg, buf, is_blocking=True):
        """使用DMA写入寄存器"""
        try:
            SPI1_BASE = 0x40040000
            SSPDR = 0x008
            
            self.dma.config(
                src_addr=uctypes.addressof(buf),
                dst_addr=SPI1_BASE + SSPDR,
                count=len(buf),
                src_inc=True,
                dst_inc=False,
                trig_dreq=DMA.DREQ_SPI1_TX
            )
            
            # 发送命令
            self.buf1[0] = reg
            self.cs.value(0)
            self.dc.value(0)
            self.spi.write(self.buf1)
            
            # 发送数据 - 修正CS和DC控制逻辑 <mcreference link="https://blog.csdn.net/silent_dusbin/article/details/120992856" index="4">4</mcreference>
            self.dc.value(1)  # 先设置数据模式
            self.dma.enable()  # 然后启动DMA传输
            
            if is_blocking:
                self.wait_dma()
            
        except Exception as e:
            print(f"DMA写入错误: {e}")
            raise e
    
    def wait_dma(self):
        """等待DMA传输完成"""
        while self.dma.is_busy():
            pass
        self.dma.disable()
        self.cs.value(1)
    
    def display_on(self):
        """开启显示"""
        self._write_cmd(self.DISPON)
        if self.bl:
            self.bl.value(1)
    
    def display_off(self):
        """关闭显示"""
        if self.bl:
            self.bl.value(0)
        self._write_cmd(self.DISPOFF)
    
    def sleep_on(self):
        """进入睡眠模式"""
        self._write_cmd(self.SLPIN)
    
    def sleep_off(self):
        """退出睡眠模式"""
        self._write_cmd(self.SLPOUT)


def test_st7789():
    """测试ST7789驱动"""
    print("=== ST7789驱动测试 ===")
    
    try:
        # 引脚定义 - 根据实际硬件连接调整
        baudrate = 40_000_000  # ST7789支持更高波特率
        sck = machine.Pin(10, machine.Pin.OUT)
        mosi = machine.Pin(11, machine.Pin.OUT)
        rst = machine.Pin(12, machine.Pin.OUT)
        dc = machine.Pin(13, machine.Pin.OUT)
        cs = machine.Pin(14, machine.Pin.OUT)
        bl = machine.Pin(15, machine.Pin.OUT)
        miso = None
        # 创建ST7789实例 (240x320分辨率)
        lcd = ST7789(baudrate, cs, sck, mosi, miso, dc, rst, bl, 
                    rotation=0)
        
        print(f"✓ ST7789初始化成功 ({lcd.width}x{lcd.height})")
        
        # 测试清屏
        print("测试清屏功能...")
        colors = [0xF800, 0x07E0, 0x001F, 0xFFE0, 0xF81F, 0x0000]  # 红绿蓝黄紫黑
        color_names = ["红色", "绿色", "蓝色", "黄色", "紫色", "黑色"]
        
        for color, name in zip(colors, color_names):
            print(f"  清屏: {name}")
            lcd.fill(color)
            time.sleep_ms(500)
        
        print("✓ ST7789测试完成")
        
    except Exception as e:
        print(f"✗ ST7789测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_st7789()
    print("测试完成")