from WinKeyMouse import WinKeyMouseDll
from WinKeyMouse import WinKeyMouseUtils
from WinKeyMouse.WinKeyMouseDll import screen, position

SLEEP_TIME = 100


def move_to(x, y, duration=SLEEP_TIME, sleep_time=SLEEP_TIME):
    duration = WinKeyMouseUtils.random_(duration, random=2)
    x, y = WinKeyMouseUtils.random_position(x, y)
    WinKeyMouseDll.send_mouse_move(x, y, duration=duration / 1000)
    WinKeyMouseUtils.random_sleep(sleep_time)


def mouse_down(event="left", sleep_time=SLEEP_TIME):
    mouse_event(event, 1, sleep_time)


def mouse_up(event="left", sleep_time=SLEEP_TIME):
    mouse_event(event, 0, sleep_time)


def mouse_click(event="left", sleep_time=SLEEP_TIME):
    mouse_event(event, 1, sleep_time)
    mouse_event(event, 0, sleep_time)


def mouse_event(event, pressed, sleep_time=SLEEP_TIME):
    WinKeyMouseDll.send_mouse(event, pressed)
    WinKeyMouseUtils.random_sleep(sleep_time)


def key_down(ch, sleep_time=SLEEP_TIME):
    key_event(ch, 1, sleep_time)


def key_up(ch, sleep_time=SLEEP_TIME):
    key_event(ch, 0, sleep_time)


def key_click(ch, sleep_time=SLEEP_TIME):
    key_event(ch, 1, sleep_time)
    key_event(ch, 0, sleep_time)


def key_event(ch, pressed, sleep_time=SLEEP_TIME):
    WinKeyMouseDll.send_keyboard(ch, pressed)
    WinKeyMouseUtils.random_sleep(sleep_time)


def keyboard_hook_manager():
    return WinKeyMouseDll.KeyRatHook(WinKeyMouseDll.KEYBOARD_WH_LL, None)


def mouse_hook_manager():
    return WinKeyMouseDll.KeyRatHook(WinKeyMouseDll.MOUSE_WH_LL, None)
