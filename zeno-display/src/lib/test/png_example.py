##############################################################################
#
# Example of the PNG image decoder Usage.
# For dragging to work reasonable, make sure LV_CACHE_DEF_SIZE is not 0!
#
##############################################################################

import usys as sys

sys.path.append("")  # See: https://github.com/micropython/micropython/issues/6419

import lvgl as lv

lv.init()
import screen

# Init


scr = lv.obj()
try:
    script_path = __file__[: __file__.rfind("/")] if __file__.find("/") >= 0 else "."
except NameError:
    script_path = ""

# Load the image

with open("%s/on_off.png" % script_path, "rb") as f:
    png_data = f.read()
png_image_dsc = lv.image_dsc_t({"data_size": len(png_data), "data": png_data})

with open("%s/off.png" % script_path, "rb") as f:
    png_data = f.read()
png_image_dsc2 = lv.image_dsc_t({"data_size": len(png_data), "data": png_data})

image1 = lv.image(scr)
image1.set_src(png_image_dsc2)
image1.set_pos(0, 0)

image1 = lv.image(scr)
image1.set_src(png_image_dsc)
image1.set_pos(0, 0)

lv.screen_load(scr)
# Drag handler
# python LVGLImage.py ./src/off.png --ofmt BIN --cf XRGB8888 -o ./src/

# def drag_event_handler(e):
#     self = e.get_target_obj()
#     indev = lv.indev_get_act()
#     vect = lv.point_t()
#     indev.get_vect(vect)
#     x = self.get_x() + vect.x
#     y = self.get_y() + vect.y
#     self.set_pos(x, y)


# # Register drag handler for images

# for image in [image1, image2]:
#     image.add_flag(image.FLAG.CLICKABLE)
#     image.add_event_cb(drag_event_handler, lv.EVENT.PRESSING, None)
