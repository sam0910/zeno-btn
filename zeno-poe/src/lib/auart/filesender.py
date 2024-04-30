import uasyncio as asyncio
from machine import UART, reset
import constants as c
import gc
import ujson

gc.enable()


class AUARTSender:
    def __init__(self, filelist):
        self.chunk_size = c.CHUNK_SIZE
        uart = UART(1, baudrate=9600, tx=c.TX, rx=c.RX, rxbuf=c.CHUNK_SIZE, txbuf=c.CHUNK_SIZE)
        self.swriter = asyncio.StreamWriter(uart, {})
        self.sreader = asyncio.StreamReader(uart)
        self.loop = asyncio.get_event_loop()
        self.handshaked = False
        self.filelist = filelist
        self.transmitting = False
        self.current_file_path = None
        self.current_file_name = None
        self.checksum = None
        self.local_final = None
        self.recv_final = None

    async def match(self, ans):
        if self.checksum:
            print("[Sending] {}".format(ans))
            await self.swriter.awrite(b"MATCH@" + ans + b"\n")

    def check_both_final(self):
        if self.local_final and self.recv_final:
            if self.local_final == self.recv_final:
                print("[FINAL] MATCHED")
                with open("/images.json", "r") as file:
                    data = file.read()
                    json_data = ujson.loads(data)
                    json_data["download_need"] = 0

                with open("/images.json", "w") as file:
                    file.write(ujson.dumps(json_data))

            else:
                with open("/images.json", "r") as file:
                    data = file.read()
                    json_data = ujson.loads(data)
                    json_data["download_need"] = 1

                with open("/images.json", "w") as file:
                    file.write(ujson.dumps(json_data))

                print("[FINAL] NOT MATCHED")
            return True
        else:
            print("[FINAL] NOT YET")
            return False

    async def recv(self):
        while True:
            if self.transmitting is False:
                print("[Listen] ... ", end="")

                response = await self.sreader.readline()
                response = response.strip().decode()
                print(response)
                if response == "BOOTED":
                    self.handshaked = True
                    print("[Listen] Got BOOTED, Handshaked ...")
                    # cancel all tasks on self.loop
                    # self.loop.stop()
                    # self.loop.close()
                    # raise asyncio.CancelledError
                if response == "RESET":
                    reset()

                if response == "OK":
                    self.transmitting = True
                    self.handshaked = True
                    self.loop.create_task(self.send_file())

                if response.startswith("MATCH"):
                    self.recv_final = True if response.split("@")[1] == "YES" else False
                    res = self.check_both_final()
                    if res:
                        await asyncio.sleep_ms(5000)
                        reset()

                if response.startswith("CHECKSUM"):
                    recv_checksum = response.split("@")[1]
                    print("")
                    print(f"[CHECKSUM] Recved: {recv_checksum}")
                    print(f"[CHECKSUM] Local : {self.checksum}")
                    if recv_checksum == self.checksum:
                        self.local_final = True
                        self.loop.create_task(self.match("YES"))
                    else:
                        self.local_final = False
                        self.loop.create_task(self.match("NO"))

                    res = self.check_both_final()
                    if res:
                        await asyncio.sleep_ms(5000)
                        reset()

                # if response.startswith("READY_TO_RECEIVE"):
                #     self.transmitting = True
                #     if len(self.filelist) % 2:
                #         self.loop.create_task(self.send_file())
                #     else:
                #         self.loop.create_task(self.send_file_slot2())
            else:
                await asyncio.sleep_ms(1000)

    async def send_checksum(self):
        await asyncio.sleep_ms(1000)
        if self.checksum:
            await self.swriter.awrite(b"CHECKSUM@" + self.checksum.encode() + b"\n")
            print("[Sending]", self.checksum)

    async def handshake_normal(self):
        try:
            retry = 0
            await asyncio.sleep_ms(300)
            while True:
                if retry > 60:
                    reset()
                print("[Sending] BOOT ...")
                if self.handshaked:
                    print("[Handshake] True")
                    raise asyncio.CancelledError

                await self.swriter.awrite(b"BOOT\n")
                retry += 1
                await asyncio.sleep_ms(1000)
        except asyncio.CancelledError:
            pass

    async def handshake(self):
        try:
            retry = 0
            await asyncio.sleep_ms(300)
            while True:
                if retry > 60:
                    reset()
                print("[Sending] Handshaking ...")
                if self.handshaked:
                    print("[Handshake] True")
                    raise asyncio.CancelledError

                await self.swriter.awrite(b"AT\n")
                retry += 1
                await asyncio.sleep_ms(1000)
        except asyncio.CancelledError:
            pass

    async def send_file(self):
        chunk = bytearray(self.chunk_size)
        _checksum = ""
        try:
            for filepath in self.filelist:
                n = 0
                await asyncio.sleep_ms(2500)
                file_name = filepath.split("/")[-1]
                _checksum += file_name
                print("[Sending] READY_TO_SEND@{}".format(file_name))
                await self.swriter.awrite(b"" + f"READY_TO_SEND@{file_name}\n")
                await asyncio.sleep_ms(2500)
                with open(filepath, "rb") as file:
                    print("[Sending] chunk ", end="")
                    while True:
                        chunk = file.read(self.chunk_size)
                        if not chunk:
                            await self.swriter.awrite(b"END_OF_FILE\n")
                            # self.transmitting = False
                            chunk = None
                            gc.collect()
                            await asyncio.sleep_ms(1000)
                            break

                        print(len(chunk), end=",")
                        await self.swriter.awrite(b"" + chunk)
                        n += 1
                        await asyncio.sleep_ms(100)  # Give time for the last chunk to be sent
                    # End of while
                    print(":::Complete", n, end="")
                    file.close()
                print("File closed.\n")

            self.transmitting = False
            self.checksum = _checksum
            self.loop.create_task(self.send_checksum())
            raise asyncio.CancelledError
        except asyncio.CancelledError:
            print("[LOOP] send_file Done")

    def init(self):
        self.loop.create_task(self.recv())
        self.loop.create_task(self.handshake())

    async def run(self):
        self.loop.run_forever()

    def normal_boot(self):
        self.loop.create_task(self.recv())
        self.loop.create_task(self.handshake_normal())


if __name__ == "__main__":
    import ujson

    try:
        # load json
        with open("/images.json", "r") as file:
            data = file.read()
            json_data = ujson.loads(data)
            filelist = json_data["images"]

        images = ["/images/" + image["url"] for image in filelist]
        # images = ["/images/name.png"]
        print(images)
        sender = AUARTSender(images)
        sender.init()
        asyncio.run(sender.run())
    except KeyboardInterrupt:
        reset()
