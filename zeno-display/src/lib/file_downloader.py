from logsam import Log
import ujson
import uasyncio as asyncio
import urequests
import os
import gc
import constants as c
from httpclient import HttpClient
import time
import machine


class FileDownloader:
    def __init__(self):
        self.log = Log(__name__)
        self.baseurl = None
        self.image_folder = "/images"

    def set_baseurl(self, url):
        if url[-1] == "/":
            url = url[:-1]
        self.baseurl = url

    def error(self, msg):
        print("Error:", msg)

    def save_json(self, data, filename):
        with open(filename, "w") as f:
            ujson.dump(data, f)
        print("Save JSON file")

    def get_json(self, url):
        print("Downloading ...", url)
        json_down = {"version": "0.0"}
        try:
            response = urequests.get(url)
            json_down = ujson.loads(response.content)
            response.close()
        except Exception as e:
            print("Download JSON file error:", str(e))
            raise ValueError("JSON_DOWNLOAD_ERROR")
        finally:
            return json_down

    def load_json(self, fname):
        loaded = {
            "version": "0.0",
            "image_url": "http://192.168.0.100:3000",
            "config_url": "http://192.168.0.100:3000/config.json",
            "images": [],
        }
        try:
            with open(fname, "r") as f:
                loaded = ujson.load(f)
                return loaded
        except OSError as e:
            print("load_json error:", str(e))
            with open(fname, "w") as f:
                ujson.dump(loaded, f)
        finally:
            return loaded

    def check_version33(self, url):
        print("Downloading JSON file ...")
        response = urequests.get("{}/images.json".format(self.baseurl))
        self.version_downloaded = ujson.loads(response.content)
        response.close()
        # load local json file
        try:
            with open("/images.json", "r") as f:
                version_local = ujson.load(f)
                self.current_version = int(version_local["version"].replace(".", ""))
                print("Local JSON version:", self.current_version)
                print("Local JSON images:", len(version_local["images"]))
        except OSError as e:
            print("\nLocal JSON file not found", str(e))
            new_file = dict(self.version_downloaded)
            new_file["version"] = "0.0"
            self.current_version = 0
            with open("images.json", "w") as f:
                ujson.dump(new_file, f)
            print("Downloaded JSON file")
            # self.download_images()

        new_version = int(self.version_downloaded["version"].replace(".", ""))
        print("downloaded JSON version:", new_version)

        if new_version != self.current_version:
            print("New JSON file version found")
            res = self.download_images()

    def download_images(self):
        print("Downloading images ...")
        # make image folder if not exist
        try:
            os.listdir(self.image_folder)
            print("Image folder exists")
        except OSError as e:
            print("Image folder not found", str(e))
            os.mkdir(self.image_folder)
            print("Created image folder")

        try:
            os.listdir("/temp")
            print("temp folder exists")
        except OSError as e:
            print("Image folder not found", str(e))
            os.mkdir("/temp")
            print("Created temp folder")

        # Delete all files in /temp folder
        temp_files = os.listdir("/temp")
        for file in temp_files:
            os.remove(f"/temp/{file}")
        print("Deleted all files in /temp folder")

        for image in self.version_downloaded["images"]:
            image_url = self.baseurl + "/" + image["url"]
            image_path = f"/temp/{image['url']}"
            print("Downloading image:", image_url, "->", image_path)
            try:
                response = urequests.get(image_url)
                with open(image_path, "wb") as f:
                    f.write(response.content)
                response.close()
                print("Downloaded image:", image["url"])
            except Exception as e:
                print("Download image error:", str(e))
                raise ValueError("IMAGE_ERROR")
            time.sleep_ms(1000)
            gc.collect()

        print("Downloaded complete!")
        temp_files = os.listdir("/images")
        for file in temp_files:
            os.remove(f"/images/{file}")
        print("Deleted all files in /images folder")

        temp_files = os.listdir("/temp")
        for file in temp_files:
            os.rename(f"/temp/{file}", f"/images/{file}")
        print("Copy to /images folder")

        self.version_downloaded["download_need"] = 1
        with open("images.json", "w") as f:
            ujson.dump(self.version_downloaded, f)
        print("Save new version file")

        machine.reset()


if __name__ == "__main__":

    lan = ConnectLAN()
    conn = lan.connect() if not lan.is_connected() else True
    print("### Connected to LAN:", conn)

    down = FileDownloader()
    local_config = down.load_json("/config.json")
    down.set_baseurl(local_config["image_url"])

    down_config = down.get_json(local_config["config_url"])
    if down_config["version"] != local_config["version"]:
        print("New config file found, save it to local")
        down.save_json(down_config, "/config.json")
        down.set_baseurl(down_config["image_url"])

    print("Done")
