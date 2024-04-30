import lvgl as lv
import gc
import time


def draw_img(layer, x, y, img_src, draw_dsc):
    """
    canvas.draw_img(80, 50, lv.ex_logo_80, img_dsc_t)
    """
    draw_dsc.src = img_src
    coord = lv.area_t()
    coord.x1 = x
    coord.y1 = y
    coord.x2 = coord.x1 + img_src.header.w - 1
    coord.y2 = coord.y1 + img_src.header.h - 1
    lv.draw_image(layer, draw_dsc, coord)


def canvas():
    with open("/ex_logo_80.png", "rb") as f:
        data = f.read()
        image_dsc_on = lv.image_dsc_t({"data_size": len(data), "data": data})

    img_dsc = lv.draw_image_dsc_t()
    img_dsc.init()

    cbuf = bytearray(lv.canvas.buf_size(320, 480, 32, lv.DRAW_BUF_STRIDE_ALIGN))
    canvas = lv.canvas(lv.screen_active())
    canvas.set_buffer(cbuf, 320, 480, lv.COLOR_FORMAT.XRGB8888)
    canvas.center()
    canvas.align(lv.ALIGN.CENTER, 0, 0)
    canvas.fill_bg(lv.color_hex(0xFF0000), lv.OPA.COVER)
    layer = lv.layer_t()
    canvas.init_layer(layer)

    draw_img(layer, 0, 0, image_dsc_on, img_dsc)
    # canvas.draw_text(90, 12, 100, label_dsc, "session")
    canvas.finish_layer(layer)
    lv.task_handler()
    lv.tick_inc(5)
    time.sleep_ms(5)
    lv.task_handler()


import screen

# image = lv.image(lv.screen_active())
# image.align(lv.ALIGN.CENTER, 0, 0)
# print("Memory {}Kb ".format(gc.mem_free() // 1024))
# image.set_src(image_dsc_off)

canvas()


lv.task_handler()
lv.tick_inc(5)
time.sleep_ms(5)
lv.task_handler()
print("Memory {}Kb ".format(gc.mem_free() // 1024))
