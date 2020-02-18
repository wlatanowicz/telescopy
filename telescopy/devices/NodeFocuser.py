import time
import logging

from indi.device import Driver, non_blocking
from indi.device.pool import DevicePool
from indi.device import properties
from indi.message import const

from telescopy.devices.hardware.focuser.NodeMCU import NodeMCU
from telescopy import settings


logger = logging.getLogger(__name__)


@DevicePool.register
class NodeFocuser(Driver):
    name = "NODE_FOCUSER"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.focuser = NodeMCU(settings.FOCUSER_IP)

    general = properties.Group(
        "GENERAL",
        vectors=dict(
            connection=properties.Standard("CONNECTION"),
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
            active_device=properties.Standard(
                "ACTIVE_DEVICES",
                elements=dict(camera=properties.Text("ACTIVE_FOCUSER", default=name)),
            ),
        ),
    )
    general.connection.connect.onwrite = "connect"

    position = properties.Group(
        "POSITION",
        enabled=False,
        vectors=dict(position=properties.Standard("ABS_FOCUS_POSITION"),),
    )
    position.position.position.onwrite = "reposition"

    @non_blocking
    def connect(self, sender, value):
        connected = value == const.SwitchState.ON
        self.general.connection.state_ = const.State.BUSY

        if connected:
            try:
                self.position.position.position.reset_value(self.focuser.get_position())
                self.general.connection.state_ = const.State.OK
            except Exception as e:
                self.general.connection.state_ = const.State.ALERT
                connected = False
                logger.error(e)

        self.general.connection.connect.bool_value = connected
        self.position.enabled = connected
        self.general.info.enabled = connected

    @non_blocking
    def reposition(self, sender, value):
        self.position.position.state_ = const.State.BUSY
        try:
            self.focuser.set_position(value, wait=False)
            while (
                abs(float(self.position.position.position.value) - float(value)) > 0.01
            ):
                time.sleep(1)
                self.position.position.position.value = self.focuser.get_position()

            self.position.position.state_ = const.State.OK
        except Exception as e:
            self.position.position.state_ = const.State.ALERT
            logger.error(e)
