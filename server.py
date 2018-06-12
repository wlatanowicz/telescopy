#!/usr/bin/env python

from indi.device.pool import DevicePool
from indi.routing import Router
from indi.transport.server import TCP as TCPServer
from indi.logging import logger, Handler

from telescopy.http import HttpServer
from telescopy import settings

import telescopy.devices

if settings.ENABLE_SIMULATORS:
    import telescopy_sims.devices

HttpServer.start()

router = Router()

logger.addHandler(Handler(router))

DevicePool.init(router)

server = TCPServer(router=router)
server.start()
