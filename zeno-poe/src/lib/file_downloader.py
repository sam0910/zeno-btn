# get json file from server. retreive image url from json file. download images from url
# json file {images:[{url: "http://www.example.com/image1.jpg"}, {url: "http://www.example.com/image2.jpg"}]}
# json file path: http://www.example.com/json_file.json


import ujson
import uasyncio as asyncio
import urequests
import os
import gc
import constants as c
from connect_lan import ConnectLAN
from httpclient import HttpClient
import time
import machine


class FileDownloader:
    def __init__(self):
        #  check end of url is "/", if so remove it
        self.baseurl = None
        self.image_folder = "/images"
        self.node_id = 0

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
        print("Getting...", url)
        # json_down = {"version": "0.0"}
        json_down = None
        try:
            # headers = {"Content-Type": "application/json", "Origin": "http://smartcouncil.xenoglobal.co.kr"}
            response = urequests.get(url, timeout=5)
            json_down = ujson.loads(response.content)
            response.close()
        except Exception as e:
            print("Download JSON file error:", str(e))
            raise ValueError("JSON_DOWNLOAD_ERROR")
        finally:
            return json_down

    def load_json(self, fname):
        #
        try:
            with open(fname, "r") as f:
                loaded = ujson.load(f)
                return loaded
        except OSError as e:
            print("load_json error", str(e))

    def download_images(self, new_version, did):
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

        for image in new_version["images"]:
            image_url = self.baseurl + "/node_{}/".format(did) + image["url"]
            print("Downloading image:", image_url)
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
