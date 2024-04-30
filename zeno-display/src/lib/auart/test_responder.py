import uasyncio as asyncio
from machine import UART
import constants as c


class TestResponder:

    def __init__(self):
        self.uart = UART(1, baudrate=9600, tx=c.TX, rx=c.RX)
        self.sreader = asyncio.StreamReader(self.uart)
        self.swriter = asyncio.StreamWriter(self.uart, {})
        self.loop = asyncio.get_event_loop()

    async def main(self):
        responses = ["Line 1", "Line 2", "Line 3", "Goodbye"]
        while True:
            res = await self.sreader.readline()
            print("Received", res)
            for response in responses:
                print("Sending ...", response),
                await self.swriter.awrite("{}\r\n".format(response))

                # Demo the fact that the master tolerates slow response.
                await asyncio.sleep_ms(300)

    async def run(self):
        self.loop.run_forever()

    def init(self):
        self.loop.create_task(self.main())


if __name__ == "__main__":
    test = TestResponder()
    test.init()

    try:
        asyncio.run(test.run())
    except KeyboardInterrupt:
        print("Interrupted")
    finally:
        test.loop = asyncio.new_event_loop()
        print("as_demos.auart_hd.test() to run again.")


test()
