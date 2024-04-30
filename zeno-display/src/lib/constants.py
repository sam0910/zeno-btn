from micropython import const

# ESP_EN resets the ESP32 module
# GPIO0, GPIO2 – are boot mode bootstrap pins make sure they are properly configured during power up
# GPIO1, GPIO3 are used for USB programming, they can be freed up if you
# GPIO2, GPIO14, GPIO15 are used for the SD-card, if no SD card they are free to use
# GPIO2, GPIO4, GPIO5, GPIO13, GPIO14, GPIO15, GPIO16, GPIO36 are shared on both UEXT
# and EXT headers so if you use them on the one connector do not use on the other
# GPI39 is connected to measure external power supply voltage
# GPI34 is connected to user button and has 10K pullup
# GPI35 is free to use by default but may be connected to measure the LiPo battery voltage
# if you close BAT_SENS_E1 jumper

# 0,1,2,3,4,5  39,36,35,34,33,32  16,15,14,13
# 0,1,2,3,4,5    15,14,13
# 0   2   4 5    15 14
# #OLIMEX
# MISO = const(32)
# MOSI = const(2)
# SCK = const(14)
# CS = const(15)
# DC = const(4)
# RST = const(0)
# BL = const(5)
# SCL = const(16)
# SDA = const(13)
# RST_NONE = const(-1)
# POWER = const(-1)
# BL_NONE = const(-1)

# PICO
MISO = const(-1)
MOSI = const(13)
SCK = const(14)
CS = const(15)
DC = const(25)
RST = const(5)
BL = const(27)
SDA = const(21)
SCL = const(22)
RST_NONE = const(-1)
POWER = const(-1)
BL_NONE = const(-1)

TX = const(33)  # 39 of POE(RX) -> 32
RX = const(39)  # 13 of POE(TX)
BUZZER = const(2)
CHUNK_SIZE = const(120)

# # 3.2inch pinmap
# RST - 21 /RESET_NC
# Master synchronizes reset, Active Low. RC reset on board.

# CS - 23 LCD_/CS
# LCD chip select input pin (“Low” enable).

# SCK - 24 D/C(SCL)
# This pin is used serial interface clock in 3-wire 9-bit / 4-wire 8-bit

# DC - 25 /WR(D/C)
# 4-line interface: Serves as command or parameter select.

# MOSI - 27 LCD_SDI

# BL - 29 BL_ON/OFF

# SCL - 30 CTP_SCL
# SDA - 31 CTP_SDA

# GND - 40 GND
