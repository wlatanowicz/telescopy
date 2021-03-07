import logging
import time

from indi.device import Driver, non_blocking, properties
from indi.device.pool import default_pool
from indi.message import const
from indi.device.properties.const import DriverInterface
from indi.device.properties import standard

import settings
from .hardware.NodeSerial import NodeSerial

logger = logging.getLogger(__name__)


@default_pool.register
class NodeFocuser(Driver):
    name = "NODE_FOCUSER"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.focuser = NodeSerial(settings.FOCUSER_PORT, onupdate=self.device_updated)

    general = properties.Group(
        "GENERAL",
        vectors=dict(
            connection=standard.common.Connection(),
            driver_info = standard.common.DriverInfo(interface=(DriverInterface.FOCUSER,)),
            info=properties.TextVector(
                "INFO",
                enabled=False,
                perm=const.Permissions.READ_ONLY,
                elements=dict(
                    manufacturer=properties.Text(
                        "MANUFACTURER", default="Wiktor Latanowicz"
                    ),
                    camera_model=properties.Text(
                        "FOCUSER_MODEL", default="NodeFocuser"
                    ),
                    ip=properties.Text("IP_ADDRESS", default=settings.FOCUSER_IP),
                ),
            ),
        ),
    )
    general.connection.connect.onwrite = "connect"

    position = properties.Group(
        "POSITION",
        enabled=False,
        vectors=dict(
            position=standard.focuser.AbsolutePosition(min=0, max=15000, step=1),
            motion=standard.focuser.FocusMotion(),
            rel_position=standard.focuser.RelativePosition(),
            fmax=standard.focuser.FocusMax(),
            speed=properties.NumberVector(
                "SPEED",
                elements=dict(
                    speed=properties.Number(
                        "SPEED_VALUE", default=100,
                    )
                )
            )
        ),
    )
    position.position.position.onwrite = "reposition"
    position.rel_position.position.onwrite = "step"
    position.speed.speed.onchange = "change_speed"

    @non_blocking
    def connect(self, sender, value):
        connected = value == const.SwitchState.ON
        self.general.connection.state_ = const.State.BUSY

        if connected:
            try:
                self.focuser.connect()
                pos = None
                for _ in range(30):
                    time.sleep(1)
                    pos = self.focuser.get_position()
                    if pos is not None:
                        self.position.position.position.reset_value(pos)
                        break
                if pos is None:
                    raise Exception("Did not get focuser position")
                self.general.connection.state_ = const.State.OK
            except Exception as e:
                self.general.connection.state_ = const.State.ALERT
                connected = False
                logger.error(e)

        self.general.connection.connect.bool_value = connected
        self.position.enabled = connected
        self.general.info.enabled = connected

    def device_updated(self):
        self.position.position.position.state_ = const.State.OK if self.focuser.get_status() == "idle" else const.State.BUSY
        self.position.position.position.value = self.focuser.get_position()

    def reposition(self, sender, value):
        self.focuser.set_position(value)

    def change_speed(self, event):
        self.focuser.set_speed(self.position.speed.speed.value)

    def step(self, sender, value):
        self.position.rel_position.position.state_ = const.State.BUSY
        current_position = self.position.position.position.value
        direction = 1 if self.position.motion.outward.bool_value else -1
        new_value = current_position + direction * value

        self.focuser.set_position(new_value)

        self.position.rel_position.position.state_ = const.State.OK
