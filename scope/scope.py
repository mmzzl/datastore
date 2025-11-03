import os
import time
import machine
import rp2
import array
import uctypes

import lvgl as lv
from gui.dear_lvgl import *
from gui.display_driver_utils import Display_Driver

# 缩放系数
SCALE = 0.4

def scale(v):
    return int(v * SCALE)

class Scope:
    def __init__(self, parent, display_driver: Display_Driver):
        self.display_driver = display_driver
        self.widgets = {}
        self.context = []
        self.build_ui(parent)
    
    def process( self ):
        pass

    def build_ui( self, parent ):
        width = scale(160)    
        self.context.append( parent )
        set_context( self.context )
        set_widgets( self.widgets )
        with Cont():
            with Cont( 0, 0, 320-50, 240-15):
                with Column():
                    lblw= 74 - 15
                    with Row():
                        add_label( "#Status", w=lblw )
                        add_label( "#lHS", w=lblw ).set_text( "1 S/D" )
                        add_label( "#lHP", w=lblw ).set_text( "0 S" )
                        add_label( "#lTP", w=lblw ).set_text( "0 V" )
                    self.chart = lv.chart( self.context[-1] )
                    self.chart.set_size( 320-50-14, 240-5-50-11)
                    #self.chart.set_style_bg_color( lv.palette_main( 0 ), 0 )
                    self.chart.set_div_line_count( 8, 10 )
                    with Row():
                        add_label( "#lVS1", w=lblw ).set_text( "1 V/D" )
                        add_label( "#lVP1", w=lblw ).set_text( "0 V" )
                        add_label( "#lVS2", w=lblw ).set_text( "1 V/D" )
                        add_label( "#lVP2", w=lblw ).set_text( "0 V" )