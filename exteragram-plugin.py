__id__ = "termux_bridge"
__name__ = "Termux bridge"
__description__ = ""
__icon__ = "sldkfjhslk/0"
__author__ = "@Nicto2282"
__version__ = "1.0.0"
__app_version__ = ">=12.5.1"
__sdk_version__ = ">=1.4.3.3"

from typing import Any

from base_plugin import BasePlugin, HookResult, HookStrategy
import socket as soc
from org.telegram.messenger import LocaleController
from ui.bulletin import BulletinHelper
from ui.settings import Switch, Input, Text
import json
import time
import hashlib

SU_ALLOW = False
HOST = "127.0.0.1"
PORT = 5462
REQUEST_SIZE = 1024
END_STRING = "<END>"
PASSWORD = ""

STRINGS = {"ru":{"command_not_transparent": "Команда не передана", "change_shell_index": "Изменён терминал на: {}", "descript": """
.term [число] - изменить текущий shell-оболочку по умолчанию (отчёт начинается с 0)
.term [текст] - выполняет команду в shell-оболочке по умолчанию
.term [число] [текст] - выполняет команду в shell-оболочке
 также можно ответить на сообщение если оно является **только** текстом или файлом (.term или .term [число]) чтобы его выполнить""",
                 "su_allow_switcher": "Разрешить команду su",
                 "command_blacklist": "Чёрный список команд"},
           "en":{}}

def get_lang():
    return "ru"
    try:
        return "ru" if str(LocaleController.getInstance().getCurrentLocale().getLanguage()).startswith("ru") else "en"
    except Exception:
        return "en"

class Connect:
    def __init__(self, port: int, host: str, request_size: int, end_string: str, socket: soc.socket = soc.socket(soc.AF_INET, soc.SOCK_STREAM)):
        self.socket = socket
        
        self.socket.connect((host, port))
        self.request_size = request_size
        self.end_string = end_string

    def close(self):
        self.socket.close()

    async def read(self):
        resalt = ""
        while True:
            text = self.socket.recv(self.request_size).decode("utf-8")
            resalt += text
            if self.end_string in resalt:
                break
        resalt = resalt[:-len(self.end_string)]
        print(resalt)
        return json.loads(resalt)

    async def write(self, text: str | bytes | bytearray):
        if isinstance(text, str):
            text = text.encode("utf-8")
        self.socket.sendall(text)

class TermuxBridge(BasePlugin):
    def on_plugin_load(self) -> None:
        self.socket = soc.socket(soc.AF_INET, soc.SOCK_STREAM)
        self.lang = get_lang()
        self.connect = Connect(PORT, HOST, REQUEST_SIZE, END_STRING, self.socket)
        self.shell_index = 0
        self.password = ""

    def create_settings(self) -> list[Any]:
        return [Switch(
            key="su_allow_key",
            text=STRINGS[self.lang]["su_allow_switcher"],
            default=self.get_setting("su_allow_key", False)
        ), Input(
            key="command_blacklist_key",
            text=STRINGS[self.lang]["command_blacklist"],
            default=self.get_setting("command_blacklist_key", "")
        ), Text(
            text=STRINGS[self.lang]["descript"]
        )]


    def on_send_message_hook(self, account, params) -> HookResult:
        if not isinstance(getattr(params, "message"), str):
            return HookResult()

        text = str(params.message.strip())
        if not text.startswith(".term"):
            return HookResult()
        if text == ".term":
            BulletinHelper.show_error(STRINGS[self.lang]["command_not_transparent"])
        text = text.split()[1:]

        if len(text) == 1:
            if text[0].isdecimal():
                self.shell_index = int(text[0])
                BulletinHelper.show_info(STRINGS[self.lang]["change_shell_index"].format(self.shell_index))
            else:
                self.socket.sendall(json.dumps({"id": self.shell_index, "data": text[0]}))

