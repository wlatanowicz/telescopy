import threading
import datetime
import os

from indi.device import Driver
from indi.device.pool import DevicePool
from indi.device import properties
from indi.message import const

from telescopy.devices.hardware.camera.SonySLTA58 import SonySLTA58 as SonySLTA58_hw
from telescopy import settings


@DevicePool.register
class SonySLTA58(Driver):
    name = 'SONY_SLT_A58'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.camera = SonySLTA58_hw()

    general = properties.Group(
        'GENERAL',
        vectors=dict(
            connection=properties.Standard('CONNECTION', onchange='connect'),
            active_device=properties.Standard(
                'ACTIVE_DEVICES',
                elements=dict(
                    camera=properties.Text('ACTIVE_CCD', default=name)
                )
            )
        )
    )

    settings = properties.Group(
        'SETTINGS',
        enabled=False,
        vectors=dict(
            upload_mode=properties.Standard('UPLOAD_MODE', default_on='UPLOAD_LOCAL'),
            iso=properties.SwitchVector(
                'ISO',
                rule=properties.SwitchVector.RULES.ONE_OF_MANY,
                default_on='100',
                onchange='iso_changed',
                elements=dict(
                    iso100=properties.Switch('100'),
                    iso200=properties.Switch('200'),
                    iso400=properties.Switch('400'),
                    iso800=properties.Switch('800'),
                    iso1600=properties.Switch('1600'),
                    iso3200=properties.Switch('3200'),
                )
            ),
        )
    )

    exposition = properties.Group(
        'EXPOSITION',
        enabled=False,
        vectors=dict(
            exposure=properties.Standard('CCD_EXPOSURE')
        )
    )
    exposition.exposure.time.onwrite = 'expose'

    images = properties.Group(
        'IMAGES',
        enabled=False,
        vectors=dict(
            last_url=properties.TextVector(
                'LAST_IMAGE_URL',
                perm=const.Permissions.READ_ONLY,
                elements=dict(
                    arw=properties.Text('RAW'),
                    jpg=properties.Text('JPEG'),
                )
            )
        )
    )

    def connect(self, sender):
        connected = sender.connect.bool_value

        if connected:
            self.settings.iso.reset_selected_value(self.camera.get_iso())

        self.exposition.enabled = connected
        self.settings.enabled = connected
        self.images.enabled = connected

    def expose(self, sender):
        def worker():
            self.exposition.exposure.state_ = const.State.BUSY
            file_name = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')
            imgs = self.camera.expose(float(self.exposition.exposure.time.value))

            if self.settings.upload_mode.selected_value in ('UPLOAD_LOCAL', 'UPLOAD_BOTH',):
                save_dir = os.path.join(settings.PUB_DIR, self.name)
                if not os.path.exists(save_dir):
                    os.mkdir(save_dir)

                for ext, data in imgs.items():
                    rel_path = os.path.join(self.name, f'{file_name}.{ext}')
                    file_path = os.path.join(save_dir, f'{file_name}.{ext}')
                    if os.path.exists(file_path):
                        os.unlink(file_path)
                    with open(file_path, mode='wb') as f:
                        f.write(data)

                    getattr(self.images.last_url, ext).value = rel_path

            self.exposition.exposure.state_ = const.State.OK

        w = threading.Thread(target=worker)
        w.start()

    def iso_changed(self, sender):
        def worker():
            self.settings.iso.state_ = const.State.BUSY
            self.camera.set_iso(self.settings.iso.selected_value)
            self.settings.iso.state_ = const.State.OK
        w = threading.Thread(target=worker)
        w.start()
