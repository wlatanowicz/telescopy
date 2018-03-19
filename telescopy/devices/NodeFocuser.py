import threading

from indi.device import Driver
from indi.device.pool import DevicePool
from indi.device import properties
from indi.message import const

from telescopy.devices.hardware.focuser.NodeMCU import NodeMCU
from telescopy import settings


@DevicePool.register
class NodeFocuser(Driver):
    name = 'NODE_FOCUSER'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.focuser = NodeMCU(settings.FOCUSER_IP)

    general = properties.Group(
        'GENERAL',
        vectors=dict(
            connection=properties.Standard('CONNECTION', onchange='connect'),
            info=properties.TextVector(
                'INFO',
                enabled=False,
                perm=const.Permissions.READ_ONLY,
                elements=dict(
                    manufacturer=properties.Text('MANUFACTURER', default='Wiktor Latanowicz'),
                    camera_model=properties.Text('FOCUSER_MODEL', default='NodeFocuser'),
                    ip=properties.Text('IP_ADDRESS', default=settings.FOCUSER_IP),
                )
            ),
            active_device=properties.Standard(
                'ACTIVE_DEVICES',
                elements=dict(
                    camera=properties.Text('ACTIVE_FOCUSER', default=name)
                )
            )
        )
    )

    position = properties.Group(
        'POSITION',
        enabled=False,
        vectors=dict(
            position=properties.Standard('ABS_FOCUS_POSITION', onchange='reposition'),
        )
    )

    def connect(self, sender):
        connected = self.general.connection.connect.bool_value

        if connected:
            self.position.position.position.reset_value(self.focuser.get_position())

        self.position.enabled = connected
        self.general.info.enabled = connected

    def reposition(self, sender):
        def worker():
            self.position.position.state_ = const.State.BUSY
            try:
                self.focuser.set_position(self.position.position.position.value)
                self.position.position.state_ = const.State.OK
            except:
                self.position.position.state_ = const.State.ALERT
                raise

        w = threading.Thread(target=worker, daemon=True)
        w.start()
