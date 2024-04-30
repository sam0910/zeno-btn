# mqtt_local.py Local configuration for mqtt_as demo programs.
from sys import platform, implementation
from mqtt.mqtt_as import config

config["server"] = "sam0910.iptime.org"
config["port"] = 1883  # Change to suit
config["user"] = "acespa"
config["password"] = "10293847"
config["keepalive"] = 60

wifi_led = lambda _: None
blue_led = wifi_led
