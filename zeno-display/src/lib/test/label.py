import lvgl as lv
import screen

lv.init()

label = lv.label(lv.screen_active())
label.set_text("Hello world")
label.set_style_text_color(lv.color_hex(0x000000), lv.PART.MAIN)
label.set_style_bg_color(lv.color_hex(0x000000), lv.PART.MAIN)

label.align(lv.ALIGN.CENTER, 0, 0)

lv.tick_inc(5)
lv.task_handler()
