import network
import time
from machine import Pin
import constants as c


class ConnectLAN:
    def __init__(self):
        self.isconnected = False
        Pin(12, Pin.OUT, value=1)  # Pin.DRIVE_3
        self.lan = network.LAN(
            mdc=Pin(23),
            mdio=Pin(18),
            power=Pin(12),
            phy_type=network.PHY_LAN8720,
            phy_addr=0,
            ref_clk=Pin(17),
            ref_clk_mode=Pin.OUT,
        )
        self.isconnected = False

    def is_connected(self):
        ip = self.lan.ifconfig()
        ipp = int(ip[0].replace(".", ""))
        if ipp > 0:
            return True
        else:
            return False

    def connect(self):
        print("Connecting to LAN")

        try:
            is_active = self.lan.active(True)
            time.sleep_ms(800)
            print("LAN Active", is_active)
            if is_active:
                ip = self.lan.ifconfig()
                print("LAN IP", ip)
                retry = 0
                while True:
                    ip = self.lan.ifconfig()
                    ipp = int(ip[0].replace(".", ""))
                    # print("retry", ip)
                    if ipp > 0:
                        print("++ Connected IP", ip)
                        return ip
                        break

                    if retry > 35:
                        raise ValueError("LAN_NOIP")
                        break
                    retry += 1
                    time.sleep_ms(400)

                else:
                    raise ValueError("LAN_NOIP")
                    return False
            else:
                raise ValueError("LAN_INACTIVE")
                return False
        except:
            raise ValueError("LAN_ERROR")
            return False


if __name__ == "__main__":
    lan = ConnectLAN()
    conn = lan.connect()
    print("### Connected to LAN:", conn)
    time.sleep(2)
    if lan.isconnected:
        print("### Connected to LAN:", conn)
    else:
        print("### Not connected to LAN")
        raise ValueError("LAN_ERROR")
