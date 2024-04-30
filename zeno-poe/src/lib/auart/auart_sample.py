# We run with no UART timeout: UART read never blocks.
import uasyncio as asyncio
from machine import UART

uart = UART(4, 9600, timeout=0)


async def sender():
    swriter = asyncio.StreamWriter(uart, {})
    while True:
        swriter.write("Hello uart\n")
        await swriter.drain()
        await asyncio.sleep(2)


async def receiver():
    sreader = asyncio.StreamReader(uart)
    while True:
        res = await sreader.readline()
        print("Received", res)


async def main():
    asyncio.create_task(sender())
    asyncio.create_task(receiver())
    while True:
        await asyncio.sleep(1)


def test():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted")
    finally:
        asyncio.new_event_loop()
        print("as_demos.auart.test() to run again.")


test()
