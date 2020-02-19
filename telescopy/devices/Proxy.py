from indi.device import Proxy, properties
from indi.device.pool import DevicePool


@DevicePool.register
class OneProxy(Proxy):
    name = "ONE_PROXY"

    address = "localhost"
    port = 7625
