import machine
import time
from machine import Pin, PWM
import constants as c
import time
import json
from logsam import Log

buzzer_pin = Pin(c.BUZZER, Pin.OUT)
buzzer_pwm = None
buzzer_array = []

arr = None

try:
    with open("/images.json", "r") as f:
        data = f.read()
        filelist = json.loads(data)
    buzzer_array = filelist["buzzer"]

except Exception:
    buzzer_array = arr

if len(buzzer_array) < 2:
    buzzer_array = None


def reset():
    time.sleep(5)
    machine.reset()


def bl(state):
    Pin(c.BL, Pin.OUT, value=state)
    print("Backlight", state)


def beep(f=4000, d=100, dd=512):
    global buzzer_pwm
    buzzer_pwm = PWM(buzzer_pin, f)
    buzzer_pwm.duty(d)  # Play at half volume
    time.sleep_ms(d)
    buzzer_pwm.duty(0)
    buzzer_pwm.deinit()


def beep_array(type="on"):
    try:
        global buzzer_pwm
        if buzzer_array[type]:
            buzzer_pwm = PWM(buzzer_pin)
            for note in buzzer_array[type]:
                # print(f"{note['freq']},{note['duration']}")
                buzzer_pwm.freq(note["freq"])
                buzzer_pwm.duty(note["duty"])
                time.sleep_ms(note["duration"])

            buzzer_pwm.duty(0)
            buzzer_pwm.deinit()
            buzzer_pwm = None
    except Exception as e:
        if buzzer_pwm is not None:
            buzzer_pwm.duty(0)
            buzzer_pwm.deinit()

        print("beep_array", e)


def get_device_id():
    # from machine import UART, machine.Pin
    bit1 = 0 if machine.Pin(7, machine.Pin.IN).value() else 1
    bit2 = 0 if machine.Pin(8, machine.Pin.IN).value() else 2
    bit3 = 0 if machine.Pin(32, machine.Pin.IN).value() else 4
    bit4 = 0 if machine.Pin(34, machine.Pin.IN).value() else 8
    bit5 = 0 if machine.Pin(37, machine.Pin.IN).value() else 16
    bit6 = 0 if machine.Pin(36, machine.Pin.IN).value() else 32
    bit7 = 0 if machine.Pin(38, machine.Pin.IN).value() else 64
    bit8 = 0 if machine.Pin(35, machine.Pin.IN).value() else 128
    did = bit1 + bit2 + bit3 + bit4 + bit5 + bit6 + bit7 + bit8
    print("Device ID:", bit1, bit2, bit3, bit4, bit5, bit6, bit7, bit8, "=", did)
    return "{}".format(did)


# beep(4000, 80, 512)


# beep_array("on")
# time.sleep(1)
# beep_array("off")
