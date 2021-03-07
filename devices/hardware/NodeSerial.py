import math
import time
import json
import threading

import requests


class NodeSerial:
    def __init__(self, port, onupdate):
        self.port = port
        self.onupdate = onupdate

        self.current_position = None
        self.current_status = None

        self._last_update = None
        self.is_connected = True

    def set_position(self, position):
        self._send_command(position=position)

    def get_position(self):
        return self.current_position

    def get_status():
        return self.current_status

    def reset_position(self, position):
        self._send_command(reset=position)

    def set_speed(self, speed):
        self._send_command(speed=speed)

    def _send_command(self, **cmd):
        with open(self.port, "w") as f:
            f.write(json.dumps(cmd))

    def connect(self):
        def connection_thread():
            with open(self.port, "r") as f:
                while self.is_connected:
                    in_data = f.readline()
                    in_data = json.loads(in_data)

                    if "status" in in_data:
                        status = in_data["status"]

                        if status != self._last_update:
                            self.current_position = status["position"]
                            self.current_status = status["status"]
                            self._last_update = status
                            self.onupdate()
        
        self.is_connected = True
        th = threading.Thread(target=connection_thread)
        th.start()

    def disconnect(self):
        self.is_connected = False
