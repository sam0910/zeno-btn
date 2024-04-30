import uasyncio as asyncio
from machine import UART, reset, wake_reason
import constants as c
import gc
import ujson
import lvgl as lv

gc.enable()
gc.collect()
print("{}Kb free".format(gc.mem_free() // 1024))


class AUARTReceiver:
    def __init__(self):
        # Configure UART
        uart = UART(
            1, baudrate=9600, tx=c.TX, rx=c.RX, rxbuf=c.CHUNK_SIZE, txbuf=c.CHUNK_SIZE
        )
        self.swriter = asyncio.StreamWriter(uart, {})
        self.sreader = asyncio.StreamReader(uart)
        self.loop = asyncio.get_event_loop()
        self.handshaked = False
        self.chunk_size = c.CHUNK_SIZE
        self.transmitting = False
        self.checksum = ""

        self.local_final = None
        self.recv_final = None

    async def receive_file(self):
        try:
            print("[Receiving] ", self.filename)
            chunk = bytearray(self.chunk_size)

            with open(f"/{self.filename}", "wb") as file:
                print("[Receiving] ", end="")
                while True:
                    chunk = await self.sreader.read(self.chunk_size)
                    lenchunk = len(chunk)  # MAX 120
                    print(".", end=".")
                    if chunk.endswith(b"END_OF_FILE\n"):
                        file.write(
                            chunk[:-12]
                        )  # Write everything except the "END_OF_FILE" marker
                        print("::: Complete, last size:", lenchunk)
                        self.transmitting = False
                        chunk = None
                        gc.collect()
                        print("{}Kb free".format(gc.mem_free() // 1024))
                        raise asyncio.CancelledError
                    else:
                        file.write(chunk)
        except asyncio.CancelledError:
            print("[LOOP] receive_file DONE.")

    async def send_checksum(self):
        await asyncio.sleep_ms(2000)
        if self.checksum:
            await self.swriter.awrite(b"CHECKSUM@" + self.checksum.encode() + b"\n")
            print("[Sending] Checksum", self.checksum)

    async def match(self, ans):
        if self.checksum:
            await self.swriter.awrite(b"MATCH@" + ans + b"\n")
            print("[Sending] {}".format(ans))

    def check_both_final(self):
        if self.local_final and self.recv_final:

            if self.local_final == self.recv_final:
                print("[FINAL] MATCHED")
            else:
                print("[FINAL] NOT MATCHED")
            reset()
        else:
            print("[FINAL] NOT YET")
            return False

    async def send(self, data):
        await self.swriter.awrite(data)

    async def recv(self):
        wr = wake_reason()
        print("WAKE_REASON: ", wr)
        if wr == 0:
            print("Woken up by UART")
            await self.swriter.awrite(b"RESET\n")

        while True:
            if self.transmitting is False:
                print("[Listen] ... ", end="")
                response = await self.sreader.readline()
                response = response.strip().decode()
                print(response)
                if response == "BOOT" and not self.handshaked:
                    self.handshaked = True
                    await self.swriter.awrite(b"BOOTED\n")
                    print("[BOOT] Received")
                    with open("/logo.png", "rb") as f:
                        data = f.read()
                        dsc = lv.image_dsc_t({"data_size": len(data), "data": data})

                    img = lv.image(lv.screen_active())
                    img.set_src(dsc)
                    img.align(lv.ALIGN.CENTER, 0, 0)

                    lv.tick_inc(5)
                    lv.task_handler()
                    lv.tick_inc(5)
                    lv.task_handler()

                if response.startswith("MATCH"):
                    self.recv_final = True if response.split("@")[1] == "YES" else False
                    self.check_both_final()

                if response == "AT" and not self.handshaked:
                    self.handshaked = True
                    await self.swriter.awrite(b"OK\n")

                if response.startswith("READY_TO_SEND"):
                    self.filename = response.split("@")[1]
                    self.checksum += self.filename
                    self.transmitting = True
                    self.loop.create_task(self.receive_file())
                    # await asyncio.sleep_ms(500)
                    # await self.swriter.awrite(b"READY_TO_RECEIVE\n")
                if response.startswith("CHECKSUM"):
                    recv_checksum = response.split("@")[1]
                    print("")
                    print(f"[CHECKSUM] Recved: {recv_checksum}")
                    print(f"[CHECKSUM] Local : {self.checksum}")

                    self.loop.create_task(self.send_checksum())
                    if recv_checksum == self.checksum:
                        self.local_final = True
                        self.loop.create_task(self.match("YES"))
                    else:
                        self.local_final = False
                        self.loop.create_task(self.match("NO"))

                    self.check_both_final()

            else:
                await asyncio.sleep(1)

    def init(self):
        self.loop.create_task(self.recv())

    async def run(self):
        self.loop.run_forever()


if __name__ == "__main__":
    try:
        recver = AUARTReceiver()
        recver.init()
        asyncio.run(recver.run())
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        reset()
