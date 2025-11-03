import time
import machine 
import rp2
import uctypes
from hal.dma import DMA 

@rp2.asm_pio(
    sideset_init =(rp2.PIO.OUT_HIGH, rp2.PIO.OUT_HIGH),
    in_shiftdir  = rp2.PIO.SHIFT_LEFT,
)
def build_sm_adc9288():
    in_( pins, 8 ) .side( 0b0 )
    push( block )  .side( 0b1 )


class Adc9288:
    PIO0_BASE = 0x50200000
    PIO0_BASE_TXF0 = PIO0_BASE + 0x10
    PIO0_BASE_RXF0 = PIO0_BASE + 0x20
    def __init__( self, sps, sck, db):
        self.db = db 
        self.sck = sck 
        self.sm = rp2.StateMachine( 
            0, 
            prog = build_sm_adc9288,
            freq = 2 * sps,
            sideset_base = self.sck,
            in_base = self.db
        )
        self.dma = DMA( 1 )
    
    def dma_config(self, buf, count, ring_size_pow2 = 0):
        self.dma.config(
            Adc9288.PIO0_BASE_RXF0,
            uctypes.addressof( buf ),
            count,
            src_inc=False,
            dst_inc=True,
            trig_dreq=DMA.DREQ_PIO0_RX0,
            ring_sel=True,
            ring_size_pow2=ring_size_pow2
        )
    
    def read(self, buf, dma_config=True):
        if (dma_config):
            self.dma_config(buf, len(buf))
        self.dma.enable()
        self.sm.active(1)
        while(self.dma.is_busy()):
            pass
        self.sm.active(False)
        self.dma.disable()

def test_adc9288():
    db = machine.Pin(0, machine.Pin.IN)
    sck = machine.Pin(21, machine.Pin.OUT)
    buf = bytearray(10_000)
    adc = Adc9288(1_000_000, sck, db)
    t0 = time.ticks_us()
    adc.read(buf)
    t1 = time.ticks_us()
    print("buf", buf[0:10], "...")
    print("Read speed [B/s]:", len(buf)/((t1 - t0) / 1e-6))
    print("@CPU freq:", machine.freq())
