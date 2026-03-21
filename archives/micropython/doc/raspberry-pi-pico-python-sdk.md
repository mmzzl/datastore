# raspberry-pi-pico-python-sdk

## 目录

- [第 1 页](#第-1-页)
- [第 2 页](#第-2-页)
- [第 3 页](#第-3-页)
- [第 4 页](#第-4-页)
- [第 5 页](#第-5-页)
- [第 6 页](#第-6-页)
- [第 7 页](#第-7-页)
- [第 8 页](#第-8-页)
- [第 9 页](#第-9-页)
- [第 10 页](#第-10-页)
- [第 11 页](#第-11-页)
- [第 12 页](#第-12-页)
- [第 13 页](#第-13-页)
- [第 14 页](#第-14-页)
- [第 15 页](#第-15-页)
- [第 16 页](#第-16-页)
- [第 17 页](#第-17-页)
- [第 18 页](#第-18-页)
- [第 19 页](#第-19-页)
- [第 20 页](#第-20-页)
- [第 21 页](#第-21-页)
- [第 22 页](#第-22-页)
- [第 23 页](#第-23-页)
- [第 24 页](#第-24-页)
- [第 25 页](#第-25-页)
- [第 26 页](#第-26-页)
- [第 27 页](#第-27-页)
- [第 28 页](#第-28-页)
- [第 29 页](#第-29-页)
- [第 30 页](#第-30-页)
- [第 31 页](#第-31-页)
- [第 32 页](#第-32-页)
- [第 33 页](#第-33-页)
- [第 34 页](#第-34-页)
- [第 35 页](#第-35-页)
- [第 36 页](#第-36-页)
- [第 37 页](#第-37-页)
- [第 38 页](#第-38-页)
- [第 39 页](#第-39-页)
- [第 40 页](#第-40-页)
- [第 41 页](#第-41-页)
- [第 42 页](#第-42-页)
- [第 43 页](#第-43-页)
- [第 44 页](#第-44-页)
- [第 45 页](#第-45-页)
- [第 46 页](#第-46-页)
- [第 47 页](#第-47-页)
- [第 48 页](#第-48-页)
- [第 49 页](#第-49-页)
- [第 50 页](#第-50-页)
- [第 51 页](#第-51-页)
- [第 52 页](#第-52-页)
- [第 53 页](#第-53-页)
- [第 54 页](#第-54-页)

---

## 第 1 页

![第 1 页](raspberry-pi-pico-python-sdk_images\page_1.png)

microcontrollers.

---

## 第 2 页

![第 2 页](raspberry-pi-pico-python-sdk_images\page_2.png)

Raspberry Pi Pico-series Python SDK © 2020-2024 Raspberry Pi Ltd (formerly Raspberry Pi (Trading) Ltd.) This documentation is licensed under a Creative Commons Attribution-NoDerivatives 4.0 International (CC BY-ND). Throughout the text "the SDK" refers to our Raspberry Pi Pico SDK. More details about the SDK can be found in Raspberry Pi Pico-series C/C++ SDK. Source code included in the documentation is Copyright © 2020-2024 Raspberry Pj Ltd (formerly Raspberry Pi (Trading) Ltd.) and licensed under the 3-Clause BSD license. build-date: 2024-12-04 build-version: 4731426-clean Legal disclaimer notice TECHNICAL AND RELIABILITY DATA FOR RASPBERRY PI PRODUCTS (INCLUDING DATASHEETS) AS MODIFIED FROM TIME TO TIME ("RESOURCES") ARE PROVIDED BY RASPBERRY PI LTD ("RPL") "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW IN NO EVENT SHALL RPL BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THE RESOURCES, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. RPL reserves the right to make any enhancements, improvements, corrections or any other modifications to the RESOURCES or any products described in them at any time and without further notice. The RESOURCES are intended for skilled users with suitable levels of design knowledge. Users are solely responsible for their selection and use of the RESOURCES and any application of the products described in them. User agrees to indemnify and hold RPL harmless againsi all liabilities, costs, damages or other losses arising out of their use of the RESOURCES. RPL grants users permission to use the RESOURCES solely in conjunction with the Raspberry Pi products. All other use of the RESOURCES is prohibited. No licence is granted to any other RPL or other third party intellectual property righi. HIGH RISK ACTIVITIES. Raspberry Pi products are not designed, manufactured or intended for use in hazardous environments requiring fail safe performance, such as in the operation of nuclear facilities, aircraft navigation or communication systems, air traffic control, weapons systems or safety-critical applications (including life support systems and other medical devices), in which the failure of the products could lead directly to death, personal injury or severe physical or environmental damage ("High Risk Activities"). RPL specifically disclaims any express or implied warranty of fitness for High Risk Activities and accepts no liability for use or inclusions of Raspberry Pi products in High Risk Activities. Raspberry Pi products are provided subject to RPL’s Standard Terms. RPL’s provision of the RESOURCES does not expand or otherwise modify RPL’s Standard Terms including but not limited to the disclaimers and warranties expressed in them. Legal disclaimer notice 1

---

## 第 3 页

![第 3 页](raspberry-pi-pico-python-sdk_images\page_3.png)

Raspberry Pi Pico-series Python SDK it Table of contents Colophon Legal disclaimer notice 1. The MicroPython Environment 1.1. Getting MicroPython for RP-series Microcontrollers 1.2. Installing MicroPython on a Pico-series Device 1.3. Building MicroPython From Source 2. Connecting to the MicroPython REPL 2.1. Connecting from a Raspberry Pi over USB 2.2. Connecting from a Raspberry Pi using UART 2.3. Connecting from a Mac 11 2.4. Say "Hello World” 12 2.5. Blink an LED 12 2.6. What next? 12 3. The RP-series microcontroller Port 13 3.1. Blinking an LED Forever (Timer) 13 3.2. UART 14 3.3. ADC 15 3.4. 15 Interrupts 3.5. Multicore Support 16 3.6. [2C 16 3.7. SPI 17 3.8. PWM 18 3.9. 19 PIO Support 3.9.1. IRQ 21 3.9.2. WS2812 LED (NeoPixel) 23 3.9.3. UART TX 24 3.9.4. SPI 25 3.9.5. PWM 26 3.9.6. Using pioasm 27 3.10. Wireless Support 28 31 A. Using an Integrated Development Environment (IDE) 4.1. Using Thonny 31 4.1.1. Blinking the LED from Thonny 32 4.2. Using Visual Studio Code 33 4.3. Using Remote MicroPython shell (rshell) 34 35 4.3.1. Blinking the LED from rshel] Appendix A: App Notes 37 Using a SSD1306-based OLED graphics display 37 Wiring information 37 List of Files 37 Bill of Materials 39 Using a SH1106-based OLED graphics display 39 Wiring information 39 List of Files 40 Bill of Materials 45 Using PIO to drive a set of NeoPixel Ring (WS2812 LEDs) 45 Wiring information 45 List of Files 45 Bill of Materials 47 Using UART on the Raspberry Pi Pico 48 Wiring information 48 List of Files 48 Bill of Materials 49 50 Documentation Release History 15 October 2024 50 it Table of contents

---

## 第 4 页

![第 4 页](raspberry-pi-pico-python-sdk_images\page_4.png)

3

---

## 第 5 页

![第 5 页](raspberry-pi-pico-python-sdk_images\page_5.png)

Raspberry Pi Pico-series Python SDK a Chapter l. The MicroPython ENV t Python is the fastest way to get started with embedded software on Pico-series devices. This book is about the official MicroPython port for RP-series microconitroller-based boards. MicroPython is a Python 3 implementation for microcontrollers and small embedded systems. Because MicroPython is highly efficient, and RP-series microcontrollers are designed with a disproportionate amount of system memory and processing power for their price, MicroPython is a serious tool for embedded systems development, which does not compromise on approachability. For exceptionally demanding pieces of software, you can fall back on the SDK (covered in Getting started with Raspberry Pi Pico-series and Raspberry Pi Pico-series C/C++ SDK), or an external C module added to your MicroPython firmware, to wring oui the very last drop of performance. For every other project, MicroPython handles a lot of heavy lifting for you, and lets you focus on writing the code that adds value to your project. The accelerated floating point libraries in RP-series on-board ROM storage are used automatically by your Python code, so you should find arithmetic performance quite snappy. Most on-chip hardware is exposed through the standard machine module, so existing MicroPython projects can be ported without too much trouble. The second processor core is exposed through the _thread module. RP-series microcontrollers have some unique hardware you won't find on other microcontrollers, with the programmable I/O system (PIO) being the prime example of this: a versatile hardware subsystem that lets you create new I/O interfaces and run them at high speed. In the rp2 module you will find a comprehensive PIO library which lets you write new PIO programs at the MicroPython prompt, and interact with them in real time, to develop interfaces for new or unusual pieces of hardware (or indeed if you just find yourself wanting an extra few serial ports). MicroPython implements the entire Python 3.4 syntax (including exceptions, with, yield from, etc., and additionally async /await keywords from Python 3.5). The following core datatypes are provided: str (including basic Unicode support), bytes, bytearray, tuple, list, dict, set, frozenset, array.array, collections.namedtuple, classes and instances. Builtin modules include sys, time, and struct, etc. Note that only a subset of Python 3 functionality is implemented for the data types and modules. MicroPython can execute scripts in textual source form (.py files) or from precompiled bytecode, in both cases either from an on-device filesystem or "frozen" into the MicroPython executable. 1.1. Getting MicroPython for RP-series Microcontrollers Pre-built Binary A pre-built binary of the latest MicroPython firmware is available from the MicroPython section of the documentation. The fastest way to get MicroPython is to download the pre-built release binary from the Documentation pages. If you can't or don’t want to use the pre-built release — for example, if you want to develop a C module for MicroPython — you can follow the instructions in Section 1.3 to get the source code for MicroPython, which you can use to build your own MicroPython firmware binary. 1.1. Getting MicroPython for RP-series Microcontrollers 4

---

## 第 6 页

![第 6 页](raspberry-pi-pico-python-sdk_images\page_6.png)

Raspberry Pi Pico-series Python SDK 1.2. Installing MicroPython on a Pico-series Device Pico-series devices have a BOOTSEL mode for programming firmware over the USB port. Holding the BOOTSEL button when powering up your board will put it into a special mode where it appears as a USB Mass Storage Device. First make sure your Pico-series device is not plugged into any source of power: disconnect the micro USB cable if plugged in, and disconnect any other wires that might be providing power to the board, e.g. through the VSYS or VBUS pin. Now hold down the BOOTSEL button, and plug in the micro USB cable (which hopefully has the other end plugged into your computer). A drive called RPFL-RP2 should pop up. Go ahead and drag the MicroPython firmware.uf2 file onto this drive. This programs the MicroPython firmware onto the flash memory on your Pico-series device. It should take a few seconds to program the UF2 file into the flash. The board will automatically reboot when finished, causing the RPI-RP2 drive to disappear, and boot into MicroPython. By default, MicroPython doesn’t do anything when it first boots. lt sits and waits for you to type in further instructions. Chapter 2 shows how you can connect with the MicroPython firmware now running on your board. You can read on to see how a custom MicroPython firmware file can be built from the source code. The Getting started with Raspberry Pi Pico-series book has detailed instructions on getting your Pico-series device into BOOTSEL mode and loading UF2 files, in case you are having trouble. There is also a section going over loading ELF files with the debugger, in case your board doesn't have an easy way of entering BOOTSEL, or you would like to debug a MicroPython C module you are developing. NOTE If you are not following these instructions on a Pico-series device, you may not have a BOOTSEL button. If this is the case, you should check if there is some other way of grounding the flash CS pin, such as a jumper, to tell the RP- series microcontroller to enter the BOOTSEL mode on boot. If there is no such method, you can load code using the Serial Wire Debug interface. 1.3. Building MicroPython From Source The prebuilt binary which can be downloaded from the MicroPython section of the documentation should serve most use cases, but you can build your own MicroPython firmware from source if you'd like to customise its low-level aspects. 2 TIP If you have already downloaded and installed a prebuilt MicroPython UF2 file, you can skip ahead to Chapter 2 to start using your board. IMPORTANT These instructions for getting and building MicroPython assume you are using Raspberry Pi OS running on a Raspberry Pi 4, or an equivalent Debian-based Linux distribution running on another platform. It's a good idea to create a pico directory to keep all pico-related checkouts in. These instructions create a pico directory at /home/pi/pico. $ cd ~/ S$ mkdir pico S$ ed pico Then clone the micropython git repository. These instructions will fetch the latest version of the source code. 1.2. Installing MicroPython on a Pico-series Device 5

---

## 第 7 页

![第 7 页](raspberry-pi-pico-python-sdk_images\page_7.png)

Raspberry Pi Pico-series Python SDK $ git clone https://github.com/micropython/micropython.git --branch master Once the download has finished, the source code for MicroPython should be in a new directory called micropython. The MicroPython repository also contains pointers (submodules) to specific versions of libraries it needs to run on a particular board, like the SDK in the case of RP-series microcontroller. We need to fetch these submodules too: $ ed micropython $ make -C ports/rp2 submodules NOTE The following instructions assume that you are using a Pico-series device. Some details may differ if you are building firmware for a different RP-series microconiroller-based board. The board vendor should detail any extra steps needed to build firmware for that particular board. The version we're building here is fairly generic, but there might be some differences like putting the default serial port on different pins, or including extra modules to drive that board’s hardware. To build the RP-series microcontroller MicroPython port, you'll need to install some extra tools. To build projects you'll need CMake, a cross-platform tool used to build the software, and the GNU Embedded Toolchain for Arm, which turns MicroPython’s C source code into a binary program RP-series microcontrollers’ processors can understand. build- essential is a bundle of tools you need to build code native to your own machine — this is needed for some internal tools in MicroPython and the SDK. You can install all of these via apt from the command line. Anything you already have installed will be ignored by apt. sudo apt update §$ sudo apt install cmake gcc-arm-none-eabi libnewlib-arm-none-eabi build-essential First we need to bootstrap a special tool for MicroPython builds, that ships with the source code: §$ make -C mpy-cross We can now build the port we need for RP-series microconiroller, that is, the version of MicroPython that has specific support for Raspberry Pi chips. $ cd ports/rp2 $ make If everything went well, there will be a new directory called build-PICO (ports/rp2/build-PIc0 relative to the micropython directory), which contains the new firmware binaries. The most important ones are: firmware .uf2 A UF2 binary file which can dragged onto the RPI-RP2 drive that pops up once your Pico-series device enters BOOTSEL mode. The firmware binary you can download from the documentation page is a UF2 file, because they're the easiest to install. firmware .elf A different type of binary file, which can be loaded by a debugger (such as gdb with openoed) over RP-series SWD debug port. This is useful for debugging either a native C module you’ve added to MicroPython, or the MicroPython core interpreter itself. The actual binary contents is the same as firmware.uf2. 1.3. Building MicroPython From Source 6

---

## 第 8 页

![第 8 页](raspberry-pi-pico-python-sdk_images\page_8.png)

Raspberry Pi Pico-series Python SDK t 1     You can take a look inside your new firmware.uf2 using picotool, see the Appendix B in the Getting started with Raspberry Pi Pico-series book for details of how to use picotool, e.g.   § picotool info -a build-PICO/firmware.uf2 File build-PICO/firmware.uf2: Program Information name: MicroPython version: v1.18-412-9965747bd9 features: USB REPL thread support frozen modules: _boot, rp2, _boot_fat, dsi8x2@, onewire, dht, uasyncio, uasyncio/core, uasyncio/event, uasyncio/funcs, uasyncio/lock, uasyncio/stream, neopixel binary start: @x19e880000 binary end: @x1004ba24 embedded drive: @x10@a90@0-0x10290008 (1488K): MicroPython Fixed Pin Information none Build Information sdk version: 1.3.0 pico_board: pico boot2_name: boot2_w25q@8a build date: May 4 2822 build attributes: MinSizeRel     t 1 1.3. Building MicroPython From Source 7

---

## 第 9 页

![第 9 页](raspberry-pi-pico-python-sdk_images\page_9.png)

Raspberry Pi Pico-series Python SDK a Chapter 2. Conmecting to the MuicroPython REPL When MicroPython boots for the first time, it will sit and wait for you to connect and tell it what to do. You can load a . py file from your computer onto the board, but a more immediate way to interact with it is through what is called the read- evaluate-print loop, or REPL (often pronounced similarly to "ripple’). Read MicroPython waits for you to type in some text, followed by ihe enter key. Evaluate Whatever you typed is interpreted as Python code, and runs immediately. Print Any results of the last line you typed are printed out for you to read. Loop Go back to the start — prompt you for another line of code. There are two ways to connect to this REPL, so you can communicate with the MicroPython firmware on your board: over USB, and over the UART serial port on Pico-series GPIOs. 2.1. Connecting from a Raspberry Pi over USB The MicroPython firmware is equipped with a virtual USB serial port which is accessed through the micro USB connecior on Pico-series devices. Your computer should notice this serial port and list it as a character device, most likely /dev/ttyACHa. @ TIP You can run 1s /dev/tty* to list your serial ports. There may be quite a few, but MicroPython’s USB serial will start with /dev/ttyAcm. If in doubt, unplug the micro USB connector and see which one disappears. If you don’t see anything, you can try rebooting your Raspberry Pi. You can install minicom to access the serial port: and then open it as such: Where the -D /dev/ttyACma is pointing minicom at MicroPython’s USB serial port, and the -o flag essentially means "just do it". There’s no need to worry about baud rate, since this is a virtual serial port. Press the enter key a few times in the terminal where you opened minicom. You should see this: This is a prompt. MicroPython wants you to type something in, and tell it what to do. If you press CTRL-D on your keyboard whilst the minicom terminal is focused, you should see a message similar to this: 2.1. Connecting from a Raspberry Pi over USB 8

---

## 第 10 页

![第 10 页](raspberry-pi-pico-python-sdk_images\page_10.png)

Raspberry Pi Pico-series Python SDK MPY: soft reboot MicroPython v1.13-422-g904433073 on 2021-01-19; Raspberry Pi Pico with RP204@ Type "help()" for more information. >>> This key combination tells MicroPython to reboot. You can do this at any time. When it reboots, MicroPython will print out a message saying exactly what firmware version it is running, and when it was built. Your version number will be different from the one shown here. 2.2. Connecting from a Raspberry Pi using UART © WARNING REPL over UART is disabled by default. The MicroPython port for RP-series microcontrollers does not expose REPL over a UART port by default. However this default can be changed in the ports/rp2/mpconfigport.h source file. If you want to use the REPL over UART you're going to have to build MicroPython yourself, see Section 1.3 for more details. Go ahead and download the MicroPython source and in ports/rp2/mpeonfigport.h change MICROPY_HW_ENABLE_UART_REPL to 1 to enable it. #define MICROPY_HW_ENABLE_UART_REPL (1) // useful if there is no USB Then continue to follow the instructions in Section 1.3 to build your own MicroPython UF2 firmware. This will allow the REPL to be accessed over a UART port, through two GPIO pins. The default settings for UARTs are taken from the C SDK. settings in UART_BAUDRATE 115,200 This alternative interface is handy if you have trouble with USB, if you don’t have any free USB ports, or if you are using some other RP-series microconiroller-based board which doesn’t have an exposed USB connector. 2.2. Connecting from a Raspberry Pi using UART 9

---

## 第 11 页

![第 11 页](raspberry-pi-pico-python-sdk_images\page_11.png)

$$Raspberry Pi Pico-series Python SDK NOTE This initially occupies the UART@ peripheral on RP-series microcontrollers. The UART1 peripheral is free for you to use in your Python code as a second UART. The next thing you'll need to do is to enable UART serial on the Raspberry Pi. To do so, run raspi-config, and go to Interfacing Options ~ Serial and select "No" when asked "Would you like a login shell to be accessible over serial?” and "Yes" when asked "Would you like the serial port hardware to be enabled?". You should see something like Figure 1. Figure 1. Enabling a ~ ea 8 serial UART using File jabs (el raspi-config on the He taps ine = Raspberry Pi. Th® Geral Tagin Sheth 4 ae) Leaving raspi-config you should choose "Yes" and reboot your Raspberry Pi to enable the serial port. You should then wire the Raspberry Pi and the Pico-series device together with the following mapping: GPIO15 (UART_RXO) GPIOO (UARTO_TX) GPIO14 (UART_TX0) GPOI1 (UARTO_RX) IMPORTANT RX matches to TX, and TX matches to RX. You musin’t connect the two opposite TX pins together, or the two RX pins. This is because MicroPython needs to listen on the channel that the Raspberry Pi transmits on, and vice versa. See Figure 2. 2.2. Connecting from a Raspberry Pi using UART 10$$

---

## 第 12 页

![第 12 页](raspberry-pi-pico-python-sdk_images\page_12.png)

Raspberry Pi Pico-series Python SDK t 1       Figure 2. A Raspberry Pi 4 and the Raspberry Pi Pico with UARTO connected together.                                       + -| aApobe ee         then connect to the board using minicom connected to /dev/ser ial,   $ minicom -b 115208 -o -D /dev/serial@   If you press the enter key, MicroPython should respond by prompting you for more input:   >>>   2.3. Connecting from a Mac So long as you're using a recent version of macOS like Catalina, drivers should already be loaded. Otherwise see the manufacturers' website for FTDI Chip Drivers. Then you should use a Terminal program to connect to Serial-over-USB (USB CDC). The serial port will show up as /dev/tty.usbmodemd000000000001 If you don’t already have a Terminal program installed you can install minicom using Homebrew,   S$ brew install minicom   and connect to the board as below.   $ minicom -b -o -D     t 1 2.3. Connecting from a Mac 11

---

## 第 13 页

![第 13 页](raspberry-pi-pico-python-sdk_images\page_13.png)

$$Raspberry Pi Pico-series Python SDK NOTE Other Terminal applications like CoolTerm or Serial can also be used. " " 2.4. Say "Hello World Once connected you can check that everything is working by typing a Python “Hello World” into the REPL, >>> print("Hello, Pico!") Hello, Pico! >>> 2.9. Blink an LED The on-board LED on Raspberry Pi Pico and Pico is connected to GPIO pin 25, whereas on Raspberry Pi Pico W it is connected to the wireless chip. On both boards you can use ithe "LED" string. You can blink this on and off from the REPL. When you see the REPL prompt enter the following, >>> from machine import Pin >>> led = Pin("LED", Pin.OUT) The machine module is used to control on-chip hardware. This is standard on all MicroPython ports, and you can read more about it in the MicroPython documentation. Here we are using it to take control of a GPIO, so we can drive it high and low. If you type this in, The LED should turn on. You can turn it off again with 2.6. What next? At this point you should have MicroPython installed on your board, and have tested your setup by typing short programs into the prompt to print some text back to you, and blink an LED. You can read on to the next chapter, which goes into the specifics of MicroPython on RP-series microcontrollers, and where it differs from other platforms. Chapter 3 also has some short examples of the different APls offered to interact with the hardware. You can learn how to set up an integrated development environment (IDE) in Chapter 4, so you don't have to type programs in line by line. You can dive straight into Appendix A if you are eager to start connecting wires to a breadboard. 2.4. Say "Hello World" 12$$

---

## 第 14 页

![第 14 页](raspberry-pi-pico-python-sdk_images\page_14.png)

$$Raspberry Pi Pico-series Python SDK a Chapter 3. The RP-series a mucrocontroller Port Currently supported features include: © REPL over USB and UART (on GPO/GP1). © 1600 kB filesystem using littlefs2 on the on-board flash. (Default size for Raspberry Pi Pico) ° utime module with sleep and ticks functions. ®° ubinascii module. ° machine module with some basic functions. o machine.Pin class. o machine.Timer class. o machine.ADC class. o machine.I2C and machine.Soft12C classes. © machine.SPI and machine.SoftSPI classes. o machine.WDT class. o machine.PWM class. o machine.UART class. ° rp2 platform-specific module. o PIO hardware access library o PIO program assembler o Raw flash read/write access ° Multicore support exposed via the standard _thread module ° Accelerated floating point arithmetic using the RP-series microcontroller ROM library and hardware divider (used automatically) Documentation around MicroPython is available from https://docs.micropython.org. For example the machine module, which can be used to access a lot of on-chip hardware, is standard, and you will find a lot of the information you need in the online documentation for that module. This chapter will give a very brief tour of some of the hardware APls, with code examples you can either type into the REPL (Chapter 2) or load onto the board using a development environment installed on your computer (Chapter 4). 3.1. Blinking an LED Forever (Timer) In Chapter 2 we saw how the machine.Pin class could be used to turn an LED on and off, by driving a GPIO high and low. >>> led = Pin("LED", Pin.OUT) >>> led..value(1) >>> led..value(@) 3.1. Blinking an LED Forever (Timer) 13$$

---

## 第 15 页

![第 15 页](raspberry-pi-pico-python-sdk_images\page_15.png)

$$Raspberry Pi Pico-series Python SDK t 1     This is, to put it mildy, quite a convoluted way of turning a light on and off. A light switch would work better. The machine.Timer class, which uses RP-series microcontrollers’ hardware timer to trigger callbacks ai regular intervals, saves a lot of typing if we want the light to turn itself on and off repeatedly, thus bringing our level of automation from "mechanical switch" to "555 timer". Pico MicroPython Examples: https://github.com/raspberrypi/pico-micropython-examples/blob/master/blink/blink.py   1 from machine import Pin, Timer 3 led = Pin("LED", Pin.OUT) 4 tim = Timer() 5 def tick(timer) : 6 global led 7 led.toggle() 8 9 mode=Timer.PERIODIC, callback=tick)   Typing this program into the REPL will cause the LED to start blinking, but the prompt will appear again:   >>>   The Timer we created will run in the background, at the interval we specified, blinking the LED. The MicroPython prompt is still running in the foreground, and we can enter more code, or start more timers. 3.2. VART NOTE REPL over UART is disabled by default. See Section 2.2 for details of how to enable REPL over UART. Example usage looping UARTO to UART1. Pico MicroPython Examples: https://github.com/raspberrypi/pico-micropython-examples/blob/master/uart/loopback/uart. py   1 from machine import UART, Pin 2 import time 3 4 uart1 = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9)) 5 6 uart@ = UART(@, baudrate=9600, tx=Pin(@), rx=Pin(1)) 7 8 txData = b'hello world\n\r' 9 uart1l.write(txData) 10 time.sleep(Q.1) 11 rxData = bytes() 12 while uart@.any() > @: 13 rxData += uart@.read(1) 15 print(rxData.decode('utf-8'))   For more detail, including a wiring diagram, see Appendix A.   J 3.2. UART 14$$

---

## 第 16 页

![第 16 页](raspberry-pi-pico-python-sdk_images\page_16.png)

$$Raspberry Pi Pico-series Python SDK 3.3. ADC An analogue-to-digital converter (ADC) measures some analogue signal and encodes it as a digital number. The ADC on RP-series microcontrollers measures voltages. An ADC has two key features: its resolution, measured in digital bits, and its channels, or how many analogue signals it can accept and convert at once. The ADC on RP2350 and RP2040 has a resolution of 12-bits, meaning that it can transform an analogue signal into a digital signal as a number ranging from 0 to 4095 — though this is handled in MicroPython transformed to a 16-bit number ranging from 0 to 65,535, so that it behaves the same as the ADC on other MicroPython microconirollers. RP2350 and RP2040 have five ADC channels total, four of which are brought out to chip GPIOs: GP26, GP27, GP28 and GP29. On Pico W and Pico, the first three of these are brought out to GPIO pins, and the fourth can be used to measure the VSYS voltage on the board. The ADC’s fifth input channel is connected to a temperature sensor built into RP2350 and RP2040. You can specify which ADC channel you're using by pin number: ade = machine.ADC(26) # Connect to GP26, which is channel @ or by channel: ade = machine.ADC(4) # Connect to the internal temperature sensor ade = machine.ADC(@) # Connect to channel @ (GP26) An example reading the fourth analogue-to-digital (ADC) converter channel, connected to the internal temperature sensor: Pico MicroPython Examples: https.//github.com/raspberrypi/pico-micropython-examples/blob/master/adc/temperature. py 1 import machine 2 import utime 3 4 sensor_temp = machine.ADC(4) 5 conversion_factor = 3.3 / (65535) 6 7 while True: 8 reading = sensor_temp.read_u16() * conversion_factor 9 10 # The temperature sensor measures the Vbe voitage of a biased bipolar diode, connected to the fifth ADC channel 11 # Typically, Vbe = @.7@6V at 27 degrees C, with a slope of -1.721imV (@.0@1721) per degree. 12 temperature = 27 - (reading - @.70@6)/0.001721 13 print (temperature) 14 utime.sleep(2) 3.4. Interrupts You can set an IRQ like this: 3.3. ADC 15$$

---

## 第 17 页

![第 17 页](raspberry-pi-pico-python-sdk_images\page_17.png)

2 2 4 5 6 led.high() 7 time.sleep(delay) 8 led.1low() 9 time.sleep(delay) 10 print('done') 11 2 7 16

---

## 第 18 页

![第 18 页](raspberry-pi-pico-python-sdk_images\page_18.png)

$$Raspberry Pi Pico-series Python SDK | Pico MicroPython Examples: https://github.com/raspberrypi/pico-micropython-examples/blob/master/i2c/i2c_without_freq.py 1 from machine import I2C 2 3 i2c = I12C(@) # defaults to SCL=Pin(9), SDA=Pin(8), freq=4eee0e © WARNING There may be some bugs reading/writing to device addresses that do not respond, the hardware seems to lock up in some cases. pins I2C Frequency 400,000 Example usage: Pico MicroPython Examples: https://github.com/raspberrypi/pico-micropython-examples/blob/master/spi/spi.py 1 from machine import SPT 2 3 spi = SPI(@) 4 spi = SPL(@, 188_000) 5 spi = SPI(@, 100_000, polarity=1, phase=1) 6 7 spi.write('test') 8 spi.read(5) 9 10 buf = bytearray(3) 11 spi.writte_readinto('out', buf) NOTE The chip select must be managed separately using a machine.Pin. pins SPI_BAUDRATE 1,000,000 | 3.7. SPI 17$$

---

## 第 19 页

![第 19 页](raspberry-pi-pico-python-sdk_images\page_19.png)

$$Raspberry Pi Pico-series Python SDK | Example of using PWM to fade an LED: Pico MicroPython Examples: https://github.com/raspberrypi/pico-micropython-examples/blob/master/pwm/pwm_fade.py 1 # Example using PWM to fade an LED. 2 3 import time 4 from machine import Pin, PWM 5 6 7 # Construct PWM object, with LED on Pin(25). 8 pwm = PWM(Pin(25)) 9 10 # Set the PWM frequency. 11 pwm. freq(1800) 12 13 # Fade the LED in and out a few times. 14 duty = @ 15 direction = 1 16 for _ in range(8 * 256): 17 duty += direction 18 if duty > 255: 19 duty = 255 20 direction = -1 21 elif duty < @: 22 duty = @ 23 direction = 1 24 pwm.duty_u16(duty * duty) 25 time.sleep(@.001) This example does not work with Raspberry Pi Pico W as the on-board LED is connected via the 43439 wireless chip rather than directly to the RP2040 itself. The example will work with an off-board LED, e.g. one wired to GP15 as shown below. | 3.8. PWM 18$$

---

## 第 20 页

![第 20 页](raspberry-pi-pico-python-sdk_images\page_20.png)

$$Raspberry Pi Pico-series Python SDK t 1     Figure 3. Connecting your Raspberry Pi Pico W to an off-board LED.   POD OD SCCES GCes                            36656 a © SG P Cc oe Tl a oe ey KOR = im o —] ag 5 Ah td = anAana OSCOCOSO# = OS SCTE CEE EEE CCC CEES 80850080 ~     SS a SOOOOOGO™                          = OOS O99 698900990006 =) ©- bone Sy DS] = = un = 2 gh S oh SOOSS OOOOH OOOO 89099 08009 99880 99090     3.9. PIO Support Current support allows you to define Programmable IO (PIO) Assembler blocks and using them in the PIO peripheral, more documentation around PIO can be found in Chapter 3 of the RP2040 Datasheet and Chapter 4 of the Raspberry Pi Pico-series C/C++ SDIK book. The Pico-series MicroPython introduces a new @rp2.asm_pio decorator, along with a rp2.PI0 class. The definition of a PIO program, and the configuration of the state machine, into 2 logical parts: ° The program definition, including how many pins are used and if they are in/out pins. This goes in the @rp2.asm_pio definition. This is close to what the pioasm tool from the SDK would generate from a .pio file (but here it’s all defined in Python). ° The program instantiation, which sets the frequency of the state machine and which pins to bind to. These get set when setting a SM to run a particular program. The aim was to allow a program to be defined once and then easily instantiated multiple times (if needed) with different GPIO. Another aim was to make it easy to do basic things without getting weighed down in too much PIO/SM configuration. NOTE The following examples will not work with the on-board LED on Raspberry Pi Pico W, as PIO is unable to access the wireless chip.   Example usage, to blink the on-board LED connected to GPIO 25, Pico MicroPython Examples: https://github.com/raspberrypi/pico-micropython-examples/blob/master/pio/pio_blink.py   1 import time 2 import rp2 3 from machine import Pin     [ 1 3.9. PIO Support 19$$

---

## 第 21 页

![第 21 页](raspberry-pi-pico-python-sdk_images\page_21.png)

$$Raspberry Pi Pico-series Python SDK it # Define the blink program. It has one GPIO to bind to on the set instruction, which is an output pin. # Use lots of delays to make the blinking visible by eye. @rp2.asm_pio(set_init=rp2.PIO.OUT_LOW) def blink(): wrap_target() 10 set(pins, 1) 31 11 nop() 31 12 31 nop() 13 nop() 31 14 nop() 31 15 31 set(pins, @) 16 nop() 31 17 nop() 31 18 nop() 31 19 nop() 31 20 wrap() 21 22 # Instantiate a state machine with the blink program, at 2@@@Hz, with set bound to Pin(25) (LED on the Pico board) = = 23 sm rp2.StateMachine(@, blink, freq=200@, set_base=Pin(25) ) 24 25 # Run the state machine for 3 seconds The LED should blink. 26 sm.active(1) 27 time.sleep(3) 28 sm.active(@) or via explicit exec. Pico MicroPython Examples: https://github.com/raspberrypi/pico-micropython-examples/blob/master/pio/pio_exec.py # Example using PIO to turn on an LED via an explicit exec. # # Demonstrates: # - using set_init and set_base # - using StateMachine.exec import time from machine import Pin import rp2 10 11 # Define an empty program that uses a single set pin. 12 @rp2.asm_pio(set_init=rp2.PIO.OUT_LOW) 13 def prog(): 14 pass 15 16 17 # Construct the StateMachine, binding Pin 25 to the set pin. 18 sm = = rp2.StateMachine(@, prog, set_base=Pin(25)) 19 20 # Turn on the set pin via an exec instruction. 21 sm.exec("set(pins, 1)”") 22 23 # Sleep for 50@@ms. 24 time.sleep(@.5) 25 26 # Turn off the set pin via an exec instruction. 27 sm.exec("set(pins, @)”") Some points to note, it 3.9. PIO Support 20$$

---

## 第 22 页

![第 22 页](raspberry-pi-pico-python-sdk_images\page_22.png)

$$Raspberry Pi Pico-series Python SDK ° All program configuration (eg autopull) is done in the @asm_pio decorator. Only the frequency and base pins are set in the StateMachine consirucior. ° [n] is used for delay, .set(n) used for sideset ° The assembler will automatically detect if sideset is used everywhere or only on a few instructions, and set the SIDE_EN bit automatically The idea is that for the 4 sets of pins (in, out, set, sideset, excluding jmp) that can be connected to a state machine, there’s the following that need configuring for each set: 1. base GPIO 2. number of consecutive GPIO 3. initial GPIO direction (in or out pin) A. initial GPIO value (high or low) In the design of the Python API for PIO these 4 items are split into "declaration" (items 2-4) and "instantiation" (item 1). In other words, a program is written with items 2-4 fixed for that program (eg a WS2812 driver would have 1 output pin) and item 1 is free to change without changing the program (eg which pin the WS2812 is connected to). So in the @asm_pio decorator you declare items 2-4, and in the StateMachine constructor you say which base pin to use (item 1). That makes it easy to define a single program and instantiate it multiple times on different pins (you can't really change items 2-4 for a different instantiation of the same program, it doesn’t really make sense to do that). To declare multiple pins in the decorator (e.g. the count: item 2 above), use a tuple. Each item in the tuple specifies items 3 and 4. For example: 1 @asm_pio(set_init=(PIO.OUT_LOW, PIO.OUT_HIGH, PIO.IN_LOW), sideset_init=PIO.OUT_LOW, in_init =PIO.IN_HIGH) 2 def foo(): 4 5 sm = StateMachine(@, foo, freq=19000, set_base=Pin(15), sideset_base=Pin(22) ) In this example: ° there are 3 set pins connected to the SM, and their initial state (set when the StateMachine is created) is: output low, output high, input low (used for open-drain) ° there is 1 sideset pin, initial state is output low ° the 3 set pins start at Pin(15) ° the 1 sideset pin starts at Pin(22) The reason to have the constants OUT_LOW, OUT_HIGH, IN_LOW and IN_HIGH is so that the pin value and dir are automatically set before the start of the PIO program (instead of wasting instruction words to do set(pindirs, 1) etc at the start). 3.9.1. IRQ There is support for PIO IRQs, e.g. Pico MicroPython Examples: https://github.com/raspberrypi/pico-micropython-examples/blob/master/pio/pio_irg.py 1 import time 2 import rp2 3 4 @rp2.asm_pio() 5 def irq_test(): 3.9. PIO Support 21$$

---

## 第 23 页

![第 23 页](raspberry-pi-pico-python-sdk_images\page_23.png)

| 6 wrap_target() 7 nop() [31] 8 nop() [31] 9 nop() [31] 10 nop() [31] 11 irq(Q) 12 nop() [31] 13 nop() [31] 14 nop() [31] 15 nop() [31] 16 irq(1) 17 wrap() 18 19 21 2 6 7 10 11 irq(rel(@)) 12 13 [5] 14 15 nop() [29] 16 17 18 19 20 [6] 21 22 nop() [29] 23 24 25 28 31 | 22

---

## 第 24 页

![第 24 页](raspberry-pi-pico-python-sdk_images\page_24.png)

$$Raspberry Pi Pico-series Python SDK     Pico MicroPython Examples: https://github.com/raspberrypi/pico-micropython-examples/blob/master/pio/pio_pinchange.py   1 # Example using PIO to wait for a pin change and raise an IRQ. 2# 3 # Demonstrates: 4 # - PIO wrapping 5 # - PIO wait instruction, waiting on an input pin 6 # - PIO irq instruction, in blocking mode with relative IRQ number 7 # - setting the in_base pin for a StateMachine 8 # - setting an irq handier for a StateMachine 9# - instantiating 2x StateMachine's with the same program and different pins 10 11 import time 12 from machine import Pin 13 import rp2 14 15 16 @rp2.asm_pio() 17 def wait_pin_low(): 18 wrap_target() 19 20 wait(@, pin, @) 21 irq(block, rel1(@)) 22 wait(1, pin, @) 23 24 wrap() 25 26 27 def handler(sm): 28 # Print a (wrapping) timestamp, and the state machine object. 29 print(time.ticks_ms(), sm) 30 31 32 # Instantiate StateMachine(@) with wait_pin_low program on Pin(16). 33 pini6 = Pin(16, Pin.IN, Pin.PULL_UP) 34 sm@ = rp2.StateMachine(@, wait_pin_low, in_base=pini6) 35 sm@.irq(handier) 36 37 # Instantiate StateMachine(1) with wait_pin_low program on Pin{17). 38 pint? = Pin(17, Pin.IN, Pin.PULL_UP) 39 smi = rp2.StateMachine(1, wait_pin_low, in_base=pini7) 4@ sm1.irq(handier) 41 42 # Start the StateMachine's running. 43 sm@.active(1) 44 sm1.active(1) 45 46 # Now, when Pin(16) or Pin(17) is pulled low a message will be printed to the REPL.   3.9.2. WS2812 LED (NeoPixel) While a WS2812 LED (NeoPixel) can be driven via the following program, Pico MicroPython Examples: https.//github.com/raspberrypi/pico-micropython-examples/blob/master/pio/pio_ws2812.py   1 # Example using PIO to drive a set of WS28712 LEDs. 2 3 import array, time 4 from machine import Pin 5 import rp2       3.9. PIO Support 23$$

---

## 第 25 页

![第 25 页](raspberry-pi-pico-python-sdk_images\page_25.png)

$$Raspberry Pi Pico-series Python SDK       7 # Configure the number of WS2812 LEDs. 8 NUM_LEDS = 8 11 @rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24) 12 def ws2812(): 13 T1 = 2 14 T2 = 5 15 T3 = 3 16 wrap_target() 17 label("bitloop" ) 18 out(x, 1) .side(@) [T3 - 1] 19 jmp(not_x, “do_zero") .side(1) [Ti - 1] 20 jmp(“bitloop”) .side(1) [T2 - 1] 21 label("do_zero") 22 nop() .side(@) [T2 - 1] 23 wrap() 24 25 26 # Create the StateMachine with the ws2812 program, outputting on Pin(22). 27 sm = rp2.StateMachine(@, ws2812, freq=8_@00_000, sideset_base=Pin(22)) 28 29 # Start the StateMachine, it will wait for data on its FIFO. 30 sm.active(1) 31 32 # Display a pattern on the LEDs via an array of LED RGB values. 33 ar = array.array("I", [@ for _ in range(NUM_LEDS)]) 34 35 # Cycle colours. 36 for i in range(4 * NUM_LEDS): 37 for j in range(NUM_LEDS): 38 r= j * 18@ // (NUM_LEDS - 1) 39 b = 108 - j * 100 // (NUM_LEDS - 1) 40 if j != i % NUM_LEDS: 41 fo >a 3 42 b >>= 3 43 ar[j] = r << 16 | b 44 sm.put(ar, 8) 45 time.sleep_ms(5@) 46 47 # Fade out. 48 for i in range(24): 49 for j in range(NUM_LEDS): 50 ar[j] >>= 1 51 sm.put(ar, 8) 52 time.sleep_ms(5@)   3.9.3. UART TX A UART TX example, Pico MicroPython Examples: https://github.com/raspberrypi/pico-micropython-examples/blob/master/pio/pio_uart_tx.py   1 # Example using PIO to create a UART TX interface 2 3 from machine import Pin 4 from rp2 import PIO, StateMachine, asm_pio 5       3.9. PIO Support 24$$

---

## 第 26 页

![第 26 页](raspberry-pi-pico-python-sdk_images\page_26.png)

$$Raspberry Pi Pico-series Python SDK t 1       6 UART_BAUD = 115200 7 PIN_BASE = 18 8 NUM_UARTS = 8 11 @asm_pio(sideset_init=PI0.OUT_HIGH, out_init=PIO.OUT_HIGH, out_shiftdir=PI0O.SHIFT_RIGHT) 12 def uart_tx(): 13 # Block with TX deasserted until data available 14. pull() 15 # Initialise bit counter, assert start bit for 8 cycles 16 set(x, 7) .side(@) [7 17 # Shift out 8 data bits, 8 execution cycles per bit 18 label("bitloop" ) 19 out(pins, 1) [6 20 jmp(x_dec, "bitloop") 21 # Assert stop bit for 8 cycles total (incl 1 for pull()) 22 nop() .side(1) [6 23 24 25 # Now we add 8 UART TXs, on pins 1@ to 17. Use the same baud rate for all of them. 26 uarts = [] 27 for i in range(NUM_UARTS) : 28 sm = StateMachine( 29 i, uart_tx, freq=8 * UART_BAUD, sideset_base=Pin(PIN_BASE + i), out_base=Pin(PIN_BASE + i) 30 ) 31 sm.active(1) 32 uarts .append(sm) 33 34 # We can print characters from each UART by pushing them to the TX FIFO 35 def pio_uart_print(sm, s): 36 for c ins: 37 sm.put(ord(c) ) 38 39 4@ # Print a different message from each UART 41 for i, u in enumerate(uarts): 42 pio_uart_print(u, “Hello from UART {}!\n".format(i))   @) NOTE     You need to specify an initial OUT pin state in your program in order to be able to pass OUT mapping to your SM instantiation, even though in this program it is redundant because the mappings overlap. 3.9.4. SPI An SPI example. Pico MicroPython Examples: https://github.com/raspberrypi/pico-micropython-examples/blob/master/pio/pio_spi.py   1 import rp2 2 from machine import Pin 4 @rp2.asm_pio(out_shiftdir=@, autopull=True, pull_thresh=8, autopush=True, push_thresh=8, sideset_init=(rp2.PIO.OUT_LOW, rp2.PIO.OUT_HIGH), out_indt=rp2.PIO.OUT_LOW) 5 def spi_cpha@(): 6 # Note X must be preinitialised by setup code before first byte, we reload after sending each byte 7 # Would normally do this via exec() but in this case it's in the instruction memory and is     [ 1 3.9. PIO Support 25$$

---

## 第 27 页

![第 27 页](raspberry-pi-pico-python-sdk_images\page_27.png)

8 9 10 wrap_target() 11 pull(ifempty) .side(@x2) [1] 12 label("bitloop") 13 .side(@x8) [1] 14 .side(@x1) 15 .side(@x1) 16 17 .side(@x@) 18 19 .side(@x1) 20 21 22 nop() .side(@x8) 23 wrap() 24 25 27 28 29 30 31 self._sm.active(1) 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 NOTE instantiation. 26

---

## 第 28 页

![第 28 页](raspberry-pi-pico-python-sdk_images\page_28.png)

$$Raspberry Pi Pico-series Python SDK | Pico MicroPython Examples: https://github.com/raspberrypi/pico-micropython-examples/blob/master/pio/pio_pwm.py 1 # Example of using PIO for PWM, and fading the brightness of an LED 2 3 from machine import Pin 4 from rp2 import PIO, StateMachine, asm_pio 5 from time import sleep 6 7 8 @asm_pio(sideset_init=PIO.OUT_LOW) 9 def pwm_prog(): 10 pull(noblock) .side(@) 11 mov(x, osr) # Keep most recent pull data stashed in X, for recycling by noblock 12 mov(y, isr) # ISR must be preloaded with PWM count max 13 labe1("pwmloop" ) 14. jmp(x_not_y, "skip") 15 nop() .side(1) 16 label("skip") 17 jmp(y_dec, "pwmloop") 18 19 20 class PIOPWM.:: 21 def __init__(self, sm_id, pin, max_count, count_freq): 22 self._sm = StateMachine(sm_id, pwm_prog, freq=2 * count_freq, sideset_base=Pin(pin) ) 23 # Use exec() to load max count into ISR 24 self ._sm.put(max_count) 25 self ._sm.exec("pull()") 26 self._sm.exec("mov(isr, osr)”") 27 self ._sm.active(1) 28 self._max_count = max_count 29 30 def set(self, value): 31 # Minimum value is -1 (completely turn off), @ actually still produces narrow pulse 32 value = max(value, -1) 33 value = min(value, self._max_count) 34 self ._sm.put(value) 35 36 37 # Pin 25 on Pico boards 38 pwm = PIOPWM(@, 25, max_count=(1 << 16) - 1, 39 40 while True: 41 for i in range(256): 42 pwm.set(i ** 2) 43 sleep(@.01) NOTE This example does not work with Raspberry Pi Pico W as the on-board LED is connected via the 43439 wireless chip rather than directly to the RP2040 itself. The example will work with an off-board LED connected via GPIO. 3.9.6. Using pioasm As well as writing PIO code inline in your MicroPython script you can use the pioasm tool from the C/C++ SDK to generate a Python file. | 3.9. PIO Support 27$$

---

## 第 29 页

![第 29 页](raspberry-pi-pico-python-sdk_images\page_29.png)

$$Raspberry Pi Pico-series Python SDK t 1       $ pioasm -o python input (output)   For more information on pioasm see the Raspberry Pi Pico-series C/C++ SDK book which talks about the C/C++ SDK. 3.10. Wireless Support IMPORTANT Wireless support is only available on Pico W and Pico 2 W, not on Pico. Example usage: Pico MicroPython Examples: https://github.com/raspberrypi/pico-micropython-examples/blob/master/wireless/webserver.py   1 import network 2 import socket 3 import time 4 5 from machine import Pin 6 7 led = Pin(15, Pin.OUT) 8 9 ssid = 'YOUR NETWORK NAME' 1@ password = NETWORK PASSWORD‘ 11 12 wlan = network .WLAN(network.STA_IF) 13 wlan.active(True) 14 wlan.connect(ssid, password) 15 16 html = """<!DOCTYPE html> 17 <html> 18 <head> <title>Pico W</title> </head> 19 <body> <h1>Pico W</h1> 20 <p>%s</p> 21 </body> 22 </html> 24 25 max_waitt = 10 26 while max_wait > @: 27 if wlan.status() < @ or wlan.status() >= 3: 28 break 29 max_wait -= 1 30 print('waiting for connection...') 31 time.sleep(1) 32 33 if wlan.status() != 3: 34 raise RuntimeError('network connection failed" ) 35 else: 36 print('connected' ) 37 status = wlan.ifconfig() 38 print( 'ip = ' + status[@] } 39 4@ addr = socket.getaddrinfo('@.0.0.0', 88)[@][-1] 41 42 s = socket.socket() 43 s.bind(addr)     t 1 3.10. Wireless Support 28$$

---

## 第 30 页

![第 30 页](raspberry-pi-pico-python-sdk_images\page_30.png)

45 47 50 try: 51 52 53 54. print(request) 55 56 57 58 59 60 61 62 63 64 led.value(1) 65 66 67 68 69 led.value(@) 78 71 72 73 74 75 cl.send(response) 76 cl.close() 77 78 79 cl.close() 80 NOTE 29

---

## 第 31 页

![第 31 页](raspberry-pi-pico-python-sdk_images\page_31.png)

$$Raspberry Pi Pico-series Python SDK t 1     Figure 4. Connecting your Raspberry Pi Pico W to a LED.                          DO OO & OOCEO     QO DAB a & SSOOQ®e Lo Cp (> &@ 4 BD                             Se or Ss wr © BS ae      Soe CBG ano nas Dal lal N= ha = sees: = Oe fo a, OS ececeoees SOSSSOGO™ a = Ore: Simi Ang = OTST                                  = Es SS ©- SOOT O008O C800 89099 08009 99880 99090     After your Pico W connects to your wireless network, you should see the IP address for your board appear on the REPL shell. To turn our LED on, you can open up a web browser and go to http://X.X.X.X/light/on to turn the LED on, and http://X.X.X.X/Light/off to turn the LED off again. NOTE You should substitute your IP address, which for most home networks will probably be in the 192.168.1.X range.     t 1 3.10. Wireless Support 30$$

---

## 第 32 页

![第 32 页](raspberry-pi-pico-python-sdk_images\page_32.png)

Raspberry Pi Pico-series Python SDK a Chapter 4. Using an Integrated Development Environment (IDE) The MicroPython port to Pico-series devices and other RP-series microcontroller-based boards works with commonly used developmeni environments. 4.1. Using Thonny Thonny packages are available for Linux, MS Windows, and macOS. After installation, the Thonny development environment works the same on all platforms. The latest release of Thonny can be downloaded from thonny.org Alternatively if you are working on a Raspberry Pi you should install Thonny using apt from the command line: This will add a Thonny icon to the Raspberry Pi desktop menu. Go ahead and select Raspberry Pi ~ Programming > Thonny Python IDE to open the development environment. When opening Thonny for the first time select "Standard Mode." For some versions this choice will be made via a popup when you first open Thonny. However for the Raspberry Pi release you should click on the text in the top right of the window to switch to "Regular Mode." Make sure your Pico-series device is plugged into your computer and, click on the word ‘Python’ followed by a version number at the bottom-right of the Thonny window — this is the Python interpreter that Thonny is currently using. Normally the interpreter is the copy of Python running on Raspberry Pi, but it needs to be changed in order to run your programs in MicroPython on your Pico, clicking the current interpreter will open a drop down. Select "MicroPython (Raspberry Pi Pico W)" or "MicroPython (Raspberry Pi Pico)" from the list, see Figure 5. Fie 6. Sitchin to MicroPython Filé Edit, View Run ‘Tools. Help Oe <untitled>% -| | Shells / \ | [python 3.7.3 (/usr/bin/python3) my |S? | MicroPython v1.14 on 2021-02-05; Raspberry Pi Pico with RP2040 | \/ Type "help()" for more information. | ‘The'same iitterpretevwhich raneiTBonny (Sau A ne IN _) “Alternative,Python’8 BY NR ] + 21 Piao) \ ee Confighre‘ititepréters.. a A.1. Using Thonny 31

---

## 第 33 页

![第 33 页](raspberry-pi-pico-python-sdk_images\page_33.png)

$$Raspberry Pi Pico-series Python SDK NOTE The Pico-series interpreter is only available in the latest version of Thonny. If you’re running an older version and can't update it, look for "MicroPython (generic)" instead. If your version of Thonny is older still and has no interpreter option at the bottom-right of the window and you can’t update it, restart Thonny, click the "Run" menu, and click ‘Select interpreter.’ Click the drop-down arrow next to ‘The same interpreter that runs Thonny (defaulty’, click on ‘MicroPython (generic)’ in the list, then click on the drop-down arrow next to ‘Port’ and click on ‘Board in FS mode’ in that list before clicking "OK" to confirm your changes. You can now access the REPL from the Shell panel, >>> print('Hello Pico!') Hello Pico! >>> see Figure 6. Figure 6. Seying ‘Helo Pico!" from the File: Edit: ‘Views Run ‘Tools: Help MicroPython REPL ——— oo inside the Thonny ae =) environment. <untitleds % “| | Shellx¢ MicroPython v1.14 on 2021-02-05; Raspberry Pi Pico with RP2040 J Type “help()" for more information. pee print('Hello Pico!') Hello Pico! | -| [>>> iz} Pt Pico) d 4.1.1. Blinking the LED from Thonny The following example uses Thonny to execute an example program thai uses a timer to blink the onboard LED on your device. Pico MicroPython Examples: https://github.com/raspberrypi/pico-micropython-examples/blob/master/blink/blink.py 1 from machine import Pin, Timer 2 3 led = Pin("LED", Pin.OUT) 4 tim = Timer() 5 def tick(timer) : 6 global led 7 led.toggle() 8 9 mode=Timer.PERIODIC, callback=tick) A.1. Using Thonny 32$$

---

## 第 34 页

![第 34 页](raspberry-pi-pico-python-sdk_images\page_34.png)

$$Raspberry Pi Pico-series Python SDK it Enter the code in the main panel, then click on the green run button. Thonny will present you with a popup, click on "MicroPython device" and enter test.py to save the code to the Pico-series device, see Figure 7. A Z 1 \ i Figure 7. Saving code yA OK to Raspberry Pi Pico = anita @ BSS File: Edit: View Run Tools Help: inside the Thonny environment. |\26 2 ©F © 1. |from machine impert Pin, Timer led = Pin(25, Pin.oOuT) tin = Timer(} def tick(timer) ; Wiese? v o B global led led. toggLe()} This:computer: tim. init (fregq=2, ck=tick) Raspberry Pi Pico Shell Ti = MicroPython v1.14 on 2021-02-05; Raspberry Pi Pico with RP2040 Type “help()" fer more information. => print('Hello Pico!"} Hello: Pico! re MicroPython (Raspberry Pi Pico) i f t © TIP If you "save a file to the device" and give it the special name main.py, then MicroPython starts running that script as soon as power is supplied to the Pico-series device in the future. The program should upload to the Pico-series device using the REPL, and automatically start running. The on-board LED should start to blink. 4,2. Using Visual Studio Code Visual Studio Code (VSCode) is a popular open source editor developed by Microsoft. It is the recommended Integrated Development Environment (IDE) on the Raspberry Pi 4 if you want a graphical interface to edit and debug your code. Visual Studio Code (VSCode) can be installed in Raspberry Pi OS using the usual apt procedure: sudo apt update §$ sudo apt install code Once the install has completed, you can then install the MicroPico Visual Studio Code Extension (aka Pico-W-Go) for working with MicroPython on a Pico-series device. code --install-extension ms-python.python code --install-extension visualstudioexptteam.vscodeintellicode code --install-extension ms-python.vscode-pylance code --install-extension paulober .pico-w-go This third-party extension includes: ° Auto-completion and docs it 4.2. Using Visual Studio Code 33$$

---

## 第 35 页

![第 35 页](raspberry-pi-pico-python-sdk_images\page_35.png)

$$Raspberry Pi Pico-series Python SDK t 1     ° Console integration for communication with MicroPython REPL on a Pico-series device ° Running and transferring files to and from your board Finally, start Visual Studio Code from a Terminal window:   $ export PICO_SDK_PATH=/home/pi/pico/pico-sdk $ code   Open a folder and press Cirl-Shift-P (or Cmd-Shift-P on a Mac) to open the VS Code command palette. Select MicroPico > Configure Project. Then click on the Pico Disconnected button on the bottom (blue) toolbar. You should now be connected to your Pico-series device, see Figure 8.   Figure 8. Visual Studio Code running with the                                                                                                                                                                                           MicroPico extension connected to a Pico-     series device. B Epicowgo] & ©     (i), s       PROBLEMS OUTPU Tall DEBUG CONSOLE >» @ oo D dev st ty susbmadem3230 1 esol] || @ Pomme PATIMECINE) @OOA0 Dim Ost Al commends Ing IF Prim S1086eb                                                                                                                                                                                                                                                                         To run a program on a connected Pico-series device: © Select MicroPico > Run current file on Pico © Use the status bar Run button in the bottom (blue) toolbar To stop a program running on a connected Pico-series device: © Select MicroPico > Stop execution © Use the Stop button in the bottom (blue) toolbar 4.3. Using Remote MicroPython shell (rshell) Remote MicroPython shell packages are available for Linux, MS Windows, and macOS. After installation, rshell works the same on all platforms. For full documentation on rsheil, see the project’s GitHub repository.   t 1 4.3. Using Remote MicroPython shell (rshell) 34$$

---

## 第 36 页

![第 36 页](raspberry-pi-pico-python-sdk_images\page_36.png)

/home/pi> device. 2 6 7 led.toggle() 8 35

---

## 第 37 页

![第 37 页](raspberry-pi-pico-python-sdk_images\page_37.png)

Raspberry Pi Pico-series Python SDK @ TIP rshell represents your device's flash storage as /pyboard. 2 TIP Use the special filename main. py to automatically execute your program on boot. The program should upload to the Pico-series device using the REPL, and automatically start running. You should see the on-board LED start blinking. 4.3. Using Remote MicroPython shell (rshell) 36

---

## 第 38 页

![第 38 页](raspberry-pi-pico-python-sdk_images\page_38.png)

$$Raspberry Pi Pico-series Python SDK a a Appendix A: App Notes ° ° ° Using a SSD1306-based OLED graphics display Display an image and text on I12C driven SSD1306-based OLED graphics display. Wiring information See Figure 9 for wiring instructions. Figure 9. Wiring the O aD eC) OLED to Pico using _—_—_——— a 20 12662 OLED | es | | SDA) A © © COSSC OO OS = GQIEO © © ©OSSSO HOGQOOGDHOS SHO = o ala SS S S| PD Pie ©2020 COCR © v Hf | ane ENG) (J ee AMM mm SQW J _ w HENS Oi 2 © «21, C U@sese » eo CE FA Ae Seo © EG |G ORO KORG ROMO KOKORO KOKO EEG Ka | KOKOKOKOKOKOKO KON? KOKO USooo SSSSS SESCE GOOWOGOG List of Files A list of files with descriptions of their function; i2c_1306o0led_using_defaults.py The example code. Pico MicroPython Examples: https://github.com/raspberrypi/pico-micropython-examples/blob/master/i2c/1306oled/i2c_1306oled_using_defaults.py 1 # Display Image & text on T2C driven ssd1306 OLED display 2 from machine import Pin, I2C 3 from ssd13@6 import SSD13@6_I2C 4 import framebuf 5 6 WIDTH = 128 # oled display width 7 HEIGHT = 32 # oled display height 8 9 i2c = 12C(@) # Init I2C using I2C@ defaults, SCL=Pin(GP9), SDA=Pin(GP8), freq=490000 1@ print("I2C Address : "thex(i2e.scan()[@]).upper()) # Display device address 11 print("I2C Configuration: "+str(i2c)) # Display I2C config 12 a Using a SSD1306-based OLED graphics display 37$$

---

## 第 39 页

![第 39 页](raspberry-pi-pico-python-sdk_images\page_39.png)

$$Raspberry Pi Pico-series Python SDK       13 14 oled = SSD1306_I2C(WIDTH, HEIGHT, i2c) # Init oled display 15 16 # Raspberry Pi logo as 32x32 bytearray 17 buffer = x88 | ' \xc1\x83\x80\xO2A\x82 @\xO@2A\x82@\ xO2\xc1\xc2@\x02\xf6>\xcO\xO1 \xfc=\x80\ \x18\x18\x86\x01\x88\x10\x80\x80\x8c 18 19 # Load the raspberry pi logo into the framebuffer (the image is 32x32) 20 fb = framebuf.FrameBuffer(buffer, 32, 32, framebuf.MONO_HLSB) 21 22 # Clear the oled display in case it has junk on it. 23 oled..fi11(@) 24 25 # Blit the image from the framebuffer to the oled display 26 oled.blit(fb, 96, Q) 27 28 # Add some text 29 oled..text("Raspberry Pi",5,5) 30 oled..text("Pico",5,15) 31 32 # Finally update the oled display so the image & text is displayed 33 oled..show()   i2c_1306o0led_with_freq.py The example code, explicitly sets a frequency. Pico MicroPython Examples: https://github.com/raspberrypi/pico-micropython-examples/blob/master/i2c/1306oled/i2c_1306oled_with_freq.py   1 # Display Image & text on T2C driven ssd1306 OLED display 2 from machine import Pin, I2C 3 from ssd13@6 import SSD13@6_I2C 4 import framebuf 5 6 WIDTH = 128 # oled display width 7 HEIGHT = 32 # oled display height 8 9 i2c = 12C(@, scl=Pin(9), sda=Pin(8), freq=200000) # Init 12C using pins GP8 & GP9 (default I2C@ pins) 1@ print("I2C Address : "thex(i2e.scan()[@]).upper()) # Display device address 11 print("I2C Configuration: "+str(i2c)) # Display I2C config 12 13 14 oled = SSD1306_I2C(WIDTH, HEIGHT, i2c) # Init oled display 15 16 # Raspberry Pi logo as 32x32 bytearray 17 buffer = x88 | ' \xc1\x83\x80\xO2A\x82 @\xO@2A\x82@\ xO2\xc1\xc2@\x02\xf6>\xcO\xO1 \xfc=\x80\ \x18\x18\x86\x01\x88\x10\x80\x80\x8c 18 19 # Load the raspberry pi logo into the framebuffer (the image is 32x32) 20 fb = framebuf.FrameBuffer(buffer, 32, 32, framebuf.MONO_HLSB) 21 22 # Clear the oled display in case it has junk on it. 23 oled..fi11(@) 24       Using a SSD1306-based OLED graphics display 38$$

---

## 第 40 页

![第 40 页](raspberry-pi-pico-python-sdk_images\page_40.png)

$$Raspberry Pi Pico-series Python SDK t 1       25 # Blit the image from the framebuffer to the oled display 26 oled.blit(fb, 96, Q) 27 28 # Add some text 29 oled..text("Raspberry Pi",5,5) 30 oled..text("Pico",5,15) 31 32 # Finally update the oled display so the image & text is displayed 33 oled..show()   Bill of Materials   Table 4. A list of     materials required for Item Quantity Details the example Breadboard q generic part Raspberry Pi Pico q htips://www.raspberrypi.com/ products/raspberry-pi-pico/   Monochrome 128x32 I2C OLED q hitps://www.adafruit.com/product/ Display 931   Using a SH1106-based OLED graphics display Display an image and text on I2C driven SH1106-based OLED graphics display such as the Pimoroni Breakout Garden 1.12” Mono OLED https://shop.pimoroni.com/products/1-12-oled-breakout?variant=29421050757203 . Wiring information See Figure 10 for wiring instructions.             Figure 10. Wiring the OLED to Pico using 12€ DEGREE TEE OLED ee |                                  SE GY BeaOoS SOEs PSS SSOGES ERE: SSOGS WEE . 2 3 2 2 R a a iat = ao oS SOSOCOSOSOS QOS SSSE= ABSSSHSD Beet eet IESE BOG ~ SOOO = Seeee     889 24 Pico 920 StL                     S Tim OTST Isssso @@ ee wooo soeo]® @ 878 O Us@lececes AR AAR oo   OD OO GB mo BHOPOSSOSS « tow Q N m Se Ee eee GOO All 6556 SSS SSSS SOO o ray 2. n = = a                   1 COON OO) LOK ie SCO COCSCOC COWo SSSCS BBEBES BOEBOS Oo OS BOOBS CESS SEOOE GCOWSOS COOCE         t 1 Using a SH1106-based OLED graphics display 39$$

---

## 第 41 页

![第 41 页](raspberry-pi-pico-python-sdk_images\page_41.png)

$$Raspberry Pi Pico-series Python SDK     List of Files A list of files with descriptions of their function; i2c_11060led_using_defaults.py The example code. Pico MicroPython Examples: https://github.com/raspberrypi/pico-micropython-examples/blob/master/i2c/1 1 06oled/i2c_1106oled_using_defaults.py   1 # Display Image & text on T2C driven SH11@6 OLED display 2 from machine import I2C, ADC 3 from shi106 import SH11@6_I2C 4 import framebuf 5 6 WIDTH = 128 # oled display width 7 HEIGHT = 128 # oled display height 8 9 i2c = 12C(@) # Init I2C using I2C@ defaults, SCL=Pin(GP9), SDA=Pin(GP8), freq=400e00 1@ print("I2C Address : "thex(i2e.scan()[@]).upper()) # Display device address 11 print("I2C Configuration: "+str(i2c)) # Display I2C config 12 13 14. oled = SH11Q6_I2C(WIDTH, HEIGHT, i2c) # Init oled display 15 16 # Raspberry Pi logo as 32x32 bytearray 17 buffer = x88 | ' \xc1\x83\x80\xO2A\x82 @\xO@2A\x82@\ xO2\xc1\xc2@\x02\xf6>\xcO\xO1 \xfc=\x80\ \x18\x18\x86\x01\x88\x10\x80\x80\x8c 18 19 # Load the raspberry pi logo into the framebuffer (the image is 32x32) 20 fb = framebuf.FrameBuffer(buffer, 32, 32, framebuf.MONO_HLSB) 21 22 # Clear the oled display in case it has junk on it. 23 oled..fi11(@) 24 25 # Blit the image from the framebuffer to the oled display 26 oled.blit(fb, 96, Q) 27 28 # Add some text 29 oled..text("Raspberry Pi",5,5) 30 oled..text("Pico",5,15) 31 32 # Finally update the oled display so the image & text is displayed 33 oled..show()   i2c_11060led_with_freq.py The example code, explicitly sets a frequency. Pico MicroPython Examples: https://github.com/raspberrypi/pico-micropython-examples/blob/master/i2c/1 106oled/i2c_1106oled_with_freq.py   1 # Display Image & text on T2C driven ssd1306 OLED display 2 from machine import Pin, I2C 3 from shi106 import SH11@6_I2C 4 import framebuf 5 6 WIDTH = 128 # oled display width 7 HEIGHT = 32 # oled display height       Using a SH1106-based OLED graphics display 40$$

---

## 第 42 页

![第 42 页](raspberry-pi-pico-python-sdk_images\page_42.png)

$$Raspberry Pi Pico-series Python SDK       8 9 i2c = 12C(@, scl=Pin(9), sda=Pin(8), freq=200000) # Init 12C using pins GP8 & GP9 (default I2C@ pins) 1@ print("I2C Address : "thex(i2e.scan()[@]).upper()) # Display device address 11 print("I2C Configuration: "+str(i2c)) # Display I2C config 12 13 14. oled = SH11Q6_I2C(WIDTH, HEIGHT, i2c) # Init oled display 15 16 # Raspberry Pi logo as 32x32 bytearray 17 buffer = x88 | ' \xc1\x83\x80\xO2A\x82 @\xO@2A\x82@\ xO2\xc1\xc2@\x02\xf6>\xcO\xO1 \xfc=\x80\ \x18\x18\x86\x01\x88\x10\x80\x80\x8c 18 19 # Load the raspberry pi logo into the framebuffer (the image is 32x32) 20 fb = framebuf.FrameBuffer(buffer, 32, 32, framebuf.MONO_HLSB) 21 22 # Clear the oled display in case it has junk on it. 23 oled..fi11(@) 24 25 # Blit the image from the framebuffer to the oled display 26 oled.blit(fb, 96, Q) 27 28 # Add some text 29 oled..text("Raspberry Pi",5,5) 30 oled..text("Pico",5,15) 31 32 # Finally update the oled display so the image & text is displayed 33 oled..show()   sh1106.py $H1106 Driver Obtained from https://github.com/robert-hh/SH1106 Pico MicroPython Examples: https://github.com/raspberrypi/pico-micropython-examples/blob/master/i2c/1 1 06oled/sh1106.py   1# 2 # MicroPython SH1186 OLED driver, I2C and SPI interfaces 3 # 4 # The MIT License (MIT) 5 # 6 # Copyright (c) 2016 Radomir Dopieralski (@deshipu), 7# 2617 Robert Hammelrath (@robert-hh) 8 # 9 # Permission is hereby granted, free of charge, to any person obtaining a copy 10 # of this software and associated documentation files (the “Software"), to deal 11 # in the Software without restriction, including without limitation the rights 12 # to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 13 # copies of the Software, and to permit persons to whom the Software is 14 # furnished to do so, subject to the following conditions: 16 # The above copyright notice and this permission notice shall be included in 17 # all copies or substantial portions of the Software. 19 # THE SOFTWARE TS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 20 # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 21 # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 22 # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 23 # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 24 # OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN       Using a SH1106-based OLED graphics display 41$$

---

## 第 43 页

![第 43 页](raspberry-pi-pico-python-sdk_images\page_43.png)

$$Raspberry Pi Pico-series Python SDK | 25 # THE SOFTWARE. 26 # 27 # Sample code sections 28 # ------------ SPI 29 # Pin Map SPI 30 # - 3V3 - Vee 31 # - GND - Gnd 32 # - GPIO 11 - DIN / MOST fixed 33 # - GPIO 1@ - CLK / Sck fixed 34 # - GPIO0 4 - CS (optional, if the only connected device, connect to GND) 35 # - GPIO 5 - D/C 36 # - GPIO 2 - Res 37 # 38 # for CS, D/C and Res other ports may be chosen. 39 # 4@ # from machine import Pin, SPI 41 # import sh11@6 42 43 # spi = SPI(1, baudrate=190000@) 44 # display = sh1106.SH11@6_SPI(128, 64, spi, Pin(5), Pin(2), Pin(4)) 45 # display.sleep(False) 46 # display. fi11(@) 47 # display.text('Testing 1', 8, 8, 1) 48 # display. show() 49 # 5Q # --------------- T2€@ ------------------ 51 # 52 # Pin Map T2C 53 # - 3V3 - Vee 54 # - GND - Gnd 55 # - GPIO 5 - CLK / SCL 56 # - GPIO 4 - DIN / SDA 57 # - GPIO 2 - Res 58 # - GND - 59 # - GND - D/C 60 # 61 # 62 # from machine import Pin, IT2C 63 # import sh11@6 64 # 65 # i2c = I2C(@, scl=Pin(5), sda=Pin(4), freq=4e000@) 66 # display = sh11@6.SH11@6_I2C(128, 64, i2c, Pin(2), @x3c) 67 # 68 # display. fi11(@) 69 # display.text('Testing 1’, 8, 8, 1) 78 # display.show() 71 72 from micropython import const 73 import utime as time 74 import framebuf 75 76 77 # a few register definitions 78 _SET_CONTRAST = const(@x81) 79 _SET_NORM_INV = const(@xa6) 8@ _SET_DISP = const(@xae) 81 _SET_SCAN_DIR = const(@xc@) 82 _SET_SEG_REMAP = const(@xa@) 83 _LOW_COLUMN_ADDRESS = const(@x@@) 84 _HIGH_COLUMN_ADDRESS = const(@x1@) 85 _SET_PAGE_ADDRESS = 86 87 88 class SH1106: | Using a SH1106-based OLED graphics display 42$$

---

## 第 44 页

![第 44 页](raspberry-pi-pico-python-sdk_images\page_44.png)

| 89 90 91 92 93 94 95 96 97 99 100 101 102 103 104 105 106 107 108 109 118 self.init_display() 171 112 113 self.reset() 114 self.fi11(0) 115 self.poweron() 116 self.show() 117 118 119 120 121 122 123 124 125 126 127 128 else: 129 138 131 132 self.show() 133 134 135 136 137 138 139 148 141 142 143 144 145 146 147 148 149 158 151 1) 152 | A3

---

## 第 45 页

![第 45 页](raspberry-pi-pico-python-sdk_images\page_45.png)

$$ss 153 154 155 res(1) 156 time.sleep_ms(1) 157 res(@) 158 time.sleep_ms(2@) 159 res(1) 160 time.sleep_ms(2@) 161 162 164 165 external_vcc=False): 166 167 168 169 170 171 172 173 174 175 176 177 178 179 188 181 182 183 super().reset(self.res) 184 185 187 188 external_vcc=False): 189 198 191 192 193 194 195 196 197 198 199 200 201 202 203 204 self.cs(1) 205 self.dc(Q) 206 self.cs(Q) 207 self.spi.write(bytearray([cmd])) 208 self.cs(1) 209 else: 210 self.dc(Q) 211 self.spi.write(bytearray([cmd])) 212 213 214 215 216 self.cs(1) ss 44$$

---

## 第 46 页

![第 46 页](raspberry-pi-pico-python-sdk_images\page_46.png)

$$Raspberry Pi Pico-series Python SDK t 1       217 self .dce(1) 218 self .cs(Q) 219 self .spi.write(buf) 220 self .cs(1) 221 else: 222 self .dce(1) 223 self .spi.write(buf) 224 225 def reset(self): 226 super().reset(self.res)   Bill of Materials       Table 5. A list of . . materials required for item Quantity Details th ft ; example Breadboard q generic part Raspberry Pi Pico q htips://www.raspberrypi.com/ products/raspberry-pi-pico/   Monochrome 128x128 I2C OLED a https://shop.pimoroni.com/products/ Display 1-12-oled-breakout? variant=29421050757203   Using PIO to drive a set of NeoPixel Ring (WS2812 LEDs) Combination of the PIO WS2812 demo with the Adafruit ‘essential’ NeoPixel example code to show off color fills, chases and of course a rainbow swirl on a 16-LED ring. Wiring information See Figure 11 for wiring instructions. Figure 11. Wiring the 16-LED NeoPixel Ring to Pico                                            BOOD®, GODS OEOBS FECTS OT MECC TOTOTOTO) CESSES TEESE DODDS FOES i ECEECE FESTCS     2 fea - in = 2 OT & 2 re 2 R a mR TOR OS                                         TOO BB Bos UBS SSSSEE SESTHE SHSBY DOSSO 8SE65 Senas b = SESS SESES SHEESH SHESBE Se¢ee BBS SESe <@ aha . 2 2 4 3     List of Files A list of files with descriptions of their function;   t 1 Using PIO to drive a set of NeoPixel Ring (WS2812 LEDs) 45$$

---

## 第 47 页

![第 47 页](raspberry-pi-pico-python-sdk_images\page_47.png)

$$Raspberry Pi Pico-series Python SDK it neopixel_ring.py The example code. Pico MicroPython Examples: htips://github.com/raspberrypi/pico-micropython-examples/blob/master/pio/neopixel_ring/neopixel_ring.py # Example using PIO to drive a set of WS2812 LEDs. import array, time from machine import Pin import rp2 # Configure the number of WS2812 LEDs. NUM_LEDS = 16 PIN_NUM = 6 18 = = 8.2 brightness 11 12 @rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24) 13 def ws2812(): 14 T1 2 15 T2 5 16 T3 3 17 wrap_target() 18 label("bitloop") 19 out(x, 1) side(@) [T3 1] 20 jmp(not_x, "do_zero") side(1) [771 1] 21 jmp ("bitloop") side(1) [T2 1] 22 label("do_zero") 23 nop() side(@) [T2 1] 24 wrap() 25 26 27 # Create the StateMachine with the ws2812 program, outputting on pin 28 sm = = rp2.StateMachine(@, ws2812, freq=8_90@_800, sideset_base=Pin(PIN_NUM) ) 29 38 # Start the StateMachine, it will wait for data on its FIFO. 31 sm.active(1) 32 33 # Display a pattern on the LEDs via an array of LED RGB values. 34 ar = = array.array("I", [@ for _ in range(NUM_LEDS) ]) 35 36 37 def pixels_show(): 38 dimmer_ar = = array.array("I”, [@ for _ in range(NUM_LEDS) ]) 39 for i,c in enumerate(ar): = = 40 r int(((c >> 8) & @xFF) * brightness) re g = = int(((c >> 16) & @xFF) * brightness) = 42 b = int((c & @xFF) * brightness) = = 43 dimmer_ar[i] (g<<16) + (r<<8) + b 44 sm.put(dimmer_ar, 8) 45 time.sleep_ms(1@) 46 47 def pixels_set(i, color): 48 ar[i] = (color[1]<<16) + (color[@]<<8) + color[2] 49 58 def pixels_fill(color): 51 for i in range(len(ar)): 52 pixels_set(i, color) 53 54 def color_chase(color, wait) 55 for i in range(NUM_LEDS) 56 pixels_set(i, color) 57 time.sleep(wait) it Using PIO to drive a set of NeoPixel Ring (WS2812 LEDs) 46$$

---

## 第 48 页

![第 48 页](raspberry-pi-pico-python-sdk_images\page_48.png)

$$Raspberry Pi Pico-series Python SDK       58 pixels_show() 59 time.sleep(@.2) 60 61 def wheel(pos): 62 # Input a value @ to 255 to get a color value. 63 # The colours are a transition r - g - b - back to r. 64 if pos < @ or pos > 255: 65 return (@, @, @) 66 if pos < 85: 67 return (255 - pos * 3, pos * 3, @) 68 if pos < 178: 69 pos -= 85 78 return (@, 255 - pos * 3, pos * 3) 71 pos -= 170 72 return (pos * 3, 6, 255 - pos * 3) 73 74 def rainbow_cycle(wait) : 75 for j in range(255): 76 for i in range(NUM_LEDS): 77 re_index = (i * 256 // NUM_LEDS) + j 78 pixels_set(i, wheel(rc_index & 255)) 79 pixels_show() 88 time.sleep(wait) 81 82 BLACK = (@, @, Q) 83 RED = (255, @, Q) 84 YELLOW = (255, 150, @) 85 GREEN = (@, 255, Q) 86 CYAN = (@, 255, 255) 87 BLUE = (@, 6, 255) 88 PURPLE = (180, 9, 255) 89 WHITE = (255, 255, 255) 9@ COLORS = (BLACK, RED, YELLOW, GREEN, CYAN, BLUE, PURPLE. WHITE) 91 92 print("fills") 93 for color in COLORS: 94 pixels_fill(color) 95 pixels_show() 96 time.sleep(@.2) 97 98 print("chases") 99 for color in COLORS: 108 color_chase(color, @.@1) 101 102 ) 103 rainbow_cycle(@)   Bill of Materials   Table 6. A list of     materials required for ltem Quantity Details the example Breadboard q generic part Raspberry Pi Pico q htips://www.raspberrypi.com/ products/raspberry-pi-pico/   NeoPixel Ring q hitps://www.adafruit.com/product/ 1463       Using PIO to drive a set of NeoPixel Ring (WS2812 LEDs) AT$$

---

## 第 49 页

![第 49 页](raspberry-pi-pico-python-sdk_images\page_49.png)

$$Raspberry Pi Pico-series Python SDK     Using UART on the Raspberry Pi Pico Send data from the UART1 port to the UARTO port. Other things to try;   uart@ = UART(@)   which will open a UART connection at the default baudrate of 115200, and   uart@.readline()   which will read until the CR (\r) and NL (\n) characters, then return the line. Wiring information See Figure 12 for wiring instructions.   Figure 12. Wiring two - ee ee ABABA BAaABAS BAaBAB BAABAS BAaBASA BO BA® BOBAB BOGS DOGGIE OGG of the Pico’s ports together. Be sure to wire UARTO TX to : = = ; UARTT RX and UARTO ee ee aS 20) 25 0 AX to UARTI TX. " SE SOOSOEE                    ooo OOO SSL LEO DOO BA BAD ORS DOGS         20) 25 30)                               SSSSS SSSSS SESSE TESTS FESOCD SESSS SSSEE STETSTSG   fritzing   List of Files A list of files with descriptions of their function; uart.py The example code. Pico MicroPython Examples: https://github.com/raspberrypi/pico-micropython-examples/blob/master/uart/loopback/uart. py   1 from machine import UART, Pin 2 import time 3 4 uart1 = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9)) 5 6 uart@ = UART(@, baudrate=9600, tx=Pin(@), rx=Pin(1)) 7 8 txData = b'hello world\n\r'       Using UART on the Raspberry Pi Pico 48$$

---

## 第 50 页

![第 50 页](raspberry-pi-pico-python-sdk_images\page_50.png)

$$Raspberry Pi Pico-series Python SDK it uart1.write(txData) 10 time.sleep(@.1) 11 rxData = = bytes() 12 while uart@.any() > @: 13 rxData += uart@.read(1) 14 15 print(rxData.decode('utf-8')) Bill of Materials Table 7. A list of tem Quantity Details materials required for the example Breadboard 1 generic part Raspberry Pi Pico 1 htips://www.raspberrypi.com/ products/raspberry-pi-pico/ it 49 Using UART on the Raspberry Pi Pico$$

---

## 第 51 页

![第 51 页](raspberry-pi-pico-python-sdk_images\page_51.png)

Raspberry Pi Pico-series Python SDK D tation Rel ust 15 October 2024 © Corrected minor typos and formatting issues. ° Switched back to separate release histories per PDF. 02 May 2024 ° Corrected minor typos and issues. 02 Feb 2024 ° Corrected minor typos and issues. ° Updated documentation to include information about Raspberry Pi 5. 14 Jun 2023 © Corrected minor typos and formatting issues. ° Added documentation around Bluetooth support for Raspberry Pi Pico W. 03 Mar 2023 ° Corrected minor typos and issues. ° Corrected SMT footprint of Raspberry Pi Pico. ° Added a wireless networking example to the Python documentation. 01 Dec 2022 ° Corrected minor typos and issues. ° Replaced SDK library documentation with links to the online version. 30 Jun 2022 © Corrected minor typos and formatting issues. 15 October 2024 50

---

## 第 52 页

![第 52 页](raspberry-pi-pico-python-sdk_images\page_52.png)

Raspberry Pi Pico-series Python SDK 17 Jun 2022 ° Corrected minor typos and issues. ° Elaborated explanation of SDK configuration. 04 Nov 2021 © Corrected minor typos and formatting issues. 03 Nov 2021 © Corrected minor typos and formatting issues. ° Described SDK "panic" handling. 30 Sep 2021 ° Corrected minor typos and issues. 23 Jun 2021 ° Corrected minor typos and issues. 07 Jun 2021 ° Corrected minor typos and issues. ° Added SDK release history. 13 Apr 2021 © Corrected minor typos and formatting issues. ° Clarified that all source code in the documentation is under the 3-Clause BSD license. 07 Apr 2021 ° Corrected minor typos and issues. 05 Mar 2021 ° Corrected minor typos and issues. 17 Jun 2022 51

---

## 第 53 页

![第 53 页](raspberry-pi-pico-python-sdk_images\page_53.png)

Raspberry Pi Pico-series Python SDK 23 Feb 2021 ° Corrected minor typos and issues. ° Changed font. ° Updated MicroPyithon build instructions. ° Added MicroPython UART example code. ° Updated Thonny insiructions. 01 Feb 2021 © Corrected minor typos and formatting issues. ° Explained how to access a MicroPython REPL over UART. 26 Jan 2021 ° Corrected minor typos and issues. ° Renamed books and optimised size of output PDFs. 21 Jan 2021 ° Initial release. 23 Feb 2021 52

---

## 第 54 页

![第 54 页](raspberry-pi-pico-python-sdk_images\page_54.png)

SE 5 Raspberry Pi Raspbeny Pi is a trademark of Rasplemy Pi Lid     Ras pberhyabisetcl

---

