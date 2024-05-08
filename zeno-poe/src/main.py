from auart.half_duplex_sender import HalfDuplexSender
import uasyncio as asyncio
from machine import UART, reset, unique_id
import constants as c
import time
from connect_lan import ConnectLAN
from file_downloader import FileDownloader
import common
import json
import sys
import gc
from umqtt.robust import MQTTClient
import ubinascii
import os
from logsam import Log


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
        self.client = None
        self.uid = ubinascii.hexlify(unique_id()).decode()
        self.node_id = 0
        self.sub_topic = ""
        self.pub_topic = ""
        self.MQTT_ERROR = True
        # "{:02}{:02}{:02}{:02}".format(id[0], id[1], id[2], id[3])
        # A0-B7-65-F0-05-47

    def sub_cb(self, topic, msg):
        # (b"zeno/0", b"sdfs")
        self.log.info("MQTT sub_cb:", (topic, msg))
        if msg == b"reboot":
            self.loop.create_task(self.reboot())

    def load_local_config(self):
        self.config = self.loader.load_json("/config.json")
        self.image_config = self.loader.load_json("/images.json")
        self.log.info("Local Version:", self.config["version"])
        self.log.info("Local Image Version:", self.image_config["version"])

    async def mqtt_connect(self):
        self.log.info("Connecting ... MQTT")
        asyncio.sleep(4)
        try:
            self.client = MQTTClient(
                self.uid,
                self.config["mqtt_url"],
                port=self.config["mqtt_port"],
                user=self.config["mqtt_user"],
                password=self.config["mqtt_passwd"],
                keepalive=int(self.config["mqtt_keepalive"]),
            )

            self.sub_topic = b"" + self.config["mqtt_sub"].replace("[id]", str(self.node_id))
            self.pub_topic = self.config["mqtt_pub"].replace("[id]", str(self.node_id))
            self.log.info("MQTT PUB topic", self.pub_topic)
            self.log.info("MQTT SUB topic", self.sub_topic)
            self.client.set_callback(self.sub_cb)

            if not self.client.connect(clean_session=False):
                self.log.info("++New session being set up")
                self.client.subscribe(self.sub_topic)
            self.client.subscribe(self.sub_topic)
            self.MQTT_ERROR = False
        except Exception as e:
            self.MQTT_ERROR = True
            self.log.info("MQTT Connection Error: " + str(e))
            self.loop.create_task(self.error_handler_async("MQTT_ERROR"))
            raise asyncio.CancelledError
        except asyncio.CancelledError:
            pass
            self.log.info("MQTT Cancelled")

        while True:
            await asyncio.sleep_ms(500)
            self.client.check_msg()

    async def set_upload_mode(self):
        self.transmitting = True
        chunk = bytearray(c.CHUNK_SIZE)
        _checksum = ""
        images = ["/images/" + image["url"] for image in self.image_config["images"]]
        # images = ["/images/name.png", "/images/logo.png"]
        self.log.info("Images:", images)
        try:
            for filepath in images:
                n = 0
                await asyncio.sleep_ms(1500)
                file_name = filepath.split("/")[-1]
                _checksum += file_name
                ready = await self.send_duplex_cmd(f"DOWNLOAD@{file_name}")
                last_size = 0
                EOF = b"EOF\n"
                if ready == "DOWNLOAD@OK":
                    with open(filepath, "rb") as file:
                        while True:
                            chunk = file.read(c.CHUNK_SIZE)
                            lenchunk = len(chunk)

                            if not chunk:
                                if last_size <= 120 - len(EOF):  # 116
                                    await self.duplex.swriter.awrite(EOF)
                                # self.transmitting = False
                                chunk = None
                                gc.collect()
                                await asyncio.sleep_ms(1000)
                                break

                            await self.duplex.swriter.awrite(b"" + chunk)
                            last_size = lenchunk
                            n += 1
                            await asyncio.sleep_ms(100)  # Give time for the last chunk to be sent
                    # End of while
                    file.close()
                else:
                    self.log.info("Error")
                    self.loop.create_task(self.error_handler_async("DOWNLOAD ERROR FROM SENDER"))
                    await asyncio.sleep_ms(5000)
                    await self.send_duplex_cmd("RESET")
                    raise asyncio.CancelledError

                await asyncio.sleep_ms(1000)

            self.transmitting = False
            result = await self.send_duplex_cmd("COMPLETE@{}".format(_checksum))
            if result.startswith("COMPLETE"):
                remote_okay = result.split("@")[1]
                recved_checksum = result.split("@")[2]
                self.log.info("Remote Checksum:", recved_checksum)
                self.log.info("Local  Checksum:", _checksum)
                if recved_checksum == _checksum and remote_okay == "OK":
                    self.loop.create_task(self.error_handler_async("SUCCESSFULLY DOWNLOADED"))
                    self.image_config["download_need"] = 0
                    self.loader.save_json(self.image_config, "/images.json")
                    dumps = json.dumps(self.image_config)
                    self.log.info("Dumps:", dumps)
                    res2 = await self.send_duplex_cmd("IMAGE_CONFIG@{}".format(dumps))
                    if res2.startswith("IMAGE_CONFIG@OK"):
                        self.log.info("Download Complete")
                        self.loop.create_task(self.reboot())
                        await self.send_duplex_cmd("ALLDONE")

        except asyncio.CancelledError:
            pass
            self.log.info("[LOOP] send_file Done")

    async def reboot(self):
        self.log.info("Rebooting ...")
        await asyncio.sleep(2)
        common.reset()

    async def start(self):
        try:
            lan = ConnectLAN()
            lan.connect() if not lan.is_connected() else True

        except Exception:
            self.loop.create_task(self.error_handler_async("LAN_ERROR"))
            await asyncio.sleep_ms(15000)
            await self.send_duplex_cmd("RESET")
            return

        try:
            down_config = self.loader.get_json(self.config["config_url"])
            self.log.info(f"CONFIG VERSION Local:{self.config['version']} == Remote:{down_config['version']}")
            if self.config["version"] != down_config["version"]:
                self.loader.save_json(down_config, "/config.json")
                self.config = down_config

        except Exception:
            self.loop.create_task(self.error_handler_async("CONFIG_ERROR"))
            await asyncio.sleep_ms(2000)
            self.loop.create_task(self.error_handler_async(self.config["config_url"]))
            # await self.send_duplex_cmd("RESET")

        self.loop.create_task(self.mqtt_connect())
        self.loader.set_baseurl(self.config["image_url"])

        try:
            down_image_config = self.loader.get_json(
                self.config["image_url"] + "/node_{}/images.json".format(self.node_id)
            )
            self.log.info(
                f"IMAGE VERSION Local:{self.image_config['version']} == Remote:{down_image_config['version']}"
            )

            if down_image_config["version"] != self.image_config["version"]:
                self.loader.download_images(down_image_config, self.node_id)
                down_image_config["download_need"] = 1
                with open("/images.json", "w") as f:
                    json.dump(down_image_config, f)
                self.image_config = down_image_config
                self.log.info("SET DOWNLOAD NEED, download_need=1")
                self.log.info("\nimage_config", self.image_config)
        except Exception:
            self.loop.create_task(self.error_handler_async("IMAGE_CONFIG_ERROR"))
            self.loop.create_task(
                self.error_handler_async(self.config["image_url"] + "/node_{}/images.json".format(self.node_id))
            )

    def down_image_config(self, did):
        url = self.config["image_url"] + "/node_{}/images.json".format(did)
        url = "http://smartcouncil.xenoglobal.co.kr:1004/node_0/images.json"
        down_config = self.loader.get_json(url)
        if down_config["version"] != self.image_config["version"]:
            self.loop.create_task(self.error_handler_async("NEW IMAGES FOUND"))
            self.loader.download_images(down_config, did)
            self.image_config = down_config
            return True
        return False

    async def direct_write(self, data):
        await self.duplex.swriter.awrite(b"" + data + "\r\n")

    async def publish(self, topic, msg):
        if self.MQTT_ERROR is False:
            try:
                self.client.publish(topic, msg)
            except Exception as e:
                self.log.info("self.publish ERROR", e)
                pass
            finally:
                return
        else:
            return

    async def _recv(self):
        while True:
            res = await self.duplex.sreader.readline()
            res = res.strip().decode()
            if res.startswith("DUPLEX"):
                self.log.info("                 [Recv DUPLEX]", res)
                cmd = res.split("@")[1:]
                cmd = "@".join(cmd)
                if cmd == "AT":
                    await self.direct_write("AT@OK")

                elif cmd == "HARD_RESET":
                    for item in os.listdir("/reset"):
                        try:
                            if item.endswith(".json"):
                                os.remove(f"/{item}")
                                with open(f"/reset/{item}", "rb") as source_file:
                                    with open(f"/{item}", "wb") as destination_file:
                                        destination_file.write(source_file.read())
                            else:
                                os.remove(f"/images/{item}")
                                with open(f"/reset/{item}", "rb") as source_file:
                                    with open(f"/images/{item}", "wb") as destination_file:
                                        destination_file.write(source_file.read())
                        except Exception as e:
                            self.log.info("Error:", e)
                            pass
                    self.log.info("HARD RESET COMPLETE, RESETING ...")
                    reset()

                elif cmd == "REBOOT_NOW":
                    await self.direct_write("REBOOT_NOW@OK")
                    await asyncio.sleep(1)
                    reset()

                elif cmd == "BOOT":
                    await self.direct_write("BOOT@OK")

                elif cmd == "RESET":
                    await asyncio.sleep(5)
                    common.reset()

                elif cmd.startswith("MQTT"):
                    onoff = cmd.split("@")[1]
                    self.log.info("MQTT onoff:", onoff)
                    msg = {"status": onoff, "node_id": self.node_id, "mac": self.uid}
                    await self.publish(self.pub_topic, json.dumps(msg))
                    self.log.info("SENT", msg)
                    # await self.publish("MQTT@{}".format(onoff))

            else:
                self.duplex.response = res  # Append to list of lines
                self.duplex.delay.trigger(self.duplex.timeout)  # Got something, retrigger timer

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

    async def handshake(self):
        try:
            retry = 0
            await asyncio.sleep_ms(300)
            while True:
                if self.handshaked:
                    raise asyncio.CancelledError  # Exit the loop
                if retry > 60:
                    self.loop.create_task(self.error_handler_async("TIMEOUT"))
                    await asyncio.sleep_ms(5000)
                    common.reset()
                self.log.info("[Sending] Handshaking ...")

                res = await self.send_duplex_cmd("HANDSHAKE")
                if res.startswith("HANDSHAKE@OK"):

                    self.log.info(
                        "[Handshake] OK, display=config:v{}, images:v{}, poe=config:v{}, images:v{}".format(
                            res.split("@")[2], res.split("@")[3], self.config["version"], self.image_config["version"]
                        )
                    )
                    self.loader.node_id = res.split("@")[4]
                    self.node_id = res.split("@")[4]
                    #
                    await self.start()
                    #

                    if self.image_config.get("download_need"):
                        if int(self.image_config["download_need"]) == 1:
                            self.handshaked = True
                            self.loop.create_task(self.set_upload_mode())
                            self.log.info("Sending images")
                            raise asyncio.CancelledError

                    c1, c2 = False, False
                    if self.config["version"] != res.split("@")[2]:
                        dumps = json.dumps(self.config)
                        self.log.info("config.json -> Display")
                        res1 = await self.send_duplex_cmd("CONFIG@{}".format(dumps))
                        if res1.startswith("CONFIG@OK"):
                            self.log.info("[Config] OK")
                            c1 = True
                    if self.image_config["version"] != res.split("@")[3]:
                        dumps = json.dumps(self.image_config)
                        self.log.info("Dumps:", dumps)
                        res2 = await self.send_duplex_cmd("IMAGE_CONFIG@{}".format(dumps))
                        if res2.startswith("IMAGE_CONFIG@OK"):
                            self.log.info("[IMAGE_CONFIG] OK")
                            c2 = True

                        if c1 and c2 is False:
                            common.reset()

                        if c2:
                            self.log.info("SENDING IMAGE")
                            self.loop.create_task(self.set_upload_mode())

                    self.handshaked = True
                    self.loop.create_task(self.error_handler_async("CLEAN"))
                    await self.send_duplex_cmd("BOOT")
                    raise asyncio.CancelledError
                retry += 1
                await asyncio.sleep_ms(1000)
        except asyncio.CancelledError:
            self.log.info("[Handshake] finished")
            pass

    async def error_handler_async(self, e):
        self.log.info("\n---------------")
        self.log.info("Error Async:", e)
        self.log.info("---------------")
        await self.send_duplex_cmd("ERROR@{}".format(e))
        return

    async def error_handler(self, e):
        self.log.info("\n---------------")
        self.log.info("Error Async:", e)
        self.log.info("---------------")

    async def run(self):
        self.loop.run_forever()
        # except Exception as e:
        #     self.loop.create_task(self.error_handler_async(e))

    def init(self):
        self.load_local_config()
        self.loop.create_task(self._recv())
        self.loop.create_task(self.handshake())
        # self.loop.create_task(self.error_handler_async("TEST_ERROR"))


if __name__ == "__main__":
    try:
        poe = ReceiverPOE()
        poe.init()
        asyncio.run(poe.run())

    except Exception as e:
        common.reset()

    finally:
        poe.loop = asyncio.new_event_loop()
