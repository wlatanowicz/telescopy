from indi.device import Driver, non_blocking
from indi.device.pool import DevicePool


@DevicePool.register
class Dome(Driver):
    name = 'DOME'
