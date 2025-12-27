import lvgl as lv

context = []
widgets = {}

style = lv.style_t()
style.init()
style.set_pad_all( 2 )
style.set_pad_gap( 2 ) 
style.set_radius( 5 )
style.set_border_width( 0 )
style.set_bg_color( lv.color_hex(0xF9EE19))


def set_context( ctx ):
    global context
    context = ctx

def get_context():
    global context
    return context

def set_widgets( wgts ):
    global widgets
    widgets = wgts

def get_widgets():
    global widgets
    return widgets


class Cont:
    def __init__( self, x=5, y=5, w=320, h=240):
        self.obj = lv.obj( context[-1] )
        self.obj.add_style( style, 0 )
        #self.obj.set_flex_flow( lv.FLEX_FLOW.COLUMN )
        self.obj.set_pos( x, y )
        self.obj.set_size( w, h )
        #if( len( context ) == 3 ):
        self.obj.set_style_border_width( 0, 0 )
    
    def __enter__( self ):
        context.append( self.obj )
        return self.obj
    
    def __exit__( self, a, b, c ):
        context.pop()

class Column:
    def __init__( self ):
        self.obj = lv.obj( context[-1] )
        self.obj.add_style( style, 0 )
        self.obj.set_flex_flow( lv.FLEX_FLOW.COLUMN )
        if( len( context ) == 3 ):
            self.obj.set_style_border_width( 2, 0 )
    
    def __enter__( self ):
        context.append( self.obj )
        return self.obj
    
    def __exit__( self, a, b, c ):
        self.obj.set_size(lv.SIZE_CONTENT, lv.SIZE_CONTENT)
        context.pop()

class Row:
    def __init__( self ):
        self.obj = lv.obj( context[-1] )
        self.obj.add_style( style, 0 )
        self.obj.set_flex_flow( lv.FLEX_FLOW.ROW )
        if( len( context ) == 3 ):
            self.obj.set_style_border_width( 2, 0 )
    
    def __enter__( self ):
        context.append( self.obj )
        return self.obj
    
    def __exit__( self, a, b, c ):
        self.obj.set_size(lv.SIZE_CONTENT, lv.SIZE_CONTENT)
        context.pop()

def add_button( name, w=40, h=20, radius=5, checkable=False ):
    btn = lv.button( context[-1] )
    btn.set_size( w, h )
    btn.set_style_radius( radius, 0 )
    btn.set_style_border_width( 1, 0 )
    btn.set_style_border_color( lv.palette_darken( lv.PALETTE.BLUE_GREY, 2 ), 0 )
    btn.set_style_bg_color( lv.palette_lighten( lv.PALETTE.BLUE_GREY, 2 ), 0 )
    btn.set_style_bg_color( lv.palette_main( lv.PALETTE.GREEN ), 1 )
    if( checkable ):
        btn.add_flag( lv.obj.FLAG.CHECKABLE )
    lbl = lv.label( btn )
    lbl.set_text( name.split("#")[0] )
    lbl.center()
    assert name not in widgets
    widgets[ name ] = btn
    return btn

def add_spinbox( name, w=100, h=40 ):
    spinbox = lv.spinbox( context[-1] )
    spinbox.set_range( 0, 1_000_000_000 )
    spinbox.set_digit_format( 9, 0 )
    spinbox.set_size( w, h )
    #lbl.set_style_border_width( 1, 0 )
    assert name not in widgets
    widgets[ name ] = spinbox
    return spinbox

def add_label( name, text=None, w=40, h=20 ):
    lbl = lv.label( context[-1] )
    if text is None:
        lbl.set_text( name.split("#")[0] )
    else:
        lbl.set_text( text )
    lbl.set_size( w, h )
    assert name not in widgets
    widgets[ name ] = lbl
    return lbl

def add_line( x=0, y=0, w=40, h=1, width=1 ):
    line = lv.line( context[-1] )
    line.set_points( [{"x":x, "y":y}, {"x":x+w-1, "y":y+h-1} ], 2 ) 
    line.set_style_line_width( width, 0 )
    #assert name not in widgets
    #widgets[ name ] = line
    return line

class WaveformDisplay:
    def __init__(self, parent, width, height, color=lv.palette_main(lv.PALETTE.BLUE)):
        self.parent = parent
        self.width = width
        self.height = height
        self.color = color
        self.data = []
        self.scale = 1.0
        self.offset = 0
        
        # 创建画布
        self.canvas = lv.canvas(parent)
        self.canvas.set_size(width, height)
        
        # 创建缓冲区
        buf_size = width * height
        self.buffer = bytearray(buf_size * lv.COLOR_FORMAT.NATIVE.size)
        self.canvas.set_buffer(self.buffer, width, height, lv.COLOR_FORMAT.NATIVE)
        
        # 初始化画布
        self.clear()
    
    def clear(self):
        """清空画布"""
        self.canvas.fill_bg(lv.color_hex(0x000000), lv.OPA.COVER)
        
        # 绘制坐标轴
        self._draw_axes()
    
    def _draw_axes(self):
        """绘制坐标轴"""
        # 绘制中心线
        line_x0 = 0
        line_y0 = self.height // 2
        line_x1 = self.width
        line_y1 = self.height // 2
        self.canvas.draw_line(line_x0, line_y0, line_x1, line_y1, lv.color_hex(0x333333), 1)
        
        # 绘制垂直刻度线
        for i in range(0, self.width, 20):
            self.canvas.draw_line(i, line_y0 - 5, i, line_y0 + 5, lv.color_hex(0x333333), 1)
    
    def set_data(self, data):
        """设置波形数据"""
        self.data = data
    
    def set_scale(self, scale):
        """设置波形缩放比例"""
        self.scale = scale
    
    def set_offset(self, offset):
        """设置波形偏移"""
        self.offset = offset
    
    def draw_waveform(self):
        """绘制波形"""
        self.clear()
        
        if not self.data or len(self.data) < 2:
            return
        
        # 计算波形数据
        points = []
        data_len = len(self.data)
        
        # 只绘制可见范围内的数据点
        for i in range(min(data_len, self.width)):
            if i < data_len:
                # 归一化数据到0-255范围
                val = self.data[i]
                # 映射到画布高度范围
                y = int((val / 255) * self.height * self.scale + self.height // 2 - (self.height * self.scale) // 2 + self.offset)
                # 确保y在画布范围内
                y = max(0, min(y, self.height - 1))
                points.append((i, y))
        
        # 绘制波形
        if len(points) > 1:
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                self.canvas.draw_line(x1, y1, x2, y2, self.color, 1)
    
    def get_widget(self):
        """获取底层widget"""
        return self.canvas
    
    def set_pos(self, x, y):
        """设置位置"""
        self.canvas.set_pos(x, y)
    
    def set_size(self, width, height):
        """设置大小"""
        self.width = width
        self.height = height
        self.canvas.set_size(width, height)
        
        # 重新创建缓冲区
        buf_size = width * height
        self.buffer = bytearray(buf_size * lv.COLOR_FORMAT.NATIVE.size)
        self.canvas.set_buffer(self.buffer, width, height, lv.COLOR_FORMAT.NATIVE)
        
        self.clear()

def add_waveform_display(name, width, height):
    """添加波形显示组件"""
    wf = WaveformDisplay(context[-1], width, height)
    assert name not in widgets
    widgets[name] = wf
    return wf

print("done")