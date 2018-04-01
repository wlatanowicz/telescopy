import os


def _to_bool(v):
    return str(v).lower()[:1] in ('t', 'y', '1')


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HTTP_PORT = 8000
PUB_DIR = os.path.join(BASE_DIR, 'pub')

GPHOTO_PATH = 'gphoto2'
FOCUSER_IP = '192.168.0.51'

ENABLE_SIMULATORS = _to_bool(os.environ.get('ENABLE_SIMULATORS', True))
