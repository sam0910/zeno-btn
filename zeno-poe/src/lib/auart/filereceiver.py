import uasyncio as asyncio
from machine import UART
import constants as c


class AUARTReceiver:
    def __init__(self):
        # Configure UART
        uart = UART(1, baudrate=9600, tx=c.TX, rx=c.RX, rxbuf=2048)
        self.swriter = asyncio.StreamWriter(uart, {})
        self.sreader = asyncio.StreamReader(uart)
        self.loop = asyncio.get_event_loop()
        self.handshaked = False
        self.chunk_size = 128

    async def receive_file(self):
        # Create a stream reader
        await self.swriter.awrite("READY_TO_RECEIVE\n")

        # Wait for the sender to start sending
        data = await self.sreader.readline().strip()

        if data.startswith(b"READY_TO_SEND"):
            file_name = data.split(b"@")[1].decode()
            print("Receiving file:", file_name)
            # Open the file for writing
            with open(file_name, "wb") as file:
                # Start receiving file data
                while True:
                    data = await self.sreader.read(self.chunk_size)
                    if data.endswith(b"END_OF_FILE\n"):
                        file.write(data[:-12])  # Write everything except the "END_OF_FILE" marker
                        print("File received successfully.")
                        break
                    else:
                        file.write(data)

    async def recv(self):
        while True:
            print("[RECV] Receiving ...")
            response = await self.sreader.readline()
            if response == b"AT\n":
                self.handshaked = True
                print("[RECV] Got AT, Handshaked ... from recv")
                await self.swriter.awrite("OK\n")

    def init(self):
        self.loop.create_task(self.handshake())
        self.loop.create_task(self.recv())


if __name__ == "__main__":
    recver = AUARTReceiver()
    recver.init()
    recver.loop.run_forever()
