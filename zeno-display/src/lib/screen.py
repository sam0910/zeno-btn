import lvgl as lv
import time
import constants as c
from ili9XXX import (
    st7789,
    PORTRAIT,
    COLOR_MODE_BGR,
    COLOR_MODE_RGB,
    LANDSCAPE,
    DISPLAY_TYPE_ILI9488,
    REVERSE_LANDSCAPE,
)
from machine import Pin
from logsam import Log

# BL = Pin(c.BL, Pin.OUT, value=1)


disp = st7789(
    mosi=c.MOSI,
    clk=c.SCK,
    cs=c.CS,
    dc=c.DC,
    rst=c.RST,
    # power=c.POWER,
    backlight=c.BL,
    power=-1,
    backlight_on=0,
    power_on=0,
    spimode=0,
    mhz=60,
    factor=2,
    hybrid=True,
    width=240,
    height=320,
    start_x=0,
    start_y=0,
    colormode=COLOR_MODE_BGR,
    rot=PORTRAIT,
    invert=True,
    double_buffer=True,
    half_duplex=True,
    asynchronous=False,
    initialize=True,
    color_format=lv.COLOR_FORMAT.RGB565,
    swap_rgb565_bytes=True,
)


time.sleep_ms(50)
disp.disp_drv.set_default()
