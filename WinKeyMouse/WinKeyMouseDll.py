# 参照Github https://github.com/bode135/VirtualKey_with_Ctypes

# from ctypes import POINTER, c_ulong, Structure, c_ushort, c_short, c_long, byref, windll, pointer, sizeof, Union
from keyboard import key_to_scan_codes
from time import sleep

from ctypes import *
from ctypes.wintypes import MSG, HINSTANCE
import win32con
from atexit import register
from warnings import warn
from traceback import format_exc

PUL = POINTER(c_ulong)


class KeyBdInput(Structure):
    _fields_ = [
        ("wVk", c_ushort),
        ("wScan", c_ushort),
        ("dwFlags", c_ulong),
        ("time", c_ulong),
        ("dwExtraInfo", PUL)
    ]


class HardwareInput(Structure):
    _fields_ = [
        ("uMsg", c_ulong),
        ("wParamL", c_short),
        ("wParamH", c_ushort)
    ]


class MouseInput(Structure):
    _fields_ = [
        ("dx", c_long),
        ("dy", c_long),
        ("mouseData", c_ulong),
        ("dwFlags", c_ulong),
        ("time", c_ulong),
        ("dwExtraInfo", PUL)
    ]


class InputI(Union):
    _fields_ = [
        ("ki", KeyBdInput),
        ("mi", MouseInput),
        ("hi", HardwareInput)
    ]


class Input(Structure):
    _fields_ = [
        ("type", c_ulong),
        ("ii", InputI)
    ]


class POINT(Structure):
    _fields_ = [
        ('x', c_long),
        ('y', c_long)
    ]


def screen():
    user32 = windll.user32
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


def position():
    orig = POINT()
    windll.user32.GetCursorPos(byref(orig))
    return int(orig.x), int(orig.y)


def set_position(pos):
    x, y = pos
    windll.user32.SetCursorPos(x, y)


def send_mouse_move(x, y, duration=0.1):
    screen_x, screen_y = screen()
    org_x, org_y = position()
    if x == org_x or y == org_y:
        return
    x = 0 if x < 0 else x
    y = 0 if y < 0 else y
    x = screen_x - 1 if x >= screen_x else x
    y = screen_y - 1 if y >= screen_y else y
    move_one_time = 0.01
    if duration <= move_one_time:
        set_position((x, y))
        return
    move_num = int(duration / move_one_time)
    move_x = int((x - org_x) / move_num)
    move_y = int((y - org_y) / move_num)
    if move_x == 0 and move_y == 0:
        set_position((x, y))
        return
    cur_x = org_x + move_x
    cur_y = org_y + move_y
    while abs(cur_x - x) > abs(move_x):
        set_position((cur_x, cur_y))
        cur_x = cur_x + move_x
        cur_y = cur_y + move_y
        sleep(move_one_time)
    if x == org_x or y == org_y:
        return
    set_position((x, y))
    sleep(move_one_time)


def send_mouse(event="left", pressed=1):
    if pressed:
        mouse_event = 0x00008 if event == "right" else 0x0002
    else:
        mouse_event = 0x0010 if event == "right" else 0x0004
    FInputs = Input * 2
    extra = c_ulong(0)
    ii_ = InputI()
    ii_.mi = MouseInput(0, 0, 0, mouse_event, 0, pointer(extra))
    x = FInputs((0, ii_))
    windll.user32.SendInput(2, pointer(x), sizeof(x[0]))


def send_keyboard(key, pressed=1):
    scancode = key_to_scan_codes(key)
    if isinstance(scancode, tuple):
        scancode = scancode[0]  # 若按键有两个扫描码, 类型: tuple; 则取第一个扫描码

    FInputs = Input * 1
    extra = c_ulong(0)
    ii_ = InputI()
    flag = 0x8
    ii_.ki = KeyBdInput(0, 0, flag, 0, pointer(extra))
    InputBox = FInputs((1, ii_))
    if scancode is None:
        return
    InputBox[0].ii.ki.wScan = scancode
    InputBox[0].ii.ki.dwFlags = 0x8

    if not pressed:
        InputBox[0].ii.ki.dwFlags |= 0x2

    windll.user32.SendInput(1, pointer(InputBox), sizeof(InputBox[0]))
    return 1


