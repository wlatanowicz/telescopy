import os


def _to_bool(v):
    return str(v).lower()[:1] in ('t', 'y', '1')


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HTTP_PORT = 8000
BASE_HTTP_URL = f'http://192.168.0.50:{HTTP_PORT}/'

PUB_DIR = os.path.join(BASE_DIR, 'pub')

GPHOTO_PATH = 'gphoto2'
FOCUSER_IP = '192.168.5.51'

PHD2_IP = '192.168.5.21'
PHD2_PORT = 4400

ENABLE_SIMULATORS = _to_bool(os.environ.get('ENABLE_SIMULATORS', True))
