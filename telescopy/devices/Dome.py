from indi.device import Driver, non_blocking
from indi.device.pool import DevicePool


@DevicePool.register
class Dome(Driver):
    name = 'DOME'

    general = properties.Group(
        'GENERAL',
        vectors=dict(
            connection=properties.Standard('CONNECTION'),
            info=properties.TextVector(
                'INFO',
                enabled=False,
                perm=const.Permissions.READ_ONLY,
                elements=dict(
                    manufacturer=properties.Text('MANUFACTURER', default='Wiktor Latanowicz'),
                    ip=properties.Text('IP_ADDRESS', default=settings.DOME_IP),
                )
            ),
            active_device=properties.Standard(
                'ACTIVE_DEVICES',
                elements=dict(
                    camera=properties.Text('ACTIVE_DOME', default=name)
                )
            )
        )
    )
    general.connection.connect.onwrite = 'connect'

    position = properties.Group(
        'POSITION',
        enabled=False,
        vectors=dict(
            position=properties.Standard('ABS_FOCUS_POSITION'),
        )
    )
    position.position.position.onwrite = 'reposition'
