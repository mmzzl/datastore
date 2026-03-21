import machine
import rp2
import math

@rp2.asm_pio(
    sideset_init=rp2.PIO.OUT_LOW,
    out_shiftdir=rp2.PIO.SHIFT_LEFT,
    autopull=True,
    pull_thresh=8
)
def square_wave():
    out(pins, 8) .side(0)
    out(pins, 8) .side(1)

@rp2.asm_pio(
    sideset_init=rp2.PIO.OUT_LOW,
    out_shiftdir=rp2.PIO.SHIFT_LEFT,
    autopull=True,
    pull_thresh=8
)
def sine_wave():
    out(pins, 8) .side(0)

class TestSignalGenerator:
    def __init__(self, output_pin, frequency=1000):
        """
        初始化测试信号生成器
        
        Args:
            output_pin: 输出引脚
            frequency: 初始频率 (Hz)
        """
        self.output_pin = output_pin
        self.frequency = frequency
        self.amplitude = 128
        self.offset = 128
        self.waveform_type = 'sine'
        self.is_running = False
        
        self.sm = None
        self._init_state_machine()
        
    def _init_state_machine(self):
        """初始化PIO状态机"""
        self.sm = rp2.StateMachine(
            1,
            freq=1000000,
            sideset_base=self.output_pin,
            out_base=self.output_pin
        )
        
    def set_frequency(self, frequency):
        """
        设置输出频率
        
        Args:
            frequency: 频率 (Hz)
        """
        self.frequency = max(1, min(100000, frequency))
        
    def set_amplitude(self, amplitude):
        """
        设置幅度
        
        Args:
            amplitude: 幅度 (0-128)
        """
        self.amplitude = max(0, min(128, amplitude))
        
    def set_offset(self, offset):
        """
        设置直流偏置
        
        Args:
            offset: 偏置 (0-255)
        """
        self.offset = max(0, min(255, offset))
        
    def set_waveform_type(self, waveform_type):
        """
        设置波形类型
        
        Args:
            waveform_type: 波形类型 ('sine', 'square', 'triangle', 'sawtooth')
        """
        if waveform_type in ['sine', 'square', 'triangle', 'sawtooth']:
            self.waveform_type = waveform_type
            
    def start(self):
        """开始输出测试信号"""
        if self.is_running:
            return
            
        self.is_running = True
        
        if self.waveform_type == 'square':
            self.sm.active(0)
            self.sm = rp2.StateMachine(
                1,
                prog=square_wave,
                freq=self.frequency * 2,
                sideset_base=self.output_pin,
                out_base=self.output_pin
            )
            self.sm.active(1)
        else:
            self.sm.active(0)
            self.sm = rp2.StateMachine(
                1,
                prog=sine_wave,
                freq=self.frequency * 256,
                sideset_base=self.output_pin,
                out_base=self.output_pin
            )
            self.sm.active(1)
            
    def stop(self):
        """停止输出测试信号"""
        if self.sm:
            self.sm.active(0)
        self.is_running = False
        
    def get_sample(self, phase):
        """
        获取指定相位的采样值
        
        Args:
            phase: 相位 (0-2π)
            
        Returns:
            int: 采样值 (0-255)
        """
        if self.waveform_type == 'sine':
            value = self.offset + self.amplitude * math.sin(phase)
        elif self.waveform_type == 'square':
            value = self.offset + self.amplitude if math.sin(phase) >= 0 else self.offset - self.amplitude
        elif self.waveform_type == 'triangle':
            value = self.offset + self.amplitude * (2 / math.pi) * math.asin(math.sin(phase))
        elif self.waveform_type == 'sawtooth':
            value = self.offset + self.amplitude * (2 / math.pi) * math.atan(math.tan(phase / 2))
        else:
            value = self.offset
            
        return int(max(0, min(255, value)))
        
    def generate_buffer(self, buffer, sample_rate):
        """
        生成测试信号缓冲区
        
        Args:
            buffer: 输出缓冲区
            sample_rate: 采样率
        """
        samples_per_cycle = sample_rate / self.frequency
        phase_step = 2 * math.pi / samples_per_cycle
        phase = 0
        
        for i in range(len(buffer)):
            buffer[i] = self.get_sample(phase)
            phase += phase_step
            if phase >= 2 * math.pi:
                phase -= 2 * math.pi

def test_signal_generator():
    """测试信号生成器"""
    print("=== 测试信号生成器测试 ===")
    
    output_pin = machine.Pin(2, machine.Pin.OUT)
    generator = TestSignalGenerator(output_pin, frequency=1000)
    
    print(f"✓ 信号生成器初始化成功")
    print(f"  频率: {generator.frequency} Hz")
    print(f"  幅度: {generator.amplitude}")
    print(f"  偏置: {generator.offset}")
    print(f"  波形类型: {generator.waveform_type}")
    
    print("\n测试生成缓冲区...")
    test_buffer = bytearray(256)
    generator.generate_buffer(test_buffer, 100000)
    print(f"✓ 生成缓冲区完成")
    print(f"  前10个采样值: {list(test_buffer[:10])}")
    
    print("\n测试不同波形类型...")
    waveforms = ['sine', 'square', 'triangle', 'sawtooth']
    for waveform in waveforms:
        generator.set_waveform_type(waveform)
        generator.generate_buffer(test_buffer, 100000)
        print(f"  {waveform}: min={min(test_buffer)}, max={max(test_buffer)}")
    
    print("✓ 测试完成")

if __name__ == "__main__":
    test_signal_generator()
