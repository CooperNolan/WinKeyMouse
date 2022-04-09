from WinKeyMouse import WinKeyMouseEvent as event


if __name__ == "__main__":
    manager = event.Manager()
    manager.start()

    record_data = manager.recording()
    event.replay(record_data)

    manager.stop()

