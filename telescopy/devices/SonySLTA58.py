import threading
import datetime
import os
import time

from indi.device import Driver, non_blocking
from indi.device.pool import DevicePool
from indi.device import properties
from indi.message import const
from indi.logging import logger

from telescopy.devices.hardware.camera.SonySLTA58 import SonySLTA58 as SonySLTA58_hw
from telescopy import settings


@DevicePool.register
class SonySLTA58(Driver):
    name = 'SONY_SLT_A58'

    BATTERY_CHECK_INTERVAL = 300

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.camera = SonySLTA58_hw()
        self.battcheck = None

    general = properties.Group(
        'GENERAL',
        vectors=dict(
            connection=properties.Standard('CONNECTION'),
            info=properties.TextVector(
                'INFO',
                enabled=False,
                perm=const.Permissions.READ_ONLY,
                elements=dict(
                    battery_level=properties.Text('BATTERY_LEVEL'),
                    manufacturer=properties.Text('MANUFACTURER'),
                    camera_model=properties.Text('CAMERA_MODEL'),
                    device_version=properties.Text('DEVICE_VERSION'),
                    serial_number=properties.Text('SERIAL_NUMBER'),
                )
            ),
            active_device=properties.Standard(
                'ACTIVE_DEVICES',
                elements=dict(
                    camera=properties.Text('ACTIVE_CCD', default=name)
                )
            )
        )
    )
    general.connection.connect.onwrite = 'connect'

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
            quality=properties.Standard('CCD_COMPRESSION')
        )
    )
    settings.quality.onchange = 'quality_changed'

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

    @non_blocking
    def connect(self, sender, value):
        self.general.connection.state_ = const.State.BUSY
        connected = value == const.SwitchState.ON
        if connected:
            try:
                try:
                    self.settings.iso.reset_selected_value(self.camera.get_iso())
                except Exception:
                    logger.error('Cannot read iso setting from camera', extra={'device': self})
                    raise

                try:
                    quality = self.camera.get_format()
                    self.settings.quality.compress.reset_bool_value('jpeg' in quality)
                    self.settings.quality.raw.reset_bool_value('raw' in quality)
                except Exception:
                    logger.error('Cannot read quality setting from camera')
                    raise

                try:
                    self.general.info.manufacturer.value = self.camera.get_manufacturer()
                    self.general.info.camera_model.value = self.camera.get_camera_model()
                    self.general.info.device_version.value = self.camera.get_device_version()
                    self.general.info.serial_number.value = self.camera.get_serial_number()
                except Exception:
                    logger.error('Cannot read properties from camera')
                    raise

                if self.battcheck is None or not self.battcheck.is_alive():
                    self.battcheck = threading.Thread(target=self.get_battery_level, daemon=True)
                    self.battcheck.start()

                self.general.connection.state_ = const.State.OK
            except Exception:
                connected = False
                self.general.connection.state_ = const.State.ALERT

        self.general.connection.connect.bool_value = connected
        self.general.info.enabled = connected
        self.exposition.enabled = connected
        self.settings.enabled = connected
        self.images.enabled = connected


    @non_blocking
    def expose(self, sender, value):
        self.exposition.exposure.state_ = const.State.BUSY
        try:
            file_name = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')
            self.exposition.exposure.time.value = value
            imgs = self.camera.expose(float(value))

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

                    getattr(self.images.last_url, ext).value = settings.BASE_HTTP_URL + rel_path
        except Exception:
            self.exposition.exposure.state_ = const.State.ALERT

        self.exposition.exposure.state_ = const.State.OK

    @non_blocking
    def iso_changed(self, sender, **kwargs):
        self.settings.iso.state_ = const.State.BUSY
        try:
            self.camera.set_iso(self.settings.iso.selected_value)
            self.settings.iso.state_ = const.State.OK
        except Exception:
            self.settings.iso.state_ = const.State.ALERT

    def get_battery_level(self):
        while self.general.connection.connect.bool_value:
            self.general.info.state_ = const.State.BUSY
            try:
                self.general.info.battery_level.value = self.camera.get_battery_level()
                self.general.info.state_ = const.State.OK
            except:
                self.general.info.battery_level.value = 'ERROR'
                self.general.info.state_ = const.State.ALERT
            time.sleep(self.BATTERY_CHECK_INTERVAL)

    @non_blocking
    def quality_changed(self, sender, **kwargs):
        self.settings.quality.state_ = const.State.BUSY
        try:
            self.camera.set_format(
                raw=self.settings.quality.raw.bool_value,
                jpeg=self.settings.quality.compress.bool_value,
            )
            self.settings.quality.state_ = const.State.OK
        except Exception:
            self.settings.quality.state_ = const.State.ALERT