KEYBOARD_WH_LL = win32con.WH_KEYBOARD_LL
MOUSE_WH_LL = win32con.WH_MOUSE_LL
HOOK_PRO_TYPE = CFUNCTYPE(c_int, c_int, HINSTANCE, POINTER(c_void_p))


class WinKeyMouseHook:

    def __init__(self, wh_ll, hook):
        self.HOOK_HD = None
        self.WH_LL = wh_ll
        self.hook = hook
        self.user32 = windll.user32

    def install(self):
        if self.WH_LL != KEYBOARD_WH_LL and self.WH_LL != MOUSE_WH_LL:
            raise RuntimeError("Error wh_ll!")

        def handler(n_code, w_param, l_param):
            next_hook = True
            try:
                if n_code == win32con.HC_ACTION:
                    if self.WH_LL == KEYBOARD_WH_LL:
                        KbDllHookStruct_p = POINTER(KbDllHookStruct)
                        param = cast(l_param, KbDllHookStruct_p)
                        print(param.contents.vkCode)
                    else:
                        MSllHookStruct_p = POINTER(MSllHookStruct)
                        param = cast(l_param, MSllHookStruct_p)
                        # 鼠标左键点击
                        if w_param == win32con.WM_LBUTTONDOWN:
                            print("左键点击，坐标：x:%d,y:%d" % (param.contents.pt.x, param.contents.pt.y))
                        elif w_param == win32con.WM_LBUTTONUP:
                            print("左键抬起，坐标：x:%d,y:%d" % (param.contents.pt.x, param.contents.pt.y))
                        elif w_param == win32con.WM_MOUSEMOVE:
                            print("鼠标移动，坐标：x:%d,y:%d" % (param.contents.pt.x, param.contents.pt.y))
                        elif w_param == win32con.WM_RBUTTONDOWN:
                            print("右键点击，坐标：x:%d,y:%d" % (param.contents.pt.x, param.contents.pt.y))
                        elif w_param == win32con.WM_RBUTTONUP:
                            print("右键抬起，坐标：x:%d,y:%d" % (param.contents.pt.x, param.contents.pt.y))
                    if self.hook is not None:
                        next_hook = self.hook(n_code, w_param, l_param)
            except Exception as e:
                warn(f'handler produced a traceback:\n{format_exc()}')
            finally:
                if next_hook is not False:
                    return self.user32.CallNextHookEx(self.HOOK_HD, n_code, w_param, l_param)
                else:
                    return False

        hook_pointer = HOOK_PRO_TYPE(handler)
        self.HOOK_HD = self.user32.SetWindowsHookExA(
            self.WH_LL,
            hook_pointer,
            None,
            0
        )
        register(self.user32.UnhookWindowsHookEx, self.HOOK_HD)
        message = MSG()
        while self.HOOK_HD is not None:
            msg = self.user32.GetMessageA(message, 0, 0, 0)
            if msg in [0, -1]:
                self.uninstall()
                break
            else:
                self.user32.TranslateMessage(message)
                self.user32.DispatchMessageW(message)

    def uninstall(self):
        if self.HOOK_HD is None:
            return
        self.user32.UnhookWindowsHookEx(self.HOOK_HD)
        self.HOOK_HD = None


class KbDllHookStruct(Structure):
    _fields_ = [
        ('vkCode', c_int),
        ('scanCode', c_int),
        ('flags', c_int),
        ('time', c_int),
        ('dwExtraInfo', c_uint),
        ('', c_void_p)
    ]

class MSllHookStruct(Structure):
    _fields_ = [
        ('pt', POINT),
        ('hwnd', c_int),
        ('wHitTestCode', c_uint),
        ('dwExtraInfo', c_uint),
    ]
