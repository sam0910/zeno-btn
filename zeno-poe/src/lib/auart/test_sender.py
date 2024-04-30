from auart.half_duplex_sender import HalfDuplexSender
import uasyncio as asyncio
from machine import UART
import constants as c


class SenderTest:
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.uart = UART(1, baudrate=9600, tx=c.TX, rx=c.RX)
        self.sender = HalfDuplexSender(self.uart, timeout=4000)

    async def main(self):
        print("START ---- SenderTest ----")
        while True:
            for cmd in ["Run", None]:
                print()
                res = await self.sender.send_command(cmd)
                # can use b''.join(res) if a single string is required.
                if res:
                    print("Result is:")
                    for line in res:
                        print(line.decode("UTF8"), end="")
                else:
                    print("Result is: Timed out.")

            print("END ---- SenderTest ----, sleep 5s.")
            asyncio.sleep(5)

    async def run(self):
        self.loop.run_forever()

    def init(self):
        self.loop.create_task(self.main())
        self.loop.create_task(self.sender._recv())


if __name__ == "__main__":
    test = SenderTest()
    test.init()

    try:
        asyncio.run(test.run())
    except KeyboardInterrupt:
        print("Interrupted")
    finally:
        test.loop = asyncio.new_event_loop()
        print("as_demos.auart_hd.test() to run again.")


test()
