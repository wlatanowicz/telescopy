#!/usr/bin/env python

import threading
import logging

from logging import config
from indi.device.pool import DevicePool
from indi.routing import Router
from indi.transport.server import TCP as TCPServer
from indi.transport.server import WebSocket as WebSocketServer

from telescopy.http import HttpServer
from telescopy import settings


router = Router()

settings.LOGGING["handlers"]["indi"]["router"] = [router]
config.dictConfig(settings.LOGGING)


import telescopy.devices

if settings.ENABLE_SIMULATORS:
    import telescopy_sims.devices

HttpServer.start()


DevicePool.init(router)

tcp_server = TCPServer(router=router)
ws_server = WebSocketServer(router=router)

tcp_th = threading.Thread(target=tcp_server.start, daemon=True,)

ws_th = threading.Thread(target=ws_server.start, daemon=True,)

tcp_th.start()
ws_th.start()

while True:
    pass
