from utime import ticks_ms, ticks_diff

# HEADER = "\033[95m"
# BLUE = "\033[94m"
# CYAN = "\033[96m"
# YELO = "\033[93m"
# GREEN = "\033[92m"
# WARN = "\033[93m"
# FAIL = "\033[91m"
# ENDC = "\033[0m"
# BOLD = "\033[1m"
# UNDERLINE = "\033[4m"
# Grey = "\033[90m"


class Log:
    def __init__(self, name, level=3):
        names = name[-17:]
        # make str with 6 chars without ljust
        self.name = " " * (17 - len(names)) + names[:17]

        self.t = ticks_ms()
        self.level = level

    @classmethod
    def stat(cls, *args):
        names = args[0][-17:]
        name = " " * (17 - len(names)) + names[:17]
        print(
            "\033[90m{:6d}:{:5d}ms STAT [{:6}]\033[0m".format(ticks_ms(), 0, name),
            args[1],
        )

    def info(self, *args):
        if self.level < 1:
            print(
                "\033[90m{:6d}:{:5d}ms INFO [{:6}]\033[0m".format(
                    ticks_ms(), ticks_diff(ticks_ms(), self.t), self.name
                ),
                *args
            )
            self.t = ticks_ms()

    def debug(self, *args):
        if self.level < 2:
            print(
                "\033[90m{:6d}:{:5d}ms\033[0m \033[93mDBUG [{:6}]\033[0m".format(
                    ticks_ms(), ticks_diff(ticks_ms(), self.t), self.name
                ),
                *args
            )
            self.t = ticks_ms()

    def warn(self, *args):
        if self.level < 3:
            print(
                "\033[90m{:6d}:{:5d}ms\033[0m \033[91mWARN [{:6}]\033[0m".format(
                    ticks_ms(), ticks_diff(ticks_ms(), self.t), self.name
                ),
                *args
            )
            self.t = ticks_ms()

    def crit(self, *args):
        if self.level < 4:
            print(
                "\033[90m{:6d}:{:5d}ms\033[0m \033[4mCRIT [{:6}]\033[0m".format(
                    ticks_ms(), ticks_diff(ticks_ms(), self.t), self.name
                ),
                *args
            )
            self.t = ticks_ms()
