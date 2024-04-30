import gc
from machine import Pin, wake_reason
import time
import lvgl as lv
import constants as c
from ft6x36 import ft6x36
from logsam import Log

gc.enable()
print("\n## Memory {}Kb ".format(gc.mem_free() // 1024))
# import screen


RST = Pin(c.RST, Pin.OUT, value=0)
time.sleep_ms(150)
RST.value(1)
print("## RESET Display")
time.sleep_ms(150)

import screen

touch = ft6x36(
    i2c_dev=0,
    sda=c.SDA,
    scl=c.SCL,
    freq=100000,
    addr=0x38,
    width=240,
    height=320,
    inv_x=False,
    inv_y=False,
    swap_xy=False,
)
# landscape
# touch = ft6x36(
#     i2c_dev=0,
#     sda=c.SDA,
#     scl=c.SCL,
#     freq=100000,
#     addr=0x38,
#     width=240,
#     height=320,
#     inv_x=False,
#     inv_y=True,
#     swap_xy=True,
# )

indev_drv = touch.indev_drv
print("## Touch ON\n")
