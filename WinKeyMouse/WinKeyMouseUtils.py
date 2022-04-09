from time import sleep as time_sleep, strftime
from re import findall, match, search
from win32gui import IsWindow, IsWindowEnabled, IsWindowVisible, GetWindowText, EnumWindows, FindWindow, \
    SetForegroundWindow
from datetime import datetime
from configparser import ConfigParser
from threading import Thread
from random import randint
from ctypes import pythonapi, py_object

CONFIG_NAME = "./config.ini"
RES_PATH = "./res/"
RANDOM_SLEEP = 0.5


def timestamp():
    return int(datetime.now().timestamp() * 1000)


def sleep(millis):
    random_sleep(millis, random=0)


def random_sleep(millis, random=RANDOM_SLEEP):
    if millis <= 0:
        return
    random_millis = random_(millis, random)
    time_sleep(random_millis / 1000)


def random_(num, random=RANDOM_SLEEP):
    if random > 0.01:
        return num + randint(0, int(num * random))
    return num


def random_position(x, y, random=5):
    random_max = abs(random)
    random_min = random_max * -1
    random_result = randint(random_min, random_max)
    return x + random_result, y + random_result


def format_date(pattern='%H:%M:%S', millis=False):
    # %Y-%m-%d %H:%M:%S
    now = datetime.now()
    date = strftime(pattern, now.timetuple())
    if millis:
        millis_str = str(int(now.microsecond / 1000))
        while len(millis_str) < 3:
            millis_str += "0"
        date = date + "." + millis_str
    return date


def parsing_position(text_content, screenwidth, screenheight):
    result = findall(r'^x=\d+,y=\d+$', text_content, flags=0)
    if len(result) == 0:
        return None
    mth = match(r'x=(\d+),y=(\d+)', result[0])
    x = int(mth.group(1))
    y = int(mth.group(2))
    if x < 0 or x >= screenwidth:
        return None
    if y < 0 or y >= screenheight:
        return None
    return x, y, result[0]


def parsing_second(text_content):
    result = findall(r'^\d+(?:.?\d{1,3})$', text_content, flags=0)
    if len(result) == 0:
        return None
    return result[0]


def get_config():
    config = ConfigParser()
    config.read(CONFIG_NAME, encoding='utf-8')
    return config


def save_config(section, dicts=None):
    if dicts is None:
        return
    config = get_config()
    if config.has_section(section) is False:
        config.add_section(section)

    for key, value in dicts.items():
        config.set(section, key, value)

    with open(CONFIG_NAME, mode='w', encoding='utf-8') as o:
        config.write(o)


WINDOWS_NAME_PATH = r".* - Visual Studio Code"


def windows_search(name_patten=WINDOWS_NAME_PATH):
    titles = set()

    def foo(hwnd_item, mouse):
        if IsWindow(hwnd_item) and IsWindowEnabled(hwnd_item) and IsWindowVisible(hwnd_item):
            titles.add(GetWindowText(hwnd_item))

    EnumWindows(foo, 0)
    for title in titles:
        if search(name_patten, title):
            return title


def windows_hwnd_find(name=None, name_patten=WINDOWS_NAME_PATH):
    if name is None:
        name = windows_search(name_patten)
    if name is None:
        return None
    hwnd = FindWindow(None, name)
    if hwnd == 0:
        return None
    return hwnd


def windows_foreground(hwnd):
    SetForegroundWindow(hwnd)


def thread_start_daemon(target):
    thread = Thread(target=target)
    thread.setDaemon(True)
    thread.start()
    return thread.native_id


def stop_thread(native_id):
    if native_id is None:
        return False
    res = pythonapi.PyThreadState_SetAsyncExc(native_id, py_object(SystemExit))
    if res > 1:
        pythonapi.PyThreadState_SetAsyncExc(native_id, 0)
    return True
