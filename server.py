#!/usr/bin/env python

import logging
import threading
from logging import config

import telescopy.devices
from indi.device.pool import DevicePool
from indi.routing import Router
from indi.transport.server import TCP as TCPServer
from indi.transport.server import WebSocket as WebSocketServer
from telescopy import settings
from telescopy.http import HttpServer

router = Router()

settings.LOGGING["handlers"]["indi"]["router"] = [router]
config.dictConfig(settings.LOGGING)



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
