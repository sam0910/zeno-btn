import uasyncio as asyncio
from primitives.delay_ms import Delay_ms


class HalfDuplexSender:
    def __init__(self, uart, timeout=4000):
        # uart = UART(1, baudrate=9600, tx=c.PICO_TX, rx=c.PICO_RX)
        self.timeout = timeout
        self.swriter = asyncio.StreamWriter(uart, {})
        self.sreader = asyncio.StreamReader(uart)
        self.delay = Delay_ms()
        self.response = ""

    async def _recv(self):
        while True:
            res = await self.sreader.readline()
            self.response = res.strip().decode()  # Append to list of lines
            self.delay.trigger(self.timeout)  # Got something, retrigger timer

    async def send_command(self, command):
        self.response = ""  # Discard any pending messages
        if command is None:
            pass
        else:
            await self.swriter.awrite(b"" + command + b"\r\n")

        self.delay.trigger(self.timeout)  # Re-initialise timer
        while self.delay.running():
            await asyncio.sleep(1)  # Wait for 4s after last msg received
        return self.response
