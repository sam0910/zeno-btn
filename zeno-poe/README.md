# 1. POE LAN Module

#### POE Firmware
```
source $FW/esp-idf/export.sh       
esptool.py --chip esp32 --port $PORT --baud 460800 write_flash -z 0x1000  ./bin/mpy_olimex.bin
```

