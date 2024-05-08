import os
import gc
import json

gc.enable()


a = os.statvfs("/")
total = int(a[0] * a[2] / 1024)
free = int(a[0] * a[3] / 1024)
used = total - free
print(f"\nTotal: {total} KB, Used: {used} KB, Free: {free} KB\n")

# pip install --user mpremote
# mpremote connect COM4
# mpremote fs cp config.json :config.json
# mpremote fs cp logsam.py :/lib/logsam.py
# mpremote connect /dev/cu.usbserial-130

# try:
#     with open("/images.json", "r") as f:
#         data = f.read()
#         filelist = json.loads(data)
#         print("DONWLOAD_NEED", filelist["download_need"])

#     if int(filelist["download_need"]) == 1:
#         from auart.filesender import AUARTSender

#         import os
#         import asyncio

#         print("Download Mode")
#         images = ["/images/" + image["url"] for image in filelist["images"]]
#         images = ["/images/name.png"]
#         sender = AUARTSender(images)
#         sender.init()
#         asyncio.run(sender.run())

# except Exception:
#     pass
