import asyncio
import random
import os

from src.core.BugBountyConsole import BugBountyConsole
from src.core.utility.Utility import Utility

ansi = Utility.colors()
config_file: str = 'src/core/config/config.json'


def heading():
    with open(f'src/core/banner/{random.choice(os.listdir("src/core/banner"))}', encoding='utf8') as f:
        lines = [line.rstrip() for line in f]
        for line in lines:
            print(f"{ansi['red']}{line}")
        print(ansi['reset'])


if __name__ == '__main__':
    import sys

    if sys.platform == 'win32':
        """ Attempting to fix ANSI/VT100 """
        from ctypes import *
        kernel32 = windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

    heading()
    console = BugBountyConsole(config_file)
    console.register_options()
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(console.main())
    except KeyboardInterrupt:
        pass
    except asyncio.CancelledError:
        pass
