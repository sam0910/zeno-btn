import usocket, os, gc
from esp32 import Partition
from micropython import const
from machine import WDT
import time
from logsam import Log


class Response:
    def __init__(self, socket, saveToFile=None, write=False, cb=None):
        self._socket = socket
        self._saveToFile = saveToFile
        self._encoding = "utf-8"
        self.magic = None
        self.WRITE = write
        self.wdt = None

        self.cb = cb
        self.file_size = 3000
        self.percent = 0

        if saveToFile is not None:
            block = 0
            types = saveToFile.split(".")
            types = types[-1]

            CHUNK_SIZE = 512  # bytes
            GC_NO = 0  #
            GC_MAX = int((500 * 1024) / CHUNK_SIZE)  # 500kb 512000b / 512 = 1000

            BLOCKLEN = const(4096)
            soc = self._socket
            self.wdt = WDT(timeout=20000)  # 30 seconds
            self.wdt.feed()

            if types == "bin" or types == "BIN":
                self.magic = False
                print("Write firmware to flash ...")
                if self.cb:
                    self.cb(0, "Download begin...")
                _part = Partition(Partition.RUNNING).get_next_update()
                _block = 0
                _buf = bytearray(BLOCKLEN)
                _magic = None  # 0xE9

                elapsed = time.ticks_ms()
                while True:
                    self.wdt.feed()
                    GC_NO += 1
                    if GC_NO > GC_MAX:
                        gc.collect()
                        GC_NO = 0

                    _buf = soc.read(BLOCKLEN)
                    if _block == 0:
                        _magic = _buf[:2]

                    buf_length = len(_buf)
                    if buf_length == BLOCKLEN:
                        # print("_part.writeblocks({}, {}) , len:{}".format(_block, _buf[:3], buf_length))
                        if self.WRITE:
                            _part.writeblocks(_block, _buf)
                        _block += 1
                        kbytes = int(BLOCKLEN * _block / 1024)
                        percent = int(kbytes / self.file_size * 100)
                        if self.cb and self.percent != percent:
                            self.percent = percent
                            self.cb(self.percent, "Downloading ...")
                        elif self.cb:
                            self.cb(None, "Downloading . ")

                    elif buf_length < BLOCKLEN:
                        print("-----------------------")
                        blank = bytearray(BLOCKLEN - buf_length)
                        _buf += blank
                        print(
                            "_part.writeblocks({}, {}) , len:{}".format(
                                _block, _buf[:3], len(_buf)
                            )
                        )
                        print("last length =", buf_length)
                        if self.WRITE:
                            _part.writeblocks(_block, _buf)
                        break
                    else:
                        print("Never see this")

                if self.cb:
                    elapsed = time.ticks_ms() - elapsed
                    self.cb(100, f"Download complete, {elapsed}ms")

                if _magic[:1] == b"\xe9":
                    print("MAGIC is xe9 ... True")
                    try:
                        _part.set_boot()
                        _part.mark_app_valid_cancel_rollback()
                        self.magic = True
                    except Exception as e:
                        print("*** Partion is not valid ***", e)
                        self.magic = False

                else:
                    print("MAGIC is Invalid!", _magic)
                    self.magic = False

            else:
                self.magic = None
                """Download normal file"""
                print("@@@ Download normal file ...magic is", self.magic)
                with open(saveToFile, "w") as outfile:
                    while True:
                        self.wdt.feed()
                        data = soc.read(CHUNK_SIZE)
                        data_len = len(data)
                        if block == 0:
                            pass
                        if data_len == CHUNK_SIZE:
                            outfile.write(data)
                        elif data_len < CHUNK_SIZE:
                            outfile.write(data)
                            break
                        else:
                            print("Never see this")

                        block += 1
                        GC_NO += 1
                        if GC_NO > GC_MAX:
                            gc.collect()
                            GC_NO = 0
                            print("     gc.collect()")
                    # end of while loop
                    outfile.close()
            self.close()
        gc.collect()

    def close(self):
        if self._socket:
            self._socket.close()
            self._socket = None

    @property
    def content(self):
        if self._saveToFile is not None:
            raise SystemError(
                "You cannot get the content from the response as you decided to save it in {}".format(
                    self._saveToFile
                )
            )

        try:
            result = self._socket.read()
            return result
        finally:
            self.close()

    @property
    def text(self):
        return str(self.content, self._encoding)

    def json(self):
        try:
            import ujson

            result = ujson.load(self._socket)
            return result
        finally:
            self.close()


