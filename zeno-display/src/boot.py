import constants as c
import lvgl as lv
import json
import time
from machine import Pin
from logsam import Log

Pin(c.BL, Pin.OUT, value=0)
print("## Backlight off\n")
# display reset
import booting


def temp_update():
    for i in range(0, 20):
        lv.tick_inc(5)
        time.sleep_ms(2)
        lv.task_handler()
        time.sleep_ms(3)


lv.screen_active().set_style_bg_color(lv.color_hex(0x000000), lv.PART.MAIN)
# temp_update()

try:
    main_logo = None
    with open("/images.json", "r") as f:
        data = f.read()
        filelist = json.loads(data)
        for key in filelist["images"]:
            if key["state"] == "boot":
                main_logo = key
                break

    if main_logo:
        print("LOGO Exitst")
        with open("/{}".format(main_logo["url"]), "rb") as f:
            data = f.read()
            dsc = lv.image_dsc_t({"data_size": len(data), "data": data})

        img = lv.image(lv.screen_active())
        img.set_src(dsc)
        img.align(lv.ALIGN.CENTER, main_logo["x"], main_logo["y"])
        temp_update()

except Exception as e:
    print(e)
finally:
    Pin(c.BL, Pin.OUT, value=1)
    print("## Backlight off\n")
