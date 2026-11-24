# core/apps.py
"""
App launching and basic system control utilities for Nova.
Windows is the primary target (per the project setup); macOS/Linux get
best-effort equivalents where a straightforward one exists.
"""

import ctypes
import os
import platform
import subprocess
import logging

# Windows virtual-key codes for media keys, used to nudge system volume
# without pulling in a heavy audio-control dependency like pycaw.
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF

# name -> (windows_cmd, macos_cmd, linux_cmd)
APP_COMMANDS = {
    "chrome": ("chrome", ["open", "-a", "Google Chrome"], ["google-chrome"]),
    "notepad": ("notepad", ["open", "-a", "TextEdit"], ["gedit"]),
    "calculator": ("calc", ["open", "-a", "Calculator"], ["gnome-calculator"]),
    "explorer": ("explorer", ["open", "."], ["xdg-open", "."]),
    "file explorer": ("explorer", ["open", "."], ["xdg-open", "."]),
    "settings": ("start ms-settings:", ["open", "-a", "System Settings"], ["gnome-control-center"]),
    "task manager": ("taskmgr", ["open", "-a", "Activity Monitor"], ["gnome-system-monitor"]),
    "command prompt": ("start cmd", ["open", "-a", "Terminal"], ["x-terminal-emulator"]),
    "terminal": ("start wt || start cmd", ["open", "-a", "Terminal"], ["x-terminal-emulator"]),
    "paint": ("mspaint", ["open", "-a", "Preview"], ["pinta"]),
}


def openVSCode():
    """Open Visual Studio Code safely on any OS."""
    try:
        system = platform.system().lower()

        if system == "windows":
            path = r"C:\Users\{}\AppData\Local\Programs\Microsoft VS Code\Code.exe".format(os.getenv("USERNAME"))
            if os.path.exists(path):
                os.startfile(path)
            else:
                subprocess.Popen("code", shell=True)
        elif system == "darwin":
            subprocess.Popen(["open", "-a", "Visual Studio Code"])
        else:
            subprocess.Popen(["code"])
        return True

    except Exception:
        logging.exception("Failed to open VS Code.")
        return False


def open_app(name: str) -> bool:
    """Open a known application by friendly name (e.g. 'chrome', 'notepad')."""
    name = (name or "").strip().lower()

    if name in ("vs code", "vscode", "code", "visual studio code"):
        return openVSCode()

    if name not in APP_COMMANDS:
        return False

    win_cmd, mac_cmd, linux_cmd = APP_COMMANDS[name]
    system = platform.system().lower()

    try:
        if system == "windows":
            subprocess.Popen(win_cmd, shell=True)
        elif system == "darwin":
            subprocess.Popen(mac_cmd)
        else:
            subprocess.Popen(linux_cmd)
        return True
    except Exception:
        logging.exception(f"Failed to open app: {name}")
        return False


def lock_screen() -> bool:
    """Lock the workstation. Windows-only for now."""
    try:
        system = platform.system().lower()
        if system == "windows":
            ctypes.windll.user32.LockWorkStation()
            return True
        elif system == "darwin":
            subprocess.Popen(["pmset", "displaysleepnow"])
            return True
        else:
            subprocess.Popen(["xdg-screensaver", "lock"])
            return True
    except Exception:
        logging.exception("Failed to lock screen.")
        return False


def _press_media_key(vk_code: int) -> bool:
    """Simulate a media key press on Windows via keybd_event."""
    try:
        ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
        ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)  # KEYEVENTF_KEYUP
        return True
    except Exception:
        logging.exception("Failed to simulate media key press.")
        return False


def volume_up() -> bool:
    if platform.system().lower() != "windows":
        return False
    return _press_media_key(VK_VOLUME_UP)


def volume_down() -> bool:
    if platform.system().lower() != "windows":
        return False
    return _press_media_key(VK_VOLUME_DOWN)


def mute() -> bool:
    if platform.system().lower() != "windows":
        return False
    return _press_media_key(VK_VOLUME_MUTE)
