import btree
from micropython import const
import uos
import utime


class DB:
    """
    Btree wrapper class
    with __exit__
    """

    def __init__(self, db_name):
        self._max_buffer = const(10240)
        self._total_bytes = 0
        self._file = None
        self._db_name = db_name
        self.db = None
        self.connected = False

    def __enter__(self):
        try:
            self._file = open(self._db_name, "r+b")
        except OSError:
            self._file = open(self._db_name, "w+b")

        cachesize = int(self._max_buffer * 1.2)
        self.db = btree.open(self._file, cachesize=cachesize)
        self.connected = True
        return self

    def set(self, key, value):
        key = bytes(str(key), "utf-8")
        value = bytes(str(value), "utf-8")

        self.db[key] = value
        self._total_bytes += len(value)

        if self._total_bytes > self._max_buffer:
            self.flush()

        # my_string="777888001"
        # key = bytes(my_string, "utf-8")
        # result = str(key, 'utf-8')
        # a = (25234248).to_bytes(8,"little")
        # b = int.from_bytes(a, "little")

    def get(self, key):
        key = bytes(str(key), "utf-8")
        try:
            res = self.db[key]
        except KeyError:
            print("get::NoKey -", key)
            return False

        return str(res, "utf-8")

    def exist(self, key) -> bool:
        key = bytes(str(key), "utf-8")
        res = key in self.db
        return res

    def delete(self, key):
        key = bytes(str(key), "utf-8")
        try:
            del self.db[key]
            return True
        except KeyError:
            print("     ... delete:No key", key)
            return False

    def connect(self):
        self.__enter__()

    def flush(self):
        # print(" ... flush", self._total_bytes)
        self.db.flush()
        self._total_bytes = 0

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.flush()
        if self.db is not None:
            self.db.close()
        if self._file is not None:
            self._file.close()
        self.connected = False

    def erase(self):
        self.__exit__(None, None, None)
        utime.sleep_ms(30)
        uos.remove(self._db_name)
        print("Erase the", self._db_name)

    def list(self):
        ret = []
        for key in self.db:
            k = str(key, "utf-8")
            v = str(self.db[key], "utf-8")
            ret.append({k: v})
        return ret

    def close(self):
        self.__exit__(None, None, None)
