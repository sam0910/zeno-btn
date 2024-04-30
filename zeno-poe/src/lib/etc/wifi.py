import network
import machine
import utime as time

from db.connect import DB
from logsam import Log


class Wifi:
    __slots__ = ("timeout", "saving")

    def disconnect(self):
        try:
            self._wlan.disconnect()
        except:
            pass
        finally:
            self._wlan.active(False)
            time.sleep_ms(100)

    def __init__(self, ssid=None, pwd=None, recent=None):
        self.log = Log(__name__)
        self.timeout = 7000
        self._ssid = ssid if ssid is not None else ""
        self._pwd = pwd if pwd is not None else ""
        self._recent = recent if recent is not None else ()
        if self._recent == ():
            # self.log.info("Loading recent wifi from DB")
            # with DB("/data/wifi.db") as db:
            #     self._recent = db.list()
            self._recent = [
                {"ACESPA": "acespa04"},
                {"ACESPA_E": "acespa04"},
                {"LATEST_CONN_WIFI_NAME": "ACESPA_E|acespa04"},
            ]

        self._wlan = network.WLAN(network.STA_IF)
        self.saving = True
        self._scans = []
        self.disconnect()
        self.log.info("Wifi init ... and disconnect()")

    def is_available(self, ssid):
        if len(self._scans) == 0:
            self.log.info("Scanning ...")
            if not self._wlan.active():
                self._wlan.active(True)
                time.sleep_ms(100)
            self._scans = self._wlan.scan()

        for item in self._scans:
            if ssid == item[0].decode("utf-8"):
                self.log.info(f"...     Found {ssid}")
                return True
        self.log.info(f"... Not found {ssid}")
        return False

    @property
    def isconnected(self):
        return self._wlan.isconnected()

    def scan(self):
        if not self._wlan.active():
            self._wlan.active(True)
            time.sleep_ms(100)
        scans = self._wlan.scan()
        return scans

    def delete_ssid(self, ssid):
        self.log.info("... delete")
        with DB("/data/wifi.db") as db:
            db.delete(ssid)
            db.set("LATEST_CONN_WIFI_NAME", "|")

        return

    def save_latest(self, ssid, pwd):
        self.log.warn("save_latest", ssid, pwd)
        isNew = True
        with DB("/data/wifi.db") as db:
            loaded = db.list()
            for item in loaded:  # Iterate over the list itself
                item_ssid = list(item.keys())[0]
                item_pwd = list(item.values())[0]

                if ssid == item_ssid:
                    self.log.info("... same ssid in DB")
                    if pwd == item_pwd:
                        self.log.info("... same pwd in DB")
                        isNew = False
                    else:
                        self.log.info("... diff pwd in DB")
                        isNew = True
                    break
            if isNew:
                self.log.info("... New, saving")
                db.set(ssid, pwd)

            self.log.info("... Setting LATEST_CONN_WIFI_NAME")
            db.set("LATEST_CONN_WIFI_NAME", f"{ssid}|{pwd}")

        with DB("/data/wifi.db") as db:
            print(db.list())
        return True

    def connect(self, ssid=None, pwd=None, recent=None, scanned=False):
        if ssid is not None:
            self._ssid = ssid
        if pwd is not None:
            self._pwd = pwd
        if recent is not None:
            self._recent = recent
        if self._wlan.isconnected():
            self.log.info("already connected...")
            return True

        if self._connect_wifi(self._ssid, self._pwd, scanned):
            return True
        else:
            for item in self._recent:  # Iterate over the list itself
                if "LATEST_CONN_WIFI_NAME" in item:
                    latest_conn_wifi_name = item["LATEST_CONN_WIFI_NAME"]
                    if bool(latest_conn_wifi_name) is False:
                        self.log.info("... LATEST_CONN_WIFI_NAME : empty")
                        break

                    l_ssid_split = latest_conn_wifi_name.split("|")
                    if len(l_ssid_split) == 2:
                        l_ssid = l_ssid_split[0]
                        l_pwd = l_ssid_split[1]
                        self.log.info(f"... LATEST_CONN_WIFI_NAME: {l_ssid}/{l_pwd}")
                        if self._connect_wifi(l_ssid, l_pwd, scanned=True):
                            return True

            self.log.warn("Recent wifi finding, recent=", self._recent)
            for item in self._recent:
                if "LATEST_CONN_WIFI_NAME" in item:
                    continue

                ssid = list(item.keys())[0]
                pwd = list(item.values())[0]

                if self._ssid == ssid and self._pwd == pwd:
                    continue
                if self._connect_wifi(ssid, pwd, scanned=True):
                    return True

            return False

    def _connect_wifi(self, ssid, pwd, scanned=False):
        if scanned:
            if not self.is_available(ssid):
                return False

        if not self._wlan.active():
            self._wlan.active(True)
            time.sleep_ms(100)

        if ssid == "" or len(ssid) < 2:
            self.log.info("ssid is empty")
            return False

        wlan = self._wlan
        if not wlan.isconnected():
            self.log.info("Connecting... {ssid}:{pwd}".format(ssid=ssid, pwd=pwd))
            wlan.connect(ssid, pwd)
            st = time.ticks_ms()
            while not wlan.isconnected():
                time.sleep_ms(300)
                if time.ticks_diff(time.ticks_ms(), st) > self.timeout:
                    self.log.info("... timeout")
                    self.disconnect()
                    return False
                pass
        self.log.info("network config:", wlan.ifconfig()[0])
        if not wlan.isconnected():
            self.disconnect()
            return False

        if self.saving:
            self.save_latest(ssid, pwd)

        return True


if __name__ == "__main__":
    with DB("/data/wifi.db") as db:
        recent = db.list()
    print(recent)
    connect = Wifi("Stella", "", recent)
    connect.saving = True
    connect.connect()


else:
    print(__name__, "importing ...")
