__id__ = "termux_bridge"
__name__ = "Termux bridge"
__description__ = ""
__author__ = "@Nicto2282"
__version__ = "1.0.0"
__app_version__ = ">=12.5.1"
__sdk_version__ = ">=1.4.3.3"

from base_plugin import BasePlugin
import socket

SU_ALLOW = False
HOST = "127.0.0.1"
PORT = 5462
REQUEST_SIZE = 1024
END_STRING = "<END>"

class TermuxBridge(BasePlugin):
    def on_plugin_load(self) -> None:
    