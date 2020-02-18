from indi.device import Proxy
from indi.device.pool import DevicePool
from indi.device import properties


@DevicePool.register
class OneProxy(Proxy):
    name = "ONE_PROXY"

    address = "localhost"
    port = 7625
