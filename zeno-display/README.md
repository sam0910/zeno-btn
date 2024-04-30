## 1. ./BIN/README.md


## V3-02 Firmware
```
source $FW/esp-idf/export.sh      
esptool.py -p $PORT -b 460800 --before default_reset --after hard_reset --chip esp32  write_flash --flash_mode dio --flash_size detect --flash_freq 40m 0x1000 ./bootloader.bin 0x8000 ./partition-table.bin 0x10000 ./micropython.bin
```


5.5 * 2
4,5,6,8

