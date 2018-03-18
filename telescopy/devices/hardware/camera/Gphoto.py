import os
import threading

from telescopy import settings


class Gphoto:
    def __init__(self, model):
        self.model = model
        self.lock = threading.Lock()

    def exec_gphoto(self, cmd):
        gphoto_bin = settings.GPHOTO_PATH
        full_cmd = f'{gphoto_bin} --camera="{self.model}" --quiet {cmd}'
        self.lock.acquire()
        try:
            f = os.popen(full_cmd)
            result = f.read()
        finally:
            self.lock.release()
        return result

    def get_camera_config(self, config):
        try:
            return self._get_current_config(
                self.exec_gphoto(f'--get-config {config}')
            )
        except Exception:
            raise Exception(f'Cannot read current setting for {config}')

    def set_camera_config(self, config, value=None, index=None):
        if value is not None:
            self.exec_gphoto(f'--set-config {config}={value}')
        elif index is not None:
            self.exec_gphoto(f'--set-config-index {config}={index}')

    def _get_current_config(self, cmd_output):
        search = 'Current: '
        for line in cmd_output.splitlines():
            if line.startswith(search):
                return line[len(search):]
        raise Exception('Cannot read current setting')

    def get_time_as_string(self, time, options, bulb='bulb'):
        for opt in options:
            opt_float = self._float_from_string(opt)

            if abs(opt_float - time) < 0.00001 or time < opt_float:
                return opt

        return bulb

    def _float_from_string(self, string):
        if '/' in string:
            numerator, denominator = string.split('/')
            return float(numerator) / float(denominator)
        return float(string)