class HttpClient:
    def __init__(self, headers={}, write=False, cb=None):
        self._headers = headers
        self.valid_firmware = False
        self.WRITE = write
        self.cb = cb

    def is_chunked_data(data):
        return getattr(data, "__iter__", None) and not getattr(data, "__len__", None)

    def request(
        self,
        method,
        url,
        data=None,
        json=None,
        file=None,
        custom=None,
        saveToFile=None,
        headers={},
        stream=None,
    ):
        chunked = data and self.is_chunked_data(data)
        redirect = None  # redirection url, None means no redirection

        def _write_headers(sock, _headers):
            for k in _headers:
                sock.write(b"{}: {}\r\n".format(k, _headers[k]))

        try:
            proto, dummy, host, path = url.split("/", 3)
        except ValueError:
            proto, dummy, host = url.split("/", 2)
            path = ""
        if proto == "http:":
            port = 80
        elif proto == "https:":
            import ussl

            port = 443
        else:
            raise ValueError("Unsupported protocol: " + proto)

        if ":" in host:
            host, port = host.split(":", 1)
            port = int(port)

        ai = usocket.getaddrinfo(host, port, 0, usocket.SOCK_STREAM)
        if len(ai) < 1:
            raise ValueError("You are not connected to the internet...")
        ai = ai[0]

        s = usocket.socket(ai[0], ai[1], ai[2])
        try:
            s.connect(ai[-1])
            if proto == "https:":
                gc.collect()
                s = ussl.wrap_socket(s, server_hostname=host)
            s.write(b"%s /%s HTTP/1.0\r\n" % (method, path))
            if not "Host" in headers:
                s.write(b"Host: %s\r\n" % host)
            # Iterate over keys to avoid tuple alloc
            _write_headers(s, self._headers)
            _write_headers(s, headers)

            # add user agent
            s.write(b"User-Agent: MicroPython Client\r\n")
            if json is not None:
                assert data is None
                import ujson

                data = ujson.dumps(json)
                s.write(b"Content-Type: application/json\r\n")

            if data:
                if chunked:
                    s.write(b"Transfer-Encoding: chunked\r\n")
                else:
                    s.write(b"Content-Length: %d\r\n" % len(data))
            s.write(b"\r\n")
            if data:
                if chunked:
                    for chunk in data:
                        s.write(b"%x\r\n" % len(chunk))
                        s.write(chunk)
                        s.write(b"\r\n")
                    s.write("0\r\n\r\n")
                else:
                    s.write(data)
            elif file:
                s.write(b"Content-Length: %d\r\n" % os.stat(file)[6])
                s.write(b"\r\n")
                with open(file, "r") as file_object:
                    for line in file_object:
                        s.write(line + "\n")
            elif custom:
                custom(s)
            else:
                s.write(b"\r\n")

            l = s.readline()
            # print('l: ', l)
            l = l.split(None, 2)
            status = int(l[1])
            reason = ""
            if len(l) > 2:
                reason = l[2].rstrip()
            while True:
                l = s.readline()
                if not l or l == b"\r\n":
                    break
                # print('l: ', l)
                if l.startswith(b"Transfer-Encoding:"):
                    if b"chunked" in l:
                        raise ValueError("Unsupported " + l)
                elif l.startswith(b"Location:") and not 200 <= status <= 299:
                    if status in [301, 302, 303, 307, 308]:
                        redirect = l[10:-2].decode()
                    else:
                        raise NotImplementedError(
                            "Redirect {} not yet supported".format(status)
                        )
        except OSError:
            s.close()
            raise

        if redirect:
            s.close()
            if status in [301, 302, 303]:
                return self.request("GET", url=redirect, **kw)
            else:
                return self.request(method, redirect, **kw)
        else:
            resp = Response(s, saveToFile, self.WRITE, cb=self.cb)
            resp.status_code = status
            resp.reason = reason
            if resp.magic is not None:
                self.valid_firmware = resp.magic

            return resp

    def head(self, url, **kw):
        return self.request("HEAD", url, **kw)

    def get(self, url, **kw):
        return self.request("GET", url, **kw)

    def post(self, url, **kw):
        return self.request("POST", url, **kw)

    def put(self, url, **kw):
        return self.request("PUT", url, **kw)

    def patch(self, url, **kw):
        return self.request("PATCH", url, **kw)

    def delete(self, url, **kw):
        return self.request("DELETE", url, **kw)
