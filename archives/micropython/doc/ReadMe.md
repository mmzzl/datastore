# rp2040 固件编译

# liunx 环境准备

sudo apt install build-essential cmake git libnewlib-arm-none-eabi gcc-arm-none-eabi python3 python3-pip
apt install python3.12-venv
python3 -m venv /home/fantom/venv
pip3 install pycparser



https://github.com/pbrier/rp2040-mp-round-lcd

https://github.com/lvgl/lv\_micropython.git

git clone https://github.com/lvgl/lv\_micropython.git
cd lv\_micropython

# 所有的子模块都更新一下

git submodule update --init --recursive
git submodule update --init --recursive lib/lv_bindings lib/pico-sdk lib/mbedtls lib/tinyusb

clash-verge
# 编译rp2

make -C ports/rp2 BOARD=RPI_PICO submodules

make -C ports/rp2 BOARD=PICO submodules

make -j10 -C mpy-cross CFLAGS="-Wno-error=dangling-pointer" 
make -j4 -C mpy-cross CFLAGS="-Wno-error=enum-int-mismatch"
make -C ports/rp2 LVGL_CFLAGS="-DLV_USE_ST7735=1"

修改python环境

export PYTHON\_EXECUTABLE=$(which python3)

cmake -S . -B build-RPI\_PICO -DPython3\_EXECUTABLE=$(which python3)
sudo make -j -C ports/rp2 BOARD=RPI\_PICO USER\_C\_MODULES=../../user\_modules/lv\_binding\_micropython/bindings.cmake

make -j4 -C ports/rp2 BOARD=PICO USER_C_MODULES=../../lib/lv_bindings/bindings.cmake CFLAGS="-Wno-error=array-bounds -Wno-error=enum-int-mismatch -Wno-error=dangling-pointer" MICROPY_PY_RP2=1 

make -j4 -C ports/rp2 BOARD=PICO USER_C_MODULES=../../lib/lv_bindings/bindings.cmake CFLAGS="-Wno-error=array-bounds -Wno-error=enum-int-mismatch -Wno-error=dangling-pointer" MICROPY_PY_RP2=1

sudo make -j10 -C ports/rp2 BOARD=RPI\_PICO USER\_C\_MODULES=../../user\_modules/lv\_binding\_micropython/bindings.cmake V=1 Python3\_EXECUTABLE=/home/fantom/bin/python3


export Python3_EXECUTABLE=/home/fantom/bin/python3
make -j1 -C ports/rp2 BOARD=RPI_PICO USER_C_MODULES=../../user_modules/lv_binding_micropython/bindings.cmake V=1 2>&1 | grep -A5 -B5 "Error 127"

make -j100 -C ports/rp2 BOARD=RPI\_PICO USER\_C\_MODULES=../../user\_modules/lv\_binding\_micropython/bindings.cmake V=1



vscode 插件市场下载
https://marketplace.visualstudio.com/\_apis/public/gallery/publishers/{fieldA}/vsextensions/{fieldB}/{version}/vspackage

https://marketplace.visualstudio.com/\_apis/public/gallery/publishers/RT-Thread/vsextensions/rt-thread-micropython/1.0.11/vspackage
from test\_st7735 import test\_st7735\_comprehensive



\# 查看lvgl 版本

print("LVGL version: {}.{}.{}".format(lv.version\_major(), lv.version\_minor(), lv.version\_patch()))



\# rp2040 修改rom 为16M

1. 修改 ports/rp2/rp2\_flash.c

```

&nbsp;	// #define MICROPY\_HW\_FLASH\_STORAGE\_BYTES (1408 \* 1024)

&nbsp;	#define MICROPY\_HW\_FLASH\_STORAGE\_BYTES (15 \* 1024 \* 1024)

```

2\. 修改mpconfigboard.h 文件， ports/rp2/boards/PICO/mpconfigboard.h

```

\#define MICROPY\_HW\_FLASH\_STORAGE\_BYTES          (15 \* 1024 \* 1024)

```

3\. 修改pico.h 文件， lib/pico-sdk/src/boards/include/boards/pico.h

```

// #define PICO\_FLASH\_SIZE\_BYTES (2 \* 1024 \* 1024)

\#define PICO\_FLASH\_SIZE\_BYTES (16 \* 1024 \* 1024)

```



v18 micropython 源码报错修复 

1. ../py/stackctrl.c

```
void mp_stack_ctrl_init(void) {
    #if __GNUC__ >= 13
    #pragma GCC diagnostic push
    #pragma GCC diagnostic ignored "-Wdangling-pointer"
    #endif
    volatile int stack_dummy;
    MP_STATE_THREAD(stack_top) = (char *)&stack_dummy;
    #if __GNUC__ >= 13
    #pragma GCC diagnostic pop
    #endif
}
```

&nbsp;2.  mpy-cross/main.c

```

//334 行 uint 改成 mp_import_stat_t

```

### lvgl 改为rgb565




