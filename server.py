#!/usr/bin/env python

from indi.device.pool import DevicePool
from indi.routing import Router
from indi.transport.server import TCP as TCPServer

from telescopy.http import HttpServer


from telescopy.devices import *

HttpServer.start()

router = Router()

DevicePool.init(router)

server = TCPServer(router=router)
server.start()
