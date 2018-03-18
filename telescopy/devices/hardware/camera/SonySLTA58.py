import os
import tempfile

from .Gphoto import Gphoto


class SonySLTA58:

    model_name = 'Sony SLT-A58 (Control)'

    iso_mapping = {
            '100': 2,
            '200': 3,
            '400': 4,
            '800': 5,
            '1600': 6,
            '3200': 7,
        }

    eposure_times = [
        '1/4000',
        '1/3200',
        '1/2500',
        '1/2000',
        '1/1250',
        '1/1000',
        '1/800',
        '1/640',
        '1/500',
        '1/400',
        '1/320',
        '1/250',
        '1/200',
        '1/200',
        '1/160',
        '1/125',
        '1/100',
        '1/80',
        '1/60',
        '1/40',
        '1/30',
        '1/25',
        '1/20',
        '1/15',
        '1/13',
        '1/10',
        '1/8',
        '1/6',
        '1/5',
        '1/4',
        '1/3',
        '4/10',
        '5/10',
        '6/10',
        '8/10',
        '1',
        '13/10',
        '16/10',
        '2',
        '25/10',
        '32/10',
        '4',
        '5',
        '6',
        '8',
        '10',
        '13',
        '15',
        '20',
        '25',
        '30',
    ]

    bulb = 'bulb'

    extensions = ['jpg', 'arw']

    def __init__(self):
        self.gphoto = Gphoto(self.model_name)

    def expose(self, time):
        time_as_string = self.gphoto.get_time_as_string(
            time,
            self.eposure_times,
            bulb=self.bulb
        )

        self._set_speed(time_as_string)

        tempdir = tempfile.mkdtemp()

        target_file = os.path.join(tempdir, 'img')

        cmd = f'--force-overwrite --filename={target_file}.%C'

        if time_as_string == self.bulb:
            cmd += ' --set-config capture=on' \
                f' --wait-event={time}s' \
                ' --set-config capture=off' \
                ' --wait-event-and-download=10s'
        else:
            cmd += ' --capture-image-and-download'

        self.gphoto.exec_gphoto(cmd)

        result = {}

        for ext in self.extensions:
            file = f'{target_file}.{ext}'
            if os.path.exists(file):
                with open(file, mode='rb') as f:
                    result[ext] = f.read()
                os.unlink(file)

        os.rmdir(tempdir)

        return result

    def get_iso(self):
        return self.gphoto.get_camera_config('iso')

    def set_iso(self, value):
        value = str(value)
        self.gphoto.set_camera_config('iso', index=self.iso_mapping[value])

    def set_format(self, *, jpeg, raw):
        if jpeg and raw:
            format_idx = 3
        elif jpeg:
            format_idx = 1
        elif raw:
            format_idx = 2
        else:
            raise Exception()

        self.gphoto.set_camera_config('imagequality', index=format_idx)

    def get_format(self):
        res = {
            'jpeg': False,
            'raw': False,
        }

        format_val = self.gphoto.get_camera_config('imagequality')

        if format_val == 'RAW+JPEG':
            res['jpeg'] = True
            res['raw'] = True
        elif format_val == 'RAW':
            res['raw'] = True
        elif format_val == 'Standard' or format_val == 'Fine':
            res['jpeg'] = True
        else:
            raise Exception()

        return res

    def get_battery_level(self):
        return self.gphoto.get_camera_config('batterylevel')

    def get_serial_number(self):
        return self.gphoto.get_camera_config('serialnumber')

    def get_device_version(self):
        return self.gphoto.get_camera_config('deviceversion')

    def get_manufacturer(self):
        return self.gphoto.get_camera_config('manufacturer')

    def get_camera_model(self):
        return self.gphoto.get_camera_config('cameramodel')

    def _set_speed(self, speed):
        self.gphoto.set_camera_config('shutterspeed', speed)
