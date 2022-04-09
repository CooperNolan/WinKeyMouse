from pynput import keyboard, mouse
from WinKeyMouse import WinKeyMouseDll
from WinKeyMouse import WinKeyMouseUtils
from uuid import uuid4
from operator import attrgetter

EVENT_TYPE_KEY = "key"
EVENT_TYPE_RAT = "rat"

MOUSE_MOVE = "move"
MOUSE_LEFT = "left"
MOUSE_RIGHT = "right"
MOUSE_SCROLL = "scroll"

# 小数字键盘VK对应值
VK_CODE = {
    "110": ".",
    "96": "0",
    "97": "1",
    "98": "2",
    "99": "3",
    "100": "4",
    "101": "5",
    "102": "6",
    "103": "7",
    "104": "8",
    "105": "9"
}


class Event:
    def __init__(self, event_type=None, pressed=1, button=None, x=0, y=0, dx=0, dy=0):
        self.event_type = event_type  # 按键类型 key键盘 rat鼠标
        self.pressed = pressed  # 1 按下 0放开
        self.button = button  # 具体的键
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.timestamp = WinKeyMouseUtils.timestamp()


def default_event_handler(event):
    log = f'{"按下" if event.pressed else "松开"}: {event.button}'
    if event.event_type == EVENT_TYPE_RAT:
        log = log + f'(x={event.x},y={event.y})'
    print(log)


class Manager:
    def __init__(self, key_handler=default_event_handler, mouse_handler=default_event_handler):
        self.thread_keyboard_id = None
        self.thread_mouse_id = None
        self.key_handler = key_handler
        self.mouse_handler = mouse_handler

        self.recording_data = {}

    def start_keyboard(self):
        if self.thread_keyboard_id is not None:
            return

        def keyboard_handler():
            with keyboard.Events() as keyboard_event:
                for e in keyboard_event:
                    event = Event(event_type=EVENT_TYPE_KEY)
                    if isinstance(e, keyboard.Events.Press):
                        event.pressed = 1
                    elif isinstance(e, keyboard.Events.Release):
                        event.pressed = 0
                    # 处理button
                    button = str(e.key).replace("'", "")
                    if button.startswith("Key."):
                        index_ = button.find("_")
                        button = button[4: index_ if index_ != -1 else None]
                    elif len(button) > 2 and (button[0], button[-1]) == ('<', '>'):
                        button = VK_CODE.get(button[1:-1])
                    elif button == "\"\"":
                        button = "'"
                    elif button == "\\\\":
                        button = "\\"
                    event.button = button
                    self.pre_handler(event)
                    if self.key_handler is not None:
                        self.key_handler(event)

        self.thread_keyboard_id = WinKeyMouseUtils.thread_start_daemon(target=keyboard_handler)
        if self.thread_keyboard_id is None:
            return False
        return True

    def stop_keyboard(self):
        if self.thread_keyboard_id is None:
            return
        stop = WinKeyMouseUtils.stop_thread(self.thread_keyboard_id)
        self.thread_keyboard_id = None
        return stop

    def start_mouse(self):
        if self.thread_mouse_id is not None:
            return

        def mouse_handler():
            with mouse.Events() as mouse_event:
                for e in mouse_event:
                    # 迭代用法。
                    event = Event(event_type=EVENT_TYPE_RAT, x=e.x, y=e.y)
                    if isinstance(e, mouse.Events.Move):  # 鼠标移动事件
                        event.button = MOUSE_MOVE
                    elif isinstance(e, mouse.Events.Click):
                        event.pressed = e.pressed
                        event.button = str(e.button)[7:]
                    elif isinstance(e, mouse.Events.Scroll):
                        event.button = MOUSE_SCROLL
                        event.dx = e.dx
                        event.dy = e.dy
                    self.pre_handler(event)
                    if self.mouse_handler is not None:
                        self.mouse_handler(event)

        self.thread_mouse_id = WinKeyMouseUtils.thread_start_daemon(target=mouse_handler)
        if self.thread_mouse_id is None:
            return False
        return True

    def pre_handler(self, event):
        if event.event_type == EVENT_TYPE_KEY and event.button == "esc":
            self.recording_data.clear()
        for key, value in self.recording_data.items():
            value.append(event)

    def stop_mouse(self):
        if self.thread_mouse_id is None:
            return
        stop = WinKeyMouseUtils.stop_thread(self.thread_mouse_id)
        self.thread_mouse_id = None
        return stop

    def start(self):
        self.start_keyboard()
        self.start_mouse()

    def stop(self):
        self.stop_keyboard()
        self.stop_mouse()

    def recording(self):
        self.start()

        uuid = uuid4()
        recoding_data = []
        self.recording_data[uuid] = recoding_data
        while True:
            WinKeyMouseUtils.sleep(50)
            if self.recording_data.__contains__(uuid) is False:
                break

        recoding_data.sort(key=attrgetter("timestamp"))

        key_down = {}  # 键盘多次按下只记录第一次
        mouse_move_event = None  # 鼠标移动10毫秒一次
        deal_data = []
        for event in recoding_data:
            if event.event_type == EVENT_TYPE_KEY:
                if event.pressed == key_down.get(event.button):
                    continue
                key_down[event.button] = event.pressed
            else:
                if event.button == MOUSE_SCROLL:
                    continue
                if event.button == MOUSE_MOVE:
                    if mouse_move_event is not None and event.timestamp - mouse_move_event.timestamp < 10:
                        continue
                    mouse_move_event = event
                    continue
            deal_data.append(event)
        return deal_data


def replay(recoding_data):
    before_timestamp = None
    for event in recoding_data:
        if before_timestamp is not None:
            WinKeyMouseUtils.sleep(event.timestamp - before_timestamp)
        before_timestamp = event.timestamp
        if event.event_type == EVENT_TYPE_KEY:
            WinKeyMouseDll.send_keyboard(event.button, pressed=event.pressed)
        else:
            if event.button == MOUSE_LEFT or event.button == MOUSE_RIGHT:
                WinKeyMouseDll.send_mouse(event.button, pressed=event.pressed)
