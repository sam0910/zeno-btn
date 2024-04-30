from auart.half_duplex_sender import HalfDuplexSender
import uasyncio as asyncio
from machine import UART, reset, Timer, wake_reason
import constants as c
import time
from file_downloader import FileDownloader
import json
import common
import gc
import lvgl as lv
import sys
from logsam import Log
import uos as os


class ReceiverPOE:
    def __init__(self):
        self.log = Log(__name__)
        self.loop = asyncio.get_event_loop()
        self.uart = UART(1, baudrate=9600, tx=c.TX, rx=c.RX)
        self.duplex = HalfDuplexSender(self.uart, timeout=1000)
        self.sending = False
        self.handshaked = False
        self.transmitting = False
        self.loader = FileDownloader()
        self.config = {}
        self.image_config = {}
        self.device_id = 0
        self.checksum = ""
        self.download_result = False
        self.state_img = {"on": None, "off": None}
        self.current_state = False
        self.layer_top = lv.layer_top()
        self.error_text = None
        self.finish_reboot = False

    def start(self):
        self.device_id = common.get_device_id()
        self.config = self.loader.load_json("/config.json")
        self.image_config = self.loader.load_json("/images.json")

    async def direct_write(self, data):
        await self.duplex.swriter.awrite(b"" + data + "\r\n")

    async def set_download_mode(self, filename=""):
        self.display_error(f"DOWNLOADING... {filename}")
        self.transmitting = True
        self.log.info("Setting download mode")

        try:
            self.log.info("[Receiving] ", filename)
            chunk = bytearray(c.CHUNK_SIZE)

            with open(f"/{filename}", "wb") as file:
                STOP = False
                while True:
                    # b'\x00IEND\xaeB`\x82EOF\n' END\xaeB`\x82EOF\n"
                    chunk = await self.duplex.sreader.read(c.CHUNK_SIZE)
                    lenchunk = len(chunk)  # MAX 120

                    if chunk.endswith(b"EOF\n"):
                        STOP = True
                        file.write(chunk[:-4])

                    elif lenchunk < c.CHUNK_SIZE:
                        STOP = True
                        file.write(chunk)

                    if STOP:
                        self.transmitting = False
                        chunk = None
                        gc.collect()
                        self.log.info("{}Kb free".format(gc.mem_free() // 1024))
                        self.checksum += filename
                        raise asyncio.CancelledError
                    else:
                        file.write(chunk)

        except asyncio.CancelledError:
            self.transmitting = False
            self.display_error(f"DONE... {filename}")
            self.log.info("[LOOP] receive_file DONE.")
        finally:
            self.transmitting = False

    async def reboot(self):
        self.log.info("Rebooting ...")
        await asyncio.sleep(2)
        common.reset()

    async def normal_boot(self):
        self.log.info("Normal Booting ...")
        await asyncio.sleep(2)

    async def _recv(self):
        while True:
            if self.transmitting is False:
                res = await self.duplex.sreader.readline()
                res = res.strip().decode()
                if res.startswith("DUPLEX"):
                    self.log.info("                 [Recv DUPLEX]", res)
                    cmd = res.split("@")[1]
                    if cmd == "CONFIG":
                        self.config = json.loads(res.split("@")[2])
                        self.loader.save_json(self.config, "/config.json")
                        await self.direct_write("CONFIG@OK")

                    elif cmd.startswith("DOWNLOAD"):
                        filename = res.split("@")[2]
                        self.loop.create_task(self.set_download_mode(filename))
                        await self.direct_write("DOWNLOAD@OK")

                    elif cmd.startswith("ALLDONE"):
                        self.loop.create_task(self.reboot())
                        await self.direct_write("ALLDONE@OK")

                    elif cmd.startswith("COMPLETE"):
                        chechksum = res.split("@")[2]
                        self.log.info("local ", self.checksum)
                        self.log.info("remote", chechksum)
                        if self.checksum == chechksum:
                            self.log.info("Checksum OK")
                            await self.direct_write(
                                "COMPLETE@OK@{}".format(self.checksum)
                            )
                        else:
                            self.log.info("Checksum FAIL")
                            await self.direct_write(
                                "COMPLETE@FAIL@{}".format(self.checksum)
                            )

                    elif cmd == "IMAGE_CONFIG":
                        self.image_config = json.loads(res.split("@")[2])
                        self.loader.save_json(self.image_config, "/images.json")
                        await self.direct_write("IMAGE_CONFIG@OK")

                    elif cmd == "HANDSHAKE" and self.finish_reboot:
                        self.handshaked = True
                        await self.direct_write(
                            "HANDSHAKE@OK@{}@{}@{}".format(
                                self.config["version"],
                                self.image_config["version"],
                                self.device_id,
                            )
                        )
                    elif cmd == "BOOT":
                        self.loop.create_task(self.canvas())
                        await self.direct_write("BOOT@OK")

                    elif cmd == "RESET":
                        await asyncio.sleep(3)
                        common.reset()

                    elif cmd.startswith("ERROR"):
                        code = res.split("@")[2]
                        self.display_error(code)

                else:
                    self.duplex.response = res  # Append to list of lines
                    self.duplex.delay.trigger(
                        self.duplex.timeout
                    )  # Got something, retrigger timer
            else:
                await asyncio.sleep(1)

    async def send_duplex_cmd(self, cmd):
        self.sending = True
        res = await self.duplex.send_command("DUPLEX@{}".format(cmd))
        self.sending = False
        return res

    async def main(self):
        while True:
            for cmd in ["RUN", "AT", "TEST"]:
                self.log.info("[Send]", cmd)
                res = await self.send_duplex_cmd(cmd)
                # can use b''.join(res) if a single string is required.
                if res:
                    self.log.info("[SendResponse]", res)
                else:
                    self.log.info("[SendResponse], timeout")

            self.log.info("Sleeping for 3s")
            await asyncio.sleep(3)

    async def run(self):
        self.loop.run_forever()

    async def task_handler(self):
        try:
            await asyncio.sleep_ms(4)
            while True:
                lv.task_handler()
                await asyncio.sleep_ms(10)

        except asyncio.CancelledError:
            return

    def get_image(self, filename):
        try:
            with open("/{}".format(filename["url"]), "rb") as f:
                data = f.read()
                dsc = lv.image_dsc_t({"data_size": len(data), "data": data})

            img = lv.image(lv.screen_active())
            img.set_src(dsc)
            img.align(lv.ALIGN.TOP_LEFT, filename["x"], filename["y"])
            img.add_flag(lv.obj.FLAG.CLICKABLE)
            img.remove_flag(lv.obj.FLAG.SCROLLABLE)

            # img.align(lv.ALIGN.CENTER, 0, 0)
            self.log.info("Image loaded", filename["url"])
            return img
        except Exception as e:
            self.log.info(e)
            return None

    def go_for_factory_reset(self, evt):
        self.log.info("Factory Reset confirmed.....")

    async def factory_reset(self):
        def go_for(evt):
            self.log.info("confirmed.....", evt)
            common.bl(0)
            try:
                for item in os.listdir("/reset"):
                    os.remove(f"/{item}")
                    with open(f"/reset/{item}", "rb") as source_file:
                        with open(f"/{item}", "wb") as destination_file:
                            destination_file.write(source_file.read())

            except Exception as e:
                self.log.info(e)

            # # finally:
            self.loop.create_task(self.send_duplex_cmd("HARD_RESET"))
            self.loop.create_task(self.reboot())

        self.log.info("Factory Reset")
        await asyncio.sleep(10)
        if self.reset_clicked >= 100:
            obj = lv.button(self.layer_top)
            obj.set_size(120, 40)
            obj.align(lv.ALIGN.CENTER, 0, 0)
            self.log.info("Factory Reset add event cb")
            obj.add_flag(lv.obj.FLAG.CLICKABLE)
            obj.add_event_cb(go_for, lv.EVENT.CLICKED, None)

            label = lv.label(obj)
            label.set_text("HARD RESET")
            label.set_style_text_color(lv.color_hex(0xFFFFFF), lv.PART.MAIN)
            label.set_style_text_font(lv.font_montserrat_14, lv.PART.MAIN)
            label.center()

        else:
            self.reset_clicked = 0
        await asyncio.sleep(10)
        self.layer_top.clean()
        return

        # await self.send_duplex_cmd("FACTORY_RESET")
        # await asyncio.sleep(3)
        # common.reset()

    async def canvas(self):
        with open("/images.json", "r") as f:
            data = f.read()
            filelist = json.loads(data)
        images = filelist["images"]
        if len(images) == 0:
            return
        else:
            self.log.info("Images:", len(images))
            lv.screen_active().clean()

        # sort by z,
        images = sorted(images, key=lambda x: x["z"])
        common.bl(0)
        for img in images:
            if img["state"] == "on":
                self.state_img["on"] = self.get_image(img)

            elif img["state"] == "off":
                self.state_img["off"] = self.get_image(img)

            elif img["state"] != "boot":
                retains = self.get_image(img)
                retains.add_event_cb(self.show_reset, lv.EVENT.CLICKED, None)

            await asyncio.sleep(0.1)

        self.state_img["on"].add_event_cb(self.show_off, lv.EVENT.CLICKED, None)
        self.state_img["off"].add_event_cb(self.show_on, lv.EVENT.CLICKED, None)

        if self.current_state:
            self.show_on(None, False)
        else:
            self.show_off(None, False)

        common.bl(1)
        self.layer_top.clean()
        # except Exception as e:
        #     self.log.info(e)
        # finally:
        #     return

    def display_error(self, code):
        self.log.info("Error Code:", code)
        try:
            if code == "CLEAN":
                self.layer_top.clean()
                self.error_text = None
                return

            if self.error_text is None:
                self.error_text = lv.label(self.layer_top)
                self.error_text.set_long_mode(lv.label.LONG.WRAP)
                self.error_text.set_width(210)
                self.error_text.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
                self.error_text.align(lv.ALIGN.CENTER, 0, 90)
                self.error_text.set_style_text_color(
                    lv.color_hex(0xFFFFFF), lv.PART.MAIN
                )
                self.error_text.set_style_text_font(lv.font_montserrat_14, lv.PART.MAIN)

            if code == "LAN_ERROR":
                code_text = "NO IP ADDRESS"
            elif code == "CONFIG_ERROR":
                code_text = "NO ACCESS TO CONFIG"
            elif code == "IMAGE_CONFIG_ERROR":
                code_text = "NO IMAGE CONFIG"
            elif code == "MQTT_ERROR":
                code_text = "MQTT CONNECT FAILED"
            else:
                code_text = code

            self.error_text.set_text(code_text)
        except Exception as e:
            print(e)

    def show_reset(self, evt):
        self.log.info("Reset clicked", self.reset_clicked)
        self.reset_clicked += 1
        if self.reset_clicked >= 12 and self.reset_clicked < 100:
            self.log.info("create_task factory_reset", self.reset_clicked)
            self.loop.create_task(self.factory_reset())
            self.reset_clicked = 100

    def show_on(self, evt=None, beep=True):
        self.reset_clicked = 0
        self.loop.create_task(self.send_duplex_cmd("MQTT@ON"))
        if beep:
            common.beep_array("on")
        if evt:
            code = evt.get_code()
            target = evt.get_target()
            self.log.info(" {},Target:{} event".format(code, target))

        self.current_state = True
        self.state_img["on"].remove_flag(lv.obj.FLAG.HIDDEN)
        self.state_img["off"].add_flag(lv.obj.FLAG.HIDDEN)

    def show_off(self, evt=None, beep=True):
        self.reset_clicked = 0
        self.loop.create_task(self.send_duplex_cmd("MQTT@OFF"))
        if beep:
            common.beep_array("off")
        if evt:
            code = evt.get_code()
            target = evt.get_target()
            self.log.info(" {},Target:{} event".format(code, target))

        self.current_state = False
        self.state_img["off"].remove_flag(lv.obj.FLAG.HIDDEN)
        self.state_img["on"].add_flag(lv.obj.FLAG.HIDDEN)

    async def reboot_now(self):
        try:
            ws = wake_reason()
            self.log.info("Wake Reason", ws)
            await asyncio.sleep(2)
            while True:
                self.log.info("SENDING REBOOT_NOW")
                if ws == 0 and self.handshaked is False:
                    res = await self.send_duplex_cmd("REBOOT_NOW")
                    self.log.info(res)
                    if res == "REBOOT_NOW@OK":
                        self.finish_reboot = True
                        raise asyncio.CancelledError
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            self.log.info("[reboot_now] finished")

    def init(self):
        self.loop.create_task(self._recv())
        self.loop.create_task(self.task_handler())
        self.loop.create_task(self.reboot_now())

        self.start()

        Timer(1).init(period=5, mode=Timer.PERIODIC, callback=lambda t: lv.tick_inc(5))


if __name__ == "__main__":
    poe = ReceiverPOE()
    poe.init()
    asyncio.run(poe.run())

    # try:
    #     poe = ReceiverPOE()
    #     poe.init()
    #     asyncio.run(poe.run())

    # except:
    #     self.log.info("Unexpected error:", sys.exc_info()[0])
    # finally:
    #     poe.loop = asyncio.new_event_loop()
    #     common.reset()
